"""Pydantic schemas for listings API extensions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

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


__all__ = [
    "AppliedRuleDetail",
    "ListingBulkUpdateRequest",
    "ListingBulkUpdateResponse",
    "ListingFieldSchema",
    "ListingPartialUpdateRequest",
    "ListingSchemaResponse",
    "ValuationBreakdownResponse",
]
