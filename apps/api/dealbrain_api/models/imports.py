"""Import and task tracking models for data ingestion."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dealbrain_core.enums import SourceType

from ..db import Base
from .base import TimestampMixin


class ImportJob(Base, TimestampMixin):
    """Legacy import job tracking (Excel/file-based imports)."""

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
    """Generic task execution tracking for background jobs."""

    __tablename__ = "task_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]


class ImportSession(Base, TimestampMixin):
    """Unified import session for both file-based and URL-based imports."""

    __tablename__ = "import_session"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128))
    checksum: Mapped[str | None] = mapped_column(String(64))
    upload_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    sheet_meta_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    mappings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    conflicts_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    preview_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    declared_entities_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_by: Mapped[str | None] = mapped_column(String(128))

    # URL Ingestion Fields (Phase 1)
    source_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default=SourceType.EXCEL.value
    )
    url: Mapped[str | None] = mapped_column(Text)
    adapter_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Progress tracking for URL ingestion (Phase 2)
    progress_pct: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)

    # Bulk Job Tracking (Phase 1.2)
    bulk_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    quality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listing.id", ondelete="SET NULL"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    audit_events: Mapped[list[ImportSessionAudit]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )


class ImportSessionAudit(Base, TimestampMixin):
    """Audit trail for import session events and changes."""

    __tablename__ = "import_session_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("import_session.id", ondelete="CASCADE"), nullable=False
    )
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    session: Mapped[ImportSession] = relationship(back_populates="audit_events")
