"""Core logic for evaluating rules with nested conditions."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ConditionNode:
    """Tree node representing a condition or condition group."""

    field_name: str | None  # None for group nodes
    operator: str | None
    value: Any | None
    logical_operator: str  # "AND" or "OR"
    children: list["ConditionNode"] | None = None

    def is_group(self) -> bool:
        return self.field_name is None and self.children is not None

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Recursively evaluate this condition/group against context."""
        if self.is_group():
            return self._evaluate_group(context)
        else:
            return self._evaluate_condition(context)

    def _evaluate_group(self, context: dict[str, Any]) -> bool:
        """Evaluate child conditions with logical operator."""
        if not self.children:
            return True

        if self.logical_operator == "AND":
            return all(child.evaluate(context) for child in self.children)
        elif self.logical_operator == "OR":
            return any(child.evaluate(context) for child in self.children)
        else:
            raise ValueError(f"Unknown logical operator: {self.logical_operator}")

    def _evaluate_condition(self, context: dict[str, Any]) -> bool:
        """Evaluate single condition."""
        # Extract value from context using field_name (supports dot notation)
        actual_value = self._get_nested_value(context, self.field_name)

        # Apply operator comparison
        if self.operator == "equals":
            return actual_value == self.value
        elif self.operator == "not_equals":
            return actual_value != self.value
        elif self.operator == "greater_than":
            return actual_value is not None and self.value is not None and actual_value > self.value
        elif self.operator == "less_than":
            return actual_value is not None and self.value is not None and actual_value < self.value
        elif self.operator == "gte":
            return (
                actual_value is not None and self.value is not None and actual_value >= self.value
            )
        elif self.operator == "lte":
            return (
                actual_value is not None and self.value is not None and actual_value <= self.value
            )
        elif self.operator == "contains":
            return self.value in str(actual_value) if actual_value is not None else False
        elif self.operator == "starts_with":
            return (
                str(actual_value).startswith(str(self.value)) if actual_value is not None else False
            )
        elif self.operator == "ends_with":
            return (
                str(actual_value).endswith(str(self.value)) if actual_value is not None else False
            )
        elif self.operator == "in":
            return actual_value in self.value if isinstance(self.value, (list, tuple)) else False
        elif self.operator == "not_in":
            return actual_value not in self.value if isinstance(self.value, (list, tuple)) else True
        elif self.operator == "between":
            if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                return (
                    self.value[0] <= actual_value <= self.value[1]
                    if actual_value is not None
                    else False
                )
            return False
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

    @staticmethod
    def _get_nested_value(context: dict, path: str) -> Any:
        """Extract value from nested dict using dot notation."""
        if path is None:
            return None

        keys = path.split(".")
        value = context
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
        return value


def parse_conditions_tree(conditions: list[dict]) -> list[ConditionNode]:
    """Parse flat condition list into tree structure."""
    if not conditions:
        return []

    # For now, simple flat structure (Phase 1)
    # Phase 2 will handle parent_condition_id for nesting
    nodes = []
    for condition in conditions:
        node = ConditionNode(
            field_name=condition.get("field_name"),
            operator=condition.get("operator"),
            value=condition.get("value"),
            logical_operator=condition.get("logical_operator", "AND"),
        )
        nodes.append(node)

    return nodes


def evaluate_conditions(conditions: list[dict], context: dict[str, Any]) -> tuple[bool, list[dict]]:
    """
    Evaluate a list of conditions against a context.

    Returns:
        Tuple of (matched: bool, condition_results: list[dict])
    """
    if not conditions:
        return True, []

    nodes = parse_conditions_tree(conditions)
    condition_results = []

    # Evaluate each condition and track results
    all_matched = True
    for i, (node, condition) in enumerate(zip(nodes, conditions)):
        matched = node.evaluate(context)
        actual_value = node._get_nested_value(context, node.field_name)

        condition_results.append(
            {
                "condition": f"{condition.get('field_name')} {condition.get('operator')} {condition.get('value')}",
                "matched": matched,
                "actual_value": actual_value,
                "expected": condition.get("value"),
            }
        )

        # Apply logical operator
        if i == 0:
            all_matched = matched
        else:
            logical_op = condition.get("logical_operator", "AND")
            if logical_op == "AND":
                all_matched = all_matched and matched
            elif logical_op == "OR":
                all_matched = all_matched or matched

    return all_matched, condition_results


__all__ = ["ConditionNode", "parse_conditions_tree", "evaluate_conditions"]
