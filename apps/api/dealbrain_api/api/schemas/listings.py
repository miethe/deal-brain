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
        """Coerce reference identifiers to integers when provided as strings."""
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

        for key in ("ram_spec_id", "primary_storage_profile_id", "secondary_storage_profile_id"):
            if key in v:
                if v[key] is None or v[key] == "":
                    v[key] = None
                elif isinstance(v[key], str):
                    v[key] = int(v[key])

        return v


class ListingBulkUpdateRequest(BaseModel):
    listing_ids: list[int] = Field(default_factory=list)
    fields: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None

    @field_validator("fields", mode="before")
    @classmethod
    def coerce_bulk_reference_fields(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is None:
            return v
        for key in ("cpu_id", "gpu_id", "ram_spec_id", "primary_storage_profile_id", "secondary_storage_profile_id"):
            if key in v:
                if v[key] is None or v[key] == "":
                    v[key] = None
                elif isinstance(v[key], str):
                    v[key] = int(v[key])
        return v


class ListingBulkUpdateResponse(BaseModel):
    updated: list[ListingRead]
    updated_count: int


class ValuationAdjustmentAction(BaseModel):
    """Breakdown of an individual action contributing to a rule adjustment."""
    action_type: str | None = Field(None, description="Action type identifier")
    metric: str | None = Field(None, description="Metric or dimension affected by the action")
    value: float = Field(..., description="Value contributed by this action in USD")
    details: dict[str, Any] | None = Field(None, description="Raw action configuration details")
    error: str | None = Field(None, description="Error encountered while executing the action")


class ValuationAdjustmentDetail(BaseModel):
    """Details of a rule adjustment applied during valuation."""
    rule_id: int | None = Field(None, description="Identifier of the valuation rule")
    rule_name: str = Field(..., description="Display name of the rule")
    rule_description: str | None = Field(None, description="Rule description from database")
    rule_group_id: int | None = Field(None, description="Identifier of the rule group")
    rule_group_name: str | None = Field(None, description="Display name of the rule group")
    adjustment_amount: float = Field(..., description="Net price adjustment in USD")
    actions: list[ValuationAdjustmentAction] = Field(
        default_factory=list,
        description="Actions executed as part of the rule evaluation",
    )


class LegacyValuationLine(BaseModel):
    """Legacy component deduction line retained for backwards compatibility."""
    label: str = Field(..., description="Component or deduction label")
    component_type: str = Field(..., description="Component type identifier")
    quantity: float = Field(..., description="Quantity associated with the deduction")
    unit_value: float = Field(..., description="Unit value in USD")
    condition_multiplier: float = Field(..., description="Condition multiplier applied")
    deduction_usd: float = Field(..., description="Deduction amount in USD")
    adjustment_usd: float | None = Field(None, description="Signed adjustment amount when available")


class ValuationBreakdownResponse(BaseModel):
    """Detailed breakdown of listing valuation calculation."""
    listing_id: int = Field(..., description="Listing ID")
    listing_title: str = Field(..., description="Listing title")
    base_price_usd: float = Field(..., description="Original listing price")
    adjusted_price_usd: float = Field(..., description="Price after rule adjustments")
    total_adjustment: float = Field(..., description="Total adjustment amount (can be positive or negative)")
    total_deductions: float | None = Field(None, description="Sum of deduction amounts when available")
    matched_rules_count: int = Field(0, description="Number of rules that contributed adjustments")
    ruleset_id: int | None = Field(None, description="Identifier of the ruleset used for valuation")
    ruleset_name: str | None = Field(None, description="Display name of the ruleset used for valuation")
    adjustments: list[ValuationAdjustmentDetail] = Field(
        default_factory=list,
        description="Applied rule adjustments",
    )
    legacy_lines: list[LegacyValuationLine] = Field(
        default_factory=list,
        description="Legacy component deductions retained for backwards compatibility",
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


class ListingValuationOverrideRequest(BaseModel):
    """Request schema for managing listing-level ruleset overrides."""
    mode: Literal["auto", "static"] = Field(
        "auto",
        description="Auto selects by priority; static locks to a specific ruleset.",
    )
    ruleset_id: int | None = Field(None, description="Required when mode is static.")
    disabled_rulesets: list[int] = Field(
        default_factory=list,
        description="Ruleset IDs to exclude when using auto matching.",
    )

    @field_validator("ruleset_id")
    @classmethod
    def validate_ruleset_id(cls, value: int | None, info) -> int | None:
        mode = info.data.get("mode", "auto")
        if mode == "static" and value is None:
            raise ValueError("ruleset_id is required when mode is 'static'")
        return value


class ListingValuationOverrideResponse(BaseModel):
    """Response describing the current listing valuation override state."""
    mode: Literal["auto", "static"]
    ruleset_id: int | None = Field(None, description="Static ruleset assignment if any.")
    disabled_rulesets: list[int] = Field(default_factory=list)


class PaginatedListingsResponse(BaseModel):
    """Cursor-based paginated listings response."""
    items: list[ListingRead] = Field(..., description="Listings in current page")
    total: int = Field(..., description="Total count of listings (cached)")
    limit: int = Field(..., description="Number of items requested per page")
    next_cursor: str | None = Field(None, description="Cursor for next page (null if last page)")
    has_next: bool = Field(..., description="Whether more pages are available")


__all__ = [
    "BulkRecalculateRequest",
    "BulkRecalculateResponse",
    "LegacyValuationLine",
    "ListingBulkUpdateRequest",
    "ListingBulkUpdateResponse",
    "ListingFieldSchema",
    "ListingPartialUpdateRequest",
    "ListingSchemaResponse",
    "ListingValuationOverrideRequest",
    "ListingValuationOverrideResponse",
    "PaginatedListingsResponse",
    "PortEntry",
    "PortsResponse",
    "UpdatePortsRequest",
    "ValuationAdjustmentAction",
    "ValuationAdjustmentDetail",
    "ValuationBreakdownResponse",
]
