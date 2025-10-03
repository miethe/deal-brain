from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, func, Index
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
    igpu_mark: Mapped[int | None]
    release_year: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    listings: Mapped[list["Listing"]] = relationship(back_populates="cpu", lazy="selectin")


class Gpu(Base, TimestampMixin):
    __tablename__ = "gpu"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(64), nullable=False)
    gpu_mark: Mapped[int | None]
    metal_score: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    listings: Mapped[list["Listing"]] = relationship(back_populates="gpu", lazy="selectin")


class PortsProfile(Base, TimestampMixin):
    __tablename__ = "ports_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

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
    rule_group_weights: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)

    listings: Mapped[list["Listing"]] = relationship(back_populates="active_profile", lazy="selectin")


class ValuationRuleset(Base, TimestampMixin):
    __tablename__ = "valuation_ruleset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    rule_groups: Mapped[list["ValuationRuleGroup"]] = relationship(
        back_populates="ruleset", cascade="all, delete-orphan", lazy="selectin"
    )


class ValuationRuleGroup(Base, TimestampMixin):
    __tablename__ = "valuation_rule_group"
    __table_args__ = (UniqueConstraint("ruleset_id", "name", name="uq_rule_group_ruleset_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ruleset_id: Mapped[int] = mapped_column(ForeignKey("valuation_ruleset.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    weight: Mapped[float] = mapped_column(nullable=True, default=1.0)

    ruleset: Mapped[ValuationRuleset] = relationship(back_populates="rule_groups")
    rules: Mapped[list["ValuationRuleV2"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )


class ValuationRuleV2(Base, TimestampMixin):
    __tablename__ = "valuation_rule_v2"
    __table_args__ = (UniqueConstraint("group_id", "name", name="uq_rule_v2_group_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("valuation_rule_group.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evaluation_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str | None] = mapped_column(String(128))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    group: Mapped[ValuationRuleGroup] = relationship(back_populates="rules")
    conditions: Mapped[list["ValuationRuleCondition"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    actions: Mapped[list["ValuationRuleAction"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    versions: Mapped[list["ValuationRuleVersion"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_logs: Mapped[list["ValuationRuleAudit"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )


class ValuationRuleCondition(Base):
    __tablename__ = "valuation_rule_condition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("valuation_rule_v2.id", ondelete="CASCADE"), nullable=False)
    parent_condition_id: Mapped[int | None] = mapped_column(
        ForeignKey("valuation_rule_condition.id", ondelete="CASCADE")
    )
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    field_type: Mapped[str] = mapped_column(String(32), nullable=False)
    operator: Mapped[str] = mapped_column(String(32), nullable=False)
    value_json: Mapped[dict[str, Any] | list[Any] | str | int | float] = mapped_column(JSON, nullable=False)
    logical_operator: Mapped[str | None] = mapped_column(String(8))
    group_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    rule: Mapped[ValuationRuleV2] = relationship(back_populates="conditions")
    parent: Mapped["ValuationRuleCondition | None"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["ValuationRuleCondition"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )


class ValuationRuleAction(Base):
    __tablename__ = "valuation_rule_action"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("valuation_rule_v2.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    metric: Mapped[str | None] = mapped_column(String(32))
    value_usd: Mapped[float | None]
    unit_type: Mapped[str | None] = mapped_column(String(32))
    formula: Mapped[str | None] = mapped_column(Text)
    modifiers_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    rule: Mapped[ValuationRuleV2] = relationship(back_populates="actions")


class ValuationRuleVersion(Base):
    __tablename__ = "valuation_rule_version"
    __table_args__ = (UniqueConstraint("rule_id", "version_number", name="uq_rule_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("valuation_rule_v2.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    rule: Mapped[ValuationRuleV2] = relationship(back_populates="versions")


class ValuationRuleAudit(Base):
    __tablename__ = "valuation_rule_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_rule_v2.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(128))
    changes_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    impact_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    rule: Mapped[ValuationRuleV2 | None] = relationship(back_populates="audit_logs")


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
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

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
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    adjustment_value_usd: Mapped[float | None]

    listing: Mapped[Listing] = relationship(back_populates="components")


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
    declared_entities_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
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


class CustomFieldDefinition(Base, TimestampMixin):
    __tablename__ = "custom_field_definition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    data_type: Mapped[str] = mapped_column(String(32), nullable=False, default="string")
    description: Mapped[str | None] = mapped_column(Text)
    required: Mapped[bool] = mapped_column(nullable=False, default=False)
    default_value: Mapped[Any | None] = mapped_column(JSON)
    options: Mapped[list[str] | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="public")
    created_by: Mapped[str | None] = mapped_column(String(128))
    validation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=dict)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    deleted_at: Mapped[datetime | None]

    __table_args__ = (
        UniqueConstraint("entity", "key", name="uq_custom_field_entity_key"),
        Index("ix_custom_field_definition_entity", "entity"),
        Index("ix_custom_field_definition_order", "entity", "display_order"),
    )

    audit_events: Mapped[list["CustomFieldAuditLog"]] = relationship(
        back_populates="field", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def validation(self) -> dict[str, Any] | None:
        return self.validation_json or None

    @validation.setter
    def validation(self, value: dict[str, Any] | None) -> None:
        self.validation_json = value or None


class CustomFieldAuditLog(Base, TimestampMixin):
    __tablename__ = "custom_field_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("custom_field_definition.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(128))
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    field: Mapped[CustomFieldDefinition] = relationship(back_populates="audit_events")


class CustomFieldAttributeHistory(Base, TimestampMixin):
    __tablename__ = "custom_field_attribute_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("custom_field_definition.id", ondelete="CASCADE"), nullable=False
    )
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    attribute_key: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_value: Mapped[Any | None] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(String(64), nullable=False, default="archived")

    __table_args__ = (
        Index("ix_custom_field_attribute_history_field", "field_id", "created_at"),
        Index("ix_custom_field_attribute_history_entity_record", "entity", "record_id"),
    )


class ApplicationSettings(Base, TimestampMixin):
    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
