"""Service for previewing rule impact before applying"""

from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.rules import (
    RuleEvaluator,
    build_context_from_listing,
    build_condition_from_dict,
    build_action_from_dict,
)

from ..models.core import Listing


class RulePreviewService:
    """Service for previewing impact of valuation rules"""

    def __init__(self):
        self.evaluator = RuleEvaluator()

    async def preview_rule(
        self,
        session: AsyncSession,
        conditions: list[dict[str, Any]],
        actions: list[dict[str, Any]],
        sample_size: int = 10,
        category_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Preview impact of a rule before saving.

        Args:
            session: Database session
            conditions: List of condition dictionaries
            actions: List of action dictionaries
            sample_size: Number of sample listings to return
            category_filter: Optional filters for listing selection

        Returns:
            Dictionary with preview data including sample listings and statistics
        """
        # Get all active listings (or filtered subset)
        stmt = select(Listing).where(Listing.status == "active")

        # Apply category filters if provided
        if category_filter:
            if "device_model" in category_filter:
                stmt = stmt.where(Listing.device_model.like(f"%{category_filter['device_model']}%"))
            if "min_ram_gb" in category_filter:
                stmt = stmt.where(Listing.ram_gb >= category_filter["min_ram_gb"])
            if "cpu_manufacturer" in category_filter:
                # Would need join to CPU table
                pass

        stmt = stmt.limit(1000)  # Limit for performance
        result = await session.execute(stmt)
        listings = list(result.scalars().all())

        # Build rule dictionary for evaluation
        rule_dict = {
            "id": 0,  # Preview rule, no ID
            "name": "Preview Rule",
            "is_active": True,
            "evaluation_order": 0,
            "conditions": conditions,
            "actions": actions,
        }

        # Evaluate rule against all listings
        matching_listings = []
        non_matching_listings = []
        adjustment_values = []

        for listing in listings:
            context = build_context_from_listing(listing)
            results = self.evaluator.evaluate_ruleset([rule_dict], context)

            if results and results[0].matched:
                matching_listings.append(
                    {
                        "listing": listing,
                        "adjustment": results[0].adjustment_value,
                        "original_price": listing.price_usd,
                        "adjusted_price": listing.price_usd + results[0].adjustment_value,
                    }
                )
                adjustment_values.append(results[0].adjustment_value)
            else:
                non_matching_listings.append(listing)

        # Calculate statistics
        total_count = len(listings)
        matched_count = len(matching_listings)
        match_percentage = (matched_count / total_count * 100) if total_count > 0 else 0

        stats = {
            "total_listings_checked": total_count,
            "matched_count": matched_count,
            "match_percentage": round(match_percentage, 2),
            "non_matched_count": len(non_matching_listings),
        }

        if adjustment_values:
            stats.update(
                {
                    "avg_adjustment": round(sum(adjustment_values) / len(adjustment_values), 2),
                    "min_adjustment": round(min(adjustment_values), 2),
                    "max_adjustment": round(max(adjustment_values), 2),
                    "total_adjustment": round(sum(adjustment_values), 2),
                }
            )

        # Sample listings
        sample_matching = matching_listings[:sample_size]
        sample_non_matching = non_matching_listings[: min(3, len(non_matching_listings))]

        return {
            "statistics": stats,
            "sample_matched_listings": [
                {
                    "id": item["listing"].id,
                    "title": item["listing"].title,
                    "original_price": item["original_price"],
                    "adjustment": item["adjustment"],
                    "adjusted_price": item["adjusted_price"],
                    "price_change_pct": round(
                        (
                            (item["adjustment"] / item["original_price"] * 100)
                            if item["original_price"] > 0
                            else 0
                        ),
                        2,
                    ),
                }
                for item in sample_matching
            ],
            "sample_non_matched_listings": [
                {
                    "id": listing.id,
                    "title": listing.title,
                    "price_usd": listing.price_usd,
                }
                for listing in sample_non_matching
            ],
        }

    async def preview_ruleset(
        self, session: AsyncSession, ruleset_id: int, sample_size: int = 10
    ) -> dict[str, Any]:
        """
        Preview impact of an entire ruleset.

        Args:
            session: Database session
            ruleset_id: Ruleset ID to preview
            sample_size: Number of sample listings

        Returns:
            Preview data with aggregated statistics
        """
        from .rule_evaluation import RuleEvaluationService

        eval_service = RuleEvaluationService()

        # Get sample of active listings
        stmt = (
            select(Listing)
            .where(Listing.status == "active")
            .limit(100)  # Sample 100 listings for preview
        )
        result = await session.execute(stmt)
        listings = list(result.scalars().all())

        # Evaluate each listing
        evaluation_results = []
        for listing in listings:
            try:
                result = await eval_service.evaluate_listing(session, listing.id, ruleset_id)
                evaluation_results.append(result)
            except Exception as e:
                # Skip listings that fail evaluation
                pass

        # Calculate statistics
        if not evaluation_results:
            return {
                "statistics": {
                    "total_listings_checked": len(listings),
                    "evaluated_count": 0,
                },
                "sample_results": [],
            }

        adjustments = [r["total_adjustment"] for r in evaluation_results]
        matched_rules_counts = [r["matched_rules_count"] for r in evaluation_results]

        stats = {
            "total_listings_checked": len(listings),
            "evaluated_count": len(evaluation_results),
            "avg_adjustment": round(sum(adjustments) / len(adjustments), 2),
            "min_adjustment": round(min(adjustments), 2),
            "max_adjustment": round(max(adjustments), 2),
            "total_adjustment": round(sum(adjustments), 2),
            "avg_rules_matched": round(sum(matched_rules_counts) / len(matched_rules_counts), 2),
        }

        # Sample results
        sample_results = evaluation_results[:sample_size]

        return {
            "statistics": stats,
            "sample_results": [
                {
                    "listing_id": r["listing_id"],
                    "original_price": r["original_price"],
                    "adjusted_price": r["adjusted_price"],
                    "total_adjustment": r["total_adjustment"],
                    "matched_rules_count": r["matched_rules_count"],
                    "price_change_pct": round(
                        (
                            (r["total_adjustment"] / r["original_price"] * 100)
                            if r["original_price"] > 0
                            else 0
                        ),
                        2,
                    ),
                }
                for r in sample_results
            ],
        }

    async def compare_rulesets(
        self, session: AsyncSession, ruleset_id_a: int, ruleset_id_b: int, sample_size: int = 50
    ) -> dict[str, Any]:
        """
        Compare impact of two rulesets.

        Args:
            session: Database session
            ruleset_id_a: First ruleset ID
            ruleset_id_b: Second ruleset ID
            sample_size: Number of listings to compare

        Returns:
            Comparison data
        """
        from .rule_evaluation import RuleEvaluationService

        eval_service = RuleEvaluationService()

        # Get sample listings
        stmt = select(Listing).where(Listing.status == "active").limit(sample_size)
        result = await session.execute(stmt)
        listings = list(result.scalars().all())

        # Evaluate with both rulesets
        comparisons = []

        for listing in listings:
            try:
                result_a = await eval_service.evaluate_listing(session, listing.id, ruleset_id_a)
                result_b = await eval_service.evaluate_listing(session, listing.id, ruleset_id_b)

                difference = result_b["adjusted_price"] - result_a["adjusted_price"]

                comparisons.append(
                    {
                        "listing_id": listing.id,
                        "original_price": listing.price_usd,
                        "ruleset_a_adjusted": result_a["adjusted_price"],
                        "ruleset_b_adjusted": result_b["adjusted_price"],
                        "difference": round(difference, 2),
                        "difference_pct": round(
                            (difference / listing.price_usd * 100) if listing.price_usd > 0 else 0,
                            2,
                        ),
                    }
                )
            except Exception:
                pass

        # Calculate aggregate statistics
        if not comparisons:
            return {"statistics": {}, "comparisons": []}

        differences = [c["difference"] for c in comparisons]

        stats = {
            "listings_compared": len(comparisons),
            "avg_difference": round(sum(differences) / len(differences), 2),
            "min_difference": round(min(differences), 2),
            "max_difference": round(max(differences), 2),
            "ruleset_a_higher_count": sum(1 for d in differences if d < 0),
            "ruleset_b_higher_count": sum(1 for d in differences if d > 0),
            "equal_count": sum(1 for d in differences if d == 0),
        }

        return {
            "statistics": stats,
            "comparisons": comparisons[:20],  # Return top 20
        }
