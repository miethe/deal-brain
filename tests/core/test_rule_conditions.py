"""
Unit tests for rule condition evaluation.

Tests all condition operators, nested groups, and edge cases.
"""

import pytest
from dealbrain_core.rules.conditions import (
    Condition,
    ConditionGroup,
    ConditionOperator,
    LogicalOperator,
    evaluate_condition,
)


class TestBasicOperators:
    """Test basic comparison operators."""

    def test_equals_operator(self):
        """Test equality comparison."""
        condition = Condition(
            field_name="cpu.cores",
            field_type="integer",
            operator=ConditionOperator.EQUALS,
            value=8
        )

        # Match
        context = {"cpu": {"cores": 8}}
        assert condition.evaluate(context) is True

        # No match
        context = {"cpu": {"cores": 6}}
        assert condition.evaluate(context) is False

    def test_not_equals_operator(self):
        """Test inequality comparison."""
        condition = Condition(
            field_name="condition",
            field_type="string",
            operator=ConditionOperator.NOT_EQUALS,
            value="new"
        )

        context = {"condition": "used"}
        assert condition.evaluate(context) is True

        context = {"condition": "new"}
        assert condition.evaluate(context) is False

    def test_greater_than_operator(self):
        """Test greater than comparison."""
        condition = Condition(
            field_name="cpu.cpu_mark_multi",
            field_type="integer",
            operator=ConditionOperator.GREATER_THAN,
            value=20000
        )

        context = {"cpu": {"cpu_mark_multi": 25000}}
        assert condition.evaluate(context) is True

        context = {"cpu": {"cpu_mark_multi": 15000}}
        assert condition.evaluate(context) is False

        context = {"cpu": {"cpu_mark_multi": 20000}}
        assert condition.evaluate(context) is False  # Not greater, equal

    def test_less_than_operator(self):
        """Test less than comparison."""
        condition = Condition(
            field_name="price_usd",
            field_type="float",
            operator=ConditionOperator.LESS_THAN,
            value=500.0
        )

        context = {"price_usd": 450.0}
        assert condition.evaluate(context) is True

        context = {"price_usd": 550.0}
        assert condition.evaluate(context) is False

    def test_greater_than_or_equal_operator(self):
        """Test >= comparison."""
        condition = Condition(
            field_name="ram_gb",
            field_type="integer",
            operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
            value=16
        )

        context = {"ram_gb": 32}
        assert condition.evaluate(context) is True

        context = {"ram_gb": 16}
        assert condition.evaluate(context) is True

        context = {"ram_gb": 8}
        assert condition.evaluate(context) is False

    def test_less_than_or_equal_operator(self):
        """Test <= comparison."""
        condition = Condition(
            field_name="tdp_w",
            field_type="integer",
            operator=ConditionOperator.LESS_THAN_OR_EQUAL,
            value=65
        )

        context = {"tdp_w": 45}
        assert condition.evaluate(context) is True

        context = {"tdp_w": 65}
        assert condition.evaluate(context) is True

        context = {"tdp_w": 95}
        assert condition.evaluate(context) is False

    def test_between_operator(self):
        """Test between operator (inclusive)."""
        condition = Condition(
            field_name="cpu.release_year",
            field_type="integer",
            operator=ConditionOperator.BETWEEN,
            value=[2020, 2023]
        )

        context = {"cpu": {"release_year": 2021}}
        assert condition.evaluate(context) is True

        context = {"cpu": {"release_year": 2020}}
        assert condition.evaluate(context) is True

        context = {"cpu": {"release_year": 2023}}
        assert condition.evaluate(context) is True

        context = {"cpu": {"release_year": 2019}}
        assert condition.evaluate(context) is False

        context = {"cpu": {"release_year": 2024}}
        assert condition.evaluate(context) is False


class TestStringOperators:
    """Test string-specific operators."""

    def test_contains_operator(self):
        """Test contains operator."""
        condition = Condition(
            field_name="primary_storage_type",
            field_type="string",
            operator=ConditionOperator.CONTAINS,
            value="NVMe"
        )

        context = {"primary_storage_type": "NVMe SSD"}
        assert condition.evaluate(context) is True

        context = {"primary_storage_type": "SATA SSD"}
        assert condition.evaluate(context) is False

    def test_starts_with_operator(self):
        """Test starts_with operator."""
        condition = Condition(
            field_name="cpu.name",
            field_type="string",
            operator=ConditionOperator.STARTS_WITH,
            value="Intel"
        )

        context = {"cpu": {"name": "Intel Core i7-12700K"}}
        assert condition.evaluate(context) is True

        context = {"cpu": {"name": "AMD Ryzen 9 5900X"}}
        assert condition.evaluate(context) is False

    def test_ends_with_operator(self):
        """Test ends_with operator."""
        condition = Condition(
            field_name="device_model",
            field_type="string",
            operator=ConditionOperator.ENDS_WITH,
            value="Pro"
        )

        context = {"device_model": "Mac Mini Pro"}
        assert condition.evaluate(context) is True

        context = {"device_model": "Mac Mini"}
        assert condition.evaluate(context) is False

    def test_regex_operator(self):
        """Test regex operator."""
        condition = Condition(
            field_name="cpu.name",
            field_type="string",
            operator=ConditionOperator.REGEX,
            value=r"i[579]-\d{4,5}[A-Z]?"
        )

        context = {"cpu": {"name": "Intel Core i7-12700K"}}
        assert condition.evaluate(context) is True

        context = {"cpu": {"name": "Intel Core i3-10100"}}
        assert condition.evaluate(context) is False


class TestSetOperators:
    """Test set membership operators."""

    def test_in_operator(self):
        """Test 'in' operator."""
        condition = Condition(
            field_name="custom.ram_generation",
            field_type="string",
            operator=ConditionOperator.IN,
            value=["DDR4", "DDR5"]
        )

        context = {"custom": {"ram_generation": "DDR5"}}
        assert condition.evaluate(context) is True

        context = {"custom": {"ram_generation": "DDR3"}}
        assert condition.evaluate(context) is False

    def test_not_in_operator(self):
        """Test 'not in' operator."""
        condition = Condition(
            field_name="condition",
            field_type="string",
            operator=ConditionOperator.NOT_IN,
            value=["parts", "for_parts"]
        )

        context = {"condition": "used"}
        assert condition.evaluate(context) is True

        context = {"condition": "parts"}
        assert condition.evaluate(context) is False


class TestNestedConditions:
    """Test nested condition groups with AND/OR logic."""

    def test_and_group(self):
        """Test AND group - all conditions must match."""
        group = ConditionGroup(
            conditions=[
                Condition(
                    field_name="cpu.cores",
                    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                    value=8
                ),
                Condition(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                    value=16
                ),
            ],
            logical_operator=LogicalOperator.AND
        )

        # Both match
        context = {"cpu": {"cores": 8}, "ram_gb": 16}
        assert group.evaluate(context) is True

        # Only first matches
        context = {"cpu": {"cores": 8}, "ram_gb": 8}
        assert group.evaluate(context) is False

        # Only second matches
        context = {"cpu": {"cores": 4}, "ram_gb": 16}
        assert group.evaluate(context) is False

        # Neither matches
        context = {"cpu": {"cores": 4}, "ram_gb": 8}
        assert group.evaluate(context) is False

    def test_or_group(self):
        """Test OR group - any condition can match."""
        group = ConditionGroup(
            conditions=[
                Condition(
                    field_name="cpu.cpu_mark_multi",
                    operator=ConditionOperator.GREATER_THAN,
                    value=30000
                ),
                Condition(
                    field_name="gpu.gpu_mark",
                    operator=ConditionOperator.GREATER_THAN,
                    value=20000
                ),
            ],
            logical_operator=LogicalOperator.OR
        )

        # Both match
        context = {"cpu": {"cpu_mark_multi": 35000}, "gpu": {"gpu_mark": 25000}}
        assert group.evaluate(context) is True

        # Only first matches
        context = {"cpu": {"cpu_mark_multi": 35000}, "gpu": {"gpu_mark": 15000}}
        assert group.evaluate(context) is True

        # Only second matches
        context = {"cpu": {"cpu_mark_multi": 25000}, "gpu": {"gpu_mark": 25000}}
        assert group.evaluate(context) is True

        # Neither matches
        context = {"cpu": {"cpu_mark_multi": 25000}, "gpu": {"gpu_mark": 15000}}
        assert group.evaluate(context) is False

    def test_deeply_nested_groups(self):
        """Test deeply nested condition groups."""
        # (cores >= 8 AND ram >= 16) OR (cpu_mark > 25000)
        group = ConditionGroup(
            conditions=[
                ConditionGroup(
                    conditions=[
                        Condition(field_name="cpu.cores", operator=ConditionOperator.GTE, value=8),
                        Condition(field_name="ram_gb", operator=ConditionOperator.GTE, value=16),
                    ],
                    logical_operator=LogicalOperator.AND
                ),
                Condition(
                    field_name="cpu.cpu_mark_multi",
                    operator=ConditionOperator.GREATER_THAN,
                    value=25000
                ),
            ],
            logical_operator=LogicalOperator.OR
        )

        # First group matches
        context = {"cpu": {"cores": 8, "cpu_mark_multi": 20000}, "ram_gb": 16}
        assert group.evaluate(context) is True

        # Second condition matches
        context = {"cpu": {"cores": 4, "cpu_mark_multi": 30000}, "ram_gb": 8}
        assert group.evaluate(context) is True

        # Both match
        context = {"cpu": {"cores": 8, "cpu_mark_multi": 30000}, "ram_gb": 16}
        assert group.evaluate(context) is True

        # Neither matches
        context = {"cpu": {"cores": 4, "cpu_mark_multi": 20000}, "ram_gb": 8}
        assert group.evaluate(context) is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_field(self):
        """Test behavior when field is missing from context."""
        condition = Condition(
            field_name="cpu.cores",
            operator=ConditionOperator.EQUALS,
            value=8
        )

        # Missing cpu object
        context = {}
        assert condition.evaluate(context) is False

        # Missing cores field
        context = {"cpu": {}}
        assert condition.evaluate(context) is False

    def test_null_value(self):
        """Test behavior with null/None values."""
        condition = Condition(
            field_name="gpu.gpu_mark",
            operator=ConditionOperator.GREATER_THAN,
            value=10000
        )

        context = {"gpu": {"gpu_mark": None}}
        assert condition.evaluate(context) is False

    def test_type_coercion(self):
        """Test automatic type coercion."""
        condition = Condition(
            field_name="ram_gb",
            field_type="integer",
            operator=ConditionOperator.EQUALS,
            value=16
        )

        # String "16" should coerce to int 16
        context = {"ram_gb": "16"}
        assert condition.evaluate(context) is True

    def test_case_insensitive_string_compare(self):
        """Test case-insensitive string comparison."""
        condition = Condition(
            field_name="condition",
            field_type="string",
            operator=ConditionOperator.EQUALS,
            value="used",
            case_sensitive=False
        )

        context = {"condition": "USED"}
        assert condition.evaluate(context) is True

        context = {"condition": "Used"}
        assert condition.evaluate(context) is True
