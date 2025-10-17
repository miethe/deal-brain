#!/usr/bin/env python
"""Backfill is_foreign_key_rule metadata for existing hydrated rules.

This script updates all hydrated rules (those with hydration_source_rule_id in metadata)
to include the is_foreign_key_rule flag based on their source baseline rule's entity_key.

Rules with entity_key in {"cpu", "gpu", "storage", "ram_spec", "ports"} are considered
foreign key rules since they reference related entities.

CONTEXT:
--------
When baseline rules are hydrated, they are expanded from placeholder rules into full
rules with conditions and actions. The hydration process now tags these expanded rules
with an is_foreign_key_rule flag to indicate whether they reference foreign key entities.

This script was created as a one-time migration to backfill this metadata for rules
that were hydrated before this feature was implemented.

USAGE:
------
    poetry run python scripts/backfill_fk_metadata.py

The script is idempotent and safe to run multiple times. It will:
1. Find all hydrated rules (those with hydration_source_rule_id in metadata)
2. For each rule, look up the source baseline rule to get its entity_key
3. Tag the rule as is_foreign_key_rule=true if entity_key is in the FK set
4. Tag the rule as is_foreign_key_rule=false otherwise
5. Skip rules that already have the is_foreign_key_rule flag

OUTPUT:
-------
The script provides detailed logging and a summary showing:
- Total hydrated rules found
- Number already tagged (skipped)
- Number tagged as FK rules
- Number tagged as non-FK rules
- Number with orphaned source references (if any)

FOREIGN KEY ENTITIES:
---------------------
The following entity_key values are considered foreign key references:
- "cpu": References the CPU entity
- "gpu": References the GPU entity
- "storage": References the Storage entity
- "ram_spec": References the RAM specification entity
- "ports": References the Ports profile entity
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes

# Add apps/api to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from dealbrain_api.db import session_scope
from dealbrain_api.models.core import ValuationRuleV2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Entity keys that represent foreign key relationships
# These are the keys used in baseline rules to reference related entities
FK_ENTITY_KEYS = {
    "cpu",           # CPU entity
    "gpu",           # GPU entity
    "storage",       # Storage entity
    "ram_spec",      # RAM specification entity
    "ports",         # Ports profile entity
}


async def fetch_source_rule(session: AsyncSession, source_rule_id: int) -> ValuationRuleV2 | None:
    """Fetch a source baseline rule by ID.

    Args:
        session: Database session
        source_rule_id: ID of the source rule

    Returns:
        Source rule if found, None otherwise
    """
    stmt = select(ValuationRuleV2).where(ValuationRuleV2.id == source_rule_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def backfill_fk_metadata():
    """Backfill is_foreign_key_rule metadata on existing hydrated rules."""
    logger.info("Starting backfill of is_foreign_key_rule metadata...")

    async with session_scope() as session:
        # Find all rules with hydration_source_rule_id in metadata
        stmt = select(ValuationRuleV2)
        result = await session.execute(stmt)
        all_rules = result.scalars().all()

        # Filter to only hydrated rules
        hydrated_rules = [
            rule for rule in all_rules
            if isinstance(rule.metadata_json, dict)
            and "hydration_source_rule_id" in rule.metadata_json
        ]

        logger.info(f"Found {len(hydrated_rules)} hydrated rules to process")

        if not hydrated_rules:
            logger.info("No hydrated rules found. Nothing to backfill.")
            return

        # Statistics
        already_tagged = 0
        tagged_as_fk = 0
        tagged_as_non_fk = 0
        source_not_found = 0

        # Process each hydrated rule
        for idx, rule in enumerate(hydrated_rules, 1):
            metadata = rule.metadata_json
            source_rule_id = metadata.get("hydration_source_rule_id")

            # Skip if already has the metadata flag
            if "is_foreign_key_rule" in metadata:
                already_tagged += 1
                logger.debug(
                    f"[{idx}/{len(hydrated_rules)}] Rule {rule.id} ({rule.name}) "
                    f"already has is_foreign_key_rule={metadata['is_foreign_key_rule']}"
                )
                continue

            # Fetch the source baseline rule
            source_rule = await fetch_source_rule(session, source_rule_id)

            if source_rule is None:
                source_not_found += 1
                logger.warning(
                    f"[{idx}/{len(hydrated_rules)}] Rule {rule.id} ({rule.name}) "
                    f"has orphaned reference to source rule {source_rule_id}"
                )
                # Default to false for orphaned rules
                metadata["is_foreign_key_rule"] = False
                rule.metadata_json = metadata
                attributes.flag_modified(rule, "metadata_json")
                tagged_as_non_fk += 1
                continue

            # Get entity_key from source rule
            source_metadata = source_rule.metadata_json or {}
            entity_key = source_metadata.get("entity_key", "")

            # Determine if it's a foreign key rule
            is_fk_rule = entity_key in FK_ENTITY_KEYS

            # Update the metadata
            metadata["is_foreign_key_rule"] = is_fk_rule
            rule.metadata_json = metadata
            # Mark the field as modified so SQLAlchemy detects the change
            attributes.flag_modified(rule, "metadata_json")

            if is_fk_rule:
                tagged_as_fk += 1
                logger.info(
                    f"[{idx}/{len(hydrated_rules)}] Rule {rule.id} ({rule.name}) "
                    f"tagged as FK rule (entity_key={entity_key})"
                )
            else:
                tagged_as_non_fk += 1
                logger.debug(
                    f"[{idx}/{len(hydrated_rules)}] Rule {rule.id} ({rule.name}) "
                    f"tagged as non-FK rule (entity_key={entity_key})"
                )

        # Commit all changes
        await session.commit()

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("BACKFILL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total hydrated rules found:      {len(hydrated_rules)}")
        logger.info(f"Already had metadata flag:       {already_tagged}")
        logger.info(f"Tagged as FK rules:              {tagged_as_fk}")
        logger.info(f"Tagged as non-FK rules:          {tagged_as_non_fk}")
        logger.info(f"Source rules not found:          {source_not_found}")
        logger.info(f"Total rules updated:             {tagged_as_fk + tagged_as_non_fk}")
        logger.info("=" * 60)

        if source_not_found > 0:
            logger.warning(
                f"\n{source_not_found} orphaned hydrated rules found. "
                "These rules reference non-existent source rules and have been "
                "tagged as non-FK rules by default."
            )


if __name__ == "__main__":
    asyncio.run(backfill_fk_metadata())
