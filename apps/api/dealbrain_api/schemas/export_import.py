"""Schemas for portable export/import of Deal Brain artifacts.

This module implements the v1.0.0 export schema for Deal Brain listings and collections.
The schema is LOCKED - v1.0.0 cannot have breaking changes.

JSON Schema: /docs/schemas/deal-brain-export-schema-v1.0.0.json
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from dealbrain_core.enums import (
    CollectionItemStatus,
    CollectionVisibility,
    ComponentType,
    Condition,
    ListingStatus,
    PortType,
    RamGeneration,
    StorageMedium,
)
from dealbrain_core.schemas.base import DealBrainModel


# ==================== Component Schemas ====================


class ListingLinkExport(DealBrainModel):
    """Additional URL link for a listing."""

    url: str
    label: str | None = None


class CPUExport(DealBrainModel):
    """CPU specification for export."""

    name: str
    manufacturer: str
    cores: int | None = None
    threads: int | None = None
    tdp_w: int | None = None
    igpu_model: str | None = None
    cpu_mark_multi: int | None = None
    cpu_mark_single: int | None = None
    igpu_mark: int | None = None
    release_year: int | None = None


class GPUExport(DealBrainModel):
    """GPU specification for export."""

    name: str
    manufacturer: str
    gpu_mark: int | None = None
    metal_score: int | None = None


class RAMExport(DealBrainModel):
    """RAM specification for export."""

    total_gb: int
    ddr_generation: RamGeneration | None = None
    speed_mhz: int | None = None
    module_count: int | None = None
    capacity_per_module_gb: int | None = None
    notes: str | None = None


class StorageExport(DealBrainModel):
    """Storage specification for export."""

    capacity_gb: int
    medium: StorageMedium | None = None
    interface: str | None = None
    form_factor: str | None = None
    performance_tier: str | None = None


class PerformanceMetricsExport(DealBrainModel):
    """Performance metrics for export."""

    dollar_per_cpu_mark_single: float | None = Field(
        None,
        description="Base price / single-thread mark"
    )
    dollar_per_cpu_mark_single_adjusted: float | None = Field(
        None,
        description="Adjusted price / single-thread mark"
    )
    dollar_per_cpu_mark_multi: float | None = Field(
        None,
        description="Base price / multi-thread mark"
    )
    dollar_per_cpu_mark_multi_adjusted: float | None = Field(
        None,
        description="Adjusted price / multi-thread mark"
    )
    score_cpu_multi: float | None = None
    score_cpu_single: float | None = None
    score_gpu: float | None = None
    score_composite: float | None = None
    perf_per_watt: float | None = None


class PortExport(DealBrainModel):
    """Port specification for export."""

    type: PortType
    count: int = Field(ge=1)
    spec_notes: str | None = None


class PortsExport(DealBrainModel):
    """Ports profile for export."""

    profile_name: str | None = None
    ports: list[PortExport] = Field(default_factory=list)


class ComponentExport(DealBrainModel):
    """Component associated with a listing."""

    component_type: ComponentType
    name: str | None = None
    quantity: int = Field(default=1, ge=1)
    metadata: dict[str, Any] | None = None
    adjustment_value_usd: float | None = None


class PerformanceExport(DealBrainModel):
    """Performance data for export."""

    cpu: CPUExport | None = None
    gpu: GPUExport | None = None
    ram: RAMExport | None = None
    storage_primary: StorageExport | None = None
    storage_secondary: StorageExport | None = None
    metrics: PerformanceMetricsExport | None = None
    ports: PortsExport | None = None
    components: list[ComponentExport] = Field(default_factory=list)


class ValuationExport(DealBrainModel):
    """Valuation data for export."""

    base_price_usd: float = Field(description="Original listing price")
    adjusted_price_usd: float | None = Field(
        None,
        description="Price after applying valuation rules"
    )
    valuation_breakdown: dict[str, Any] | None = Field(
        None,
        description="Detailed breakdown of applied valuation rules"
    )
    ruleset_name: str | None = Field(
        None,
        description="Name of the valuation ruleset used"
    )


class MetadataExport(DealBrainModel):
    """Product metadata for export."""

    manufacturer: str | None = Field(None, max_length=64)
    series: str | None = Field(None, max_length=128)
    model_number: str | None = Field(None, max_length=128)
    form_factor: str | None = Field(None, max_length=32)


class ListingExport(DealBrainModel):
    """Listing data for export."""

    id: int = Field(
        description="Original listing ID (reference only, may not be unique in target system)"
    )
    title: str = Field(min_length=1, max_length=255)
    listing_url: str | None = None
    other_urls: list[ListingLinkExport] = Field(default_factory=list)
    seller: str | None = Field(None, max_length=128)
    price_usd: float = Field(ge=0)
    price_date: datetime | None = None
    condition: Condition
    status: ListingStatus
    device_model: str | None = Field(None, max_length=255)
    notes: str | None = None
    custom_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom field values (attributes_json)"
    )
    created_at: datetime
    updated_at: datetime


# ==================== Deal Export ====================


class DealDataExport(DealBrainModel):
    """Complete deal data for export."""

    listing: ListingExport
    valuation: ValuationExport | None = None
    performance: PerformanceExport | None = None
    metadata: MetadataExport | None = None


# ==================== Collection Export ====================


class CollectionExport(DealBrainModel):
    """Collection metadata for export."""

    id: int = Field(description="Original collection ID (reference only)")
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    visibility: CollectionVisibility
    created_at: datetime
    updated_at: datetime


class CollectionItemExport(DealBrainModel):
    """Collection item for export."""

    listing: DealDataExport
    status: CollectionItemStatus
    notes: str | None = Field(None, max_length=500)
    position: int | None = None
    added_at: datetime


class CollectionDataExport(DealBrainModel):
    """Complete collection data for export."""

    collection: CollectionExport
    items: list[CollectionItemExport] = Field(default_factory=list)


# ==================== Export Metadata ====================


class ExportMetadata(DealBrainModel):
    """Metadata for export wrapper."""

    version: Literal["1.0.0"] = "1.0.0"
    exported_at: datetime
    exported_by: UUID | None = None
    type: Literal["deal", "collection"]

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        """Ensure version is exactly 1.0.0."""
        if value != "1.0.0":
            raise ValueError("Export schema version must be 1.0.0")
        return value


# ==================== Top-Level Export Wrappers ====================


class PortableDealExport(DealBrainModel):
    """Top-level wrapper for portable deal export.

    This schema is LOCKED - v1.0.0 cannot have breaking changes.
    Future versions (v1.1+) must maintain backward compatibility.
    """

    deal_brain_export: ExportMetadata
    data: DealDataExport

    @field_validator("deal_brain_export")
    @classmethod
    def validate_deal_type(cls, value: ExportMetadata) -> ExportMetadata:
        """Ensure export type is 'deal'."""
        if value.type != "deal":
            raise ValueError("Export type must be 'deal' for PortableDealExport")
        return value


class PortableCollectionExport(DealBrainModel):
    """Top-level wrapper for portable collection export.

    This schema is LOCKED - v1.0.0 cannot have breaking changes.
    Future versions (v1.1+) must maintain backward compatibility.
    """

    deal_brain_export: ExportMetadata
    data: CollectionDataExport

    @field_validator("deal_brain_export")
    @classmethod
    def validate_collection_type(cls, value: ExportMetadata) -> ExportMetadata:
        """Ensure export type is 'collection'."""
        if value.type != "collection":
            raise ValueError("Export type must be 'collection' for PortableCollectionExport")
        return value


# ==================== Generic Export Wrapper ====================


class PortableExport(DealBrainModel):
    """Generic wrapper for any portable export.

    Use this for parsing exports when you don't know the type upfront.
    After parsing, inspect deal_brain_export.type to determine which
    specific model to use.
    """

    deal_brain_export: ExportMetadata
    data: DealDataExport | CollectionDataExport


__all__ = [
    # Component schemas
    "ListingLinkExport",
    "CPUExport",
    "GPUExport",
    "RAMExport",
    "StorageExport",
    "PerformanceMetricsExport",
    "PortExport",
    "PortsExport",
    "ComponentExport",
    "PerformanceExport",
    "ValuationExport",
    "MetadataExport",
    "ListingExport",
    # Deal export
    "DealDataExport",
    # Collection export
    "CollectionExport",
    "CollectionItemExport",
    "CollectionDataExport",
    # Export metadata
    "ExportMetadata",
    # Top-level wrappers
    "PortableDealExport",
    "PortableCollectionExport",
    "PortableExport",
]
