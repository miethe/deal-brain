#!/usr/bin/env python
"""Fix missing field_type in baseline rule metadata.

This script updates all baseline rules to have a proper field_type in their metadata_json.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import select, cast, String, update
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.db import session_scope
from dealbrain_api.models.core import ValuationRuleset, ValuationRuleGroup, ValuationRuleV2
from dealbrain_api.services.baseline_loader import BaselineLoaderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def derive_field_type(rule_meta: dict[str, Any]) -> str:
    """Derive the field type from rule metadata.

    Args:
        rule_meta: Rule metadata dictionary

    Returns:
        Field type: "formula", "multiplier", or "scalar"
    """
    # Check if it's a formula field
    formula_text = rule_meta.get("formula_text")
    if formula_text and isinstance(formula_text, str) and formula_text.strip():
        return "formula"

    # Check if it's a multiplier field
    unit = rule_meta.get("unit")
    if isinstance(unit, str) and unit.lower() == "multiplier":
        return "multiplier"

    # Default to scalar
    return "scalar"


async def fix_baseline_field_types():
    """Update all baseline rules with missing field_type."""
    async with session_scope() as session:
        # Find all baseline rulesets (active or not)
        stmt = select(ValuationRuleset).where(
            cast(ValuationRuleset.metadata_json["system_baseline"], String) == "true"
        )
        result = await session.execute(stmt)
        rulesets = result.scalars().all()

        if not rulesets:
            logger.info("No baseline rulesets found")
            return

        logger.info(f"Found {len(rulesets)} baseline ruleset(s)")

        total_updated = 0

        for ruleset in rulesets:
            logger.info(f"Processing ruleset: {ruleset.name} (ID: {ruleset.id})")

            for group in ruleset.rule_groups:
                logger.info(f"  Group: {group.name} ({len(group.rules)} rules)")

                for rule in group.rules:
                    rule_meta = rule.metadata_json or {}
                    field_type = rule_meta.get("field_type")

                    if field_type is None:
                        # Derive the correct field type
                        derived_type = derive_field_type(rule_meta)

                        # Update the metadata
                        rule_meta["field_type"] = derived_type
                        rule.metadata_json = rule_meta

                        logger.info(
                            f"    Updated rule '{rule.name}': "
                            f"field_type={derived_type} (unit={rule_meta.get('unit')})"
                        )
                        total_updated += 1

        # Commit all changes
        await session.commit()
        logger.info(f"\nTotal rules updated: {total_updated}")


if __name__ == "__main__":
    asyncio.run(fix_baseline_field_types())
