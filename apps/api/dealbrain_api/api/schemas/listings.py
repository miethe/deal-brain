"""Pydantic schemas for listings API extensions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from dealbrain_core.schemas import ListingRead

from .custom_fields import CustomFieldResponse


class ListingFieldSchema(BaseModel):
    key: str
    label: str
    data_type: str
    required: bool = False
    editable: bool = True
    description: str | None = None
    options: list[str] | None = None
    validation: dict[str, Any] | None = None
    origin: Literal["core", "custom"] = "core"


class ListingSchemaResponse(BaseModel):
    core_fields: list[ListingFieldSchema] = Field(default_factory=list)
    custom_fields: list[CustomFieldResponse] = Field(default_factory=list)


class ListingPartialUpdateRequest(BaseModel):
    fields: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None

    @field_validator("fields", mode="before")
    @classmethod
    def coerce_reference_fields(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Coerce cpu_id and gpu_id to integers if they are strings."""
        if v is None:
            return v

        # Coerce cpu_id to int
        if "cpu_id" in v:
            if v["cpu_id"] is None or v["cpu_id"] == "":
                v["cpu_id"] = None
            elif isinstance(v["cpu_id"], str):
                v["cpu_id"] = int(v["cpu_id"])

        # Coerce gpu_id to int
        if "gpu_id" in v:
            if v["gpu_id"] is None or v["gpu_id"] == "":
                v["gpu_id"] = None
            elif isinstance(v["gpu_id"], str):
                v["gpu_id"] = int(v["gpu_id"])

        return v


class ListingBulkUpdateRequest(BaseModel):
    listing_ids: list[int] = Field(default_factory=list)
    fields: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None


class ListingBulkUpdateResponse(BaseModel):
    updated: list[ListingRead]
    updated_count: int


class AppliedRuleDetail(BaseModel):
    """Details of a single rule applied during valuation"""
    rule_group_name: str = Field(..., description="Name of the rule group")
    rule_name: str = Field(..., description="Name of the specific rule")
    rule_description: str | None = Field(None, description="Description of the rule")
    adjustment_amount: float = Field(..., description="Price adjustment amount in USD")
    conditions_met: list[str] = Field(default_factory=list, description="Human-readable condition descriptions")
    actions_applied: list[str] = Field(default_factory=list, description="Human-readable action descriptions")


class ValuationBreakdownResponse(BaseModel):
    """Detailed breakdown of listing valuation calculation"""
    listing_id: int = Field(..., description="Listing ID")
    listing_title: str = Field(..., description="Listing title")
    base_price_usd: float = Field(..., description="Original listing price")
    adjusted_price_usd: float = Field(..., description="Price after rule adjustments")
    total_adjustment: float = Field(..., description="Total adjustment amount")
    active_ruleset: str = Field(..., description="Name of the active ruleset used")
    applied_rules: list[AppliedRuleDetail] = Field(
        default_factory=list,
        description="List of rules that were applied"
    )


class BulkRecalculateRequest(BaseModel):
    """Request to recalculate metrics for multiple listings"""
    listing_ids: list[int] | None = Field(None, description="List of listing IDs. If None, updates all.")


class BulkRecalculateResponse(BaseModel):
    """Response after bulk metric recalculation"""
    updated_count: int = Field(..., description="Number of listings updated")
    message: str = Field(..., description="Status message")


class PortEntry(BaseModel):
    """Single port entry with type and quantity"""
    port_type: str = Field(..., description="Port type (e.g., USB-A, HDMI)")
    quantity: int = Field(..., ge=1, le=16, description="Quantity of this port type")


class UpdatePortsRequest(BaseModel):
    """Request to update ports for a listing"""
    ports: list[PortEntry] = Field(default_factory=list, description="List of port entries")


class PortsResponse(BaseModel):
    """Response with ports data"""
    ports: list[PortEntry] = Field(default_factory=list, description="List of port entries")


__all__ = [
    "AppliedRuleDetail",
    "BulkRecalculateRequest",
    "BulkRecalculateResponse",
    "ListingBulkUpdateRequest",
    "ListingBulkUpdateResponse",
    "ListingFieldSchema",
    "ListingPartialUpdateRequest",
    "ListingSchemaResponse",
    "PortEntry",
    "PortsResponse",
    "UpdatePortsRequest",
    "ValuationBreakdownResponse",
]
