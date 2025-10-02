"""
Service for ruleset packaging and installation.

Handles export of rulesets to .dbrs packages and import/installation
of packages with validation and dependency resolution.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dealbrain_api.models.core import (
    ValuationRuleset,
    ValuationRuleGroup,
    ValuationRuleV2,
    ValuationRuleCondition,
    ValuationRuleAction,
    ValuationRuleAudit
)
from dealbrain_core.rules.packaging import (
    RulesetPackage,
    PackageBuilder,
    PackageMetadata,
    RulesetExport,
    RuleGroupExport,
    RuleExport,
    RuleConditionExport,
    RuleActionExport,
    CustomFieldDefinition
)


class RulesetPackagingService:
    """Service for packaging and installing rulesets."""

    async def export_ruleset_to_package(
        self,
        session: AsyncSession,
        ruleset_id: int,
        metadata: PackageMetadata,
        include_examples: bool = False
    ) -> RulesetPackage:
        """
        Export a ruleset to a complete package.

        Args:
            session: Database session
            ruleset_id: ID of the ruleset to export
            metadata: Package metadata
            include_examples: Whether to include example listings

        Returns:
            Complete RulesetPackage ready for export
        """
        # Load ruleset with all relationships
        query = (
            select(ValuationRuleset)
            .where(ValuationRuleset.id == ruleset_id)
            .options(
                selectinload(ValuationRuleset.rule_groups).selectinload(
                    ValuationRuleGroup.rules
                ).selectinload(ValuationRuleV2.conditions),
                selectinload(ValuationRuleset.rule_groups).selectinload(
                    ValuationRuleGroup.rules
                ).selectinload(ValuationRuleV2.actions)
            )
        )
        result = await session.execute(query)
        ruleset = result.scalar_one_or_none()

        if not ruleset:
            raise ValueError(f"Ruleset {ruleset_id} not found")

        # Build package
        builder = PackageBuilder()

        # Add ruleset
        ruleset_export = RulesetExport(
            id=ruleset.id,
            name=ruleset.name,
            description=ruleset.description,
            version=ruleset.version,
            is_active=ruleset.is_active,
            metadata_json=ruleset.metadata_json,
            created_by=ruleset.created_by,
            created_at=ruleset.created_at,
            updated_at=ruleset.updated_at
        )
        builder.add_ruleset(ruleset_export)

        # Add rule groups and rules
        for group in ruleset.rule_groups:
            group_export = RuleGroupExport(
                id=group.id,
                ruleset_id=group.ruleset_id,
                name=group.name,
                category=group.category,
                description=group.description,
                display_order=group.display_order,
                weight=float(group.weight) if group.weight else 1.0,
                created_at=group.created_at,
                updated_at=group.updated_at
            )
            builder.add_rule_group(group_export)

            # Add rules with conditions and actions
            for rule in group.rules:
                # Export conditions
                conditions = [
                    RuleConditionExport(
                        id=cond.id,
                        rule_id=cond.rule_id,
                        parent_condition_id=cond.parent_condition_id,
                        field_name=cond.field_name,
                        field_type=cond.field_type,
                        operator=cond.operator,
                        value_json=cond.value_json,
                        logical_operator=cond.logical_operator,
                        group_order=cond.group_order
                    )
                    for cond in rule.conditions
                ]

                # Export actions
                actions = [
                    RuleActionExport(
                        id=act.id,
                        rule_id=act.rule_id,
                        action_type=act.action_type,
                        metric=act.metric,
                        value_usd=float(act.value_usd) if act.value_usd else None,
                        unit_type=act.unit_type,
                        formula=act.formula,
                        modifiers_json=act.modifiers_json,
                        display_order=act.display_order
                    )
                    for act in rule.actions
                ]

                rule_export = RuleExport(
                    id=rule.id,
                    group_id=rule.group_id,
                    name=rule.name,
                    description=rule.description,
                    priority=rule.priority,
                    is_active=rule.is_active,
                    evaluation_order=rule.evaluation_order,
                    metadata_json=rule.metadata_json,
                    created_by=rule.created_by,
                    version=rule.version,
                    created_at=rule.created_at,
                    updated_at=rule.updated_at,
                    conditions=conditions,
                    actions=actions
                )
                builder.add_rule(rule_export)

        # Add custom field definitions (extract from conditions)
        custom_fields = await self._extract_custom_fields(session, ruleset_id)
        for field in custom_fields:
            builder.add_custom_field(field)

        # Add examples if requested
        if include_examples:
            examples = await self._get_example_listings(session, ruleset_id)
            for example in examples:
                builder.add_example(example)

        # Build and return package
        return builder.build(metadata)

    async def install_package(
        self,
        session: AsyncSession,
        package: RulesetPackage,
        actor: str,
        merge_strategy: str = "replace"
    ) -> Dict[str, Any]:
        """
        Install a ruleset package into the database.

        Args:
            session: Database session
            package: Package to install
            actor: User performing the installation
            merge_strategy: How to handle conflicts ("replace", "skip", "merge")

        Returns:
            Dict with installation results
        """
        results = {
            "rulesets_created": 0,
            "rule_groups_created": 0,
            "rules_created": 0,
            "rulesets_updated": 0,
            "warnings": []
        }

        # Validate compatibility
        app_version = "1.0.0"  # TODO: Get from settings
        available_fields = await self._get_available_custom_fields(session)
        compat = package.validate_compatibility(app_version, available_fields)

        if not compat["compatible"]:
            raise ValueError(f"Package not compatible: {compat['warnings']}")

        if compat["warnings"]:
            results["warnings"].extend(compat["warnings"])

        # Install rulesets
        id_mapping = {
            "rulesets": {},
            "rule_groups": {},
            "rules": {}
        }

        for ruleset_export in package.rulesets:
            # Check if ruleset exists
            query = select(ValuationRuleset).where(
                ValuationRuleset.name == ruleset_export.name
            )
            result = await session.execute(query)
            existing_ruleset = result.scalar_one_or_none()

            if existing_ruleset:
                if merge_strategy == "skip":
                    results["warnings"].append(
                        f"Skipped existing ruleset: {ruleset_export.name}"
                    )
                    continue
                elif merge_strategy == "replace":
                    # Update existing
                    existing_ruleset.description = ruleset_export.description
                    existing_ruleset.version = ruleset_export.version
                    existing_ruleset.is_active = ruleset_export.is_active
                    existing_ruleset.metadata_json = ruleset_export.metadata_json
                    existing_ruleset.updated_at = datetime.utcnow()
                    await session.flush()
                    id_mapping["rulesets"][ruleset_export.id] = existing_ruleset.id
                    results["rulesets_updated"] += 1
                else:
                    # Merge strategy - create new version
                    new_name = f"{ruleset_export.name} (Imported)"
                    existing_ruleset = None

            if not existing_ruleset:
                # Create new ruleset
                new_ruleset = ValuationRuleset(
                    name=ruleset_export.name,
                    description=ruleset_export.description,
                    version=ruleset_export.version,
                    is_active=ruleset_export.is_active,
                    metadata_json=ruleset_export.metadata_json,
                    created_by=actor
                )
                session.add(new_ruleset)
                await session.flush()
                id_mapping["rulesets"][ruleset_export.id] = new_ruleset.id
                results["rulesets_created"] += 1

                # Audit log
                audit = ValuationRuleAudit(
                    rule_id=None,
                    action="install_package",
                    actor=actor,
                    changes_json={
                        "package_name": package.metadata.name,
                        "package_version": package.metadata.version,
                        "ruleset_name": ruleset_export.name
                    }
                )
                session.add(audit)

        # Install rule groups
        for group_export in package.rule_groups:
            new_ruleset_id = id_mapping["rulesets"].get(group_export.ruleset_id)
            if not new_ruleset_id:
                continue

            new_group = ValuationRuleGroup(
                ruleset_id=new_ruleset_id,
                name=group_export.name,
                category=group_export.category,
                description=group_export.description,
                display_order=group_export.display_order,
                weight=group_export.weight
            )
            session.add(new_group)
            await session.flush()
            id_mapping["rule_groups"][group_export.id] = new_group.id
            results["rule_groups_created"] += 1

        # Install rules with conditions and actions
        for rule_export in package.rules:
            new_group_id = id_mapping["rule_groups"].get(rule_export.group_id)
            if not new_group_id:
                continue

            new_rule = ValuationRuleV2(
                group_id=new_group_id,
                name=rule_export.name,
                description=rule_export.description,
                priority=rule_export.priority,
                is_active=rule_export.is_active,
                evaluation_order=rule_export.evaluation_order,
                metadata_json=rule_export.metadata_json,
                created_by=actor,
                version=1  # Reset version for new install
            )
            session.add(new_rule)
            await session.flush()
            id_mapping["rules"][rule_export.id] = new_rule.id
            results["rules_created"] += 1

            # Install conditions
            condition_id_mapping = {}
            for cond_export in rule_export.conditions:
                parent_id = None
                if cond_export.parent_condition_id:
                    parent_id = condition_id_mapping.get(
                        cond_export.parent_condition_id
                    )

                new_condition = ValuationRuleCondition(
                    rule_id=new_rule.id,
                    parent_condition_id=parent_id,
                    field_name=cond_export.field_name,
                    field_type=cond_export.field_type,
                    operator=cond_export.operator,
                    value_json=cond_export.value_json,
                    logical_operator=cond_export.logical_operator,
                    group_order=cond_export.group_order
                )
                session.add(new_condition)
                await session.flush()
                condition_id_mapping[cond_export.id] = new_condition.id

            # Install actions
            for action_export in rule_export.actions:
                new_action = ValuationRuleAction(
                    rule_id=new_rule.id,
                    action_type=action_export.action_type,
                    metric=action_export.metric,
                    value_usd=action_export.value_usd,
                    unit_type=action_export.unit_type,
                    formula=action_export.formula,
                    modifiers_json=action_export.modifiers_json,
                    display_order=action_export.display_order
                )
                session.add(new_action)

        await session.commit()
        return results

    async def _extract_custom_fields(
        self,
        session: AsyncSession,
        ruleset_id: int
    ) -> List[CustomFieldDefinition]:
        """Extract custom field definitions used by the ruleset."""
        # Query all conditions for the ruleset
        query = (
            select(ValuationRuleCondition)
            .join(ValuationRuleV2)
            .join(ValuationRuleGroup)
            .where(ValuationRuleGroup.ruleset_id == ruleset_id)
        )
        result = await session.execute(query)
        conditions = result.scalars().all()

        # Extract unique custom fields
        custom_fields = {}
        for condition in conditions:
            if condition.field_name.startswith("custom."):
                field_name = condition.field_name.replace("custom.", "")
                if field_name not in custom_fields:
                    custom_fields[field_name] = CustomFieldDefinition(
                        field_name=field_name,
                        field_type=condition.field_type,
                        entity_type="listing",  # Default
                        description=f"Custom field used in conditions",
                        required=False
                    )

        return list(custom_fields.values())

    async def _get_example_listings(
        self,
        session: AsyncSession,
        ruleset_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get example listings affected by the ruleset."""
        # TODO: Implement actual listing query
        # For now, return empty list
        return []

    async def _get_available_custom_fields(
        self,
        session: AsyncSession
    ) -> List[str]:
        """Get list of available custom field names in the system."""
        # TODO: Query EntityField table for available fields
        # For now, return empty list
        return []
