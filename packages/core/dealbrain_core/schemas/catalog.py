"""Schemas for catalog entities (CPU, GPU, valuation rules, profiles)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ..enums import ComponentMetric, ComponentType, RamGeneration, StorageMedium
from .base import DealBrainModel


class CpuBase(DealBrainModel):
    name: str
    manufacturer: str
    socket: str | None = None
    cores: int | None = None
    threads: int | None = None
    tdp_w: int | None = None
    igpu_model: str | None = None
    cpu_mark_multi: int | None = None
    cpu_mark_single: int | None = None
    igpu_mark: int | None = None
    release_year: int | None = None
    notes: str | None = None
    passmark_slug: str | None = None
    passmark_category: str | None = None
    passmark_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict, alias="attributes_json")


class CpuCreate(CpuBase):
    pass


class CpuUpdate(DealBrainModel):
    """Schema for updating CPU entities. All fields optional to support partial updates (PATCH)."""

    name: str | None = None
    manufacturer: str | None = None
    socket: str | None = None
    cores: int | None = Field(None, ge=1, le=256)
    threads: int | None = Field(None, ge=1, le=512)
    tdp_w: int | None = Field(None, ge=1, le=1000)
    igpu_model: str | None = None
    cpu_mark_multi: int | None = Field(None, ge=0)
    cpu_mark_single: int | None = Field(None, ge=0)
    igpu_mark: int | None = Field(None, ge=0)
    release_year: int | None = Field(None, ge=1970, le=2100)
    notes: str | None = None
    passmark_slug: str | None = None
    passmark_category: str | None = None
    passmark_id: str | None = None
    attributes: dict[str, Any] | None = None


class CpuRead(CpuBase):
    id: int
    created_at: datetime
    updated_at: datetime


class GpuBase(DealBrainModel):
    name: str
    manufacturer: str
    gpu_mark: int | None = None
    metal_score: int | None = None
    notes: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict, alias="attributes_json")


class GpuCreate(GpuBase):
    pass


class GpuUpdate(DealBrainModel):
    """Schema for updating GPU entities. All fields optional to support partial updates (PATCH)."""

    name: str | None = None
    manufacturer: str | None = None
    gpu_mark: int | None = Field(None, ge=0)
    metal_score: int | None = Field(None, ge=0)
    notes: str | None = None
    attributes: dict[str, Any] | None = None


class GpuRead(GpuBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ValuationRuleBase(DealBrainModel):
    name: str
    component_type: ComponentType
    metric: ComponentMetric
    unit_value_usd: float
    condition_new: float = 1.0
    condition_refurb: float = 0.75
    condition_used: float = 0.6
    age_curve_json: dict[str, Any] | None = None
    notes: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class ValuationRuleCreate(ValuationRuleBase):
    pass


class ValuationRuleRead(ValuationRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime


class ProfileBase(DealBrainModel):
    name: str
    description: str | None = None
    weights_json: dict[str, float]
    is_default: bool = False


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(DealBrainModel):
    """Schema for updating Profile entities. All fields optional for partial updates (PATCH)."""

    name: str | None = None
    description: str | None = None
    weights_json: dict[str, float] | None = None
    is_default: bool | None = None


class ProfileRead(ProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime


class PortsProfileBase(DealBrainModel):
    name: str
    description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict, alias="attributes_json")


class PortsProfileCreate(PortsProfileBase):
    ports: list[PortCreate] | None = None


class PortsProfileUpdate(DealBrainModel):
    """Schema for updating PortsProfile. All fields optional for partial updates (PATCH)."""

    name: str | None = None
    description: str | None = None
    attributes: dict[str, Any] | None = None
    ports: list[PortCreate] | None = None


class PortsProfileRead(PortsProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime
    ports: list[PortRead] = Field(default_factory=list)


class RamSpecBase(DealBrainModel):
    label: str | None = None
    ddr_generation: RamGeneration = RamGeneration.UNKNOWN
    speed_mhz: int | None = None
    module_count: int | None = None
    capacity_per_module_gb: int | None = None
    total_capacity_gb: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict, alias="attributes_json")
    notes: str | None = None


class RamSpecCreate(RamSpecBase):
    pass


class RamSpecUpdate(DealBrainModel):
    """Schema for updating RamSpec entities. All fields optional for partial updates (PATCH)."""

    label: str | None = None
    ddr_generation: RamGeneration | None = None
    speed_mhz: int | None = Field(None, ge=0, le=10000)
    module_count: int | None = Field(None, ge=1, le=8)
    capacity_per_module_gb: int | None = Field(None, ge=1, le=256)
    total_capacity_gb: int | None = Field(None, ge=1, le=2048)
    attributes: dict[str, Any] | None = None
    notes: str | None = None


class RamSpecRead(RamSpecBase):
    id: int
    created_at: datetime
    updated_at: datetime


class StorageProfileBase(DealBrainModel):
    label: str | None = None
    medium: StorageMedium = StorageMedium.UNKNOWN
    interface: str | None = None
    form_factor: str | None = None
    capacity_gb: int | None = None
    performance_tier: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict, alias="attributes_json")
    notes: str | None = None


class StorageProfileCreate(StorageProfileBase):
    pass


class StorageProfileUpdate(DealBrainModel):
    """Schema for updating StorageProfile. All fields optional for partial updates (PATCH)."""

    label: str | None = None
    medium: StorageMedium | None = None
    interface: str | None = None
    form_factor: str | None = None
    capacity_gb: int | None = Field(None, ge=1, le=100000)
    performance_tier: str | None = None
    attributes: dict[str, Any] | None = None
    notes: str | None = None


class StorageProfileRead(StorageProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime


class PortBase(DealBrainModel):
    type: str
    count: int = 1
    spec_notes: str | None = None


class PortCreate(PortBase):
    pass


class PortRead(PortBase):
    id: int
    created_at: datetime
    updated_at: datetime


PortsProfileRead.model_rebuild()
