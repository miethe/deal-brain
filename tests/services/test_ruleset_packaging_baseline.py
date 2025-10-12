"""
Tests for baseline ruleset packaging and import functionality.

Tests the special handling of baseline rulesets during export/import operations.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

try:  # pragma: no cover - optional dependency
    import aiosqlite  # type: ignore  # noqa: F401
    AIOSQLITE_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - executed when optional dep missing
    AIOSQLITE_AVAILABLE = False

try:  # pragma: no cover - optional dependency
    import pytest_asyncio  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - executed when plugin missing
    pytest_asyncio = None

from dealbrain_api.db import Base
from dealbrain_api.services.rules import RulesService
from dealbrain_api.services.ruleset_packaging import RulesetPackagingService
from dealbrain_api.models.core import ValuationRuleset, ValuationRuleGroup
from dealbrain_api.schemas.rules import (
    RulesetCreate,
    RuleGroupCreate,
    RuleCreate,
    ConditionCreate,
    ActionCreate,
    ConditionOperator,
    ActionType,
)
from dealbrain_core.rules.packaging import PackageMetadata


pytestmark = pytest.mark.asyncio


if pytest_asyncio:
    @pytest_asyncio.fixture
    async def db_session() -> AsyncSession:
        """Provide an isolated in-memory database session for baseline tests."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping baseline packaging tests")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session = async_session()
        try:
            yield session
        finally:
            await session.close()
            await engine.dispose()


@pytest.fixture
async def packaging_service():
    """Create RulesetPackagingService instance."""
    return RulesetPackagingService()


@pytest.fixture
async def rules_service():
    """Create RulesService instance."""
    return RulesService()


@pytest.fixture
async def baseline_ruleset(db_session: AsyncSession):
    """Create a baseline ruleset for testing."""
    # Create baseline ruleset with metadata
    baseline = ValuationRuleset(
        name="System: Baseline v1.0",
        description="Baseline valuation rules",
        version="1.0.0",
        is_active=True,
        priority=1,  # Baseline priority <= 5
        metadata_json={
            "system_baseline": True,
            "source_version": "1.0.0",
            "source_hash": "abc123def456",
            "read_only": True
        },
        created_by="system"
    )
    db_session.add(baseline)
    await db_session.flush()

    # Create baseline rule group with metadata
    group = ValuationRuleGroup(
        ruleset_id=baseline.id,
        name="Basic RAM",
        category="ram",
        description="Baseline RAM valuation",
        display_order=1,
        weight=1.0,
        metadata_json={
            "entity_key": "ram",
            "basic_managed": False,
            "read_only": True
        }
    )
    db_session.add(group)
    await db_session.commit()

    return baseline


@pytest.fixture
async def customer_ruleset(db_session: AsyncSession, rules_service: RulesService):
    """Create a customer ruleset for testing."""
    ruleset = await rules_service.create_ruleset(
        db_session,
        RulesetCreate(
            name="Customer Valuation",
            version="1.0.0",
            description="Customer-specific valuation rules",
            is_active=True,
            metadata={"custom": True},
        ),
    )

    # Create adjustment group
    adjustment_group = await rules_service.create_rule_group(
        db_session,
        ruleset.id,
        RuleGroupCreate(
            name="Basic · Adjustments",
            category="adjustments",
            description="Customer adjustments to baseline",
            weight=1.0,
            display_order=100,
            metadata={"basic_managed": True}
        ),
    )

    return ruleset


class TestBaselineExport:
    """Test baseline ruleset export functionality."""

    @pytest.mark.asyncio
    async def test_export_baseline_requires_flag(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
    ):
        """Test that baseline rulesets require explicit flag for export."""
        metadata = PackageMetadata(
            name="test-baseline-export",
            version="1.0.0",
            author="Test",
            description="Test baseline export",
        )

        # Should fail without include_baseline flag
        with pytest.raises(ValueError, match="baseline ruleset.*include_baseline=True"):
            await packaging_service.export_ruleset_to_package(
                db_session, baseline_ruleset.id, metadata
            )

        # Should succeed with include_baseline flag
        package = await packaging_service.export_ruleset_to_package(
            db_session, baseline_ruleset.id, metadata, include_baseline=True
        )

        assert package is not None
        assert len(package.rulesets) == 1
        exported_ruleset = package.rulesets[0]
        assert exported_ruleset.metadata_json["system_baseline"] is True
        assert exported_ruleset.metadata_json["source_version"] == "1.0.0"
        assert exported_ruleset.metadata_json["source_hash"] == "abc123def456"

    @pytest.mark.asyncio
    async def test_export_preserves_baseline_metadata(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
    ):
        """Test that baseline metadata is preserved during export."""
        metadata = PackageMetadata(
            name="baseline-metadata-test",
            version="1.0.0",
            author="Test",
            description="Test metadata preservation",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, baseline_ruleset.id, metadata, include_baseline=True
        )

        # Verify ruleset metadata
        exported_ruleset = package.rulesets[0]
        assert exported_ruleset.metadata_json["system_baseline"] is True
        assert exported_ruleset.metadata_json["source_version"] == "1.0.0"
        assert exported_ruleset.metadata_json["source_hash"] == "abc123def456"
        assert exported_ruleset.metadata_json["read_only"] is True

        # Verify group metadata
        exported_group = package.rule_groups[0]
        assert exported_group.metadata_json["entity_key"] == "ram"
        assert exported_group.metadata_json["read_only"] is True

    @pytest.mark.asyncio
    async def test_export_customer_ruleset_default(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        customer_ruleset: dict,
    ):
        """Test that customer rulesets export normally without baseline flag."""
        metadata = PackageMetadata(
            name="customer-export-test",
            version="1.0.0",
            author="Test",
            description="Test customer export",
        )

        # Should export without any special flags
        package = await packaging_service.export_ruleset_to_package(
            db_session, customer_ruleset.id, metadata
        )

        assert package is not None
        assert len(package.rulesets) == 1
        exported_ruleset = package.rulesets[0]
        assert exported_ruleset.metadata_json.get("system_baseline") is not True


class TestBaselineImport:
    """Test baseline ruleset import functionality."""

    @pytest.mark.asyncio
    async def test_import_baseline_creates_version(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
    ):
        """Test that importing a baseline creates a new version."""
        # Export baseline
        metadata = PackageMetadata(
            name="baseline-version-test",
            version="1.1.0",
            author="Test",
            description="Test baseline versioning",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, baseline_ruleset.id, metadata, include_baseline=True
        )

        # Modify package to simulate update
        package.rulesets[0].metadata_json["source_version"] = "1.1.0"
        package.rulesets[0].metadata_json["source_hash"] = "xyz789uvw123"

        # Import with version mode (default)
        result = await packaging_service.install_package(
            db_session,
            package,
            actor="test_user",
            baseline_import_mode="version"
        )

        assert result["baseline_versioned"] == 1
        assert result["rulesets_created"] == 1

        # Verify new version was created
        query = select(ValuationRuleset).where(
            ValuationRuleset.name.like("System: Baseline v%")
        )
        result = await db_session.execute(query)
        baselines = result.scalars().all()

        assert len(baselines) == 2  # Original + new version
        names = [b.name for b in baselines]
        assert "System: Baseline v1.0" in names
        assert "System: Baseline v1.1" in names

        # Verify new version is inactive by default
        new_baseline = next(b for b in baselines if b.name == "System: Baseline v1.1")
        assert new_baseline.is_active is False
        assert new_baseline.metadata_json["source_hash"] == "xyz789uvw123"

    @pytest.mark.asyncio
    async def test_import_baseline_validates_priority(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
    ):
        """Test that baseline imports validate priority <= 5."""
        metadata = PackageMetadata(
            name="baseline-priority-test",
            version="1.0.0",
            author="Test",
            description="Test baseline priority validation",
        )

        # Create package with invalid priority
        from dealbrain_core.rules.packaging import RulesetExport, PackageBuilder

        invalid_ruleset = RulesetExport(
            id=1,
            name="System: Baseline v2.0",
            description="Invalid baseline",
            version="2.0.0",
            is_active=True,
            metadata_json={
                "system_baseline": True,
                "priority": 10  # Invalid: > 5
            },
            created_by="test",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        builder = PackageBuilder()
        builder.add_ruleset(invalid_ruleset)
        package = builder.build(metadata)

        # Should fail due to invalid priority
        with pytest.raises(ValueError, match="invalid priority.*must have priority ≤ 5"):
            await packaging_service.install_package(
                db_session,
                package,
                actor="test_user"
            )

    @pytest.mark.asyncio
    async def test_import_baseline_preserves_read_only(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
    ):
        """Test that baseline imports preserve read_only flags."""
        # Export baseline
        metadata = PackageMetadata(
            name="baseline-readonly-test",
            version="1.0.0",
            author="Test",
            description="Test read-only preservation",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, baseline_ruleset.id, metadata, include_baseline=True
        )

        # Clear database
        await db_session.delete(baseline_ruleset)
        await db_session.commit()

        # Import baseline
        result = await packaging_service.install_package(
            db_session,
            package,
            actor="test_user",
            baseline_import_mode="replace"  # Use replace to test metadata preservation
        )

        assert result["rulesets_created"] == 1

        # Verify read_only flags preserved
        query = select(ValuationRuleGroup).options(
            selectinload(ValuationRuleGroup.ruleset)
        )
        result = await db_session.execute(query)
        groups = result.scalars().all()

        baseline_group = next(
            g for g in groups
            if g.ruleset.metadata_json.get("system_baseline") is True
        )
        assert baseline_group.metadata_json["read_only"] is True

    @pytest.mark.asyncio
    async def test_import_baseline_replace_mode(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
    ):
        """Test baseline import with replace mode."""
        original_hash = baseline_ruleset.metadata_json["source_hash"]

        # Export baseline
        metadata = PackageMetadata(
            name="baseline-replace-test",
            version="1.0.1",
            author="Test",
            description="Test baseline replace",
        )

        package = await packaging_service.export_ruleset_to_package(
            db_session, baseline_ruleset.id, metadata, include_baseline=True
        )

        # Modify package slightly
        package.rulesets[0].description = "Updated baseline description"
        package.rulesets[0].version = "1.0.1"

        # Import with replace mode
        result = await packaging_service.install_package(
            db_session,
            package,
            actor="test_user",
            baseline_import_mode="replace"
        )

        assert result["rulesets_updated"] == 1

        # Verify existing baseline was updated
        await db_session.refresh(baseline_ruleset)
        assert baseline_ruleset.description == "Updated baseline description"
        assert baseline_ruleset.version == "1.0.1"
        assert baseline_ruleset.metadata_json["source_hash"] == original_hash


class TestMixedPackageImport:
    """Test importing packages with both baseline and customer rulesets."""

    @pytest.mark.asyncio
    async def test_mixed_package_import(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
        customer_ruleset: dict,
    ):
        """Test importing a package with both baseline and customer rulesets."""
        # Create a mixed package
        from dealbrain_core.rules.packaging import RulesetExport, PackageBuilder

        metadata = PackageMetadata(
            name="mixed-package",
            version="1.0.0",
            author="Test",
            description="Mixed baseline and customer package",
        )

        builder = PackageBuilder()

        # Add baseline ruleset
        baseline_export = RulesetExport(
            id=1,
            name="System: Baseline v2.0",
            description="New baseline",
            version="2.0.0",
            is_active=False,
            metadata_json={
                "system_baseline": True,
                "source_version": "2.0.0",
                "source_hash": "new_hash",
                "priority": 1
            },
            created_by="system",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        builder.add_ruleset(baseline_export)

        # Add customer ruleset
        customer_export = RulesetExport(
            id=2,
            name="New Customer Rules",
            description="Customer rules",
            version="1.0.0",
            is_active=True,
            metadata_json={"custom": True},
            created_by="user",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        builder.add_ruleset(customer_export)

        package = builder.build(metadata)

        # Import mixed package
        result = await packaging_service.install_package(
            db_session,
            package,
            actor="test_user",
            merge_strategy="replace",
            baseline_import_mode="version"
        )

        assert result["baseline_versioned"] == 1
        assert result["rulesets_created"] == 2

        # Verify both rulesets were created
        query = select(ValuationRuleset)
        result = await db_session.execute(query)
        all_rulesets = result.scalars().all()

        baseline_names = [
            r.name for r in all_rulesets
            if r.metadata_json.get("system_baseline") is True
        ]
        customer_names = [
            r.name for r in all_rulesets
            if r.metadata_json.get("system_baseline") is not True
        ]

        assert "System: Baseline v2.0" in baseline_names
        assert "New Customer Rules" in customer_names


class TestBaselineExportToFile:
    """Test exporting baseline rulesets to file."""

    @pytest.mark.asyncio
    async def test_export_baseline_to_file(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
        tmp_path: Path,
    ):
        """Test exporting baseline to .dbrs file."""
        metadata = PackageMetadata(
            name="baseline-file-export",
            version="1.0.0",
            author="Test",
            description="Baseline file export test",
        )

        output_path = tmp_path / "baseline.dbrs"

        await packaging_service.export_to_file(
            db_session,
            baseline_ruleset.id,
            metadata,
            str(output_path),
            include_baseline=True
        )

        # Verify file exists and contains baseline metadata
        assert output_path.exists()

        with open(output_path, "r") as f:
            data = json.load(f)

        assert data["metadata"]["name"] == "baseline-file-export"
        assert len(data["rulesets"]) == 1
        assert data["rulesets"][0]["metadata_json"]["system_baseline"] is True

    @pytest.mark.asyncio
    async def test_import_baseline_from_file(
        self,
        db_session: AsyncSession,
        packaging_service: RulesetPackagingService,
        baseline_ruleset: ValuationRuleset,
        tmp_path: Path,
    ):
        """Test importing baseline from .dbrs file."""
        # Export to file
        metadata = PackageMetadata(
            name="baseline-file-import",
            version="2.0.0",
            author="Test",
            description="Baseline file import test",
        )

        output_path = tmp_path / "baseline-import.dbrs"
        await packaging_service.export_to_file(
            db_session,
            baseline_ruleset.id,
            metadata,
            str(output_path),
            include_baseline=True
        )

        # Modify the exported file to simulate version update
        with open(output_path, "r") as f:
            data = json.load(f)

        data["rulesets"][0]["metadata_json"]["source_version"] = "2.0.0"
        data["rulesets"][0]["metadata_json"]["source_hash"] = "file_import_hash"

        with open(output_path, "w") as f:
            json.dump(data, f)

        # Import from file
        result = await packaging_service.install_from_file(
            db_session,
            str(output_path),
            actor="file_import_user",
            baseline_import_mode="version"
        )

        assert result["baseline_versioned"] == 1
        assert result["rulesets_created"] == 1

        # Verify new version created
        query = select(ValuationRuleset).where(
            ValuationRuleset.name.like("System: Baseline v%")
        )
        result = await db_session.execute(query)
        baselines = result.scalars().all()

        assert len(baselines) == 2
        new_baseline = next(
            b for b in baselines
            if b.metadata_json.get("source_hash") == "file_import_hash"
        )
        assert new_baseline is not None
        assert new_baseline.metadata_json["source_version"] == "2.0.0"