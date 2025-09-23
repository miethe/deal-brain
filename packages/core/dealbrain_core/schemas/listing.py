"""Schemas for listings and derived metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import DealBrainModel
from ..enums import ComponentType, Condition, ListingStatus


class ListingComponentBase(DealBrainModel):
    component_type: ComponentType
    name: str | None = None
    quantity: int = 1
    metadata_json: dict[str, Any] | None = None
    adjustment_value_usd: float | None = None
    rule_id: int | None = None


class ListingComponentCreate(ListingComponentBase):
    pass


class ListingComponentRead(ListingComponentBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ListingBase(DealBrainModel):
    title: str
    url: str | None = None
    seller: str | None = None
    price_usd: float
    price_date: datetime | None = None
    condition: Condition = Condition.USED
    status: ListingStatus = ListingStatus.ACTIVE
    cpu_id: int | None = None
    gpu_id: int | None = None
    ports_profile_id: int | None = None
    device_model: str | None = None
    ram_gb: int = 0
    ram_notes: str | None = None
    primary_storage_gb: int = 0
    primary_storage_type: str | None = None
    secondary_storage_gb: int | None = None
    secondary_storage_type: str | None = None
    os_license: str | None = None
    other_components: list[str] = Field(default_factory=list)
    notes: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ListingCreate(ListingBase):
    components: list[ListingComponentCreate] | None = None


class ListingRead(ListingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    adjusted_price_usd: float | None = None
    valuation_breakdown: dict[str, Any] | None = None
    score_cpu_multi: float | None = None
    score_cpu_single: float | None = None
    score_gpu: float | None = None
    score_composite: float | None = None
    dollar_per_cpu_mark: float | None = None
    dollar_per_single_mark: float | None = None
    perf_per_watt: float | None = None
    active_profile_id: int | None = None
    components: list[ListingComponentRead] = Field(default_factory=list)


ListingRead.model_rebuild()
