"""Database models for baseline audit logging."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class BaselineAuditLog(Base):
    """Audit log for baseline valuation operations."""

    __tablename__ = "baseline_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor_name: Mapped[str | None] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        index=True
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result: Mapped[str] = mapped_column(
        String(16), nullable=False, default="success"
    )  # success, failure
    error_message: Mapped[str | None] = mapped_column(Text)

    # Specific fields for different operations
    ruleset_id: Mapped[int | None] = mapped_column(Integer, index=True)
    source_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    version: Mapped[str | None] = mapped_column(String(32))
    entity_key: Mapped[str | None] = mapped_column(String(128))
    field_name: Mapped[str | None] = mapped_column(String(128))

    # Impact tracking
    affected_listings_count: Mapped[int | None] = mapped_column(Integer)
    total_adjustment_change: Mapped[float | None] = mapped_column(JSON)  # Store as Decimal

    def to_dict(self) -> dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "operation": self.operation,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "ruleset_id": self.ruleset_id,
            "source_hash": self.source_hash,
            "version": self.version,
            "entity_key": self.entity_key,
            "field_name": self.field_name,
            "affected_listings_count": self.affected_listings_count,
            "total_adjustment_change": self.total_adjustment_change,
        }