"""CPU analytics schemas for price targets and performance value metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import DealBrainModel
from .catalog import CpuRead


class PriceTarget(DealBrainModel):
    """CPU price target ranges from listing data.

    Price targets are calculated from active listing adjusted prices:
    - good: Average adjusted price (typical market price)
    - great: One standard deviation below average (better deals)
    - fair: One standard deviation above average (premium pricing)

    Confidence levels based on sample size:
    - high: 10+ listings
    - medium: 5-9 listings
    - low: 2-4 listings
    - insufficient: <2 listings
    """
    good: float | None = Field(
        None,
        description="Average adjusted price (typical market price)",
        ge=0
    )
    great: float | None = Field(
        None,
        description="One std dev below average (better deals)",
        ge=0
    )
    fair: float | None = Field(
        None,
        description="One std dev above average (premium pricing)",
        ge=0
    )
    sample_size: int = Field(
        0,
        description="Number of listings used for calculation",
        ge=0
    )
    confidence: Literal['high', 'medium', 'low', 'insufficient'] = Field(
        'insufficient',
        description="Confidence level: high(10+), medium(5-9), low(2-4), insufficient(<2)"
    )
    stddev: float | None = Field(
        None,
        description="Standard deviation of prices",
        ge=0
    )
    updated_at: datetime | None = Field(
        None,
        description="Last calculation timestamp"
    )


class PerformanceValue(DealBrainModel):
    """CPU performance value metrics ($/PassMark).

    Measures price efficiency based on PassMark benchmark scores:
    - Lower $/mark ratio = better value
    - Percentile ranks CPUs where 0 = best value, 100 = worst value

    Rating quartiles:
    - excellent: 0-25th percentile (top 25% value)
    - good: 25-50th percentile
    - fair: 50-75th percentile
    - poor: 75-100th percentile (bottom 25% value)
    """
    dollar_per_mark_single: float | None = Field(
        None,
        description="Price per single-thread PassMark point",
        ge=0
    )
    dollar_per_mark_multi: float | None = Field(
        None,
        description="Price per multi-thread PassMark point",
        ge=0
    )
    percentile: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Performance value percentile rank (0=best, 100=worst)"
    )
    rating: Literal['excellent', 'good', 'fair', 'poor'] | None = Field(
        None,
        description="Value rating: excellent(0-25th), good(25-50th), fair(50-75th), poor(75-100th)"
    )
    updated_at: datetime | None = Field(
        None,
        description="Last calculation timestamp"
    )


class CPUAnalytics(DealBrainModel):
    """Complete analytics data for a CPU.

    Combines price targets, performance value metrics, and market statistics.
    Used for displaying analytics in CPU detail views and filter options.
    """
    price_targets: PriceTarget = Field(
        default_factory=PriceTarget,
        description="Price target ranges with confidence levels"
    )
    performance_value: PerformanceValue = Field(
        default_factory=PerformanceValue,
        description="Performance value metrics and ratings"
    )
    listings_count: int = Field(
        0,
        description="Number of active listings with this CPU",
        ge=0
    )
    price_distribution: list[float] = Field(
        default_factory=list,
        description="Price values for histogram visualization"
    )


class CPUWithAnalytics(CpuRead):
    """CPU with embedded analytics fields.

    Extends CpuRead with flattened analytics for efficient API responses.
    Used in CPU list views where analytics are displayed inline.
    """
    # Price target fields (flattened from PriceTarget)
    price_target_good: float | None = None
    price_target_great: float | None = None
    price_target_fair: float | None = None
    price_target_sample_size: int = 0
    price_target_confidence: Literal['high', 'medium', 'low', 'insufficient'] = 'insufficient'
    price_target_stddev: float | None = None
    price_target_updated_at: datetime | None = None

    # Performance value fields (flattened from PerformanceValue)
    dollar_per_mark_single: float | None = None
    dollar_per_mark_multi: float | None = None
    performance_value_percentile: float | None = None
    performance_value_rating: Literal['excellent', 'good', 'fair', 'poor'] | None = None
    performance_metrics_updated_at: datetime | None = None

    # Additional context
    listings_count: int = 0


class CPUStatistics(DealBrainModel):
    """Global CPU statistics for filter options.

    Provides metadata about available CPUs for building filter UI controls.
    Used in CPU catalog views to populate filter dropdowns and range sliders.
    """
    manufacturers: list[str] = Field(
        default_factory=list,
        description="Unique manufacturers in the catalog"
    )
    sockets: list[str] = Field(
        default_factory=list,
        description="Unique socket types in the catalog"
    )
    core_range: tuple[int, int] = Field(
        (2, 64),
        description="Min and max core counts"
    )
    tdp_range: tuple[int, int] = Field(
        (15, 280),
        description="Min and max TDP values in watts"
    )
    year_range: tuple[int, int] = Field(
        (2015, 2025),
        description="Min and max release years"
    )
    total_count: int = Field(
        0,
        description="Total number of CPUs in catalog",
        ge=0
    )


__all__ = [
    "PriceTarget",
    "PerformanceValue",
    "CPUAnalytics",
    "CPUWithAnalytics",
    "CPUStatistics",
]
