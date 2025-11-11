"""Base models and mixins for SQLAlchemy models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False)
