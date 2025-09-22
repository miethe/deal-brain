from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dealbrain_core.enums import Condition, ListingStatus

from ..db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False)


class Cpu(Base, TimestampMixin):
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
    release_year: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)

    listings: Mapped[list["Listing"]] = relationship(back_populates="cpu", lazy="selectin")


class Gpu(Base, TimestampMixin):
    __tablename__ = "gpu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)
    gpu_mark: Mapped[int | None]
    metal_score: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)

    listings: Mapped[list["Listing"]] = relationship(back_populates="gpu", lazy="selectin")


class PortsProfile(Base, TimestampMixin):
    __tablename__ = "ports_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    ports: Mapped[list["Port"]] = relationship(back_populates="profile", cascade="all, delete-orphan", lazy="selectin")
    listings: Mapped[list["Listing"]] = relationship(back_populates="ports_profile", lazy="selectin")


class Port(Base, TimestampMixin):
    __tablename__ = "port"
    __table_args__ = (UniqueConstraint("ports_profile_id", "type", "spec_notes", name="uq_port_profile_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ports_profile_id: Mapped[int] = mapped_column(ForeignKey("ports_profile.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    spec_notes: Mapped[str | None] = mapped_column(String(255))

    profile: Mapped[PortsProfile] = relationship(back_populates="ports")


class Profile(Base, TimestampMixin):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weights_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    listings: Mapped[list["Listing"]] = relationship(back_populates="active_profile", lazy="selectin")


class ValuationRule(Base, TimestampMixin):
    __tablename__ = "valuation_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)
    metric: Mapped[str] = mapped_column(String(16), nullable=False)
    unit_value_usd: Mapped[float] = mapped_column(nullable=False)
    condition_new: Mapped[float] = mapped_column(nullable=False, default=1.0)
    condition_refurb: Mapped[float] = mapped_column(nullable=False, default=0.75)
    condition_used: Mapped[float] = mapped_column(nullable=False, default=0.6)
    age_curve_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)

    listing_components: Mapped[list["ListingComponent"]] = relationship(back_populates="rule")


class Listing(Base, TimestampMixin):
    __tablename__ = "listing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    seller: Mapped[str | None] = mapped_column(String(128))
    price_usd: Mapped[float] = mapped_column(nullable=False)
    price_date: Mapped[datetime | None]
    condition: Mapped[str] = mapped_column(String(16), nullable=False, default=Condition.USED.value)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=ListingStatus.ACTIVE.value)
    cpu_id: Mapped[int | None] = mapped_column(ForeignKey("cpu.id"))
    gpu_id: Mapped[int | None] = mapped_column(ForeignKey("gpu.id"))
    ports_profile_id: Mapped[int | None] = mapped_column(ForeignKey("ports_profile.id"))
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

    cpu: Mapped[Cpu | None] = relationship(back_populates="listings", lazy="joined")
    gpu: Mapped[Gpu | None] = relationship(back_populates="listings", lazy="joined")
    ports_profile: Mapped[PortsProfile | None] = relationship(back_populates="listings", lazy="joined")
    active_profile: Mapped[Profile | None] = relationship(back_populates="listings", lazy="joined")
    components: Mapped[list["ListingComponent"]] = relationship(back_populates="listing", cascade="all, delete-orphan", lazy="selectin")
    score_history: Mapped[list["ListingScoreSnapshot"]] = relationship(back_populates="listing", cascade="all, delete-orphan", lazy="selectin")


class ListingComponent(Base, TimestampMixin):
    __tablename__ = "listing_component"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listing.id", ondelete="CASCADE"), nullable=False)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_rule.id"))
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    adjustment_value_usd: Mapped[float | None]

    listing: Mapped[Listing] = relationship(back_populates="components")
    rule: Mapped[ValuationRule | None] = relationship(back_populates="listing_components")


class ListingScoreSnapshot(Base, TimestampMixin):
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


class ImportJob(Base, TimestampMixin):
    __tablename__ = "import_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    total_rows: Mapped[int | None]
    processed_rows: Mapped[int | None]
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]


class TaskRun(Base, TimestampMixin):
    __tablename__ = "task_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]


class ImportSession(Base, TimestampMixin):
    __tablename__ = "import_session"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    checksum: Mapped[str | None] = mapped_column(String(64))
    upload_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    sheet_meta_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    mappings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    conflicts_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    preview_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(128))

    audit_events: Mapped[list["ImportSessionAudit"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )


class ImportSessionAudit(Base, TimestampMixin):
    __tablename__ = "import_session_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("import_session.id", ondelete="CASCADE"), nullable=False
    )
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    session: Mapped[ImportSession] = relationship(back_populates="audit_events")
