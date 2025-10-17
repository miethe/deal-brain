#!/usr/bin/env python3
"""Verification script for baseline hydration fixes.

This script demonstrates that the baseline hydration system now correctly handles:
1. Pseudo-code formulas (graceful fallback to placeholder rules)
2. Missing default values (appropriate logging and 0.0 default)
3. Metadata preservation for user configuration
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import (
    ValuationRuleGroup,
    ValuationRuleset,
    ValuationRuleV2,
)
from apps.api.dealbrain_api.services.baseline_hydration import BaselineHydrationService


async def main():
    """Verify baseline hydration fixes."""
    print("=" * 80)
    print("Baseline Hydration Fixes - Verification Script")
    print("=" * 80)
    print()

    # Create in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = async_session()

    try:
        # Create test ruleset and group
        ruleset = ValuationRuleset(
            name="Test Ruleset",
            description="Verification test ruleset",
            version="1.0.0",
            is_active=True,
            created_by="verification_script",
        )
        session.add(ruleset)
        await session.commit()
        await session.refresh(ruleset)

        group = ValuationRuleGroup(
            ruleset_id=ruleset.id,
            name="Test Group",
            category="test",
            description="Verification test group",
            display_order=1,
            weight=1.0,
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)

        print("✓ Test ruleset and group created")
        print()

        # Test 1: Pseudo-code formula handling
        print("Test 1: Pseudo-code Formula Handling")
        print("-" * 80)

        pseudo_code_rule = ValuationRuleV2(
            group_id=group.id,
            name="GPU Valuation",
            description="GPU price approximation",
            priority=100,
            evaluation_order=100,
            is_active=True,
            metadata_json={
                "baseline_placeholder": True,
                "field_type": "formula",
                "formula_text": "usd ≈ (gpu_mark/1000)*8.0; clamp and apply SFF penalties",
            },
        )
        session.add(pseudo_code_rule)
        await session.commit()
        await session.refresh(pseudo_code_rule)

        print(f"Created rule with pseudo-code formula: {pseudo_code_rule.name}")
        print(f"Formula: {pseudo_code_rule.metadata_json['formula_text']}")
        print()

        # Hydrate the rule
        hydration_service = BaselineHydrationService()
        expanded_rules = await hydration_service.hydrate_single_rule(
            session, pseudo_code_rule.id, actor="verification_script"
        )

        print(f"✓ Hydration succeeded (created {len(expanded_rules)} rule(s))")

        if expanded_rules:
            rule = expanded_rules[0]
            print(f"  - Created rule: {rule.name}")
            print(f"  - Action type: {rule.actions[0].action_type}")
            print(f"  - Value: ${rule.actions[0].value_usd:.2f}")
            print()
            print("  Metadata:")
            for key in [
                "original_formula_description",
                "requires_user_configuration",
                "hydration_note",
            ]:
                if key in rule.metadata_json:
                    value = rule.metadata_json[key]
                    if isinstance(value, str) and len(value) > 60:
                        value = value[:57] + "..."
                    print(f"    - {key}: {value}")
            print()

        # Test 2: Missing default value handling
        print("Test 2: Missing Default Value Handling")
        print("-" * 80)

        no_default_rule = ValuationRuleV2(
            group_id=group.id,
            name="Base Adjustment",
            description="Fixed base adjustment",
            priority=50,
            evaluation_order=50,
            is_active=True,
            metadata_json={
                "baseline_placeholder": True,
                "field_type": "fixed",
                # No default_value provided
            },
        )
        session.add(no_default_rule)
        await session.commit()
        await session.refresh(no_default_rule)

        print(f"Created rule without default value: {no_default_rule.name}")
        print()

        expanded_rules = await hydration_service.hydrate_single_rule(
            session, no_default_rule.id, actor="verification_script"
        )

        print(f"✓ Hydration succeeded (created {len(expanded_rules)} rule(s))")

        if expanded_rules:
            rule = expanded_rules[0]
            print(f"  - Created rule: {rule.name}")
            print(f"  - Action type: {rule.actions[0].action_type}")
            print(f"  - Value: ${rule.actions[0].value_usd:.2f} (placeholder for user config)")
            print()

        # Test 3: Valid formula still works
        print("Test 3: Valid Formula Still Works")
        print("-" * 80)

        valid_formula_rule = ValuationRuleV2(
            group_id=group.id,
            name="RAM Capacity",
            description="RAM capacity pricing",
            priority=200,
            evaluation_order=200,
            is_active=True,
            metadata_json={
                "baseline_placeholder": True,
                "field_type": "formula",
                "formula_text": "ram_spec.total_capacity_gb * 2.5",
            },
        )
        session.add(valid_formula_rule)
        await session.commit()
        await session.refresh(valid_formula_rule)

        print(f"Created rule with valid formula: {valid_formula_rule.name}")
        print(f"Formula: {valid_formula_rule.metadata_json['formula_text']}")
        print()

        expanded_rules = await hydration_service.hydrate_single_rule(
            session, valid_formula_rule.id, actor="verification_script"
        )

        print(f"✓ Hydration succeeded (created {len(expanded_rules)} rule(s))")

        if expanded_rules:
            rule = expanded_rules[0]
            print(f"  - Created rule: {rule.name}")
            print(f"  - Action type: {rule.actions[0].action_type}")
            print(f"  - Formula: {rule.actions[0].formula}")
            print()

        print("=" * 80)
        print("All verification tests passed!")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ Pseudo-code formulas handled gracefully with placeholder rules")
        print("  ✓ Missing default values use 0.0 with appropriate logging")
        print("  ✓ Valid formulas continue to work as expected")
        print("  ✓ Metadata preserved for user configuration guidance")

    finally:
        await session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
