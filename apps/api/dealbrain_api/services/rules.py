"""Service layer for valuation rules CRUD operations"""

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dealbrain_core.rules import (
    Condition,
    ConditionGroup,
    Action,
    build_condition_from_dict,
    build_action_from_dict,
)

from ..models.core import (
    ValuationRuleset,
    ValuationRuleGroup,
    ValuationRuleV2,
    ValuationRuleCondition,
    ValuationRuleAction,
    ValuationRuleVersion,
    ValuationRuleAudit,
)


class RulesService:
    """Service for managing valuation rules"""

    # --- Ruleset operations ---

    async def create_ruleset(
        self,
        session: AsyncSession,
        name: str,
        description: str | None = None,
        version: str = "1.0.0",
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ValuationRuleset:
        """Create a new ruleset"""
        ruleset = ValuationRuleset(
            name=name,
            description=description,
            version=version,
            created_by=created_by,
            metadata_json=metadata or {},
        )

        session.add(ruleset)
        await session.commit()
        await session.refresh(ruleset)

        # Audit
        await self._audit_action(
            session,
            rule_id=None,
            action="ruleset_created",
            actor=created_by,
            changes={"ruleset_id": ruleset.id, "name": name}
        )

        return ruleset

    async def get_ruleset(
        self,
        session: AsyncSession,
        ruleset_id: int
    ) -> ValuationRuleset | None:
        """Get ruleset by ID with all related data"""
        stmt = (
            select(ValuationRuleset)
            .where(ValuationRuleset.id == ruleset_id)
            .options(selectinload(ValuationRuleset.rule_groups))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rulesets(
        self,
        session: AsyncSession,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> list[ValuationRuleset]:
        """List all rulesets"""
        stmt = select(ValuationRuleset)

        if active_only:
            stmt = stmt.where(ValuationRuleset.is_active == True)

        stmt = stmt.offset(skip).limit(limit).order_by(ValuationRuleset.name)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_ruleset(
        self,
        session: AsyncSession,
        ruleset_id: int,
        updates: dict[str, Any],
        updated_by: str | None = None
    ) -> ValuationRuleset | None:
        """Update ruleset"""
        ruleset = await self.get_ruleset(session, ruleset_id)
        if not ruleset:
            return None

        for key, value in updates.items():
            if hasattr(ruleset, key):
                setattr(ruleset, key, value)

        await session.commit()
        await session.refresh(ruleset)

        # Audit
        await self._audit_action(
            session,
            rule_id=None,
            action="ruleset_updated",
            actor=updated_by,
            changes={"ruleset_id": ruleset_id, "updates": updates}
        )

        return ruleset

    async def delete_ruleset(
        self,
        session: AsyncSession,
        ruleset_id: int,
        deleted_by: str | None = None
    ) -> bool:
        """Delete ruleset (cascades to groups and rules)"""
        ruleset = await self.get_ruleset(session, ruleset_id)
        if not ruleset:
            return False

        # Audit before delete
        await self._audit_action(
            session,
            rule_id=None,
            action="ruleset_deleted",
            actor=deleted_by,
            changes={"ruleset_id": ruleset_id, "name": ruleset.name}
        )

        await session.delete(ruleset)
        await session.commit()
        return True

    # --- Rule Group operations ---

    async def create_rule_group(
        self,
        session: AsyncSession,
        ruleset_id: int,
        name: str,
        category: str,
        description: str | None = None,
        display_order: int = 100,
        weight: float = 1.0,
    ) -> ValuationRuleGroup:
        """Create a new rule group"""
        group = ValuationRuleGroup(
            ruleset_id=ruleset_id,
            name=name,
            category=category,
            description=description,
            display_order=display_order,
            weight=weight,
        )

        session.add(group)
        await session.commit()
        await session.refresh(group)

        return group

    async def get_rule_group(
        self,
        session: AsyncSession,
        group_id: int
    ) -> ValuationRuleGroup | None:
        """Get rule group by ID"""
        stmt = (
            select(ValuationRuleGroup)
            .where(ValuationRuleGroup.id == group_id)
            .options(selectinload(ValuationRuleGroup.rules))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rule_groups(
        self,
        session: AsyncSession,
        ruleset_id: int | None = None,
        category: str | None = None
    ) -> list[ValuationRuleGroup]:
        """List rule groups"""
        stmt = select(ValuationRuleGroup)

        if ruleset_id:
            stmt = stmt.where(ValuationRuleGroup.ruleset_id == ruleset_id)
        if category:
            stmt = stmt.where(ValuationRuleGroup.category == category)

        stmt = stmt.order_by(ValuationRuleGroup.display_order, ValuationRuleGroup.name)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    # --- Rule operations ---

    async def create_rule(
        self,
        session: AsyncSession,
        group_id: int,
        name: str,
        description: str | None = None,
        priority: int = 100,
        evaluation_order: int = 100,
        conditions: list[dict[str, Any]] | None = None,
        actions: list[dict[str, Any]] | None = None,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ValuationRuleV2:
        """Create a new rule with conditions and actions"""
        # Create rule
        rule = ValuationRuleV2(
            group_id=group_id,
            name=name,
            description=description,
            priority=priority,
            evaluation_order=evaluation_order,
            created_by=created_by,
            metadata_json=metadata or {},
        )

        session.add(rule)
        await session.flush()  # Get rule ID

        # Add conditions
        if conditions:
            for cond_data in conditions:
                condition = ValuationRuleCondition(
                    rule_id=rule.id,
                    field_name=cond_data["field_name"],
                    field_type=cond_data["field_type"],
                    operator=cond_data["operator"],
                    value_json=cond_data["value"],
                    logical_operator=cond_data.get("logical_operator"),
                    group_order=cond_data.get("group_order", 0),
                )
                session.add(condition)

        # Add actions
        if actions:
            for idx, action_data in enumerate(actions):
                action = ValuationRuleAction(
                    rule_id=rule.id,
                    action_type=action_data["action_type"],
                    metric=action_data.get("metric"),
                    value_usd=action_data.get("value_usd"),
                    unit_type=action_data.get("unit_type"),
                    formula=action_data.get("formula"),
                    modifiers_json=action_data.get("modifiers", {}),
                    display_order=idx,
                )
                session.add(action)

        await session.commit()
        await session.refresh(rule)

        # Create version snapshot
        await self._create_version_snapshot(session, rule, created_by, "Initial version")

        # Audit
        await self._audit_action(
            session,
            rule_id=rule.id,
            action="rule_created",
            actor=created_by,
            changes={"rule_name": name, "group_id": group_id}
        )

        return rule

    async def get_rule(
        self,
        session: AsyncSession,
        rule_id: int
    ) -> ValuationRuleV2 | None:
        """Get rule by ID with all related data"""
        stmt = (
            select(ValuationRuleV2)
            .where(ValuationRuleV2.id == rule_id)
            .options(
                selectinload(ValuationRuleV2.conditions),
                selectinload(ValuationRuleV2.actions),
                selectinload(ValuationRuleV2.group),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_rules(
        self,
        session: AsyncSession,
        group_id: int | None = None,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> list[ValuationRuleV2]:
        """List rules"""
        stmt = select(ValuationRuleV2)

        if group_id:
            stmt = stmt.where(ValuationRuleV2.group_id == group_id)
        if active_only:
            stmt = stmt.where(ValuationRuleV2.is_active == True)

        stmt = (
            stmt.offset(skip)
            .limit(limit)
            .order_by(ValuationRuleV2.evaluation_order, ValuationRuleV2.priority)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_rule(
        self,
        session: AsyncSession,
        rule_id: int,
        updates: dict[str, Any],
        updated_by: str | None = None,
        change_summary: str | None = None
    ) -> ValuationRuleV2 | None:
        """Update rule and create version snapshot"""
        rule = await self.get_rule(session, rule_id)
        if not rule:
            return None

        # Update basic fields
        for key in ["name", "description", "priority", "is_active", "evaluation_order"]:
            if key in updates:
                setattr(rule, key, updates[key])

        # Update metadata
        if "metadata" in updates:
            rule.metadata_json = updates["metadata"]

        # Increment version
        rule.version += 1

        # Update conditions if provided
        if "conditions" in updates:
            # Delete existing conditions
            for cond in rule.conditions:
                await session.delete(cond)
            await session.flush()

            # Add new conditions
            for cond_data in updates["conditions"]:
                condition = ValuationRuleCondition(
                    rule_id=rule.id,
                    field_name=cond_data["field_name"],
                    field_type=cond_data["field_type"],
                    operator=cond_data["operator"],
                    value_json=cond_data["value"],
                    logical_operator=cond_data.get("logical_operator"),
                    group_order=cond_data.get("group_order", 0),
                )
                session.add(condition)

        # Update actions if provided
        if "actions" in updates:
            # Delete existing actions
            for action in rule.actions:
                await session.delete(action)
            await session.flush()

            # Add new actions
            for idx, action_data in enumerate(updates["actions"]):
                action = ValuationRuleAction(
                    rule_id=rule.id,
                    action_type=action_data["action_type"],
                    metric=action_data.get("metric"),
                    value_usd=action_data.get("value_usd"),
                    unit_type=action_data.get("unit_type"),
                    formula=action_data.get("formula"),
                    modifiers_json=action_data.get("modifiers", {}),
                    display_order=idx,
                )
                session.add(action)

        await session.commit()
        await session.refresh(rule)

        # Create version snapshot
        await self._create_version_snapshot(session, rule, updated_by, change_summary)

        # Audit
        await self._audit_action(
            session,
            rule_id=rule.id,
            action="rule_updated",
            actor=updated_by,
            changes=updates
        )

        return rule

    async def delete_rule(
        self,
        session: AsyncSession,
        rule_id: int,
        deleted_by: str | None = None
    ) -> bool:
        """Delete rule"""
        rule = await self.get_rule(session, rule_id)
        if not rule:
            return False

        # Audit before delete
        await self._audit_action(
            session,
            rule_id=rule.id,
            action="rule_deleted",
            actor=deleted_by,
            changes={"rule_name": rule.name}
        )

        await session.delete(rule)
        await session.commit()
        return True

    # --- Helper methods ---

    async def _create_version_snapshot(
        self,
        session: AsyncSession,
        rule: ValuationRuleV2,
        changed_by: str | None,
        change_summary: str | None
    ) -> ValuationRuleVersion:
        """Create version snapshot of rule"""
        snapshot = {
            "name": rule.name,
            "description": rule.description,
            "priority": rule.priority,
            "evaluation_order": rule.evaluation_order,
            "metadata": rule.metadata_json,
            "conditions": [
                {
                    "field_name": c.field_name,
                    "field_type": c.field_type,
                    "operator": c.operator,
                    "value": c.value_json,
                    "logical_operator": c.logical_operator,
                    "group_order": c.group_order,
                }
                for c in rule.conditions
            ],
            "actions": [
                {
                    "action_type": a.action_type,
                    "metric": a.metric,
                    "value_usd": a.value_usd,
                    "unit_type": a.unit_type,
                    "formula": a.formula,
                    "modifiers": a.modifiers_json,
                }
                for a in rule.actions
            ],
        }

        version = ValuationRuleVersion(
            rule_id=rule.id,
            version_number=rule.version,
            snapshot_json=snapshot,
            change_summary=change_summary,
            changed_by=changed_by,
        )

        session.add(version)
        await session.commit()
        return version

    async def _audit_action(
        self,
        session: AsyncSession,
        rule_id: int | None,
        action: str,
        actor: str | None,
        changes: dict[str, Any] | None = None,
        impact: dict[str, Any] | None = None
    ) -> ValuationRuleAudit:
        """Create audit log entry"""
        audit = ValuationRuleAudit(
            rule_id=rule_id,
            action=action,
            actor=actor,
            changes_json=changes,
            impact_summary=impact,
        )

        session.add(audit)
        await session.commit()
        return audit

    async def get_audit_log(
        self,
        session: AsyncSession,
        rule_id: int | None = None,
        limit: int = 100
    ) -> list[ValuationRuleAudit]:
        """Get audit log entries"""
        stmt = select(ValuationRuleAudit)

        if rule_id:
            stmt = stmt.where(ValuationRuleAudit.rule_id == rule_id)

        stmt = stmt.order_by(ValuationRuleAudit.created_at.desc()).limit(limit)

        result = await session.execute(stmt)
        return list(result.scalars().all())
