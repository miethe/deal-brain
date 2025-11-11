"""Catalog models for CPU, GPU, RAM, and Storage specifications."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum as SAEnum, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dealbrain_core.enums import RamGeneration, StorageMedium

from ..db import Base
from .base import TimestampMixin

if TYPE_CHECKING:
    from .listings import Listing


class Cpu(Base, TimestampMixin):
    """CPU catalog with benchmarks and pricing analytics."""
    __tablename__ = "cpu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)
    socket: Mapped[str | None] = mapped_column(String(64))
    cores: Mapped[int | None]
    threads: Mapped[int | None]
    tdp_w: Mapped[int | None]
    igpu_model: Mapped[str | None] = mapped_column(String(255))
    cpu_mark_multi: Mapped[int | None]
    cpu_mark_single: Mapped[int | None]
    igpu_mark: Mapped[int | None]
    release_year: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)
    passmark_slug: Mapped[str | None] = mapped_column(String(512))
    passmark_category: Mapped[str | None] = mapped_column(String(64))
    passmark_id: Mapped[str | None] = mapped_column(String(64))
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Price Target Fields (computed from listing analytics)
    price_target_good: Mapped[float | None]
    price_target_great: Mapped[float | None]
    price_target_fair: Mapped[float | None]
    price_target_sample_size: Mapped[int] = mapped_column(default=0)
    price_target_confidence: Mapped[str | None] = mapped_column(String(16))
    price_target_stddev: Mapped[float | None]
    price_target_updated_at: Mapped[datetime | None]

    # Performance Value Fields ($/PassMark metrics)
    dollar_per_mark_single: Mapped[float | None]
    dollar_per_mark_multi: Mapped[float | None]
    performance_value_percentile: Mapped[float | None]
    performance_value_rating: Mapped[str | None] = mapped_column(String(16))
    performance_metrics_updated_at: Mapped[datetime | None]

    listings: Mapped[list[Listing]] = relationship(back_populates="cpu", lazy="selectin")

    @property
    def has_sufficient_pricing_data(self) -> bool:
        """Returns True if sample size >= 2 listings"""
        return self.price_target_sample_size >= 2

    @property
    def price_targets_fresh(self) -> bool:
        """Returns True if updated within last 7 days"""
        if not self.price_target_updated_at:
            return False
        age = datetime.utcnow() - self.price_target_updated_at
        return age.days < 7


class Gpu(Base, TimestampMixin):
    """GPU catalog with benchmark scores."""
    __tablename__ = "gpu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)
    gpu_mark: Mapped[int | None]
    metal_score: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    listings: Mapped[list[Listing]] = relationship(back_populates="gpu", lazy="selectin")


class RamSpec(Base, TimestampMixin):
    """RAM specification with DDR generation and module configuration."""
    __tablename__ = "ram_spec"
    __table_args__ = (
        UniqueConstraint(
            "ddr_generation",
            "speed_mhz",
            "module_count",
            "capacity_per_module_gb",
            "total_capacity_gb",
            name="uq_ram_spec_dimensions",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str | None] = mapped_column(String(128))
    ddr_generation: Mapped[RamGeneration] = mapped_column(
        SAEnum(RamGeneration, name="ram_generation", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RamGeneration.UNKNOWN,
    )
    speed_mhz: Mapped[int | None] = mapped_column(Integer)
    module_count: Mapped[int | None] = mapped_column(Integer)
    capacity_per_module_gb: Mapped[int | None] = mapped_column(Integer)
    total_capacity_gb: Mapped[int | None] = mapped_column(Integer)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)

    listings: Mapped[list[Listing]] = relationship(back_populates="ram_spec", lazy="selectin")


class StorageProfile(Base, TimestampMixin):
    """Storage specification with medium, interface, and performance tier."""
    __tablename__ = "storage_profile"
    __table_args__ = (
        UniqueConstraint(
            "medium",
            "interface",
            "form_factor",
            "capacity_gb",
            "performance_tier",
            name="uq_storage_profile_dimensions",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str | None] = mapped_column(String(128))
    medium: Mapped[StorageMedium] = mapped_column(
        SAEnum(StorageMedium, name="storage_medium", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=StorageMedium.UNKNOWN,
    )
    interface: Mapped[str | None] = mapped_column(String(64))
    form_factor: Mapped[str | None] = mapped_column(String(64))
    capacity_gb: Mapped[int | None] = mapped_column(Integer)
    performance_tier: Mapped[str | None] = mapped_column(String(64))
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)

    listings_primary: Mapped[list[Listing]] = relationship(
        back_populates="primary_storage_profile",
        foreign_keys="Listing.primary_storage_profile_id",
        lazy="selectin",
    )
    listings_secondary: Mapped[list[Listing]] = relationship(
        back_populates="secondary_storage_profile",
        foreign_keys="Listing.secondary_storage_profile_id",
        lazy="selectin",
    )
