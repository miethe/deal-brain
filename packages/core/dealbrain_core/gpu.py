"""GPU normalization helpers."""

from __future__ import annotations

from typing import Optional


def compute_gpu_score(
    *, gpu_mark: Optional[float], metal_score: Optional[float], is_apple: bool
) -> Optional[float]:
    if is_apple:
        metal_component = metal_score or 0.0
        gpu_component = gpu_mark or metal_component
        return (
            0.8 * metal_component + 0.2 * gpu_component
            if metal_component or gpu_component
            else None
        )
    if gpu_mark:
        return float(gpu_mark)
    return None


__all__ = ["compute_gpu_score"]
