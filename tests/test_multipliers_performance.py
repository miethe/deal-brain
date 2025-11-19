"""
Performance benchmarks for action multipliers.

Tests the performance of multiplier evaluation to ensure it meets requirements.
"""

import time
import pytest
from dealbrain_core.rules.actions import Action


def test_many_multipliers_performance():
    """Test performance with 10 multipliers - should complete in < 500ms"""
    # Create action with 10 multipliers
    multipliers_list = []
    for i in range(10):
        multipliers_list.append(
            {
                "name": f"Multiplier {i}",
                "field": f"test_field_{i}",
                "conditions": [
                    {"value": "value1", "multiplier": 1.0 + (i * 0.1)},
                    {"value": "value2", "multiplier": 0.9 + (i * 0.1)},
                ],
            }
        )

    action = Action(
        action_type="fixed_value",
        value_usd=100.0,
        modifiers={
            "multipliers": multipliers_list,
            "condition_multipliers": {
                "new": 1.0,
                "refurb": 0.75,
                "used": 0.6,
            },
        },
    )

    context = {
        "test_field_0": "value1",
        "test_field_1": "value2",
        "test_field_2": "value1",
        "test_field_3": "value2",
        "test_field_4": "value1",
        "condition": "new",
    }

    # Warm up
    for _ in range(10):
        action.calculate(context)

    # Time 1000 iterations
    start = time.time()
    iterations = 1000
    for _ in range(iterations):
        result = action.calculate(context)
    elapsed = time.time() - start

    # Should be fast (< 500ms for 1000 iterations)
    assert elapsed < 0.5, f"Too slow: {elapsed:.3f}s for {iterations} iterations"

    avg_time_ms = (elapsed / iterations) * 1000
    print(
        f"\nPerformance: {iterations} iterations in {elapsed:.3f}s (avg {avg_time_ms:.4f}ms per call)"
    )
    assert result > 0  # Verify it actually calculated


def test_nested_field_path_performance():
    """Test performance with deeply nested field paths"""
    action = Action(
        action_type="fixed_value",
        value_usd=100.0,
        modifiers={
            "multipliers": [
                {
                    "name": "Deep Multiplier 1",
                    "field": "level1.level2.level3.level4.field1",
                    "conditions": [{"value": "test", "multiplier": 1.2}],
                },
                {
                    "name": "Deep Multiplier 2",
                    "field": "level1.level2.level3.level4.field2",
                    "conditions": [{"value": "test", "multiplier": 1.3}],
                },
            ]
        },
    )

    context = {"level1": {"level2": {"level3": {"level4": {"field1": "test", "field2": "test"}}}}}

    # Warm up
    for _ in range(10):
        action.calculate(context)

    # Time 1000 iterations
    start = time.time()
    iterations = 1000
    for _ in range(iterations):
        result = action.calculate(context)
    elapsed = time.time() - start

    # Should handle deep paths efficiently (< 300ms for 1000 iterations)
    assert elapsed < 0.3, f"Too slow for nested paths: {elapsed:.3f}s for {iterations} iterations"

    avg_time_ms = (elapsed / iterations) * 1000
    print(
        f"\nDeep path performance: {iterations} iterations in {elapsed:.3f}s (avg {avg_time_ms:.4f}ms per call)"
    )
    assert result == pytest.approx(100.0 * 1.2 * 1.3)


def test_simple_multiplier_performance():
    """Baseline performance test with single multiplier"""
    action = Action(
        action_type="per_unit",
        metric="ram_spec.total_capacity_gb",
        value_usd=2.50,
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

    context = {"ram_spec": {"total_capacity_gb": 16, "ddr_generation": "ddr4"}}

    # Time 10000 iterations
    start = time.time()
    iterations = 10000
    for _ in range(iterations):
        result = action.calculate(context)
    elapsed = time.time() - start

    # Should be very fast (< 100ms for 10000 iterations)
    assert elapsed < 0.1, f"Too slow: {elapsed:.3f}s for {iterations} iterations"

    avg_time_us = (elapsed / iterations) * 1000000
    print(
        f"\nSimple multiplier performance: {iterations} iterations in {elapsed:.3f}s (avg {avg_time_us:.2f}µs per call)"
    )
    assert result == pytest.approx(40.0)  # 16 * 2.5 * 1.0
