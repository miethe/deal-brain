"""Schemas for listings and derived metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, field_validator

from .base import DealBrainModel
from .catalog import CpuRead, GpuRead, PortsProfileRead, RamSpecRead, StorageProfileRead
from ..enums import ComponentType, Condition, ListingStatus


def _normalize_http_url(value: str) -> str:
    if value is None:
        return value
    url_str = str(value).strip()
    if not url_str:
        return ""
    parsed = urlparse(url_str)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must start with http:// or https:// and include a host")
    return url_str


class ListingLink(DealBrainModel):
    url: str
    label: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        normalized = _normalize_http_url(value)
        if not normalized:
            raise ValueError("URL is required")
        return normalized

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


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
    listing_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("listing_url", "url"),
        serialization_alias="listing_url",
    )
    other_urls: list[ListingLink] = Field(default_factory=list)
    seller: str | None = None
    price_usd: float
    price_date: datetime | None = None
    condition: Condition = Condition.USED
    status: ListingStatus = ListingStatus.ACTIVE
    cpu_id: int | None = None
    gpu_id: int | None = None
    ports_profile_id: int | None = None
    ram_spec_id: int | None = None
    primary_storage_profile_id: int | None = None
    secondary_storage_profile_id: int | None = None
    ram_spec: dict[str, Any] | None = Field(default=None, exclude=True)
    primary_storage_profile: dict[str, Any] | None = Field(default=None, exclude=True)
    secondary_storage_profile: dict[str, Any] | None = Field(default=None, exclude=True)
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
    ruleset_id: int | None = None
    # Product Metadata (New)
    manufacturer: str | None = None
    series: str | None = None
    model_number: str | None = None
    form_factor: str | None = None

    @field_validator("listing_url", mode="before")
    @classmethod
    def validate_listing_url(cls, value: Any) -> Any:
        if value in (None, ""):
            return None
        return _normalize_http_url(value)

    @field_validator("other_urls", mode="before")
    @classmethod
    def coerce_other_urls(cls, value: Any) -> Any:
        if not value:
            return []
        if isinstance(value, dict):
            value = [value]
        normalized: list[dict[str, Any]] = []
        for entry in value:
            if isinstance(entry, ListingLink):
                normalized.append(entry.model_dump())
            elif isinstance(entry, str):
                normalized.append({"url": entry})
            elif isinstance(entry, dict):
                data = dict(entry)
                url_value = data.get("url") or data.get("href")
                if not url_value:
                    continue
                label_value = data.get("label") or data.get("text")
                normalized.append({"url": url_value, "label": label_value})
        return normalized


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
    # Performance Metrics (New)
    dollar_per_cpu_mark_single: float | None = None
    dollar_per_cpu_mark_single_adjusted: float | None = None
    dollar_per_cpu_mark_multi: float | None = None
    dollar_per_cpu_mark_multi_adjusted: float | None = None
    components: list[ListingComponentRead] = Field(default_factory=list)
    cpu: CpuRead | None = None
    gpu: GpuRead | None = None
    ports_profile: PortsProfileRead | None = None
    ram_spec: RamSpecRead | None = None
    primary_storage_profile: StorageProfileRead | None = None
    secondary_storage_profile: StorageProfileRead | None = None
    ram_type: str | None = None
    ram_speed_mhz: int | None = None

ListingRead.model_rebuild()
