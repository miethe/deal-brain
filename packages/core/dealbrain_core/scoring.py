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


__all__ = ["ListingMetrics", "compute_composite_score", "dollar_per_metric"]
