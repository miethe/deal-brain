"""Ports and connectivity profile models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import TimestampMixin

if TYPE_CHECKING:
    from .listings import Listing


class PortsProfile(Base, TimestampMixin):
    """Named collection of port specifications for a system."""

    __tablename__ = "ports_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    attributes_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    ports: Mapped[list[Port]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    listings: Mapped[list[Listing]] = relationship(back_populates="ports_profile", lazy="selectin")


class Port(Base, TimestampMixin):
    """Individual port specification within a PortsProfile."""

    __tablename__ = "port"
    __table_args__ = (
        UniqueConstraint("ports_profile_id", "type", "spec_notes", name="uq_port_profile_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ports_profile_id: Mapped[int] = mapped_column(
        ForeignKey("ports_profile.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    spec_notes: Mapped[str | None] = mapped_column(String(255))

    profile: Mapped[PortsProfile] = relationship(back_populates="ports")
