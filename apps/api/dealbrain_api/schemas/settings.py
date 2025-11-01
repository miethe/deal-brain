"""Settings schemas for application configuration."""

from pydantic import BaseModel, Field


class ValuationThresholdsResponse(BaseModel):
    """Valuation thresholds for pricing color coding.

    These are percentage values representing price differences from base valuation.
    """
    good_deal: float = Field(
        ...,
        description="Percentage threshold for good deal (e.g., 15.0 means 15% below base)"
    )
    great_deal: float = Field(
        ...,
        description="Percentage threshold for great deal (e.g., 25.0 means 25% below base)"
    )
    premium_warning: float = Field(
        ...,
        description="Percentage threshold for premium warning (e.g., 10.0 means 10% above base)"
    )


class CpuMarkThresholdsResponse(BaseModel):
    """CPU Mark thresholds for performance efficiency color coding.

    These are percentage improvement values representing price-to-performance efficiency.
    Positive values indicate better efficiency (lower $/mark), negative values indicate
    worse efficiency (higher $/mark) compared to baseline.

    Example: excellent=20.0 means ≥20% improvement (20% lower $/mark than baseline)
    """
    excellent: float = Field(
        ...,
        description="Percentage improvement for excellent tier (e.g., 20.0 means ≥20% improvement)"
    )
    good: float = Field(
        ...,
        description="Percentage improvement for good tier (e.g., 10.0 means 10-20% improvement)"
    )
    fair: float = Field(
        ...,
        description="Percentage improvement for fair tier (e.g., 5.0 means 5-10% improvement)"
    )
    neutral: float = Field(
        ...,
        description="Percentage improvement for neutral tier (e.g., 0.0 means 0-5% change)"
    )
    poor: float = Field(
        ...,
        description="Percentage improvement for poor tier (e.g., -10.0 means -10-0% degradation)"
    )
    premium: float = Field(
        ...,
        description="Percentage improvement for premium tier (e.g., -20.0 means <-10% degradation)"
    )


__all__ = ["ValuationThresholdsResponse", "CpuMarkThresholdsResponse"]
