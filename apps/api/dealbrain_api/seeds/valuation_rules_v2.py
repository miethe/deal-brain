"""Seed script for valuation rules v2 system"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dealbrain_api.db import session_scope
from dealbrain_api.services.rules import RulesService


async def seed_sample_ruleset():
    """Create a sample ruleset with example rules"""

    async with session_scope() as session:
        service = RulesService()

        print("Creating sample ruleset...")

        # Create ruleset
        ruleset = await service.create_ruleset(
            session=session,
            name="Gaming PC Valuation Q4 2025",
            description="Optimized valuation rules for gaming PC listings",
            version="1.0.0",
            created_by="system",
            metadata={"category": "gaming", "market": "used_pc"},
        )

        print(f"✓ Created ruleset: {ruleset.name} (ID: {ruleset.id})")

        # Create rule groups
        cpu_group = await service.create_rule_group(
            session=session,
            ruleset_id=ruleset.id,
            name="CPU Valuation",
            category="cpu",
            description="CPU pricing rules based on performance and generation",
            display_order=1,
            weight=0.25,
        )

        ram_group = await service.create_rule_group(
            session=session,
            ruleset_id=ruleset.id,
            name="RAM Valuation",
            category="ram",
            description="RAM pricing based on capacity and generation",
            display_order=2,
            weight=0.15,
        )

        storage_group = await service.create_rule_group(
            session=session,
            ruleset_id=ruleset.id,
            name="Storage Valuation",
            category="storage",
            description="Storage pricing based on type and capacity",
            display_order=3,
            weight=0.10,
        )

        print(f"✓ Created 3 rule groups")

        # Create CPU rules
        await service.create_rule(
            session=session,
            group_id=cpu_group.id,
            name="High-End CPU (Passmark 20K+)",
            description="Premium pricing for high-performance CPUs",
            priority=10,
            evaluation_order=1,
            conditions=[
                {
                    "field_name": "cpu.cpu_mark_multi",
                    "field_type": "integer",
                    "operator": "greater_than",
                    "value": 20000,
                }
            ],
            actions=[
                {
                    "action_type": "benchmark_based",
                    "metric": "cpu.cpu_mark_multi",
                    "value_usd": 5.0,
                    "unit_type": "per_1000_points",
                    "modifiers": {
                        "condition_new": 1.0,
                        "condition_refurb": 0.85,
                        "condition_used": 0.70,
                    }
                }
            ],
            created_by="system",
        )

        await service.create_rule(
            session=session,
            group_id=cpu_group.id,
            name="Mid-Range CPU (Passmark 10K-20K)",
            description="Standard pricing for mid-range CPUs",
            priority=20,
            evaluation_order=2,
            conditions=[
                {
                    "field_name": "cpu.cpu_mark_multi",
                    "field_type": "integer",
                    "operator": "between",
                    "value": [10000, 20000],
                }
            ],
            actions=[
                {
                    "action_type": "benchmark_based",
                    "metric": "cpu.cpu_mark_multi",
                    "value_usd": 3.5,
                    "unit_type": "per_1000_points",
                    "modifiers": {
                        "condition_new": 1.0,
                        "condition_refurb": 0.80,
                        "condition_used": 0.65,
                    }
                }
            ],
            created_by="system",
        )

        print(f"✓ Created 2 CPU rules")

        # Create RAM rules
        await service.create_rule(
            session=session,
            group_id=ram_group.id,
            name="DDR5 RAM Premium",
            description="Higher valuation for DDR5 memory",
            priority=10,
            evaluation_order=1,
            conditions=[
                {
                    "field_name": "ram_notes",
                    "field_type": "string",
                    "operator": "contains",
                    "value": "DDR5",
                }
            ],
            actions=[
                {
                    "action_type": "per_unit",
                    "metric": "per_gb",
                    "value_usd": 4.50,
                    "modifiers": {
                        "condition_new": 1.0,
                        "condition_refurb": 0.80,
                        "condition_used": 0.65,
                    }
                }
            ],
            created_by="system",
        )

        await service.create_rule(
            session=session,
            group_id=ram_group.id,
            name="DDR4 RAM Standard",
            description="Standard pricing for DDR4 memory",
            priority=20,
            evaluation_order=2,
            conditions=[
                {
                    "field_name": "ram_notes",
                    "field_type": "string",
                    "operator": "contains",
                    "value": "DDR4",
                }
            ],
            actions=[
                {
                    "action_type": "per_unit",
                    "metric": "per_gb",
                    "value_usd": 2.50,
                    "modifiers": {
                        "condition_new": 1.0,
                        "condition_refurb": 0.75,
                        "condition_used": 0.60,
                    }
                }
            ],
            created_by="system",
        )

        await service.create_rule(
            session=session,
            group_id=ram_group.id,
            name="High Capacity RAM Bonus",
            description="Bonus adjustment for 32GB+ RAM",
            priority=30,
            evaluation_order=3,
            conditions=[
                {
                    "field_name": "ram_gb",
                    "field_type": "integer",
                    "operator": "greater_than_or_equal",
                    "value": 32,
                }
            ],
            actions=[
                {
                    "action_type": "additive",
                    "value_usd": 25.0,
                    "modifiers": {}
                }
            ],
            created_by="system",
        )

        print(f"✓ Created 3 RAM rules")

        # Create storage rules
        await service.create_rule(
            session=session,
            group_id=storage_group.id,
            name="NVMe SSD Premium",
            description="Premium pricing for NVMe storage",
            priority=10,
            evaluation_order=1,
            conditions=[
                {
                    "field_name": "primary_storage_type",
                    "field_type": "string",
                    "operator": "contains",
                    "value": "NVMe",
                }
            ],
            actions=[
                {
                    "action_type": "per_unit",
                    "metric": "per_gb",
                    "value_usd": 0.15,
                    "modifiers": {
                        "condition_new": 1.0,
                        "condition_refurb": 0.85,
                        "condition_used": 0.70,
                    }
                }
            ],
            created_by="system",
        )

        await service.create_rule(
            session=session,
            group_id=storage_group.id,
            name="SATA SSD Standard",
            description="Standard pricing for SATA SSDs",
            priority=20,
            evaluation_order=2,
            conditions=[
                {
                    "field_name": "primary_storage_type",
                    "field_type": "string",
                    "operator": "contains",
                    "value": "SSD",
                },
                {
                    "field_name": "primary_storage_type",
                    "field_type": "string",
                    "operator": "not_in",
                    "value": ["NVMe"],
                }
            ],
            actions=[
                {
                    "action_type": "per_unit",
                    "metric": "per_gb",
                    "value_usd": 0.08,
                    "modifiers": {
                        "condition_new": 1.0,
                        "condition_refurb": 0.80,
                        "condition_used": 0.65,
                    }
                }
            ],
            created_by="system",
        )

        print(f"✓ Created 2 storage rules")

        print(f"\n✅ Successfully seeded ruleset '{ruleset.name}' with 7 rules across 3 categories")

        return ruleset


if __name__ == "__main__":
    asyncio.run(seed_sample_ruleset())
