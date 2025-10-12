"""Service layer for valuation rules CRUD operations"""

from typing import Any, Mapping, Sequence
from pydantic import BaseModel
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
from ..tasks import enqueue_listing_recalculation


class RulesService:
    """Service for managing valuation rules"""

    # --- Ruleset operations ---

    async def create_ruleset(
        self,
        session: AsyncSession,
        name: str | BaseModel | dict[str, Any],
        description: str | None = None,
        version: str = "1.0.0",
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
        priority: int = 10,
        conditions: dict[str, Any] | None = None,
        is_active: bool = True,
    ) -> ValuationRuleset:
        """Create a new ruleset.

        Accepts either explicit parameters or a schema/dict payload supplied via the `name` argument.
        """
        payload: dict[str, Any] | None = None
        if isinstance(name, BaseModel):
            payload = name.model_dump(exclude_unset=True)
        elif isinstance(name, dict):
            payload = dict(name)

        if payload is not None:
            extracted_name = payload.get("name")
            if not extracted_name:
                raise ValueError("Ruleset name is required")
            name = extracted_name
            description = payload.get("description", description)
            version = payload.get("version", version)
            created_by = payload.get("created_by", created_by)
            metadata = payload.get("metadata", metadata)
            priority = payload.get("priority", priority)
            conditions = payload.get("conditions", conditions)
            is_active = payload.get("is_active", is_active)
        elif not isinstance(name, str) or not name:
            raise ValueError("Ruleset name is required")

        if priority < 0:
            raise ValueError("Ruleset priority must be zero or greater")

        condition_payload = conditions or {}
        if condition_payload:
            # Validate condition shape before persisting
            build_condition_from_dict(condition_payload)

        ruleset = ValuationRuleset(
            name=name,
            description=description,
            version=version,
            created_by=created_by,
            metadata_json=metadata or {},
            priority=priority,
            conditions_json=condition_payload,
            is_active=is_active,
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

        enqueue_listing_recalculation(ruleset_id=ruleset.id, reason="ruleset_created")
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

        stmt = (
            stmt.order_by(
                ValuationRuleset.priority.asc(),
                ValuationRuleset.name.asc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_ruleset(
        self,
        session: AsyncSession,
        ruleset_id: int,
        updates: dict[str, Any] | BaseModel,
        updated_by: str | None = None
    ) -> ValuationRuleset | None:
        """Update ruleset"""
        ruleset = await self.get_ruleset(session, ruleset_id)
        if not ruleset:
            return None

        if isinstance(updates, BaseModel):
            updates = updates.model_dump(exclude_unset=True)
        else:
            updates = dict(updates)
        if "priority" in updates and updates["priority"] is not None:
            if updates["priority"] < 0:
                raise ValueError("Ruleset priority must be zero or greater")

        if "conditions" in updates:
            condition_payload = updates.pop("conditions") or {}
            if condition_payload:
                build_condition_from_dict(condition_payload)
            updates["conditions_json"] = condition_payload

        if "metadata" in updates and updates["metadata"] is not None:
            updates["metadata_json"] = updates.pop("metadata")

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

        enqueue_listing_recalculation(ruleset_id=ruleset_id, reason="ruleset_updated")
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

        enqueue_listing_recalculation(ruleset_id=ruleset_id, reason="ruleset_deleted")
        return True

    # --- Rule Group operations ---

    async def create_rule_group(
        self,
        session: AsyncSession,
        ruleset_id: int,
        name: str | BaseModel | dict[str, Any],
        category: str | None = None,
        description: str | None = None,
        display_order: int = 100,
        weight: float = 1.0,
        is_active: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ValuationRuleGroup:
        """Create a new rule group"""
        payload: dict[str, Any] | None = None
        if isinstance(name, BaseModel):
            payload = name.model_dump(exclude_unset=True)
        elif isinstance(name, dict):
            payload = dict(name)

        if payload is not None:
            ruleset_id = payload.get("ruleset_id", ruleset_id)
            extracted_name = payload.get("name")
            if not extracted_name:
                raise ValueError("Rule group name is required")
            name = extracted_name
            category = payload.get("category", category)
            description = payload.get("description", description)
            display_order = payload.get("display_order", display_order)
            weight = payload.get("weight", weight)
            is_active = payload.get("is_active", is_active)
            metadata = payload.get("metadata", metadata)

        if not category:
            raise ValueError("Rule group category is required")

        group = ValuationRuleGroup(
            ruleset_id=ruleset_id,
            name=name,
            category=category,
            description=description,
            display_order=display_order,
            weight=weight,
            is_active=is_active,
            metadata_json=metadata or {},
        )

        session.add(group)
        await session.commit()
        await session.refresh(group)

        enqueue_listing_recalculation(ruleset_id=ruleset_id, reason="rule_group_created")
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

    async def update_rule_group(
        self,
        session: AsyncSession,
        group_id: int,
        updates: dict[str, Any] | BaseModel,
        updated_by: str | None = None,
    ) -> ValuationRuleGroup | None:
        """Update a rule group"""
        group = await self.get_rule_group(session, group_id)
        if not group:
            return None

        if isinstance(updates, BaseModel):
            updates = updates.model_dump(exclude_unset=True)
        else:
            updates = dict(updates)

        metadata_marker = object()
        metadata_payload = updates.pop("metadata", metadata_marker)

        filtered_updates = {key: value for key, value in updates.items() if value is not None}

        for key, value in filtered_updates.items():
            if hasattr(group, key):
                setattr(group, key, value)

        if metadata_payload is not metadata_marker:
            group.metadata_json = metadata_payload or {}

        await session.commit()
        await session.refresh(group)

        enqueue_listing_recalculation(ruleset_id=group.ruleset_id, reason="rule_group_updated")
        return group

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
        parent_group = await session.get(ValuationRuleGroup, group_id)
        ruleset_id = parent_group.ruleset_id if parent_group else None

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
            self._validate_actions_payload(actions)
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

        enqueue_listing_recalculation(ruleset_id=ruleset_id, reason="rule_created")
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

        ruleset_id = rule.group.ruleset_id if rule.group else None

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
            self._validate_actions_payload(updates["actions"] or [])
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

        enqueue_listing_recalculation(ruleset_id=ruleset_id, reason="rule_updated")
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

        ruleset_id = rule.group.ruleset_id if rule.group else None

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

        enqueue_listing_recalculation(ruleset_id=ruleset_id, reason="rule_deleted")
        return True

    # --- Helper methods ---

    @staticmethod
    def _validate_actions_payload(actions: Sequence[Mapping[str, Any]] | None) -> None:
        """Ensure action payloads satisfy required fields."""
        for action in actions or []:
            action_type = action.get("action_type")
            metric = action.get("metric")
            if action_type == "per_unit" and not (metric and str(metric).strip()):
                raise ValueError("Per-unit actions must include a metric.")

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
