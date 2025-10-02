"""Scoring utilities for Deal Brain listings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass
class ListingMetrics:
    cpu_mark_multi: float | None = None
    cpu_mark_single: float | None = None
    gpu_score: float | None = None
    perf_per_watt: float | None = None
    ram_capacity: float | None = None
    expandability: float | None = None
    encoder_capability: float | None = None
    ports_fit: float | None = None


def compute_composite_score(weights: Mapping[str, float], metrics: ListingMetrics) -> float:
    score = 0.0
    total_weight = 0.0
    metrics_dict = metrics.__dict__
    for key, weight in weights.items():
        value = metrics_dict.get(key)
        if value is None:
            continue
        score += value * weight
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return score / total_weight


def dollar_per_metric(price_usd: float, metric: float | None) -> float | None:
    if not metric or metric <= 0:
        return None
    return round(price_usd / metric, 4)


def apply_rule_group_weights(
    rule_group_adjustments: dict[str, float],
    rule_group_weights: dict[str, float]
) -> float:
    """
    Apply weighted rule group adjustments to compute total valuation adjustment.

    Args:
        rule_group_adjustments: Dict mapping rule group names to their adjustment amounts
        rule_group_weights: Dict mapping rule group names to their weights (should sum to 1.0)

    Returns:
        Total weighted adjustment amount

    Example:
        >>> adjustments = {"cpu_valuation": 50.0, "ram_valuation": 20.0, "gpu_valuation": 100.0}
        >>> weights = {"cpu_valuation": 0.3, "ram_valuation": 0.2, "gpu_valuation": 0.5}
        >>> apply_rule_group_weights(adjustments, weights)
        75.0  # (50*0.3 + 20*0.2 + 100*0.5)
    """
    if not rule_group_weights:
        # If no weights defined, sum all adjustments equally
        return sum(rule_group_adjustments.values())

    total_adjustment = 0.0
    for group_name, adjustment in rule_group_adjustments.items():
        weight = rule_group_weights.get(group_name, 0.0)
        total_adjustment += adjustment * weight

    return total_adjustment


def validate_rule_group_weights(weights: dict[str, float]) -> tuple[bool, str | None]:
    """
    Validate that rule group weights are valid.

    Args:
        weights: Dict mapping rule group names to weights

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not weights:
        return True, None

    # Check all weights are non-negative
    for name, weight in weights.items():
        if weight < 0:
            return False, f"Weight for '{name}' must be non-negative (got {weight})"
        if weight > 1.0:
            return False, f"Weight for '{name}' must be <= 1.0 (got {weight})"

    # Check weights sum to approximately 1.0 (allow small floating point errors)
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        return False, f"Weights must sum to 1.0 (got {total:.3f})"

    return True, None


__all__ = [
    "ListingMetrics",
    "compute_composite_score",
    "dollar_per_metric",
    "apply_rule_group_weights",
    "validate_rule_group_weights",
]
