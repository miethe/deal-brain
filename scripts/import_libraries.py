#!/usr/bin/env python3
"""
Library Import Script

Automated import of reference data libraries for Deal Brain.
Imports custom fields, valuation rules, rulesets, and scoring profiles.

Usage:
    poetry run python scripts/import_libraries.py --all
    poetry run python scripts/import_libraries.py --fields
    poetry run python scripts/import_libraries.py --rules
    poetry run python scripts/import_libraries.py --profiles
    poetry run python scripts/import_libraries.py --ruleset gaming
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
import yaml
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from dealbrain_api.db import session_scope
from dealbrain_api.services.custom_fields import CustomFieldService
from dealbrain_api.services.rules import RulesService
from dealbrain_api.models.core import Profile
from dealbrain_api.schemas.rules import (
    RulesetCreateRequest,
    RuleGroupCreateRequest,
    RuleCreateRequest,
    ConditionSchema,
    ActionSchema,
)


# Directory paths
EXAMPLES_DIR = Path(__file__).parent.parent / "docs" / "examples" / "libraries"
FIELDS_DIR = EXAMPLES_DIR / "fields"
RULES_DIR = EXAMPLES_DIR / "rules"
RULESETS_DIR = EXAMPLES_DIR / "rulesets"
PROFILES_DIR = EXAMPLES_DIR / "profiles"


class LibraryImporter:
    """Handles importing reference libraries into the database."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.fields_service = CustomFieldService()
        self.rules_service = RulesService()

    async def import_custom_fields(self, filepath: Path) -> Dict[str, Any]:
        """Import custom field definitions from YAML."""
        print(f"\n📋 Importing custom fields from {filepath.name}...")

        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        entity_type = data.get("entity_type", "listing")
        fields = data.get("fields", [])

        imported = 0
        skipped = 0
        errors = []

        for field_data in fields:
            try:
                field_name = field_data["name"]

                # Check if field already exists
                existing = await self.fields_service.get_field_definition(
                    self.session, entity_type, field_name
                )

                if existing:
                    print(f"  ⏭️  Skipping existing field: {field_name}")
                    skipped += 1
                    continue

                # Create field definition
                await self.fields_service.create_field_definition(
                    self.session, entity_type, field_data
                )

                print(f"  ✅ Imported field: {field_name}")
                imported += 1

            except Exception as e:
                error_msg = f"Error importing field {field_data.get('name', 'unknown')}: {e}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)

        await self.session.commit()

        return {
            "filepath": str(filepath),
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }

    async def import_rules_yaml(self, filepath: Path) -> Dict[str, Any]:
        """Import valuation rules from YAML."""
        print(f"\n🎯 Importing rules from {filepath.name}...")

        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        ruleset_data = data.get("ruleset", {})
        rule_groups_data = data.get("rule_groups", [])

        # Create ruleset
        ruleset_create = RulesetCreateRequest(
            name=ruleset_data["name"],
            version=ruleset_data["version"],
            description=ruleset_data.get("description", ""),
            is_active=ruleset_data.get("is_active", True),
            metadata=ruleset_data.get("metadata", {}),
        )

        # Check if ruleset exists
        existing_rulesets = await self.rules_service.list_rulesets(self.session)
        existing = next(
            (rs for rs in existing_rulesets if rs.name == ruleset_create.name), None
        )

        if existing:
            print(f"  ⏭️  Ruleset '{ruleset_create.name}' already exists (ID: {existing.id})")
            ruleset = existing
        else:
            ruleset = await self.rules_service.create_ruleset(self.session, ruleset_create)
            print(f"  ✅ Created ruleset: {ruleset.name} (ID: {ruleset.id})")

        # Import rule groups and rules
        groups_created = 0
        rules_created = 0
        errors = []

        for group_data in rule_groups_data:
            try:
                # Create rule group
                group_create = RuleGroupCreateRequest(
                    name=group_data["name"],
                    category=group_data["category"],
                    description=group_data.get("description", ""),
                    weight=group_data.get("weight", 1.0),
                    display_order=group_data.get("display_order", 0),
                )

                group = await self.rules_service.create_rule_group(
                    self.session, ruleset.id, group_create
                )
                groups_created += 1
                print(f"  ✅ Created group: {group.name}")

                # Create rules in group
                for rule_data in group_data.get("rules", []):
                    try:
                        # Parse conditions recursively
                        conditions = self._parse_conditions(rule_data["conditions"])

                        # Parse actions
                        actions = [
                            ActionSchema(**action_data)
                            for action_data in rule_data["actions"]
                        ]

                        # Create rule
                        rule_create = RuleCreateRequest(
                            name=rule_data["name"],
                            description=rule_data.get("description", ""),
                            category=rule_data["category"],
                            evaluation_order=rule_data.get("evaluation_order", 100),
                            is_active=rule_data.get("is_active", True),
                            conditions=conditions,
                            actions=actions,
                        )

                        rule = await self.rules_service.create_rule(
                            self.session, group.id, rule_create
                        )
                        rules_created += 1
                        print(f"    ✅ Created rule: {rule.name}")

                    except Exception as e:
                        error_msg = f"Error creating rule {rule_data.get('name', 'unknown')}: {e}"
                        print(f"    ❌ {error_msg}")
                        errors.append(error_msg)

            except Exception as e:
                error_msg = f"Error creating group {group_data.get('name', 'unknown')}: {e}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)

        await self.session.commit()

        return {
            "filepath": str(filepath),
            "ruleset_id": ruleset.id,
            "ruleset_name": ruleset.name,
            "groups_created": groups_created,
            "rules_created": rules_created,
            "errors": errors,
        }

    def _parse_conditions(self, condition_data: Dict[str, Any]) -> ConditionSchema:
        """Recursively parse condition data into ConditionSchema objects."""
        if "logical_operator" in condition_data:
            # Nested condition group
            return ConditionSchema(
                logical_operator=condition_data["logical_operator"],
                conditions=[
                    self._parse_conditions(c) for c in condition_data["conditions"]
                ],
            )
        else:
            # Leaf condition
            return ConditionSchema(
                field_name=condition_data["field_name"],
                field_type=condition_data.get("field_type"),
                operator=condition_data["operator"],
                value=condition_data["value"],
            )

    async def import_profiles(self, filepath: Path) -> Dict[str, Any]:
        """Import scoring profiles from YAML."""
        print(f"\n⚖️  Importing profiles from {filepath.name}...")

        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        profiles_data = data.get("profiles", [])

        imported = 0
        skipped = 0
        errors = []

        for profile_data in profiles_data:
            try:
                name = profile_data["name"]

                # Check if profile exists
                from sqlalchemy import select

                stmt = select(Profile).where(Profile.name == name)
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"  ⏭️  Skipping existing profile: {name}")
                    skipped += 1
                    continue

                # Create profile
                profile = Profile(
                    name=name,
                    description=profile_data.get("description", ""),
                    is_active=profile_data.get("is_active", True),
                    metric_weights=profile_data.get("metric_weights", {}),
                    rule_group_weights=profile_data.get("rule_group_weights", {}),
                    metadata=profile_data.get("metadata", {}),
                )

                self.session.add(profile)
                print(f"  ✅ Imported profile: {name}")
                imported += 1

            except Exception as e:
                error_msg = f"Error importing profile {profile_data.get('name', 'unknown')}: {e}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)

        await self.session.commit()

        return {
            "filepath": str(filepath),
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }


async def import_all_fields(session: AsyncSession) -> List[Dict[str, Any]]:
    """Import all custom field libraries."""
    importer = LibraryImporter(session)
    results = []

    for filepath in FIELDS_DIR.glob("*.yaml"):
        result = await importer.import_custom_fields(filepath)
        results.append(result)

    return results


async def import_all_rules(session: AsyncSession) -> List[Dict[str, Any]]:
    """Import all rule libraries."""
    importer = LibraryImporter(session)
    results = []

    for filepath in RULES_DIR.glob("*.yaml"):
        result = await importer.import_rules_yaml(filepath)
        results.append(result)

    return results


async def import_all_profiles(session: AsyncSession) -> List[Dict[str, Any]]:
    """Import all profile libraries."""
    importer = LibraryImporter(session)
    results = []

    for filepath in PROFILES_DIR.glob("*.yaml"):
        result = await importer.import_profiles(filepath)
        results.append(result)

    return results


async def import_specific_ruleset(session: AsyncSession, ruleset_name: str) -> Dict[str, Any]:
    """Import a specific ruleset by name."""
    importer = LibraryImporter(session)

    # Find matching file
    filepath = RULES_DIR / f"{ruleset_name}.yaml"

    if not filepath.exists():
        # Try fuzzy match
        for f in RULES_DIR.glob("*.yaml"):
            if ruleset_name.lower() in f.stem.lower():
                filepath = f
                break

    if not filepath.exists():
        raise FileNotFoundError(f"Ruleset file not found: {ruleset_name}")

    return await importer.import_rules_yaml(filepath)


def print_summary(results: List[Dict[str, Any]], import_type: str):
    """Print import summary."""
    print(f"\n{'='*60}")
    print(f"📊 {import_type.upper()} IMPORT SUMMARY")
    print(f"{'='*60}")

    total_imported = 0
    total_skipped = 0
    total_errors = 0

    for result in results:
        filepath = Path(result["filepath"]).name

        if "imported" in result:
            imported = result["imported"]
            skipped = result["skipped"]
            total_imported += imported
            total_skipped += skipped
        elif "rules_created" in result:
            imported = result["rules_created"]
            skipped = 0
            total_imported += imported
            print(f"\n{filepath}:")
            print(f"  Ruleset: {result['ruleset_name']} (ID: {result['ruleset_id']})")
            print(f"  Groups: {result['groups_created']}")
            print(f"  Rules: {result['rules_created']}")

        errors = result.get("errors", [])
        total_errors += len(errors)

        if errors:
            print(f"\n  ⚠️  Errors in {filepath}:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"    - {error}")
            if len(errors) > 5:
                print(f"    ... and {len(errors) - 5} more errors")

    print(f"\n{'='*60}")
    print(f"✅ Total Imported: {total_imported}")
    print(f"⏭️  Total Skipped: {total_skipped}")
    print(f"❌ Total Errors: {total_errors}")
    print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(description="Import Deal Brain reference libraries")
    parser.add_argument("--all", action="store_true", help="Import all libraries")
    parser.add_argument("--fields", action="store_true", help="Import custom fields")
    parser.add_argument("--rules", action="store_true", help="Import valuation rules")
    parser.add_argument("--profiles", action="store_true", help="Import scoring profiles")
    parser.add_argument("--ruleset", type=str, help="Import specific ruleset by name")

    args = parser.parse_args()

    # Default to --all if no options specified
    if not any([args.all, args.fields, args.rules, args.profiles, args.ruleset]):
        args.all = True

    print("\n" + "="*60)
    print("🚀 Deal Brain Library Importer")
    print("="*60)

    async with session_scope() as session:
        try:
            if args.all or args.fields:
                results = await import_all_fields(session)
                print_summary(results, "Custom Fields")

            if args.all or args.rules:
                results = await import_all_rules(session)
                print_summary(results, "Valuation Rules")

            if args.all or args.profiles:
                results = await import_all_profiles(session)
                print_summary(results, "Scoring Profiles")

            if args.ruleset:
                result = await import_specific_ruleset(session, args.ruleset)
                print_summary([result], f"Ruleset: {args.ruleset}")

            print("\n✨ Import completed successfully!\n")

        except Exception as e:
            print(f"\n❌ Import failed: {e}\n")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
