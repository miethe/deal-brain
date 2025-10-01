"""Rule evaluator orchestrates condition checking and action execution"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actions import Action, ActionEngine
from .conditions import Condition, ConditionGroup
from .formula import FormulaEngine


@dataclass
class RuleEvaluationResult:
    """Result of evaluating a rule against a listing"""
    rule_id: int
    rule_name: str
    matched: bool
    adjustment_value: float = 0.0
    breakdown: list[dict[str, Any]] | None = None
    error: str | None = None


class RuleEvaluator:
    """Orchestrates rule evaluation: condition checking + action execution"""

    def __init__(self, formula_engine: FormulaEngine | None = None):
        self.formula_engine = formula_engine or FormulaEngine()
        self.action_engine = ActionEngine(self.formula_engine)

    def evaluate_rule(
        self,
        rule_id: int,
        rule_name: str,
        conditions: Condition | ConditionGroup | list[Condition | ConditionGroup],
        actions: list[Action],
        context: dict[str, Any],
        is_active: bool = True
    ) -> RuleEvaluationResult:
        """
        Evaluate a single rule against a context.

        Args:
            rule_id: Rule identifier
            rule_name: Rule name for reporting
            conditions: Condition, ConditionGroup, or list of conditions
            actions: List of Action instances
            context: Context dictionary with listing data
            is_active: Whether the rule is active

        Returns:
            RuleEvaluationResult with match status and calculated value
        """
        # Skip inactive rules
        if not is_active:
            return RuleEvaluationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                matched=False,
                adjustment_value=0.0
            )

        try:
            # Check conditions
            matched = self._evaluate_conditions(conditions, context)

            if not matched:
                return RuleEvaluationResult(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    matched=False,
                    adjustment_value=0.0
                )

            # Execute actions
            action_result = self.action_engine.execute_actions(actions, context)

            return RuleEvaluationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                matched=True,
                adjustment_value=action_result["total_adjustment"],
                breakdown=action_result["breakdown"]
            )

        except Exception as e:
            return RuleEvaluationResult(
                rule_id=rule_id,
                rule_name=rule_name,
                matched=False,
                adjustment_value=0.0,
                error=str(e)
            )

    def _evaluate_conditions(
        self,
        conditions: Condition | ConditionGroup | list[Condition | ConditionGroup],
        context: dict[str, Any]
    ) -> bool:
        """
        Evaluate conditions (single, group, or list).

        Args:
            conditions: Condition(s) to evaluate
            context: Context dictionary

        Returns:
            True if all conditions are satisfied
        """
        if not conditions:
            return True

        if isinstance(conditions, (Condition, ConditionGroup)):
            return conditions.evaluate(context)

        if isinstance(conditions, list):
            # List of conditions - treat as AND group
            return all(cond.evaluate(context) for cond in conditions)

        raise ValueError(f"Unsupported conditions type: {type(conditions)}")

    def evaluate_ruleset(
        self,
        rules: list[dict[str, Any]],
        context: dict[str, Any],
        stop_on_first_match: bool = False
    ) -> list[RuleEvaluationResult]:
        """
        Evaluate multiple rules in a ruleset.

        Args:
            rules: List of rule dictionaries with id, name, conditions, actions, is_active
            context: Context dictionary with listing data
            stop_on_first_match: If True, stop after first matching rule

        Returns:
            List of RuleEvaluationResult for each rule
        """
        results = []

        # Sort rules by evaluation_order if present
        sorted_rules = sorted(
            rules,
            key=lambda r: r.get("evaluation_order", r.get("priority", 100))
        )

        for rule_dict in sorted_rules:
            # Build conditions and actions from dict
            from .conditions import build_condition_from_dict
            from .actions import build_action_from_dict

            conditions = None
            if "conditions" in rule_dict and rule_dict["conditions"]:
                if isinstance(rule_dict["conditions"], list):
                    conditions = [
                        build_condition_from_dict(cond) for cond in rule_dict["conditions"]
                    ]
                else:
                    conditions = build_condition_from_dict(rule_dict["conditions"])

            actions = [
                build_action_from_dict(action) for action in rule_dict.get("actions", [])
            ]

            result = self.evaluate_rule(
                rule_id=rule_dict["id"],
                rule_name=rule_dict["name"],
                conditions=conditions,
                actions=actions,
                context=context,
                is_active=rule_dict.get("is_active", True)
            )

            results.append(result)

            if stop_on_first_match and result.matched:
                break

        return results

    def calculate_total_adjustment(
        self,
        evaluation_results: list[RuleEvaluationResult]
    ) -> dict[str, Any]:
        """
        Calculate total adjustment from multiple rule evaluations.

        Args:
            evaluation_results: List of RuleEvaluationResult

        Returns:
            Dictionary with total_adjustment and detailed breakdown
        """
        total = 0.0
        matched_rules = []

        for result in evaluation_results:
            if result.matched and not result.error:
                total += result.adjustment_value
                matched_rules.append({
                    "rule_id": result.rule_id,
                    "rule_name": result.rule_name,
                    "adjustment": result.adjustment_value,
                    "breakdown": result.breakdown
                })

        return {
            "total_adjustment": total,
            "matched_rules_count": len(matched_rules),
            "matched_rules": matched_rules
        }


def build_context_from_listing(listing: Any) -> dict[str, Any]:
    """
    Build evaluation context from a listing object.

    Args:
        listing: Listing model instance or dictionary

    Returns:
        Context dictionary suitable for rule evaluation
    """
    if isinstance(listing, dict):
        return listing

    # Convert model instance to dict
    context = {}

    # Core listing fields
    for field in [
        "id", "title", "price_usd", "condition", "status",
        "ram_gb", "ram_notes",
        "primary_storage_gb", "primary_storage_type",
        "secondary_storage_gb", "secondary_storage_type",
        "os_license", "device_model",
        "adjusted_price_usd"
    ]:
        if hasattr(listing, field):
            context[field] = getattr(listing, field)

    # CPU data (nested)
    if hasattr(listing, "cpu") and listing.cpu:
        context["cpu"] = {
            "id": listing.cpu.id,
            "name": listing.cpu.name,
            "manufacturer": listing.cpu.manufacturer,
            "socket": listing.cpu.socket,
            "cores": listing.cpu.cores,
            "threads": listing.cpu.threads,
            "tdp_w": listing.cpu.tdp_w,
            "igpu_model": listing.cpu.igpu_model,
            "cpu_mark_multi": listing.cpu.cpu_mark_multi,
            "cpu_mark_single": listing.cpu.cpu_mark_single,
            "release_year": listing.cpu.release_year,
        }

    # GPU data (nested)
    if hasattr(listing, "gpu") and listing.gpu:
        context["gpu"] = {
            "id": listing.gpu.id,
            "name": listing.gpu.name,
            "manufacturer": listing.gpu.manufacturer,
            "gpu_mark": listing.gpu.gpu_mark,
            "metal_score": listing.gpu.metal_score,
        }

    # Custom fields from attributes_json
    if hasattr(listing, "attributes_json") and listing.attributes_json:
        context["custom"] = listing.attributes_json

    return context
