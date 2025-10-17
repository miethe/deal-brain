"""Service for hydrating baseline placeholder rules into full rule structures.

This service converts compact baseline rules (stored with metadata like valuation_buckets
and formula_text) into expanded, editable rules with explicit conditions and actions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.core import ValuationRuleGroup, ValuationRuleV2
from .rules import RulesService

logger = logging.getLogger(__name__)


@dataclass
class HydrationResult:
    """Result of hydrating baseline rules in a ruleset."""

    status: str
    ruleset_id: int
    hydrated_rule_count: int
    created_rule_count: int
    hydration_summary: list[dict[str, Any]]


class BaselineHydrationService:
    """Service for hydrating baseline placeholder rules into editable rule structures."""

    # Entity keys that represent foreign key relationships
    FK_ENTITY_KEYS = {"cpu", "gpu", "storage", "ram_spec", "ports"}

    def __init__(self, rules_service: RulesService | None = None) -> None:
        """Initialize the hydration service.

        Args:
            rules_service: RulesService instance for creating rules.
                          If None, creates a new instance with recalculation disabled.
        """
        # Disable recalculation during hydration to avoid triggering on each rule
        self.rules_service = rules_service or RulesService(trigger_recalculation=False)

    def _is_foreign_key_rule(self, rule: ValuationRuleV2) -> bool:
        """Determine if a rule represents a foreign key relationship.

        Args:
            rule: The rule to check

        Returns:
            True if the rule's entity_key is in the FK entity keys set
        """
        entity_key = rule.metadata_json.get("entity_key", "")
        is_fk = entity_key in self.FK_ENTITY_KEYS

        if is_fk:
            logger.debug(
                f"Rule {rule.id} ({rule.name}) identified as FK rule with entity_key: {entity_key}"
            )

        return is_fk

    async def hydrate_baseline_rules(
        self, session: AsyncSession, ruleset_id: int, actor: str = "system"
    ) -> HydrationResult:
        """Hydrate all placeholder baseline rules in a ruleset.

        This method:
        1. Finds all rules marked as baseline_placeholder in the ruleset
        2. Expands each placeholder into full rules with conditions/actions
        3. Marks original placeholders as hydrated and deactivates them
        4. Returns a summary of the hydration operation

        Args:
            session: Database session
            ruleset_id: ID of the ruleset to hydrate
            actor: User or system identifier performing the hydration

        Returns:
            HydrationResult with status, counts, and summary
        """
        # Find all placeholder rules in the ruleset
        stmt = (
            select(ValuationRuleV2)
            .join(ValuationRuleGroup)
            .where(
                ValuationRuleGroup.ruleset_id == ruleset_id,
                ValuationRuleV2.metadata_json["baseline_placeholder"].as_boolean() == True,
            )
        )
        result = await session.execute(stmt)
        placeholder_rules = result.scalars().all()

        hydrated_count = 0
        created_count = 0
        summary = []

        for rule in placeholder_rules:
            # Skip if already hydrated
            if rule.metadata_json.get("hydrated"):
                continue

            # Hydrate single rule
            expanded_rules = await self.hydrate_single_rule(session, rule.id, actor=actor)

            # Mark original as hydrated and deactivate
            rule.is_active = False
            rule.metadata_json = {
                **rule.metadata_json,
                "hydrated": True,
                "hydrated_at": datetime.utcnow().isoformat(),
                "hydrated_by": actor,
            }

            hydrated_count += 1
            created_count += len(expanded_rules)

            summary.append(
                {
                    "original_rule_id": rule.id,
                    "field_name": rule.name,
                    "field_type": rule.metadata_json.get("field_type"),
                    "expanded_rule_ids": [r.id for r in expanded_rules],
                }
            )

        await session.commit()

        return HydrationResult(
            status="success",
            ruleset_id=ruleset_id,
            hydrated_rule_count=hydrated_count,
            created_rule_count=created_count,
            hydration_summary=summary,
        )

    async def hydrate_single_rule(
        self, session: AsyncSession, rule_id: int, actor: str = "system"
    ) -> list[ValuationRuleV2]:
        """Hydrate a single placeholder rule into expanded rules.

        Routes to the appropriate hydration strategy based on field_type metadata:
        - enum_multiplier: Creates one rule per enum value with conditions
        - formula: Creates single rule with formula action
        - fixed/additive: Creates single rule with fixed value action
        - scalar: Skipped (represents FK relationships, not valuation rules)

        Args:
            session: Database session
            rule_id: ID of the placeholder rule to hydrate
            actor: User or system identifier performing the hydration

        Returns:
            List of expanded rules created from the placeholder.
            Empty list if rule is scalar type (FK relationship).

        Raises:
            ValueError: If rule not found or not a baseline placeholder
        """
        # Load rule
        stmt = select(ValuationRuleV2).where(ValuationRuleV2.id == rule_id)
        result = await session.execute(stmt)
        rule = result.scalar_one_or_none()

        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        if not rule.metadata_json.get("baseline_placeholder"):
            raise ValueError(f"Rule {rule_id} is not a baseline placeholder")

        # Determine field type
        field_type = rule.metadata_json.get("field_type", "fixed")

        # Skip scalar fields - they represent FK relationships, not valuation rules
        if field_type == "scalar":
            logger.info(
                f"Skipping hydration for scalar field rule {rule.id} ({rule.name}). "
                "Scalar fields represent foreign key relationships."
            )
            return []

        # Route to strategy
        if field_type == "enum_multiplier":
            return await self._hydrate_enum_multiplier(session, rule, actor)
        elif field_type == "formula":
            return await self._hydrate_formula(session, rule, actor)
        else:  # fixed, additive, etc.
            return await self._hydrate_fixed(session, rule, actor)

    async def _hydrate_enum_multiplier(
        self, session: AsyncSession, rule: ValuationRuleV2, actor: str
    ) -> list[ValuationRuleV2]:
        """Create one rule per enum value with condition + multiplier action.

        For enum fields like DDR generation, creates a separate rule for each enum value
        with a condition matching that value and a multiplier action.

        Args:
            session: Database session
            rule: Placeholder rule to expand
            actor: User or system identifier

        Returns:
            List of expanded rules, one per enum value
        """
        valuation_buckets = rule.metadata_json.get("valuation_buckets", {})
        field_path = rule.metadata_json.get("field_id")  # e.g., "ram_spec.ddr_generation"

        # Validate required fields
        if not field_path:
            logger.warning(
                f"No field_id found in enum_multiplier rule {rule.id}. "
                f"Metadata keys: {list(rule.metadata_json.keys())}"
            )
            return []

        if not valuation_buckets:
            logger.warning(f"Empty valuation_buckets for enum_multiplier rule {rule.id}")
            return []

        expanded_rules = []

        for enum_value, multiplier in valuation_buckets.items():
            # Validate multiplier is not None and can be converted to float
            if multiplier is None:
                logger.warning(
                    f"Null multiplier for enum value '{enum_value}' in rule {rule.id}. Skipping."
                )
                continue

            try:
                multiplier_float = float(multiplier)
            except (TypeError, ValueError) as e:
                logger.warning(
                    f"Invalid multiplier value '{multiplier}' for enum value '{enum_value}' "
                    f"in rule {rule.id}: {str(e)}. Skipping."
                )
                continue

            # Create condition
            condition = {
                "field_name": field_path,
                "field_type": "string",  # Enums are stored as strings
                "operator": "equals",
                "value": enum_value,
                "logical_operator": None,
                "group_order": 0,
            }

            # Create action (multiplier * 100 for percentage)
            # The multiplier is stored as decimal (e.g., 0.7 for 70%)
            # but action value_usd expects percentage (70.0)
            action = {
                "action_type": "multiplier",
                "value_usd": multiplier_float * 100.0,
                "metric": None,
                "unit_type": None,
                "formula": None,
                "modifiers": {"original_multiplier": multiplier_float},
            }

            # Create rule
            new_rule = await self.rules_service.create_rule(
                session=session,
                group_id=rule.group_id,
                name=f"{rule.name}: {enum_value}",
                description=f"{rule.description or rule.name} - {enum_value}",
                priority=rule.priority,
                evaluation_order=rule.evaluation_order,
                conditions=[condition],
                actions=[action],
                created_by=actor,
                metadata={
                    "hydration_source_rule_id": rule.id,
                    "enum_value": enum_value,
                    "field_type": "enum_multiplier",
                    "is_foreign_key_rule": self._is_foreign_key_rule(rule),
                },
            )
            expanded_rules.append(new_rule)

        return expanded_rules

    async def _hydrate_formula(
        self, session: AsyncSession, rule: ValuationRuleV2, actor: str
    ) -> list[ValuationRuleV2]:
        """Create single rule with formula action.

        For formula-based rules like RAM capacity pricing, creates a rule
        with a formula action and no conditions (applies to all).

        Args:
            session: Database session
            rule: Placeholder rule to expand
            actor: User or system identifier

        Returns:
            List containing single formula rule
        """
        # Check multiple possible formula keys
        formula_text = (
            rule.metadata_json.get("formula_text")
            or rule.metadata_json.get("Formula")
            or rule.metadata_json.get("formula")
        )

        if not formula_text:
            logger.warning(
                f"No formula found in metadata for rule {rule.id}. "
                f"Metadata keys: {list(rule.metadata_json.keys())}"
            )
            # Fall back to fixed strategy
            return await self._hydrate_fixed(session, rule, actor)

        # Validate that the formula can be parsed
        try:
            from dealbrain_core.rules.formula import FormulaEngine

            engine = FormulaEngine()
            # Try to parse the formula to ensure it's valid
            engine.parser.parse(formula_text)
            logger.info(
                f"Formula validated successfully for rule {rule.id}",
                extra={"rule_id": rule.id, "formula": formula_text},
            )
        except Exception as e:
            logger.warning(
                f"Formula contains pseudo-code for rule {rule.id}: {str(e)}. "
                f"Creating placeholder rule for user configuration.",
                extra={"rule_id": rule.id, "formula": formula_text},
            )
            # Fall back to creating a placeholder fixed rule with metadata
            return await self._hydrate_fixed(
                session,
                rule,
                actor,
                override_metadata={
                    "original_formula_description": formula_text,
                    "requires_user_configuration": True,
                    "hydration_note": "Original formula was pseudo-code. Please configure manually.",
                },
            )

        action = {
            "action_type": "formula",
            "formula": formula_text,
            "value_usd": None,
            "metric": None,
            "unit_type": None,
            "modifiers": {},
        }

        new_rule = await self.rules_service.create_rule(
            session=session,
            group_id=rule.group_id,
            name=f"{rule.name} (Formula)",
            description=rule.description,
            priority=rule.priority,
            evaluation_order=rule.evaluation_order,
            conditions=[],  # Always applies
            actions=[action],
            created_by=actor,
            metadata={
                "hydration_source_rule_id": rule.id,
                "field_type": "formula",
                "is_foreign_key_rule": self._is_foreign_key_rule(rule),
            },
        )

        return [new_rule]

    async def _hydrate_fixed(
        self,
        session: AsyncSession,
        rule: ValuationRuleV2,
        actor: str,
        override_metadata: dict[str, Any] | None = None,
    ) -> list[ValuationRuleV2]:
        """Create single rule with fixed value action.

        For fixed value rules like base depreciation, creates a rule
        with a fixed value action and no conditions.

        Args:
            session: Database session
            rule: Placeholder rule to expand
            actor: User or system identifier
            override_metadata: Additional metadata to merge into created rule

        Returns:
            List containing single fixed value rule
        """
        # Extract value from metadata - check multiple possible keys
        # Try different key variants that may be present in metadata
        base_value = None
        for key in ["default_value", "Default", "value", "Value", "base_value"]:
            if key in rule.metadata_json:
                base_value = rule.metadata_json[key]
                break

        # If still no value found, use 0.0 as safe fallback
        if base_value is None:
            # For valuation rules without explicit defaults, 0.0 is appropriate
            # (user will configure the actual value)
            logger.info(
                f"No default value in metadata for rule {rule.id} ({rule.name}). "
                f"Using 0.0 as placeholder for user configuration. "
                f"Available metadata keys: {list(rule.metadata_json.keys())}"
            )
            base_value = 0.0

        # Convert to float with validation
        try:
            value_float = float(base_value)
        except (TypeError, ValueError) as e:
            logger.warning(
                f"Invalid default value '{base_value}' in fixed rule {rule.id}: {str(e)}. "
                f"Using 0.0 as fallback."
            )
            value_float = 0.0

        action = {
            "action_type": "fixed_value",
            "value_usd": value_float,
            "metric": None,
            "unit_type": None,
            "formula": None,
            "modifiers": {},
        }

        # Build metadata
        metadata = {
            "hydration_source_rule_id": rule.id,
            "field_type": "fixed",
            "is_foreign_key_rule": self._is_foreign_key_rule(rule),
        }

        # Merge override metadata if provided
        if override_metadata:
            metadata.update(override_metadata)

        new_rule = await self.rules_service.create_rule(
            session=session,
            group_id=rule.group_id,
            name=f"{rule.name} (Fixed)",
            description=rule.description,
            priority=rule.priority,
            evaluation_order=rule.evaluation_order,
            conditions=[],
            actions=[action],
            created_by=actor,
            metadata=metadata,
        )

        return [new_rule]
