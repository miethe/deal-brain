"""Service for evaluating rules against listings with caching"""

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_core.rules import (
    RuleEvaluator,
    build_context_from_listing,
    Action,
    Condition,
    ConditionGroup,
    build_condition_from_dict,
    build_action_from_dict,
)

from ..models.core import (
    ValuationRuleset,
    ValuationRuleGroup,
    ValuationRuleV2,
    Listing,
)


class RuleEvaluationService:
    """Service for evaluating valuation rules against listings"""

    def __init__(self):
        self.evaluator = RuleEvaluator()
        self._cache = {}  # Simple in-memory cache (TODO: use Redis in production)

    async def evaluate_listing(
        self,
        session: AsyncSession,
        listing_id: int,
        ruleset_id: int | None = None
    ) -> dict[str, Any]:
        """
        Evaluate a listing against a ruleset.

        Args:
            session: Database session
            listing_id: Listing ID to evaluate
            ruleset_id: Ruleset to use (uses active ruleset if None)

        Returns:
            Dictionary with valuation results
        """
        # Get listing with related data
        stmt = select(Listing).where(Listing.id == listing_id)
        result = await session.execute(stmt)
        listing = result.scalar_one_or_none()

        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # Build context from listing (used for ruleset selection and evaluation)
        context = build_context_from_listing(listing)

        # Get ruleset
        if ruleset_id is None:
            ruleset = None
            if listing.ruleset_id:
                ruleset = await self._get_ruleset(session, listing.ruleset_id)
                if ruleset and not ruleset.is_active:
                    ruleset = None

            if not ruleset:
                ruleset = await self._match_ruleset_for_context(session, context)

            if not ruleset:
                ruleset = await self._get_active_ruleset(session)
        else:
            ruleset = await self._get_ruleset(session, ruleset_id)

        if not ruleset:
            raise ValueError("No active ruleset found")

        # Get all rules from ruleset
        rules = await self._get_rules_from_ruleset(session, ruleset.id)

        # Evaluate rules
        evaluation_results = self.evaluator.evaluate_ruleset(rules, context)

        # Calculate total adjustment
        summary = self.evaluator.calculate_total_adjustment(evaluation_results)

        # Calculate adjusted price
        original_price = listing.price_usd
        total_adjustment = summary["total_adjustment"]
        adjusted_price = original_price + total_adjustment

        return {
            "listing_id": listing_id,
            "original_price": original_price,
            "total_adjustment": total_adjustment,
            "adjusted_price": adjusted_price,
            "ruleset_id": ruleset.id,
            "ruleset_name": ruleset.name,
            "matched_rules_count": summary["matched_rules_count"],
            "matched_rules": summary["matched_rules"],
            "evaluation_results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "matched": r.matched,
                    "adjustment_value": r.adjustment_value,
                    "error": r.error,
                }
                for r in evaluation_results
            ]
        }

    async def evaluate_multiple_listings(
        self,
        session: AsyncSession,
        listing_ids: list[int],
        ruleset_id: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Evaluate multiple listings against a ruleset.

        Args:
            session: Database session
            listing_ids: List of listing IDs
            ruleset_id: Ruleset to use (uses active ruleset if None)

        Returns:
            List of evaluation results
        """
        results = []

        for listing_id in listing_ids:
            try:
                result = await self.evaluate_listing(session, listing_id, ruleset_id)
                results.append(result)
            except Exception as e:
                results.append({
                    "listing_id": listing_id,
                    "error": str(e)
                })

        return results

    async def apply_ruleset_to_listing(
        self,
        session: AsyncSession,
        listing_id: int,
        ruleset_id: int | None = None,
        commit: bool = True
    ) -> dict[str, Any]:
        """
        Evaluate and apply ruleset to a listing, updating adjusted_price_usd and valuation_breakdown.

        Args:
            session: Database session
            listing_id: Listing ID
            ruleset_id: Ruleset to apply
            commit: Whether to commit changes

        Returns:
            Evaluation result
        """
        # Evaluate
        result = await self.evaluate_listing(session, listing_id, ruleset_id)

        # Update listing
        stmt = select(Listing).where(Listing.id == listing_id)
        db_result = await session.execute(stmt)
        listing = db_result.scalar_one_or_none()

        if listing:
            listing.adjusted_price_usd = result["adjusted_price"]
            listing.valuation_breakdown = {
                "ruleset_id": result["ruleset_id"],
                "ruleset_name": result["ruleset_name"],
                "total_adjustment": result["total_adjustment"],
                "matched_rules": result["matched_rules"],
            }

            if commit:
                await session.commit()
                await session.refresh(listing)

        return result

    async def apply_ruleset_to_all_listings(
        self,
        session: AsyncSession,
        ruleset_id: int | None = None,
        batch_size: int = 100
    ) -> dict[str, Any]:
        """
        Apply ruleset to all active listings in batches.

        Args:
            session: Database session
            ruleset_id: Ruleset to apply
            batch_size: Number of listings to process at once

        Returns:
            Summary of application
        """
        # Get all active listings
        stmt = select(Listing).where(Listing.status == "active")
        result = await session.execute(stmt)
        all_listings = list(result.scalars().all())

        processed = 0
        succeeded = 0
        failed = 0
        errors = []

        # Process in batches
        for i in range(0, len(all_listings), batch_size):
            batch = all_listings[i:i + batch_size]

            for listing in batch:
                try:
                    await self.apply_ruleset_to_listing(
                        session, listing.id, ruleset_id, commit=False
                    )
                    succeeded += 1
                except Exception as e:
                    failed += 1
                    errors.append({
                        "listing_id": listing.id,
                        "error": str(e)
                    })

                processed += 1

            # Commit batch
            await session.commit()

        return {
            "total_listings": len(all_listings),
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors[:10],  # Return first 10 errors
        }

    # --- Helper methods ---

    async def _get_ruleset(
        self,
        session: AsyncSession,
        ruleset_id: int
    ) -> ValuationRuleset | None:
        """Get ruleset by ID"""
        stmt = select(ValuationRuleset).where(ValuationRuleset.id == ruleset_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_active_ruleset(
        self,
        session: AsyncSession
    ) -> ValuationRuleset | None:
        """Get first active ruleset"""
        stmt = (
            select(ValuationRuleset)
            .where(ValuationRuleset.is_active == True)
            .order_by(
                ValuationRuleset.priority.asc(),
                ValuationRuleset.created_at.asc(),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _match_ruleset_for_context(
        self,
        session: AsyncSession,
        context: dict[str, Any],
    ) -> ValuationRuleset | None:
        """Find the highest priority active ruleset whose conditions match the provided context."""
        stmt = (
            select(ValuationRuleset)
            .where(ValuationRuleset.is_active == True)
            .order_by(
                ValuationRuleset.priority.asc(),
                ValuationRuleset.created_at.asc(),
            )
        )
        result = await session.execute(stmt)
        for ruleset in result.scalars().all():
            if self._ruleset_matches_context(ruleset, context):
                return ruleset
        return None

    def _ruleset_matches_context(
        self,
        ruleset: ValuationRuleset,
        context: dict[str, Any],
    ) -> bool:
        """Evaluate a ruleset's condition tree against the provided context."""
        conditions_data = ruleset.conditions_json or {}
        if not conditions_data:
            return True

        try:
            condition_obj = build_condition_from_dict(conditions_data)
        except Exception:
            # Invalid condition payloads should not break evaluation; treat as non-match.
            return False

        if isinstance(condition_obj, ConditionGroup):
            return condition_obj.evaluate(context)
        return condition_obj.evaluate(context)

    async def _get_rules_from_ruleset(
        self,
        session: AsyncSession,
        ruleset_id: int
    ) -> list[dict[str, Any]]:
        """
        Get all rules from a ruleset formatted for evaluation.

        Returns:
            List of rule dictionaries ready for RuleEvaluator
        """
        # Get all groups in ruleset
        groups_stmt = (
            select(ValuationRuleGroup)
            .where(ValuationRuleGroup.ruleset_id == ruleset_id)
            .order_by(ValuationRuleGroup.display_order)
        )
        groups_result = await session.execute(groups_stmt)
        groups = list(groups_result.scalars().all())

        # Get all rules from all groups
        all_rules = []

        for group in groups:
            rules_stmt = (
                select(ValuationRuleV2)
                .where(ValuationRuleV2.group_id == group.id)
                .where(ValuationRuleV2.is_active == True)
                .order_by(ValuationRuleV2.evaluation_order)
            )
            rules_result = await session.execute(rules_stmt)
            rules = list(rules_result.scalars().all())

            for rule in rules:
                all_rules.append({
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "priority": rule.priority,
                    "evaluation_order": rule.evaluation_order,
                    "is_active": rule.is_active,
                    "conditions": [
                        {
                            "field_name": c.field_name,
                            "field_type": c.field_type,
                            "operator": c.operator,
                            "value": c.value_json,
                            "logical_operator": c.logical_operator,
                        }
                        for c in rule.conditions
                    ],
                    "actions": [
                        {
                            "action_type": a.action_type,
                            "metric": a.metric,
                            "value_usd": float(a.value_usd) if a.value_usd else None,
                            "unit_type": a.unit_type,
                            "formula": a.formula,
                            "modifiers": a.modifiers_json,
                        }
                        for a in rule.actions
                    ],
                })

        return all_rules

    def clear_cache(self):
        """Clear evaluation cache"""
        self._cache = {}
