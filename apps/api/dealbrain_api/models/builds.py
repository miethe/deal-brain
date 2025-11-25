"""Build models for saved PC build configurations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import JSONBType, StringArray, TimestampMixin

if TYPE_CHECKING:
    from .catalog import Cpu, Gpu


class SavedBuild(Base, TimestampMixin):
    """Saved PC build configuration with component selections and valuation snapshots.

    Supports the Deal Builder feature for interactive PC build configuration.
    Users can create custom builds, receive real-time valuation feedback,
    and share builds via unique share tokens.

    Soft delete pattern is implemented to maintain audit trail.
    """

    __tablename__ = "saved_builds"
    __table_args__ = (
        Index("idx_user_builds", "user_id", "deleted_at"),
        Index("idx_visibility", "visibility", "deleted_at"),
        CheckConstraint("name != ''", name="ck_saved_builds_name_not_empty"),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Ownership
    user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # FK to User table when implemented

    # Build Metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(StringArray, nullable=True)

    # Visibility & Sharing
    visibility: Mapped[str] = mapped_column(
        String(16), nullable=False, default="private", server_default="private"
    )
    share_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, default=lambda: uuid.uuid4().hex
    )

    # Component References
    cpu_id: Mapped[int | None] = mapped_column(
        ForeignKey("cpu.id", ondelete="SET NULL"), nullable=True
    )
    gpu_id: Mapped[int | None] = mapped_column(
        ForeignKey("gpu.id", ondelete="SET NULL"), nullable=True
    )
    ram_spec_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_spec_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    psu_spec_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    case_spec_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Snapshot Fields (JSONB for efficient storage and queryability)
    pricing_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONBType,
        nullable=True,
        comment="Stores {base_price, adjusted_price, delta_amount, delta_percentage}",
    )
    metrics_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONBType,
        nullable=True,
        comment="Stores {dollar_per_cpu_mark_multi, dollar_per_cpu_mark_single, composite_score}",
    )
    valuation_breakdown: Mapped[dict[str, Any] | None] = mapped_column(
        JSONBType, nullable=True, comment="Detailed breakdown of applied valuation rules"
    )

    # Soft Delete
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    cpu: Mapped[Cpu | None] = relationship(lazy="joined")
    gpu: Mapped[Gpu | None] = relationship(lazy="joined")

    def soft_delete(self) -> None:
        """Mark this build as deleted without removing from database.

        Maintains audit trail and allows for potential recovery.
        """
        self.deleted_at = datetime.now(timezone.utc)

    @property
    def is_deleted(self) -> bool:
        """Check if this build has been soft-deleted."""
        return self.deleted_at is not None

    @property
    def is_public(self) -> bool:
        """Check if this build is publicly visible."""
        return self.visibility == "public"

    @property
    def is_unlisted(self) -> bool:
        """Check if this build is unlisted (accessible via share link only)."""
        return self.visibility == "unlisted"

    @property
    def share_url(self) -> str:
        """Generate the shareable URL path for this build."""
        return f"/builds/{self.share_token}"
