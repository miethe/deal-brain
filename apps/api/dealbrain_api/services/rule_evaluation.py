"""Service for evaluating rules against listings with caching"""

from datetime import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

VALUATION_DISABLED_RULESETS_KEY = "valuation_disabled_rulesets"


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
        Evaluate a listing against one or more rulesets.

        If ruleset_id is provided, only that ruleset is evaluated.
        Otherwise, evaluates all active rulesets in priority order.

        Args:
            session: Database session
            listing_id: Listing ID to evaluate
            ruleset_id: Specific ruleset to use (optional)

        Returns:
            Dictionary with valuation results including layer attribution
        """
        # Get listing with related data
        stmt = (
            select(Listing)
            .where(Listing.id == listing_id)
            .options(
                selectinload(Listing.cpu),
                selectinload(Listing.gpu),
                selectinload(Listing.ram_spec),
                selectinload(Listing.primary_storage_profile),
                selectinload(Listing.secondary_storage_profile),
            )
        )
        result = await session.execute(stmt)
        listing = result.scalar_one_or_none()

        if not listing:
            raise ValueError(f"Listing {listing_id} not found")

        # Build context from listing (used for ruleset selection and evaluation)
        context = build_context_from_listing(listing)
        disabled_rulesets = {
            int(ruleset_id)
            for ruleset_id in (listing.attributes_json or {}).get(VALUATION_DISABLED_RULESETS_KEY, [])
            if isinstance(ruleset_id, (int, str)) and str(ruleset_id).isdigit()
        }

        # Get rulesets to evaluate
        if ruleset_id is not None:
            # Evaluate specific ruleset only
            ruleset = await self._get_ruleset(session, ruleset_id)
            if not ruleset:
                raise ValueError(f"Ruleset {ruleset_id} not found")
            rulesets_to_evaluate = [ruleset]
        else:
            # Get all applicable rulesets in priority order
            rulesets_to_evaluate = await self._get_rulesets_for_evaluation(
                session, context, disabled_rulesets
            )

        if not rulesets_to_evaluate:
            raise ValueError("No active rulesets found")

        # Evaluate all rulesets in order and combine results
        all_evaluation_results = []
        matched_rules_by_layer = {}
        total_adjustment = 0.0

        for ruleset in rulesets_to_evaluate:
            # Determine layer type from ruleset metadata
            layer_type = self._get_layer_type(ruleset)

            # Get all rules from this ruleset
            rules = await self._get_rules_from_ruleset(session, ruleset.id)

            if not rules:
                continue

            # Evaluate rules from this ruleset
            evaluation_results = self.evaluator.evaluate_ruleset(rules, context)

            # Calculate adjustment for this layer
            layer_summary = self.evaluator.calculate_total_adjustment(evaluation_results)
            layer_adjustment = layer_summary["total_adjustment"]

            # Track results by layer
            if layer_summary["matched_rules"]:
                matched_rules_by_layer[layer_type] = {
                    "ruleset_id": ruleset.id,
                    "ruleset_name": ruleset.name,
                    "priority": ruleset.priority,
                    "adjustment": layer_adjustment,
                    "matched_rules": layer_summary["matched_rules"]
                }

            # Add to cumulative results
            total_adjustment += layer_adjustment
            all_evaluation_results.extend([
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "ruleset_id": ruleset.id,
                    "ruleset_name": ruleset.name,
                    "layer": layer_type,
                    "matched": r.matched,
                    "adjustment_value": r.adjustment_value,
                    "error": r.error,
                }
                for r in evaluation_results
            ])

        # Calculate adjusted price (ensure consistent types)
        original_price = float(listing.price_usd) if listing.price_usd else 0.0
        adjusted_price = original_price + total_adjustment

        # Count total matched rules across all layers
        total_matched_rules = sum(
            len(layer["matched_rules"])
            for layer in matched_rules_by_layer.values()
        )

        return {
            "listing_id": listing_id,
            "original_price": original_price,
            "total_adjustment": total_adjustment,
            "adjusted_price": adjusted_price,
            "matched_rules_count": total_matched_rules,
            "layers": matched_rules_by_layer,  # New: breakdown by layer
            "matched_rules": self._flatten_matched_rules(matched_rules_by_layer),
            "evaluation_results": all_evaluation_results,
            "rulesets_evaluated": [
                {
                    "id": rs.id,
                    "name": rs.name,
                    "priority": rs.priority,
                    "layer": self._get_layer_type(rs)
                }
                for rs in rulesets_to_evaluate
            ]
        }

    async def evaluate_multiple_listings(
        self,
        session: AsyncSession,
        listing_ids: list[int],
        ruleset_id: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Evaluate multiple listings against rulesets.

        Args:
            session: Database session
            listing_ids: List of listing IDs
            ruleset_id: Specific ruleset to use (uses all active if None)

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
        Evaluate and apply rulesets to a listing, updating adjusted_price_usd and valuation_breakdown.

        Args:
            session: Database session
            listing_id: Listing ID
            ruleset_id: Specific ruleset to apply (uses all active if None)
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

            # Enhanced breakdown with layer attribution
            listing.valuation_breakdown = {
                "total_adjustment": result["total_adjustment"],
                "layers": result["layers"],  # Layer-by-layer breakdown
                "matched_rules": result["matched_rules"],  # Flattened list for compatibility
                "rulesets_evaluated": result["rulesets_evaluated"],
                "evaluated_at": datetime.utcnow().isoformat()
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
        Apply rulesets to all active listings in batches.

        Args:
            session: Database session
            ruleset_id: Specific ruleset to apply (uses all active if None)
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

    async def _get_rulesets_for_evaluation(
        self,
        session: AsyncSession,
        context: dict[str, Any],
        excluded_ids: set[int]
    ) -> list[ValuationRuleset]:
        """
        Get all active rulesets that should be evaluated, ordered by priority.

        This implements the multi-layered evaluation approach:
        1. System baseline rulesets (priority=5)
        2. Standard/user rulesets (priority=10+)

        Args:
            session: Database session
            context: Evaluation context for conditional ruleset matching
            excluded_ids: Set of ruleset IDs to exclude

        Returns:
            List of rulesets ordered by priority (ascending)
        """
        # Get all active rulesets ordered by priority
        stmt = (
            select(ValuationRuleset)
            .where(ValuationRuleset.is_active == True)
            .order_by(
                ValuationRuleset.priority.asc(),
                ValuationRuleset.created_at.asc()
            )
        )
        result = await session.execute(stmt)
        all_rulesets = list(result.scalars().all())

        # Filter out excluded rulesets and those that don't match context
        applicable_rulesets = []
        for ruleset in all_rulesets:
            if ruleset.id in excluded_ids:
                continue

            # Check if ruleset has conditions and if they match
            if ruleset.conditions_json:
                if not self._ruleset_matches_context(ruleset, context):
                    continue

            applicable_rulesets.append(ruleset)

        return applicable_rulesets

    async def _get_active_ruleset(
        self,
        session: AsyncSession,
        excluded_ids: set[int],
    ) -> ValuationRuleset | None:
        """Get first active ruleset (legacy single-ruleset mode)"""
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
        for ruleset in result.scalars().all():
            if ruleset.id in excluded_ids:
                continue
            return ruleset
        return None

    async def _match_ruleset_for_context(
        self,
        session: AsyncSession,
        context: dict[str, Any],
        excluded_ids: set[int],
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
            if ruleset.id in excluded_ids:
                continue
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
            if not group.is_active:
                continue
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

    def _get_layer_type(self, ruleset: ValuationRuleset) -> str:
        """
        Determine the layer type based on ruleset metadata and priority.

        Returns:
            Layer type: 'baseline', 'basic', or 'advanced'
        """
        metadata = ruleset.metadata_json or {}

        # Check if it's a system baseline ruleset
        if metadata.get("system_baseline") is True:
            return "baseline"

        # Check priority ranges (baseline=5, standard=10+)
        if ruleset.priority <= 5:
            return "baseline"
        elif ruleset.priority <= 10:
            return "basic"
        else:
            return "advanced"

    def _flatten_matched_rules(self, matched_rules_by_layer: dict[str, Any]) -> list[dict]:
        """
        Flatten the layer-based matched rules into a single list for backward compatibility.

        Args:
            matched_rules_by_layer: Dictionary of layer -> matched rules

        Returns:
            Flattened list of matched rules with layer attribution
        """
        flattened = []
        for layer_type, layer_data in matched_rules_by_layer.items():
            for rule in layer_data["matched_rules"]:
                rule_with_layer = rule.copy()
                rule_with_layer["layer"] = layer_type
                rule_with_layer["ruleset_id"] = layer_data["ruleset_id"]
                rule_with_layer["ruleset_name"] = layer_data["ruleset_name"]
                flattened.append(rule_with_layer)
        return flattened

    def clear_cache(self):
        """Clear evaluation cache"""
        self._cache = {}