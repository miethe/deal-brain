"""Condition evaluation system for valuation rules"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any


class ConditionOperator(str, Enum):
    """Supported condition operators"""
    # Equality
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"

    # Comparison
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    BETWEEN = "between"

    # String
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"

    # Set
    IN = "in"
    NOT_IN = "not_in"

    # Existence
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions"""
    AND = "and"
    OR = "or"
    NOT = "not"


class Condition:
    """Individual condition that can be evaluated against a context"""

    def __init__(
        self,
        field_name: str,
        field_type: str,
        operator: ConditionOperator | str,
        value: Any = None
    ):
        self.field_name = field_name
        self.field_type = field_type
        self.operator = ConditionOperator(operator) if isinstance(operator, str) else operator
        self.value = value

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate condition against a context dictionary.

        Args:
            context: Dictionary with field values (supports nested access via dot notation)

        Returns:
            True if condition is satisfied, False otherwise
        """
        # Get field value from context (support dot notation)
        field_value = self._get_field_value(context, self.field_name)

        # Handle null checks first
        if self.operator == ConditionOperator.IS_NULL:
            return field_value is None
        if self.operator == ConditionOperator.IS_NOT_NULL:
            return field_value is not None

        # For other operators, None values fail the condition
        if field_value is None:
            return False

        # Equality operators
        if self.operator == ConditionOperator.EQUALS:
            return self._compare_equals(field_value, self.value)
        if self.operator == ConditionOperator.NOT_EQUALS:
            return not self._compare_equals(field_value, self.value)

        # Comparison operators (numeric)
        if self.operator == ConditionOperator.GREATER_THAN:
            return self._to_number(field_value) > self._to_number(self.value)
        if self.operator == ConditionOperator.LESS_THAN:
            return self._to_number(field_value) < self._to_number(self.value)
        if self.operator == ConditionOperator.GREATER_THAN_OR_EQUAL:
            return self._to_number(field_value) >= self._to_number(self.value)
        if self.operator == ConditionOperator.LESS_THAN_OR_EQUAL:
            return self._to_number(field_value) <= self._to_number(self.value)
        if self.operator == ConditionOperator.BETWEEN:
            if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                raise ValueError("BETWEEN operator requires array of [min, max]")
            num_val = self._to_number(field_value)
            return self._to_number(self.value[0]) <= num_val <= self._to_number(self.value[1])

        # String operators
        if self.operator == ConditionOperator.CONTAINS:
            return str(self.value).lower() in str(field_value).lower()
        if self.operator == ConditionOperator.STARTS_WITH:
            return str(field_value).lower().startswith(str(self.value).lower())
        if self.operator == ConditionOperator.ENDS_WITH:
            return str(field_value).lower().endswith(str(self.value).lower())
        if self.operator == ConditionOperator.REGEX:
            return bool(re.search(str(self.value), str(field_value), re.IGNORECASE))

        # Set operators
        if self.operator == ConditionOperator.IN:
            if not isinstance(self.value, (list, tuple, set)):
                raise ValueError("IN operator requires array value")
            return field_value in self.value
        if self.operator == ConditionOperator.NOT_IN:
            if not isinstance(self.value, (list, tuple, set)):
                raise ValueError("NOT_IN operator requires array value")
            return field_value not in self.value

        raise ValueError(f"Unsupported operator: {self.operator}")

    def _get_field_value(self, context: dict[str, Any], field_path: str) -> Any:
        """Get field value from context, supporting dot notation (e.g., 'cpu.cpu_mark_multi')"""
        parts = field_path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return None
            else:
                # Try to get attribute if not a dict
                value = getattr(value, part, None)
                if value is None:
                    return None

        return value

    def _compare_equals(self, a: Any, b: Any) -> bool:
        """Compare two values for equality with type coercion"""
        # Handle case-insensitive string comparison
        if isinstance(a, str) and isinstance(b, str):
            return a.lower() == b.lower()

        # Try numeric comparison if both can be numbers
        try:
            return self._to_number(a) == self._to_number(b)
        except (ValueError, TypeError):
            pass

        # Direct comparison
        return a == b

    def _to_number(self, value: Any) -> float | int:
        """Convert value to number, raising ValueError if not possible"""
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            # Try int first, then float
            try:
                if "." not in value:
                    return int(value)
                return float(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to number")
        raise TypeError(f"Cannot convert {type(value).__name__} to number")

    def to_dict(self) -> dict[str, Any]:
        """Convert condition to dictionary representation"""
        return {
            "field_name": self.field_name,
            "field_type": self.field_type,
            "operator": self.operator.value,
            "value": self.value
        }


class ConditionGroup:
    """Group of conditions combined with logical operators"""

    def __init__(
        self,
        conditions: list[Condition | "ConditionGroup"],
        logical_operator: LogicalOperator | str = LogicalOperator.AND
    ):
        self.conditions = conditions
        self.logical_operator = LogicalOperator(logical_operator) if isinstance(logical_operator, str) else logical_operator

    def evaluate(self, context: dict[str, Any]) -> bool:
        """
        Evaluate all conditions in the group with the logical operator.

        Args:
            context: Dictionary with field values

        Returns:
            True if the group conditions are satisfied, False otherwise
        """
        if not self.conditions:
            return True

        results = [cond.evaluate(context) for cond in self.conditions]

        if self.logical_operator == LogicalOperator.AND:
            return all(results)
        elif self.logical_operator == LogicalOperator.OR:
            return any(results)
        elif self.logical_operator == LogicalOperator.NOT:
            # NOT applies to the first condition only
            return not results[0] if results else True

        raise ValueError(f"Unsupported logical operator: {self.logical_operator}")

    def to_dict(self) -> dict[str, Any]:
        """Convert condition group to dictionary representation"""
        return {
            "logical_operator": self.logical_operator.value,
            "conditions": [cond.to_dict() for cond in self.conditions]
        }


def build_condition_from_dict(data: dict[str, Any]) -> Condition | ConditionGroup:
    """
    Build a Condition or ConditionGroup from dictionary representation.

    Args:
        data: Dictionary with condition data

    Returns:
        Condition or ConditionGroup instance
    """
    if "logical_operator" in data:
        # This is a condition group
        nested_conditions = [
            build_condition_from_dict(cond_data)
            for cond_data in data.get("conditions", [])
        ]
        return ConditionGroup(
            conditions=nested_conditions,
            logical_operator=data["logical_operator"]
        )
    else:
        # This is a single condition
        return Condition(
            field_name=data["field_name"],
            field_type=data["field_type"],
            operator=data["operator"],
            value=data.get("value")
        )
