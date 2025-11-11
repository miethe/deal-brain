"""Listing models for PC listings and their components, scores, and profiles."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dealbrain_core.enums import Condition, ListingStatus, Marketplace

from ..db import Base
from .base import TimestampMixin

if TYPE_CHECKING:
    from .catalog import Cpu, Gpu, RamSpec, StorageProfile
    from .ports import PortsProfile
    from .rules import ValuationRuleset


class Profile(Base, TimestampMixin):
    """Scoring profile with configurable weights for different metrics."""
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weights_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    rule_group_weights: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    listings: Mapped[list[Listing]] = relationship(back_populates="active_profile", lazy="selectin")


class Listing(Base, TimestampMixin):
    """PC listing with pricing, components, and performance metrics."""
    __tablename__ = "listing"
    __table_args__ = (
        UniqueConstraint("vendor_item_id", "marketplace", name="uq_listing_vendor_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    listing_url: Mapped[str | None] = mapped_column(Text)
    seller: Mapped[str | None] = mapped_column(String(128))
    price_usd: Mapped[float | None] = mapped_column(nullable=True)
    price_date: Mapped[datetime | None]
    condition: Mapped[str] = mapped_column(String(16), nullable=False, default=Condition.USED.value)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=ListingStatus.ACTIVE.value)

    # Partial Import Support (Phase 1)
    quality: Mapped[str] = mapped_column(String(20), nullable=False, default="full", server_default="full")
    extraction_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # URL Ingestion Fields (Phase 1)
    vendor_item_id: Mapped[str | None] = mapped_column(String(128))
    marketplace: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=Marketplace.OTHER.value
    )
    provenance: Mapped[str | None] = mapped_column(String(64))
    last_seen_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    dedup_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    cpu_id: Mapped[int | None] = mapped_column(ForeignKey("cpu.id"))
    gpu_id: Mapped[int | None] = mapped_column(ForeignKey("gpu.id"))
    ports_profile_id: Mapped[int | None] = mapped_column(ForeignKey("ports_profile.id"))
    ram_spec_id: Mapped[int | None] = mapped_column(ForeignKey("ram_spec.id", ondelete="SET NULL"))
    primary_storage_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_profile.id", ondelete="SET NULL")
    )
    secondary_storage_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("storage_profile.id", ondelete="SET NULL")
    )
    device_model: Mapped[str | None] = mapped_column(String(255))
    ram_gb: Mapped[int] = mapped_column(default=0)
    ram_notes: Mapped[str | None] = mapped_column(Text)
    primary_storage_gb: Mapped[int] = mapped_column(default=0)
    primary_storage_type: Mapped[str | None] = mapped_column(String(64))
    secondary_storage_gb: Mapped[int | None]
    secondary_storage_type: Mapped[str | None] = mapped_column(String(64))
    os_license: Mapped[str | None] = mapped_column(String(64))
    other_components: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    raw_listing_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    other_urls: Mapped[list[dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)

    adjusted_price_usd: Mapped[float | None]
    valuation_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    score_cpu_multi: Mapped[float | None]
    score_cpu_single: Mapped[float | None]
    score_gpu: Mapped[float | None]
    score_composite: Mapped[float | None]
    dollar_per_cpu_mark: Mapped[float | None]
    dollar_per_single_mark: Mapped[float | None]
    perf_per_watt: Mapped[float | None]
    active_profile_id: Mapped[int | None] = mapped_column(ForeignKey("profile.id"))

    # Performance Metrics (New)
    dollar_per_cpu_mark_single: Mapped[float | None]  # base_price / single-thread mark
    dollar_per_cpu_mark_single_adjusted: Mapped[float | None]  # (base_price + component_adjustments) / single-thread mark
    dollar_per_cpu_mark_multi: Mapped[float | None]  # base_price / multi-thread mark
    dollar_per_cpu_mark_multi_adjusted: Mapped[float | None]  # (base_price + component_adjustments) / multi-thread mark

    # Product Metadata (New)
    manufacturer: Mapped[str | None] = mapped_column(String(64))
    series: Mapped[str | None] = mapped_column(String(128))
    model_number: Mapped[str | None] = mapped_column(String(128))
    form_factor: Mapped[str | None] = mapped_column(String(32))

    ruleset_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_ruleset.id", ondelete="SET NULL"))

    cpu: Mapped[Cpu | None] = relationship(back_populates="listings", lazy="joined")
    gpu: Mapped[Gpu | None] = relationship(back_populates="listings", lazy="joined")
    ports_profile: Mapped[PortsProfile | None] = relationship(back_populates="listings", lazy="joined")
    active_profile: Mapped[Profile | None] = relationship(back_populates="listings", lazy="joined")
    components: Mapped[list[ListingComponent]] = relationship(back_populates="listing", cascade="all, delete-orphan", lazy="selectin")
    score_history: Mapped[list[ListingScoreSnapshot]] = relationship(back_populates="listing", cascade="all, delete-orphan", lazy="selectin")
    ruleset: Mapped[ValuationRuleset | None] = relationship(back_populates="listings", lazy="joined")
    ram_spec: Mapped[RamSpec | None] = relationship(back_populates="listings", lazy="joined")
    primary_storage_profile: Mapped[StorageProfile | None] = relationship(
        back_populates="listings_primary",
        lazy="joined",
        foreign_keys=[primary_storage_profile_id],
    )
    secondary_storage_profile: Mapped[StorageProfile | None] = relationship(
        back_populates="listings_secondary",
        lazy="joined",
        foreign_keys=[secondary_storage_profile_id],
    )

    @property
    def ram_type(self) -> str | None:
        return self.ram_spec.ddr_generation.value if self.ram_spec else None

    @property
    def ram_speed_mhz(self) -> int | None:
        return self.ram_spec.speed_mhz if self.ram_spec else None

    @property
    def cpu_name(self) -> str | None:
        """Denormalized CPU name for frontend convenience."""
        return self.cpu.name if self.cpu else None

    @property
    def gpu_name(self) -> str | None:
        """Denormalized GPU name for frontend convenience."""
        return self.gpu.name if self.gpu else None

    @property
    def thumbnail_url(self) -> str | None:
        """Extract thumbnail URL from raw listing JSON or attributes."""
        if self.raw_listing_json:
            # Check common fields from marketplace adapters
            for key in ['image_url', 'thumbnail_url', 'imageUrl', 'thumbnailUrl', 'img_url']:
                if key in self.raw_listing_json and self.raw_listing_json[key]:
                    return self.raw_listing_json[key]

        # Fallback to attributes_json
        if self.attributes_json:
            for key in ['image_url', 'thumbnail_url']:
                if key in self.attributes_json and self.attributes_json[key]:
                    return self.attributes_json[key]

        return None


class ListingComponent(Base, TimestampMixin):
    """Component associated with a listing (e.g., RAM, storage, GPU)."""
    __tablename__ = "listing_component"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    adjustment_value_usd: Mapped[float | None]

    listing: Mapped[Listing] = relationship(back_populates="components")


class ListingScoreSnapshot(Base, TimestampMixin):
    """Historical snapshot of listing scores for trend analysis."""
    __tablename__ = "listing_score_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profile.id"))
    score_composite: Mapped[float | None]
    adjusted_price_usd: Mapped[float | None]
    dollar_per_cpu_mark: Mapped[float | None]
    dollar_per_single_mark: Mapped[float | None]
    perf_per_watt: Mapped[float | None]
    explain_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    listing: Mapped[Listing] = relationship(back_populates="score_history")
    profile: Mapped[Profile | None] = relationship()
