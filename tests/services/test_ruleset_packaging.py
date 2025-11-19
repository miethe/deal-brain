"""
Integration tests for RulesetPackagingService.

Tests package export/import functionality with database persistence.
"""

import pytest
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.services.rules import RulesService
from dealbrain_api.services.ruleset_packaging import RulesetPackagingService
from dealbrain_api.schemas.rules import (
    RulesetCreate,
    RuleGroupCreate,
    RuleCreate,
    ConditionCreate,
    ActionCreate,
    ConditionOperator,
    ActionType,
)
from dealbrain_core.rules.packaging import PackageMetadata, MergeStrategy


@pytest.fixture
async def packaging_service():
    """Create RulesetPackagingService instance."""
    return RulesetPackagingService()


@pytest.fixture
async def rules_service():
    """Create RulesService instance."""
    return RulesService()


@pytest.fixture
async def complete_ruleset(db_session: AsyncSession, rules_service: RulesService):
    """Create a complete ruleset with groups and rules for testing."""
    # Create ruleset
    ruleset = await rules_service.create_ruleset(
        db_session,
        RulesetCreate(
            name="Complete Test Ruleset",
            version="1.0.0",
            description="Full ruleset for packaging tests",
            is_active=True,
            metadata={"author": "Test Suite", "tags": ["test", "complete"]},
        ),
    )

    # Create RAM group
    ram_group = await rules_service.create_rule_group(
        db_session,
        ruleset.id,
        RuleGroupCreate(
            name="RAM Valuation",
            category="ram",
            description="RAM-based rules",
            weight=0.30,
            display_order=1,
        ),
    )

    # Create RAM rule
    ram_rule = await rules_service.create_rule(
        db_session,
        ram_group.id,
        RuleCreate(
            name="32GB RAM Premium",
            description="Premium for 32GB+ RAM",
            category="ram",
            evaluation_order=100,
            is_active=True,
            conditions=ConditionCreate(
                field_name="ram_gb",
                operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
                value=32,
            ),
            actions=[
                ActionCreate(
                    action_type=ActionType.FIXED_VALUE,
                    value_usd=50.00,
                    description="Add $50 for 32GB+ RAM",
                )
            ],
        ),
    )

    # Create CPU group
    cpu_group = await rules_service.create_rule_group(
        db_session,
        ruleset.id,
        RuleGroupCreate(
            name="CPU Valuation",
            category="cpu",
            description="CPU-based rules",
            weight=0.40,
            display_order=2,
        ),
    )

    # Create CPU rule
    cpu_rule = await rules_service.create_rule(
        db_session,
        cpu_group.id,
        RuleCreate(
            name="High-End CPU",
            description="Premium for high-end CPUs",
            category="cpu",
            evaluation_order=100,
            is_active=True,
            conditions=ConditionCreate(
                field_name="cpu.cpu_mark_multi",
                operator=ConditionOperator.GREATER_THAN,
                value=30000,
            ),
            actions=[
                ActionCreate(
                    action_type=ActionType.FIXED_VALUE,
                    value_usd=100.00,
                    description="Add $100 for high-end CPU",
                )
            ],
        ),
    )

    return {
        "ruleset": ruleset,
        "groups": [ram_group, cpu_group],
        "rules": [ram_rule, cpu_rule],
    }


class TestPackageExport:
    """Test ruleset package export functionality."""

    @pytest.mark.asyncio
    async def test_export_basic_package(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test exporting a basic package."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="test-package",
            version="1.0.0",
            author="Test Author",
            description="Test package",
            required_app_version=">=1.0.0",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata
        )

        assert package is not None
        assert package.metadata.name == "test-package"
        assert package.metadata.version == "1.0.0"
        assert len(package.rulesets) == 1
        assert len(package.rule_groups) == 2
        assert len(package.rules) == 2

    @pytest.mark.asyncio
    async def test_export_with_dependencies(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test export includes all dependencies."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="dependency-test",
            version="1.0.0",
            author="Test",
            description="Test dependencies",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata, include_dependencies=True
        )

        # Verify all related entities are included
        assert len(package.rulesets) == 1
        assert len(package.rule_groups) == 2
        assert len(package.rules) == 2

        # Verify relationships are preserved
        exported_ruleset = package.rulesets[0]
        assert exported_ruleset.name == ruleset.name
        assert exported_ruleset.version == ruleset.version

    @pytest.mark.asyncio
    async def test_export_to_file(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
        tmp_path: Path,
    ):
        """Test exporting package to .dbrs file."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="file-export-test",
            version="1.0.0",
            author="Test",
            description="File export test",
        )

        output_path = tmp_path / "test-package.dbrs"

        await packaging_service.export_to_file(db_session, ruleset.id, metadata, str(output_path))

        # Verify file exists
        assert output_path.exists()

        # Verify file content is valid JSON
        with open(output_path, "r") as f:
            data = json.load(f)
            assert data["metadata"]["name"] == "file-export-test"
            assert "rulesets" in data
            assert "rule_groups" in data
            assert "rules" in data

    @pytest.mark.asyncio
    async def test_export_active_rules_only(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test exporting only active rules."""
        ruleset = complete_ruleset["ruleset"]
        ram_group = complete_ruleset["groups"][0]

        # Create an inactive rule
        inactive_rule = await rules_service.create_rule(
            db_session,
            ram_group.id,
            RuleCreate(
                name="Inactive Rule",
                category="ram",
                evaluation_order=50,
                is_active=False,  # Inactive
                conditions=ConditionCreate(
                    field_name="ram_gb",
                    operator=ConditionOperator.GREATER_THAN,
                    value=0,
                ),
                actions=[ActionCreate(action_type=ActionType.FIXED_VALUE, value_usd=10.00)],
            ),
        )

        metadata = PackageMetadata(
            name="active-only-test",
            version="1.0.0",
            author="Test",
            description="Active rules only",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata, active_only=True
        )

        # Should only include 2 active rules, not the inactive one
        assert len(package.rules) == 2
        assert all(rule.is_active for rule in package.rules)


class TestPackageImport:
    """Test ruleset package import functionality."""

    @pytest.mark.asyncio
    async def test_import_basic_package(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test importing a package."""
        # First export a package
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="import-test",
            version="1.0.0",
            author="Test",
            description="Import test package",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata
        )

        # Delete original ruleset
        await db_session.delete(ruleset)
        await db_session.commit()

        # Import the package
        result = await packaging_service.install_package(
            db_session, package, merge_strategy=MergeStrategy.REPLACE
        )

        assert result.success is True
        assert result.rulesets_created == 1
        assert result.rule_groups_created == 2
        assert result.rules_created == 2

    @pytest.mark.asyncio
    async def test_import_with_merge_strategy_skip(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test import with SKIP merge strategy."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="skip-test",
            version="1.0.0",
            author="Test",
            description="Skip test",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata
        )

        # Try to import with existing ruleset (should skip)
        result = await packaging_service.install_package(
            db_session, package, merge_strategy=MergeStrategy.SKIP
        )

        # Should skip because ruleset already exists
        assert result.rulesets_created == 0
        assert result.rulesets_skipped == 1

    @pytest.mark.asyncio
    async def test_import_with_merge_strategy_replace(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test import with REPLACE merge strategy."""
        ruleset = complete_ruleset["ruleset"]

        # Modify ruleset description
        from dealbrain_api.schemas.rules import RulesetUpdate

        await rules_service.update_ruleset(
            db_session,
            ruleset.id,
            RulesetUpdate(description="Modified description"),
        )

        metadata = PackageMetadata(
            name="replace-test",
            version="1.0.0",
            author="Test",
            description="Replace test",
        )

        # Export with original description
        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata
        )

        # Modify description in package
        package.rulesets[0].description = "Package description"

        # Import with REPLACE
        result = await packaging_service.install_package(
            db_session, package, merge_strategy=MergeStrategy.REPLACE
        )

        assert result.success is True

        # Verify description was replaced
        updated_ruleset = await rules_service.get_ruleset(db_session, ruleset.id)
        assert updated_ruleset.description == "Package description"

    @pytest.mark.asyncio
    async def test_import_from_file(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
        tmp_path: Path,
    ):
        """Test importing package from .dbrs file."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="file-import-test",
            version="1.0.0",
            author="Test",
            description="File import test",
        )

        # Export to file
        output_path = tmp_path / "import-test.dbrs"
        await packaging_service.export_to_file(db_session, ruleset.id, metadata, str(output_path))

        # Delete original
        await db_session.delete(ruleset)
        await db_session.commit()

        # Import from file
        result = await packaging_service.install_from_file(
            db_session, str(output_path), merge_strategy=MergeStrategy.REPLACE
        )

        assert result.success is True
        assert result.rulesets_created == 1


class TestPackageValidation:
    """Test package validation and compatibility checking."""

    @pytest.mark.asyncio
    async def test_validate_compatible_package(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test validating a compatible package."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="validation-test",
            version="1.0.0",
            author="Test",
            description="Validation test",
            required_app_version=">=1.0.0",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata
        )

        # Validate package
        validation = package.validate_compatibility(
            app_version="1.5.0", available_fields=["ram_gb", "cpu.cpu_mark_multi"]
        )

        assert validation["compatible"] is True
        assert len(validation["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_incompatible_version(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test validating package with incompatible app version."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="version-test",
            version="1.0.0",
            author="Test",
            description="Version test",
            required_app_version=">=2.0.0",  # Requires newer version
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata
        )

        # Validate with older app version
        validation = package.validate_compatibility(
            app_version="1.5.0", available_fields=["ram_gb", "cpu.cpu_mark_multi"]
        )

        assert validation["compatible"] is False
        assert len(validation["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_missing_fields(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test validation with missing required fields."""
        ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="missing-fields-test",
            version="1.0.0",
            author="Test",
            description="Missing fields test",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, ruleset.id, metadata
        )

        # Validate with missing fields
        validation = package.validate_compatibility(
            app_version="1.5.0",
            available_fields=["ram_gb"],  # Missing cpu.cpu_mark_multi
        )

        assert validation["compatible"] is False
        assert len(validation["warnings"]) > 0


class TestPackageRoundTrip:
    """Test complete export/import round trip."""

    @pytest.mark.asyncio
    async def test_complete_round_trip(
        self,
        db_session: AsyncSession,
        rules_service: RulesService,
        packaging_service: RulesetPackagingService,
        complete_ruleset: dict,
    ):
        """Test complete export and re-import preserves all data."""
        original_ruleset = complete_ruleset["ruleset"]

        metadata = PackageMetadata(
            name="roundtrip-test",
            version="1.0.0",
            author="Test",
            description="Round trip test",
        )

        # Export
        package = await packaging_service.export_ruleset_to_package(
            db_session, original_ruleset.id, metadata
        )

        # Delete original
        await db_session.delete(original_ruleset)
        await db_session.commit()

        # Re-import
        await packaging_service.install_package(
            db_session, package, merge_strategy=MergeStrategy.REPLACE
        )

        # Verify all data is preserved
        rulesets = await rules_service.list_rulesets(db_session)
        reimported = next(rs for rs in rulesets if rs.name == "Complete Test Ruleset")

        assert reimported.name == original_ruleset.name
        assert reimported.version == original_ruleset.version
        assert reimported.description == original_ruleset.description

        # Verify groups
        groups = await rules_service.list_rule_groups(db_session, reimported.id)
        assert len(groups) == 2

        # Verify rules
        for group in groups:
            rules = await rules_service.list_rules(db_session, group.id)
            assert len(rules) == 1
