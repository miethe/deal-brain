"""Base models and mixins for SQLAlchemy models."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class StringArray(TypeDecorator):
    """A type that uses PostgreSQL ARRAY for PostgreSQL and JSON-encoded TEXT for SQLite.

    This allows models to use list[str] columns that work seamlessly across
    PostgreSQL (production) and SQLite (testing) environments.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Use ARRAY for PostgreSQL, Text for everything else (SQLite)."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(Text))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        """Convert Python list to DB format."""
        if dialect.name == "postgresql":
            # PostgreSQL handles arrays natively
            return value
        else:
            # SQLite: encode as JSON string
            if value is not None:
                return json.dumps(value)
            return value

    def process_result_value(self, value, dialect):
        """Convert DB format to Python list."""
        if dialect.name == "postgresql":
            # PostgreSQL returns arrays directly
            return value
        else:
            # SQLite: decode from JSON string
            if value is not None:
                return json.loads(value)
            return value


class JSONBType(TypeDecorator):
    """A type that uses PostgreSQL JSONB for PostgreSQL and JSON for SQLite.

    This allows models to use dict columns that work seamlessly across
    PostgreSQL (production) and SQLite (testing) environments.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Use JSONB for PostgreSQL, JSON for everything else (SQLite)."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False)
