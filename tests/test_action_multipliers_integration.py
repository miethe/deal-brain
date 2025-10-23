"""
Integration test to verify real-world action multipliers scenarios.

This test simulates real valuation scenarios from the frontend.
"""
from dealbrain_core.rules.actions import Action, ActionType


def test_ram_valuation_with_generation_and_condition():
    """
    Real-world scenario: RAM valuation with:
    - DDR generation multiplier (DDR3 is worth less)
    - Condition multiplier (used condition reduces value)
    """
    action = Action(
        action_type=ActionType.PER_UNIT,
        metric="per_ram_spec_gb",
        value_usd=5.0,  # $5 per GB base
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
            ],
            "condition_multipliers": {
                "new": 1.0,
                "refurb": 0.75,
                "used": 0.6,
            },
        },
    )

    # Scenario 1: 32GB DDR4 RAM, used condition
    # Expected: 32 * $5 * 1.0 (ddr4) * 0.6 (used) = $96
    context = {
        "ram_spec": {"total_capacity_gb": 32, "ddr_generation": "ddr4"},
        "condition": "used",
    }
    result = action.calculate(context)
    assert result == 96.0, f"Expected $96, got ${result}"

    # Scenario 2: 16GB DDR3 RAM, refurb condition
    # Expected: 16 * $5 * 0.7 (ddr3) * 0.75 (refurb) = $42
    context = {
        "ram_spec": {"total_capacity_gb": 16, "ddr_generation": "ddr3"},
        "condition": "refurb",
    }
    result = action.calculate(context)
    assert result == 42.0, f"Expected $42, got ${result}"

    # Scenario 3: 64GB DDR5 RAM, new condition
    # Expected: 64 * $5 * 1.3 (ddr5) * 1.0 (new) = $416
    context = {
        "ram_spec": {"total_capacity_gb": 64, "ddr_generation": "ddr5"},
        "condition": "new",
    }
    result = action.calculate(context)
    assert result == 416.0, f"Expected $416, got ${result}"


def test_storage_valuation_with_type_and_age():
    """
    Real-world scenario: Storage valuation with:
    - Storage type multiplier (HDD worth less than SSD)
    - Age depreciation (older drives worth less)
    """
    action = Action(
        action_type=ActionType.PER_UNIT,
        metric="per_primary_storage_gb",
        value_usd=0.10,  # $0.10 per GB base
        modifiers={
            "multipliers": [
                {
                    "name": "Storage Type Multiplier",
                    "field": "storage.primary.type",
                    "conditions": [
                        {"value": "hdd", "multiplier": 0.3},
                        {"value": "ssd", "multiplier": 1.0},
                        {"value": "nvme", "multiplier": 1.5},
                    ],
                }
            ],
            "condition_multipliers": {"new": 1.0, "used": 0.7},
            "age_curve": {"rate_per_year": 0.15, "max": 0.6},
        },
    )

    # Scenario: 1TB HDD, used, 3 years old
    # Expected: 1000 * $0.10 * 0.3 (hdd) * 0.7 (used) * 0.55 (age: 1-0.45) = $11.55
    context = {
        "storage": {"primary": {"capacity_gb": 1000, "type": "hdd"}},
        "condition": "used",
        "age_years": 3,
    }
    result = action.calculate(context)
    assert result == 11.55, f"Expected $11.55, got ${result}"


def test_complete_pc_valuation():
    """
    Real-world scenario: Complete PC with multiple components and multipliers.
    """
    # Base price adjustment action
    base_action = Action(
        action_type=ActionType.FIXED_VALUE,
        value_usd=100.0,
        modifiers={
            "multipliers": [
                {
                    "name": "Form Factor Premium",
                    "field": "form_factor",
                    "conditions": [
                        {"value": "mini", "multiplier": 1.2},
                        {"value": "micro", "multiplier": 1.1},
                        {"value": "tower", "multiplier": 1.0},
                    ],
                }
            ],
            "condition_multipliers": {"new": 1.0, "refurb": 0.8},
            "brand_multipliers": {"dell": 1.1, "hp": 1.05, "lenovo": 1.08},
        },
    )

    # Scenario: Mini PC, refurb, Dell brand
    # Expected: $100 * 1.2 (mini) * 0.8 (refurb) * 1.1 (dell) = $105.60
    context = {
        "form_factor": "mini",
        "condition": "refurb",
        "manufacturer": "dell",
    }
    result = base_action.calculate(context)
    assert abs(result - 105.6) < 0.01, f"Expected $105.60, got ${result}"


def test_frontend_payload_format():
    """
    Test with exact payload format that would come from the frontend.
    This ensures compatibility with the UI.
    """
    # This is the exact format the frontend sends
    frontend_modifiers = {
        "multipliers": [
            {
                "name": "RAM Generation Multiplier",
                "field": "ram_spec.ddr_generation",
                "conditions": [
                    {"value": "ddr3", "multiplier": 0.7},
                    {"value": "ddr4", "multiplier": 1.0},
                    {"value": "ddr5", "multiplier": 1.3},
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
        ],
        "condition_multipliers": {"new": 1.0, "refurb": 0.75, "used": 0.6},
    }

    action = Action(
        action_type=ActionType.FIXED_VALUE,
        value_usd=100.0,
        modifiers=frontend_modifiers,
    )

    # Verify it works with the frontend format
    context = {
        "ram_spec": {"ddr_generation": "ddr5"},
        "storage": {"primary": {"type": "nvme"}},
        "condition": "new",
    }

    # Expected: $100 * 1.3 (ddr5) * 1.2 (nvme) * 1.0 (new) = $156
    result = action.calculate(context)
    assert result == 156.0, f"Expected $156, got ${result}"
