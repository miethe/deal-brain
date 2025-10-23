"""Action system for valuation rules"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Supported action types for valuation rules"""
    FIXED_VALUE = "fixed_value"  # Set specific dollar amount
    PER_UNIT = "per_unit"  # Value based on quantity (per-GB, per-core, etc.)
    BENCHMARK_BASED = "benchmark_based"  # Value proportional to performance score
    MULTIPLIER = "multiplier"  # Apply percentage to base value
    ADDITIVE = "additive"  # Add/subtract fixed amount
    FORMULA = "formula"  # Custom calculation


class Action:
    """Valuation action that calculates an adjustment value"""

    def __init__(
        self,
        action_type: ActionType | str,
        metric: str | None = None,
        value_usd: float | None = None,
        unit_type: str | None = None,
        formula: str | None = None,
        modifiers: dict[str, Any] | None = None,
    ):
        self.action_type = ActionType(action_type) if isinstance(action_type, str) else action_type
        self.metric = metric
        self.value_usd = value_usd
        self.unit_type = unit_type
        self.formula = formula
        self.modifiers = modifiers or {}

    def calculate(self, context: dict[str, Any], formula_engine: Any = None) -> float:
        """
        Calculate the valuation adjustment based on the action type.

        Args:
            context: Dictionary with listing data (supports dot notation)
            formula_engine: Optional formula engine for custom formulas

        Returns:
            Calculated adjustment value in USD
        """
        base_value = 0.0

        if self.action_type == ActionType.FIXED_VALUE:
            base_value = self.value_usd or 0.0

        elif self.action_type == ActionType.PER_UNIT:
            # Get quantity from context based on metric
            quantity = self._get_quantity(context, self.metric or "quantity")
            base_value = quantity * (self.value_usd or 0.0)

        elif self.action_type == ActionType.BENCHMARK_BASED:
            # Value proportional to benchmark score
            score = self._get_field_value(context, self.metric or "score")
            unit_divisor = self._parse_unit_divisor(self.unit_type or "per_1000_points")
            base_value = (score / unit_divisor) * (self.value_usd or 0.0)

        elif self.action_type == ActionType.MULTIPLIER:
            # Apply multiplier to existing base value
            base_amount = self._get_field_value(context, "adjusted_price_usd") or 0.0
            # Use explicit None check to distinguish 0.0 (no adjustment) from unset (100% default)
            multiplier = (self.value_usd if self.value_usd is not None else 100.0) / 100.0
            base_value = base_amount * multiplier

        elif self.action_type == ActionType.ADDITIVE:
            # Add or subtract fixed amount
            base_value = self.value_usd or 0.0

        elif self.action_type == ActionType.FORMULA:
            # Custom formula calculation
            if formula_engine is None:
                raise ValueError("Formula engine required for FORMULA action type")
            base_value = formula_engine.evaluate(self.formula or "", context)

        else:
            raise ValueError(f"Unsupported action type: {self.action_type}")

        # Apply modifiers (e.g., condition multipliers)
        return self._apply_modifiers(base_value, context)

    def _get_field_value(self, context: dict[str, Any], field_path: str) -> Any:
        """Get field value from context, supporting dot notation"""
        parts = field_path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return None
            else:
                value = getattr(value, part, None)
                if value is None:
                    return None

        return value

    def _get_quantity(self, context: dict[str, Any], metric: str) -> float:
        """Get quantity value based on metric type"""
        # Map common metrics to context fields
        metric_map = {
            "per_gb": "ram_gb",
            "per_tb": "primary_storage_gb",
             "per_ram_spec_gb": "ram_spec.total_capacity_gb",
            "per_ram_speed": "ram_spec.speed_mhz",
            "per_primary_storage_gb": "storage.primary.capacity_gb",
            "per_secondary_storage_gb": "storage.secondary.capacity_gb",
            "per_core": "cpu.cores",
            "per_thread": "cpu.threads",
            "quantity": "quantity",
        }

        field_name = metric_map.get(metric, metric)
        value = self._get_field_value(context, field_name)

        # Convert storage to TB if needed
        if metric == "per_tb" and value:
            value = value / 1000.0

        return float(value or 0)

    def _parse_unit_divisor(self, unit_type: str) -> float:
        """Parse unit type to get divisor (e.g., 'per_1000_points' -> 1000)"""
        if "1000" in unit_type:
            return 1000.0
        elif "100" in unit_type:
            return 100.0
        elif "10" in unit_type:
            return 10.0
        return 1.0

    def _apply_field_multipliers(self, base_value: float, context: dict[str, Any]) -> float:
        """
        Apply field-based multipliers from modifiers['multipliers'] array.

        Each multiplier config:
        {
          "name": "RAM Generation Multiplier",
          "field": "ram_spec.ddr_generation",
          "conditions": [
            {"value": "ddr3", "multiplier": 0.7},
            {"value": "ddr4", "multiplier": 1.0}
          ]
        }

        Args:
            base_value: The base value to apply multipliers to
            context: Dictionary with listing data (supports dot notation)

        Returns:
            Value with all field multipliers applied
        """
        if "multipliers" not in self.modifiers:
            return base_value

        total_multiplier = 1.0

        for multiplier_config in self.modifiers["multipliers"]:
            if not isinstance(multiplier_config, dict):
                logger.warning(f"Invalid multiplier config (not a dict): {multiplier_config}")
                continue

            field_path = multiplier_config.get("field")
            if not field_path:
                logger.warning(f"Multiplier config missing 'field': {multiplier_config}")
                continue

            # Get field value using dot notation (e.g., "ram_spec.ddr_generation")
            field_value = self._get_field_value(context, field_path)
            if field_value is None:
                logger.debug(
                    f"Field '{field_path}' not found in context for multiplier "
                    f"'{multiplier_config.get('name', 'unnamed')}', skipping"
                )
                continue

            # Find matching condition
            conditions = multiplier_config.get("conditions", [])
            if not isinstance(conditions, list):
                logger.warning(f"Multiplier config 'conditions' is not a list: {conditions}")
                continue

            for condition in conditions:
                if not isinstance(condition, dict):
                    continue

                condition_value = condition.get("value")
                if condition_value is None:
                    continue

                # Case-insensitive string comparison
                if str(field_value).lower() == str(condition_value).lower():
                    multiplier = condition.get("multiplier", 1.0)
                    total_multiplier *= multiplier
                    logger.debug(
                        f"Applied {multiplier_config.get('name', 'unnamed multiplier')} multiplier: "
                        f"{multiplier} (field={field_path}, value={field_value})"
                    )
                    break

        return base_value * total_multiplier

    def _apply_modifiers(self, base_value: float, context: dict[str, Any]) -> float:
        """
        Apply all modifiers to the base value in the correct order.

        Order of application:
        1. Field-based multipliers (dynamic, e.g., RAM generation)
        2. Condition multipliers (new, refurb, used)
        3. Age depreciation
        4. Brand/model multipliers

        Args:
            base_value: The base value to modify
            context: Dictionary with listing data

        Returns:
            Fully adjusted value with all modifiers applied
        """
        adjusted_value = base_value

        # 1. Apply field-based multipliers first (new feature)
        adjusted_value = self._apply_field_multipliers(adjusted_value, context)

        # 2. Apply condition multipliers (fixed bug - no "condition_" prefix)
        condition = self._get_field_value(context, "condition")
        if condition and "condition_multipliers" in self.modifiers:
            condition_key = condition.lower()
            multiplier = self.modifiers["condition_multipliers"].get(condition_key, 1.0)
            if multiplier != 1.0:
                logger.debug(f"Applied condition multiplier {multiplier} for condition '{condition}'")
                adjusted_value *= multiplier

        # 3. Apply age depreciation
        if "age_curve" in self.modifiers:
            age_years = self._get_field_value(context, "age_years") or 0
            age_curve = self.modifiers["age_curve"]
            # Simple linear depreciation for now
            if isinstance(age_curve, dict) and "rate_per_year" in age_curve:
                depreciation = min(age_years * age_curve["rate_per_year"], age_curve.get("max", 0.5))
                if depreciation > 0:
                    logger.debug(f"Applied age depreciation {depreciation:.2%} for {age_years} years")
                    adjusted_value *= (1.0 - depreciation)

        # 4. Apply brand/model multipliers
        if "brand_multipliers" in self.modifiers:
            brand = self._get_field_value(context, "brand") or self._get_field_value(context, "manufacturer")
            if brand:
                multiplier = self.modifiers["brand_multipliers"].get(brand.lower(), 1.0)
                if multiplier != 1.0:
                    logger.debug(f"Applied brand multiplier {multiplier} for brand '{brand}'")
                    adjusted_value *= multiplier

        # Log final result if any modifiers were applied
        if adjusted_value != base_value:
            logger.debug(f"Modifier application: {base_value:.2f} -> {adjusted_value:.2f}")

        return adjusted_value

    def to_dict(self) -> dict[str, Any]:
        """Convert action to dictionary representation"""
        return {
            "action_type": self.action_type.value,
            "metric": self.metric,
            "value_usd": self.value_usd,
            "unit_type": self.unit_type,
            "formula": self.formula,
            "modifiers": self.modifiers,
        }


class ActionEngine:
    """Engine for executing multiple actions and combining results"""

    def __init__(self, formula_engine: Any = None):
        self.formula_engine = formula_engine

    def execute_actions(
        self,
        actions: list[Action],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute multiple actions and return combined results.

        Args:
            actions: List of Action instances to execute
            context: Context dictionary with listing data

        Returns:
            Dictionary with:
                - total_adjustment: Sum of all action values
                - breakdown: List of individual action results
        """
        breakdown = []
        total_adjustment = 0.0

        for action in actions:
            try:
                value = action.calculate(context, self.formula_engine)
                breakdown.append({
                    "action_type": action.action_type.value,
                    "metric": action.metric,
                    "value": value,
                    "details": action.to_dict()
                })
                total_adjustment += value
            except Exception as e:
                breakdown.append({
                    "action_type": action.action_type.value,
                    "metric": action.metric,
                    "value": 0.0,
                    "error": str(e)
                })

        return {
            "total_adjustment": total_adjustment,
            "breakdown": breakdown
        }


def build_action_from_dict(data: dict[str, Any]) -> Action:
    """
    Build an Action from dictionary representation.

    Args:
        data: Dictionary with action data

    Returns:
        Action instance
    """
    return Action(
        action_type=data["action_type"],
        metric=data.get("metric"),
        value_usd=data.get("value_usd"),
        unit_type=data.get("unit_type"),
        formula=data.get("formula"),
        modifiers=data.get("modifiers"),
    )
