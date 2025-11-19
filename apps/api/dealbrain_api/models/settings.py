"""Application settings and custom field definition models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import TimestampMixin


class ApplicationSettings(Base, TimestampMixin):
    """Global application configuration stored in database."""

    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class CustomFieldDefinition(Base, TimestampMixin):
    """Dynamic custom field definitions for extensible entity attributes."""

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

    audit_events: Mapped[list[CustomFieldAuditLog]] = relationship(
        back_populates="field", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def validation(self) -> dict[str, Any] | None:
        return self.validation_json or None

    @validation.setter
    def validation(self, value: dict[str, Any] | None) -> None:
        self.validation_json = value or None


class CustomFieldAuditLog(Base, TimestampMixin):
    """Audit trail for custom field definition changes."""

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
    """Historical tracking of custom field value changes on entities."""

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
