"""
Comprehensive tests for action multipliers system.

Tests cover:
- Field-based multipliers (dynamic, e.g., RAM generation)
- Condition multipliers (fixed bug)
- Multiple multipliers stacking
- Edge cases and error handling
"""
from dealbrain_core.rules.actions import Action, ActionType


class TestFieldMultipliers:
    """Test field-based multipliers functionality"""

    def test_single_field_multiplier_applied(self):
        """Test a single field multiplier is correctly applied"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "RAM Generation Multiplier",
                        "field": "ram_spec.ddr_generation",
                        "conditions": [
                            {"value": "ddr3", "multiplier": 0.7},
                            {"value": "ddr4", "multiplier": 1.0},
                            {"value": "ddr5", "multiplier": 1.3},
                        ],
                    }
                ]
            },
        )

        # Test DDR3 (0.7x multiplier)
        context = {"ram_spec": {"ddr_generation": "ddr3"}}
        result = action.calculate(context)
        assert result == 70.0, f"Expected 70.0, got {result}"

        # Test DDR4 (1.0x multiplier - no change)
        context = {"ram_spec": {"ddr_generation": "ddr4"}}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0, got {result}"

        # Test DDR5 (1.3x multiplier)
        context = {"ram_spec": {"ddr_generation": "ddr5"}}
        result = action.calculate(context)
        assert result == 130.0, f"Expected 130.0, got {result}"

    def test_multiple_field_multipliers_stacking(self):
        """Test multiple field multipliers stack multiplicatively"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "RAM Generation Multiplier",
                        "field": "ram_spec.ddr_generation",
                        "conditions": [
                            {"value": "ddr3", "multiplier": 0.8},
                            {"value": "ddr4", "multiplier": 1.0},
                        ],
                    },
                    {
                        "name": "Storage Type Multiplier",
                        "field": "storage.primary.type",
                        "conditions": [
                            {"value": "hdd", "multiplier": 0.5},
                            {"value": "ssd", "multiplier": 1.0},
                            {"value": "nvme", "multiplier": 1.2},
                        ],
                    },
                ]
            },
        )

        # Test DDR3 (0.8x) + HDD (0.5x) = 0.4x = $40
        context = {
            "ram_spec": {"ddr_generation": "ddr3"},
            "storage": {"primary": {"type": "hdd"}},
        }
        result = action.calculate(context)
        assert result == 40.0, f"Expected 40.0 (100 * 0.8 * 0.5), got {result}"

        # Test DDR4 (1.0x) + NVMe (1.2x) = 1.2x = $120
        context = {
            "ram_spec": {"ddr_generation": "ddr4"},
            "storage": {"primary": {"type": "nvme"}},
        }
        result = action.calculate(context)
        assert result == 120.0, f"Expected 120.0 (100 * 1.0 * 1.2), got {result}"

    def test_field_multiplier_case_insensitive(self):
        """Test field multipliers work with different cases"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Form Factor Multiplier",
                        "field": "form_factor",
                        "conditions": [
                            {"value": "mini", "multiplier": 1.2},
                            {"value": "micro", "multiplier": 1.1},
                        ],
                    }
                ]
            },
        )

        # Test various cases
        for form_factor in ["MINI", "mini", "Mini", "MiNi"]:
            context = {"form_factor": form_factor}
            result = action.calculate(context)
            assert result == 120.0, f"Case-insensitive match failed for '{form_factor}'"

    def test_missing_field_graceful_handling(self):
        """Test graceful handling when field doesn't exist"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Missing Field Multiplier",
                        "field": "nonexistent.field.path",
                        "conditions": [{"value": "test", "multiplier": 0.5}],
                    }
                ]
            },
        )

        # Should return base value when field doesn't exist
        context = {"some_other_field": "value"}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 (no multiplier), got {result}"

    def test_no_matching_condition_returns_base_value(self):
        """Test that unmatched conditions don't apply any multiplier"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "RAM Generation Multiplier",
                        "field": "ram_spec.ddr_generation",
                        "conditions": [
                            {"value": "ddr3", "multiplier": 0.7},
                            {"value": "ddr4", "multiplier": 1.0},
                        ],
                    }
                ]
            },
        )

        # Test with DDR5 (not in conditions list)
        context = {"ram_spec": {"ddr_generation": "ddr5"}}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 (no match), got {result}"


class TestConditionMultipliers:
    """Test condition multipliers (bug fix verification)"""

    def test_condition_multiplier_fixed(self):
        """Test condition multipliers work without 'condition_' prefix"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "condition_multipliers": {
                    "new": 1.0,
                    "refurb": 0.75,
                    "used": 0.6,
                }
            },
        )

        # Test new condition
        context = {"condition": "new"}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 for 'new', got {result}"

        # Test refurb condition
        context = {"condition": "refurb"}
        result = action.calculate(context)
        assert result == 75.0, f"Expected 75.0 for 'refurb', got {result}"

        # Test used condition
        context = {"condition": "used"}
        result = action.calculate(context)
        assert result == 60.0, f"Expected 60.0 for 'used', got {result}"

    def test_condition_multiplier_case_insensitive(self):
        """Test condition multipliers work with different cases"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={"condition_multipliers": {"new": 1.0, "refurb": 0.75}},
        )

        # Test various cases
        for condition in ["NEW", "new", "New", "NeW"]:
            context = {"condition": condition}
            result = action.calculate(context)
            assert result == 100.0, f"Case-insensitive condition failed for '{condition}'"


class TestCombinedMultipliers:
    """Test combinations of different multiplier types"""

    def test_field_and_condition_multipliers_stack(self):
        """Test field and condition multipliers work together"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "RAM Generation Multiplier",
                        "field": "ram_spec.ddr_generation",
                        "conditions": [
                            {"value": "ddr3", "multiplier": 0.8},
                            {"value": "ddr4", "multiplier": 1.0},
                        ],
                    }
                ],
                "condition_multipliers": {
                    "new": 1.0,
                    "refurb": 0.75,
                    "used": 0.6,
                },
            },
        )

        # Test DDR3 (0.8x) + used (0.6x) = 0.48x = $48
        context = {
            "ram_spec": {"ddr_generation": "ddr3"},
            "condition": "used",
        }
        result = action.calculate(context)
        assert result == 48.0, f"Expected 48.0 (100 * 0.8 * 0.6), got {result}"

        # Test DDR4 (1.0x) + refurb (0.75x) = 0.75x = $75
        context = {
            "ram_spec": {"ddr_generation": "ddr4"},
            "condition": "refurb",
        }
        result = action.calculate(context)
        assert result == 75.0, f"Expected 75.0 (100 * 1.0 * 0.75), got {result}"

    def test_field_condition_age_multipliers_stack(self):
        """Test field, condition, and age multipliers stack in correct order"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Storage Type Multiplier",
                        "field": "storage_type",
                        "conditions": [{"value": "hdd", "multiplier": 0.5}],
                    }
                ],
                "condition_multipliers": {"used": 0.6},
                "age_curve": {"rate_per_year": 0.1, "max": 0.5},
            },
        )

        # Test HDD (0.5x) + used (0.6x) + 2 years age (0.8x) = 0.24x = $24
        context = {
            "storage_type": "hdd",
            "condition": "used",
            "age_years": 2,
        }
        result = action.calculate(context)
        # 100 * 0.5 (storage) * 0.6 (condition) * 0.8 (age: 1.0 - 0.2) = 24
        assert result == 24.0, f"Expected 24.0, got {result}"

    def test_field_condition_brand_multipliers_stack(self):
        """Test field, condition, and brand multipliers stack correctly"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "RAM Generation Multiplier",
                        "field": "ram_spec.ddr_generation",
                        "conditions": [{"value": "ddr5", "multiplier": 1.3}],
                    }
                ],
                "condition_multipliers": {"new": 1.0},
                "brand_multipliers": {"dell": 1.1, "hp": 1.0},
            },
        )

        # Test DDR5 (1.3x) + new (1.0x) + Dell (1.1x) = 1.43x = $143
        context = {
            "ram_spec": {"ddr_generation": "ddr5"},
            "condition": "new",
            "manufacturer": "Dell",
        }
        result = action.calculate(context)
        assert result == 143.0, f"Expected 143.0 (100 * 1.3 * 1.0 * 1.1), got {result}"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_multipliers_array(self):
        """Test empty multipliers array doesn't cause errors"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={"multipliers": []},
        )

        context = {"some_field": "value"}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 (no multipliers), got {result}"

    def test_invalid_multiplier_config_skipped(self):
        """Test invalid multiplier configs are gracefully skipped"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    "not a dict",  # Invalid - should be skipped
                    {"field": None},  # Invalid - missing field
                    {
                        "name": "Valid Multiplier",
                        "field": "test_field",
                        "conditions": [{"value": "test", "multiplier": 0.5}],
                    },
                ]
            },
        )

        context = {"test_field": "test"}
        result = action.calculate(context)
        assert result == 50.0, f"Expected 50.0 (only valid multiplier), got {result}"

    def test_invalid_conditions_not_list(self):
        """Test invalid conditions (not a list) are handled gracefully"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Invalid Conditions",
                        "field": "test_field",
                        "conditions": "not a list",  # Invalid
                    }
                ]
            },
        )

        context = {"test_field": "test"}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 (invalid config), got {result}"

    def test_condition_without_value_skipped(self):
        """Test conditions without 'value' key are skipped"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Partial Conditions",
                        "field": "test_field",
                        "conditions": [
                            {"multiplier": 0.5},  # Missing 'value'
                            {"value": "test", "multiplier": 0.8},  # Valid
                        ],
                    }
                ]
            },
        )

        context = {"test_field": "test"}
        result = action.calculate(context)
        assert result == 80.0, f"Expected 80.0 (only valid condition), got {result}"

    def test_multiplier_default_to_one(self):
        """Test missing 'multiplier' value defaults to 1.0"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Default Multiplier",
                        "field": "test_field",
                        "conditions": [{"value": "test"}],  # Missing 'multiplier'
                    }
                ]
            },
        )

        context = {"test_field": "test"}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 (default multiplier), got {result}"

    def test_nested_field_path_with_none_values(self):
        """Test deeply nested field paths with None intermediate values"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Deep Path Multiplier",
                        "field": "level1.level2.level3.field",
                        "conditions": [{"value": "test", "multiplier": 0.5}],
                    }
                ]
            },
        )

        # Test with None at level2
        context = {"level1": {"level2": None}}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 (None in path), got {result}"

    def test_no_modifiers_returns_base_value(self):
        """Test action without any modifiers returns base value"""
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={},
        )

        context = {"condition": "used", "ram_spec": {"ddr_generation": "ddr3"}}
        result = action.calculate(context)
        assert result == 100.0, f"Expected 100.0 (no modifiers), got {result}"


class TestMultiplierOrdering:
    """Test multipliers are applied in the correct order"""

    def test_multiplier_application_order(self):
        """
        Test multipliers are applied in order:
        1. Field multipliers
        2. Condition multipliers
        3. Age depreciation
        4. Brand multipliers
        """
        action = Action(
            action_type=ActionType.FIXED_VALUE,
            value_usd=100.0,
            modifiers={
                "multipliers": [
                    {
                        "name": "Test Multiplier",
                        "field": "test_field",
                        "conditions": [{"value": "test", "multiplier": 2.0}],
                    }
                ],
                "condition_multipliers": {"new": 0.5},
                "age_curve": {"rate_per_year": 0.1, "max": 0.5},
                "brand_multipliers": {"testbrand": 2.0},
            },
        )

        context = {
            "test_field": "test",
            "condition": "new",
            "age_years": 1,
            "manufacturer": "TestBrand",
        }

        # Order: 100 * 2.0 (field) * 0.5 (condition) * 0.9 (age) * 2.0 (brand) = 180
        result = action.calculate(context)
        assert result == 180.0, f"Expected 180.0 (ordered application), got {result}"
