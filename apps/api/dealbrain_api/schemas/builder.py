"""Pydantic schemas for Deal Builder API.

Request and response models for custom build calculation, saving,
retrieval, and comparison endpoints.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# --- Request Schemas ---


class BuildComponentsRequest(BaseModel):
    """Component selection for build calculation.

    CPU is required. All other components are optional.
    Component IDs reference catalog entries (CPU, GPU) or spec IDs
    for configurable components (RAM, storage, PSU, case).
    """

    cpu_id: int = Field(..., gt=0, description="CPU ID (required)")
    gpu_id: Optional[int] = Field(None, gt=0, description="GPU ID (optional)")
    ram_spec_id: Optional[int] = Field(None, gt=0, description="RAM spec ID (optional)")
    storage_spec_id: Optional[int] = Field(None, gt=0, description="Storage spec ID (optional)")
    psu_spec_id: Optional[int] = Field(None, gt=0, description="PSU spec ID (optional)")
    case_spec_id: Optional[int] = Field(None, gt=0, description="Case spec ID (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_id": 123,
                "gpu_id": 456,
                "ram_spec_id": 789
            }
        }


class SaveBuildRequest(BaseModel):
    """Request to save a custom build.

    Includes build metadata (name, description, tags, visibility)
    and component selection. All fields are validated before save.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Build name (required, 1-255 characters)"
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Build description (optional, max 2000 characters)"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Build tags for organization and search"
    )
    visibility: str = Field(
        'private',
        pattern='^(private|public|unlisted)$',
        description="Build visibility: private (owner only), public (everyone), unlisted (share link)"
    )
    components: BuildComponentsRequest = Field(
        ...,
        description="Build component selection (CPU required)"
    )

    @field_validator('visibility')
    @classmethod
    def validate_visibility(cls, v: str) -> str:
        """Ensure visibility is one of the allowed values."""
        if v not in ['private', 'public', 'unlisted']:
            raise ValueError('visibility must be private, public, or unlisted')
        return v

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError('name cannot be empty or whitespace')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Gaming Build - Intel i5",
                "description": "Budget gaming build with i5-12400 and GTX 1660",
                "tags": ["gaming", "budget", "intel"],
                "visibility": "public",
                "components": {
                    "cpu_id": 123,
                    "gpu_id": 456,
                    "ram_spec_id": 789
                }
            }
        }


# --- Response Schemas ---


class ValuationBreakdownResponse(BaseModel):
    """Valuation breakdown with component pricing and adjustments.

    Provides transparency into how build pricing is calculated,
    showing individual component contributions and adjustment rules.
    """

    components: List[Dict[str, Any]] = Field(
        ...,
        description="List of components with name, type, and price"
    )
    adjustments: List[Dict[str, Any]] = Field(
        ...,
        description="List of valuation adjustments (rules applied)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "components": [
                    {"type": "CPU", "name": "Intel i5-12400", "price": 175.00},
                    {"type": "GPU", "name": "GTX 1660", "price": 150.00}
                ],
                "adjustments": []
            }
        }


class ValuationResponse(BaseModel):
    """Build valuation calculation result.

    Contains base price (sum of components), adjusted price (after rules),
    delta (difference), and detailed breakdown for transparency.
    """

    base_price: Decimal = Field(..., description="Sum of component prices")
    adjusted_price: Decimal = Field(..., description="Price after valuation adjustments")
    delta_amount: Decimal = Field(..., description="Absolute price difference (adjusted - base)")
    delta_percentage: float = Field(..., description="Percentage price difference")
    breakdown: ValuationBreakdownResponse = Field(..., description="Detailed pricing breakdown")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        json_schema_extra = {
            "example": {
                "base_price": 325.00,
                "adjusted_price": 325.00,
                "delta_amount": 0.00,
                "delta_percentage": 0.0,
                "breakdown": {
                    "components": [
                        {"type": "CPU", "name": "Intel i5-12400", "price": 175.00}
                    ],
                    "adjustments": []
                }
            }
        }


class MetricsResponse(BaseModel):
    """Build performance metrics.

    Includes price-per-performance ratios ($/CPU Mark) and
    composite score for overall build value assessment.
    """

    dollar_per_cpu_mark_multi: Optional[Decimal] = Field(
        None,
        description="Dollars per CPU Mark (multi-thread) - lower is better"
    )
    dollar_per_cpu_mark_single: Optional[Decimal] = Field(
        None,
        description="Dollars per CPU Mark (single-thread) - lower is better"
    )
    composite_score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Composite score (0-100 scale, higher is better)"
    )
    cpu_mark_multi: Optional[int] = Field(
        None,
        description="CPU multi-thread benchmark score"
    )
    cpu_mark_single: Optional[int] = Field(
        None,
        description="CPU single-thread benchmark score"
    )

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None else None
        }
        json_schema_extra = {
            "example": {
                "dollar_per_cpu_mark_multi": 0.018,
                "dollar_per_cpu_mark_single": 0.100,
                "composite_score": 75,
                "cpu_mark_multi": 17500,
                "cpu_mark_single": 3200
            }
        }


class SavedBuildResponse(BaseModel):
    """Saved build with all metadata and snapshots.

    Complete build representation including component IDs,
    pricing/metrics snapshots, and sharing information.
    """

    id: int = Field(..., description="Unique build ID")
    user_id: Optional[int] = Field(None, description="Owner user ID (null for anonymous)")
    name: str = Field(..., description="Build name")
    description: Optional[str] = Field(None, description="Build description")
    tags: Optional[List[str]] = Field(None, description="Build tags")
    visibility: str = Field(..., description="Build visibility (private/public/unlisted)")
    share_token: str = Field(..., description="Unique token for share URLs")

    # Component IDs
    cpu_id: Optional[int] = Field(None, description="CPU component ID")
    gpu_id: Optional[int] = Field(None, description="GPU component ID")
    ram_spec_id: Optional[int] = Field(None, description="RAM spec ID")
    storage_spec_id: Optional[int] = Field(None, description="Storage spec ID")
    psu_spec_id: Optional[int] = Field(None, description="PSU spec ID")
    case_spec_id: Optional[int] = Field(None, description="Case spec ID")

    # Snapshots
    pricing_snapshot: Optional[Dict[str, Any]] = Field(
        None,
        description="Pricing data snapshot at save time"
    )
    metrics_snapshot: Optional[Dict[str, Any]] = Field(
        None,
        description="Performance metrics snapshot at save time"
    )
    valuation_breakdown: Optional[Dict[str, Any]] = Field(
        None,
        description="Valuation breakdown for transparency"
    )

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True  # Pydantic V2 (was orm_mode in V1)
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 42,
                "name": "Gaming Build - Intel i5",
                "description": "Budget gaming build",
                "tags": ["gaming", "budget"],
                "visibility": "public",
                "share_token": "a1b2c3d4e5f6",
                "cpu_id": 123,
                "gpu_id": 456,
                "ram_spec_id": None,
                "storage_spec_id": None,
                "psu_spec_id": None,
                "case_spec_id": None,
                "pricing_snapshot": {
                    "base_price": "325.00",
                    "adjusted_price": "325.00"
                },
                "metrics_snapshot": {
                    "composite_score": 75
                },
                "valuation_breakdown": {},
                "created_at": "2025-11-14T10:30:00Z",
                "updated_at": "2025-11-14T10:30:00Z"
            }
        }


class BuildListResponse(BaseModel):
    """Paginated list of builds.

    Includes builds array and pagination metadata for
    efficient list navigation.
    """

    builds: List[SavedBuildResponse] = Field(..., description="List of builds")
    total: int = Field(..., ge=0, description="Total number of builds (for pagination)")
    limit: int = Field(..., ge=1, description="Maximum builds per page")
    offset: int = Field(..., ge=0, description="Number of builds skipped")

    class Config:
        json_schema_extra = {
            "example": {
                "builds": [
                    {
                        "id": 1,
                        "name": "Gaming Build",
                        "visibility": "public",
                        "cpu_id": 123,
                        "created_at": "2025-11-14T10:30:00Z"
                    }
                ],
                "total": 1,
                "limit": 10,
                "offset": 0
            }
        }


class CalculateResponse(BaseModel):
    """Combined valuation and metrics response.

    Returned by the calculate endpoint for real-time
    pricing and performance calculations.
    """

    valuation: ValuationResponse = Field(..., description="Pricing valuation data")
    metrics: MetricsResponse = Field(..., description="Performance metrics data")

    class Config:
        json_schema_extra = {
            "example": {
                "valuation": {
                    "base_price": 325.00,
                    "adjusted_price": 325.00,
                    "delta_amount": 0.00,
                    "delta_percentage": 0.0,
                    "breakdown": {
                        "components": [],
                        "adjustments": []
                    }
                },
                "metrics": {
                    "dollar_per_cpu_mark_multi": 0.018,
                    "composite_score": 75
                }
            }
        }


class ListingComparisonResponse(BaseModel):
    """Single listing comparison result.

    Used in the compare endpoint to show how custom build
    compares to similar pre-built listings.
    """

    listing_id: int = Field(..., description="Listing ID")
    name: str = Field(..., description="Listing title")
    price: Decimal = Field(..., description="Original price")
    adjusted_price: Decimal = Field(..., description="Adjusted price")
    deal_quality: str = Field(..., description="Deal quality (great/good/fair/premium)")
    price_difference: Decimal = Field(..., description="Price vs custom build")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class CompareResponse(BaseModel):
    """List of similar listings for comparison.

    Helps users evaluate if custom build is better value
    than pre-built alternatives.
    """

    listings: List[ListingComparisonResponse] = Field(
        ...,
        description="Similar pre-built listings"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "listings": [
                    {
                        "listing_id": 101,
                        "name": "Intel i5 Gaming PC",
                        "price": 350.00,
                        "adjusted_price": 340.00,
                        "deal_quality": "good",
                        "price_difference": 15.00,
                        "similarity_score": 0.95
                    }
                ]
            }
        }


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    deleted: bool = Field(..., description="Whether deletion was successful")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted": True
            }
        }


__all__ = [
    "BuildComponentsRequest",
    "SaveBuildRequest",
    "ValuationBreakdownResponse",
    "ValuationResponse",
    "MetricsResponse",
    "SavedBuildResponse",
    "BuildListResponse",
    "CalculateResponse",
    "ListingComparisonResponse",
    "CompareResponse",
    "DeleteResponse",
]
