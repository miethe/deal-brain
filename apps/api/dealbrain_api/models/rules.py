"""Valuation rules system for pricing adjustments and calculations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import TimestampMixin

if TYPE_CHECKING:
    from .listings import Listing


class ValuationRuleset(Base, TimestampMixin):
    """Top-level container for a coherent set of valuation rules."""
    __tablename__ = "valuation_ruleset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    conditions_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    rule_groups: Mapped[list[ValuationRuleGroup]] = relationship(
        back_populates="ruleset", cascade="all, delete-orphan", lazy="selectin"
    )
    listings: Mapped[list[Listing]] = relationship(back_populates="ruleset", lazy="selectin")


class ValuationRuleGroup(Base, TimestampMixin):
    """Logical grouping of related valuation rules within a ruleset."""
    __tablename__ = "valuation_rule_group"
    __table_args__ = (UniqueConstraint("ruleset_id", "name", name="uq_rule_group_ruleset_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ruleset_id: Mapped[int] = mapped_column(ForeignKey("valuation_ruleset.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    weight: Mapped[float] = mapped_column(nullable=True, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    ruleset: Mapped[ValuationRuleset] = relationship(back_populates="rule_groups")
    rules: Mapped[list[ValuationRuleV2]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )


class ValuationRuleV2(Base, TimestampMixin):
    """Individual valuation rule with conditions and actions."""
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
    conditions: Mapped[list[ValuationRuleCondition]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    actions: Mapped[list[ValuationRuleAction]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    versions: Mapped[list[ValuationRuleVersion]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_logs: Mapped[list[ValuationRuleAudit]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", lazy="selectin"
    )


class ValuationRuleCondition(Base):
    """Condition that must be met for a valuation rule to apply."""
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
    parent: Mapped[ValuationRuleCondition | None] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list[ValuationRuleCondition]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )


class ValuationRuleAction(Base):
    """Action to apply when a valuation rule matches.

    Actions define how to adjust pricing or valuation based on matched conditions.
    The modifiers_json field supports two formats for applying multipliers:

    1. Dynamic Field-Based Multipliers (Primary Format):
        {
            "multipliers": [
                {
                    "name": "RAM Generation Multiplier",
                    "field": "ram_spec.ddr_generation",
                    "conditions": [
                        {"value": "ddr3", "multiplier": 0.7},
                        {"value": "ddr4", "multiplier": 1.0},
                        {"value": "ddr5", "multiplier": 1.3}
                    ]
                }
            ]
        }

    2. Legacy Condition Multipliers (Backward Compatible):
        {
            "condition_multipliers": {
                "new": 1.0,
                "refurb": 0.75,
                "used": 0.6
            }
        }

    Both formats can coexist. Field paths use dot notation to navigate nested
    structures (e.g., "ram_spec.ddr_generation"). Empty dict {} is valid.
    """
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
    """Historical version of a valuation rule for audit trail."""
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
    """Audit log for valuation rule changes and impacts."""
    __tablename__ = "valuation_rule_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_rule_v2.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(128))
    changes_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    impact_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    rule: Mapped[ValuationRuleV2 | None] = relationship(back_populates="audit_logs")
