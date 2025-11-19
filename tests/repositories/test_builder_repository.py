"""Tests for BuilderRepository (Phase 2: Repository Layer).

This test suite verifies:
- All CRUD operations (create, read, update, delete)
- Access control for private builds
- Query optimization (joinedload for CPU/GPU)
- Soft delete filtering
- Pagination and ordering
- Error handling and edge cases

Target: >90% code coverage
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.builds import SavedBuild
from apps.api.dealbrain_api.models.catalog import Cpu, Gpu
from apps.api.dealbrain_api.repositories.builder_repository import BuilderRepository

AIOSQLITE_AVAILABLE = True
try:
    import aiosqlite  # type: ignore
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():
    """Configure async backend for tests."""
    return "asyncio"


@pytest_asyncio.fixture
async def session():
    """Create an in-memory async database session for testing."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            yield session
            await session.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def repository(session: AsyncSession):
    """Create BuilderRepository instance with test session."""
    return BuilderRepository(session)


@pytest_asyncio.fixture
async def sample_cpu(session: AsyncSession):
    """Create sample CPU for testing."""
    cpu = Cpu(
        name="Intel Core i7-12700K",
        manufacturer="Intel",
        cpu_mark_single=3985,
        cpu_mark_multi=35864,
    )
    session.add(cpu)
    await session.flush()
    return cpu


@pytest_asyncio.fixture
async def sample_gpu(session: AsyncSession):
    """Create sample GPU for testing."""
    gpu = Gpu(name="NVIDIA RTX 3080", manufacturer="NVIDIA")
    session.add(gpu)
    await session.flush()
    return gpu


@pytest.mark.asyncio
class TestCreate:
    """Test BuilderRepository.create() method."""

    async def test_create_minimal_build(self, repository: BuilderRepository, session: AsyncSession):
        """Test creating build with minimal required fields."""
        data = {
            "name": "Budget Gaming PC",
            "visibility": "private",
            "share_token": uuid.uuid4().hex,
        }

        build = await repository.create(data)
        await session.commit()

        assert build.id is not None
        assert build.name == "Budget Gaming PC"
        assert build.visibility == "private"
        assert len(build.share_token) == 32
        assert build.created_at is not None
        assert build.updated_at is not None
        assert build.deleted_at is None

    async def test_create_complete_build(
        self, repository: BuilderRepository, session: AsyncSession, sample_cpu: Cpu, sample_gpu: Gpu
    ):
        """Test creating build with all optional fields."""
        data = {
            "user_id": 1,
            "name": "High-End Workstation",
            "description": "Professional video editing build",
            "tags": ["workstation", "4k-editing", "rendering"],
            "visibility": "public",
            "share_token": uuid.uuid4().hex,
            "cpu_id": sample_cpu.id,
            "gpu_id": sample_gpu.id,
            "ram_spec_id": 1,
            "storage_spec_id": 2,
            "psu_spec_id": 3,
            "case_spec_id": 4,
            "pricing_snapshot": {
                "base_price": 2500.0,
                "adjusted_price": 2400.0,
                "delta_amount": -100.0,
                "delta_percentage": -4.0,
            },
            "metrics_snapshot": {
                "dollar_per_cpu_mark_multi": 6.7,
                "dollar_per_cpu_mark_single": 9.5,
                "composite_score": 92.3,
            },
            "valuation_breakdown": {
                "rules_applied": ["BULK_DISCOUNT", "EXCELLENT_CONDITION"],
                "total_adjustment": -100.0,
            },
        }

        build = await repository.create(data)
        await session.commit()

        assert build.id is not None
        assert build.user_id == 1
        assert build.name == "High-End Workstation"
        assert build.description == "Professional video editing build"
        assert build.tags == ["workstation", "4k-editing", "rendering"]
        assert build.visibility == "public"
        assert build.cpu_id == sample_cpu.id
        assert build.gpu_id == sample_gpu.id
        assert build.ram_spec_id == 1
        assert build.pricing_snapshot["base_price"] == 2500.0
        assert build.metrics_snapshot["composite_score"] == 92.3
        assert build.valuation_breakdown["total_adjustment"] == -100.0

    async def test_create_missing_required_fields(self, repository: BuilderRepository):
        """Test error when required fields are missing."""
        # Missing 'name'
        data = {"visibility": "private", "share_token": uuid.uuid4().hex}

        with pytest.raises(ValueError, match="Missing required fields: name"):
            await repository.create(data)

        # Missing 'visibility' and 'share_token'
        data = {"name": "Test Build"}

        with pytest.raises(ValueError, match="Missing required fields"):
            await repository.create(data)


@pytest.mark.asyncio
class TestGetById:
    """Test BuilderRepository.get_by_id() method."""

    async def test_get_existing_build(
        self, repository: BuilderRepository, session: AsyncSession, sample_cpu: Cpu, sample_gpu: Gpu
    ):
        """Test retrieving existing build by ID."""
        # Create build
        build = SavedBuild(
            name="Test Build",
            visibility="public",
            share_token=uuid.uuid4().hex,
            cpu_id=sample_cpu.id,
            gpu_id=sample_gpu.id,
        )
        session.add(build)
        await session.commit()

        # Retrieve build
        retrieved = await repository.get_by_id(build.id)

        assert retrieved is not None
        assert retrieved.id == build.id
        assert retrieved.name == "Test Build"
        # Verify eager loading worked
        assert retrieved.cpu is not None
        assert retrieved.cpu.name == "Intel Core i7-12700K"
        assert retrieved.gpu is not None
        assert retrieved.gpu.name == "NVIDIA RTX 3080"

    async def test_get_nonexistent_build(self, repository: BuilderRepository):
        """Test getting build that doesn't exist."""
        retrieved = await repository.get_by_id(99999)
        assert retrieved is None

    async def test_get_deleted_build_returns_none(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that soft-deleted builds are not returned."""
        # Create and delete build
        build = SavedBuild(name="Deleted Build", visibility="public", share_token=uuid.uuid4().hex)
        build.soft_delete()
        session.add(build)
        await session.commit()

        # Should not be retrievable
        retrieved = await repository.get_by_id(build.id)
        assert retrieved is None

    async def test_get_private_build_access_control(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test access control for private builds."""
        # Create private build owned by user 1
        build = SavedBuild(
            user_id=1, name="Private Build", visibility="private", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        # Owner can access
        retrieved = await repository.get_by_id(build.id, user_id=1)
        assert retrieved is not None
        assert retrieved.id == build.id

        # Non-owner cannot access
        retrieved = await repository.get_by_id(build.id, user_id=2)
        assert retrieved is None

    async def test_get_public_build_no_access_control(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that public builds are accessible to anyone."""
        # Create public build
        build = SavedBuild(
            user_id=1, name="Public Build", visibility="public", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        # Anyone can access without user_id
        retrieved = await repository.get_by_id(build.id)
        assert retrieved is not None

        # Anyone can access with different user_id
        retrieved = await repository.get_by_id(build.id, user_id=2)
        assert retrieved is not None


@pytest.mark.asyncio
class TestGetByShareToken:
    """Test BuilderRepository.get_by_share_token() method."""

    async def test_get_public_build_by_token(
        self, repository: BuilderRepository, session: AsyncSession, sample_cpu: Cpu
    ):
        """Test getting public build by share token."""
        share_token = uuid.uuid4().hex
        build = SavedBuild(
            name="Public Build", visibility="public", share_token=share_token, cpu_id=sample_cpu.id
        )
        session.add(build)
        await session.commit()

        retrieved = await repository.get_by_share_token(share_token)

        assert retrieved is not None
        assert retrieved.share_token == share_token
        assert retrieved.name == "Public Build"
        # Verify eager loading
        assert retrieved.cpu is not None

    async def test_get_unlisted_build_by_token(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test getting unlisted build by share token."""
        share_token = uuid.uuid4().hex
        build = SavedBuild(name="Unlisted Build", visibility="unlisted", share_token=share_token)
        session.add(build)
        await session.commit()

        retrieved = await repository.get_by_share_token(share_token)

        assert retrieved is not None
        assert retrieved.visibility == "unlisted"

    async def test_get_private_build_by_token_returns_none(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that private builds cannot be accessed via share token."""
        share_token = uuid.uuid4().hex
        build = SavedBuild(
            user_id=1, name="Private Build", visibility="private", share_token=share_token
        )
        session.add(build)
        await session.commit()

        # Private builds not accessible via share token
        retrieved = await repository.get_by_share_token(share_token)
        assert retrieved is None

    async def test_get_by_invalid_token(self, repository: BuilderRepository):
        """Test getting build with invalid token."""
        retrieved = await repository.get_by_share_token("invalid_token_12345")
        assert retrieved is None

    async def test_get_deleted_build_by_token_returns_none(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that deleted builds cannot be accessed via share token."""
        share_token = uuid.uuid4().hex
        build = SavedBuild(name="Deleted Build", visibility="public", share_token=share_token)
        build.soft_delete()
        session.add(build)
        await session.commit()

        retrieved = await repository.get_by_share_token(share_token)
        assert retrieved is None


@pytest.mark.asyncio
class TestListByUser:
    """Test BuilderRepository.list_by_user() method."""

    async def test_list_user_builds(
        self, repository: BuilderRepository, session: AsyncSession, sample_cpu: Cpu, sample_gpu: Gpu
    ):
        """Test listing builds for a user."""
        # Create multiple builds for user 1
        builds = [
            SavedBuild(
                user_id=1,
                name=f"Build {i}",
                visibility="private",
                share_token=uuid.uuid4().hex,
                cpu_id=sample_cpu.id if i % 2 == 0 else None,
                gpu_id=sample_gpu.id if i % 2 == 1 else None,
            )
            for i in range(5)
        ]
        session.add_all(builds)
        await session.commit()

        # List builds
        retrieved = await repository.list_by_user(user_id=1)

        assert len(retrieved) == 5
        # Verify ordering (newest first)
        for i in range(len(retrieved) - 1):
            assert retrieved[i].created_at >= retrieved[i + 1].created_at

    async def test_list_user_builds_with_eager_loading(
        self, repository: BuilderRepository, session: AsyncSession, sample_cpu: Cpu, sample_gpu: Gpu
    ):
        """Test that list operation uses eager loading (no N+1 queries)."""
        # Create builds with CPU and GPU
        builds = [
            SavedBuild(
                user_id=1,
                name=f"Build {i}",
                visibility="private",
                share_token=uuid.uuid4().hex,
                cpu_id=sample_cpu.id,
                gpu_id=sample_gpu.id,
            )
            for i in range(3)
        ]
        session.add_all(builds)
        await session.commit()

        # List builds - should use joinedload
        retrieved = await repository.list_by_user(user_id=1)

        # Access CPU and GPU without additional queries
        for build in retrieved:
            assert build.cpu is not None
            assert build.cpu.name == "Intel Core i7-12700K"
            assert build.gpu is not None
            assert build.gpu.name == "NVIDIA RTX 3080"

    async def test_list_user_builds_pagination(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test pagination for user builds list."""
        # Create 15 builds
        builds = [
            SavedBuild(
                user_id=1, name=f"Build {i}", visibility="private", share_token=uuid.uuid4().hex
            )
            for i in range(15)
        ]
        session.add_all(builds)
        await session.commit()

        # Get first page
        page1 = await repository.list_by_user(user_id=1, limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await repository.list_by_user(user_id=1, limit=5, offset=5)
        assert len(page2) == 5

        # Get third page
        page3 = await repository.list_by_user(user_id=1, limit=5, offset=10)
        assert len(page3) == 5

        # Verify no overlap
        page1_ids = {b.id for b in page1}
        page2_ids = {b.id for b in page2}
        page3_ids = {b.id for b in page3}
        assert len(page1_ids & page2_ids) == 0
        assert len(page2_ids & page3_ids) == 0
        assert len(page1_ids & page3_ids) == 0

    async def test_list_excludes_deleted_builds(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that soft-deleted builds are excluded from list."""
        # Create active builds
        active_builds = [
            SavedBuild(
                user_id=1, name=f"Active {i}", visibility="private", share_token=uuid.uuid4().hex
            )
            for i in range(3)
        ]
        session.add_all(active_builds)

        # Create deleted builds
        deleted_builds = [
            SavedBuild(
                user_id=1, name=f"Deleted {i}", visibility="private", share_token=uuid.uuid4().hex
            )
            for i in range(2)
        ]
        for build in deleted_builds:
            build.soft_delete()
        session.add_all(deleted_builds)

        await session.commit()

        # List should only return active builds
        retrieved = await repository.list_by_user(user_id=1)
        assert len(retrieved) == 3
        assert all("Active" in b.name for b in retrieved)

    async def test_list_empty_for_user_with_no_builds(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test listing builds for user with no builds."""
        # Create builds for user 1
        build = SavedBuild(
            user_id=1, name="User 1 Build", visibility="private", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        # List builds for user 2 (no builds)
        retrieved = await repository.list_by_user(user_id=2)
        assert len(retrieved) == 0


@pytest.mark.asyncio
class TestUpdate:
    """Test BuilderRepository.update() method."""

    async def test_update_build_fields(self, repository: BuilderRepository, session: AsyncSession):
        """Test updating allowed build fields."""
        # Create build
        build = SavedBuild(
            user_id=1,
            name="Original Name",
            description="Original description",
            tags=["original"],
            visibility="private",
            share_token=uuid.uuid4().hex,
        )
        session.add(build)
        await session.commit()

        original_updated_at = build.updated_at

        # Update build
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "tags": ["updated", "modified"],
            "visibility": "public",
        }
        updated = await repository.update(build.id, update_data, user_id=1)
        await session.commit()

        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.tags == ["updated", "modified"]
        assert updated.visibility == "public"
        assert updated.updated_at > original_updated_at

    async def test_update_component_ids(
        self, repository: BuilderRepository, session: AsyncSession, sample_cpu: Cpu, sample_gpu: Gpu
    ):
        """Test updating component IDs."""
        # Create build without components
        build = SavedBuild(
            user_id=1, name="Build", visibility="private", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        # Update with components
        update_data = {
            "cpu_id": sample_cpu.id,
            "gpu_id": sample_gpu.id,
            "ram_spec_id": 1,
            "storage_spec_id": 2,
        }
        updated = await repository.update(build.id, update_data, user_id=1)
        await session.commit()

        assert updated.cpu_id == sample_cpu.id
        assert updated.gpu_id == sample_gpu.id
        assert updated.ram_spec_id == 1
        assert updated.storage_spec_id == 2

    async def test_update_snapshots(self, repository: BuilderRepository, session: AsyncSession):
        """Test updating snapshot fields."""
        # Create build
        build = SavedBuild(
            user_id=1, name="Build", visibility="private", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        # Update snapshots
        update_data = {
            "pricing_snapshot": {"base_price": 1000.0, "adjusted_price": 950.0},
            "metrics_snapshot": {"composite_score": 85.5},
            "valuation_breakdown": {"rules_applied": ["DISCOUNT"]},
        }
        updated = await repository.update(build.id, update_data, user_id=1)
        await session.commit()

        assert updated.pricing_snapshot["base_price"] == 1000.0
        assert updated.metrics_snapshot["composite_score"] == 85.5
        assert updated.valuation_breakdown["rules_applied"] == ["DISCOUNT"]

    async def test_update_protected_fields_ignored(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that protected fields are ignored during update."""
        # Create build
        original_token = uuid.uuid4().hex
        build = SavedBuild(
            user_id=1, name="Build", visibility="private", share_token=original_token
        )
        session.add(build)
        await session.commit()

        original_id = build.id
        original_created_at = build.created_at

        # Attempt to update protected fields
        update_data = {
            "id": 99999,
            "user_id": 2,
            "share_token": "hacked_token",
            "created_at": datetime(2020, 1, 1),
            "deleted_at": datetime.utcnow(),
            "name": "Updated Name",  # This should work
        }
        updated = await repository.update(build.id, update_data, user_id=1)
        await session.commit()

        # Protected fields unchanged
        assert updated.id == original_id
        assert updated.user_id == 1
        assert updated.share_token == original_token
        assert updated.created_at == original_created_at
        assert updated.deleted_at is None
        # Allowed field updated
        assert updated.name == "Updated Name"

    async def test_update_access_denied_for_non_owner(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that non-owners cannot update builds."""
        # Create build owned by user 1
        build = SavedBuild(
            user_id=1, name="User 1 Build", visibility="private", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        # User 2 attempts to update
        update_data = {"name": "Hacked Name"}

        with pytest.raises(ValueError, match="not found or access denied"):
            await repository.update(build.id, update_data, user_id=2)

    async def test_update_nonexistent_build(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test error when updating non-existent build."""
        update_data = {"name": "New Name"}

        with pytest.raises(ValueError, match="not found or access denied"):
            await repository.update(99999, update_data, user_id=1)


@pytest.mark.asyncio
class TestSoftDelete:
    """Test BuilderRepository.soft_delete() method."""

    async def test_soft_delete_build(self, repository: BuilderRepository, session: AsyncSession):
        """Test soft deleting a build."""
        # Create build
        build = SavedBuild(
            user_id=1, name="Build to Delete", visibility="private", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        build_id = build.id

        # Soft delete
        result = await repository.soft_delete(build_id, user_id=1)
        await session.commit()

        assert result is True

        # Verify build is soft-deleted (not retrievable)
        retrieved = await repository.get_by_id(build_id)
        assert retrieved is None

        # Verify build still exists in database with deleted_at set (bypass soft delete filter)
        from sqlalchemy import select

        result = await session.execute(select(SavedBuild).where(SavedBuild.id == build_id))
        deleted_build = result.scalar_one_or_none()
        assert deleted_build is not None
        assert deleted_build.deleted_at is not None

    async def test_soft_delete_access_denied(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that non-owners cannot delete builds."""
        # Create build owned by user 1
        build = SavedBuild(
            user_id=1, name="User 1 Build", visibility="private", share_token=uuid.uuid4().hex
        )
        session.add(build)
        await session.commit()

        # User 2 attempts to delete
        with pytest.raises(ValueError, match="not found or access denied"):
            await repository.soft_delete(build.id, user_id=2)

    async def test_soft_delete_nonexistent_build(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test error when deleting non-existent build."""
        with pytest.raises(ValueError, match="not found or access denied"):
            await repository.soft_delete(99999, user_id=1)

    async def test_soft_deleted_not_in_user_list(
        self, repository: BuilderRepository, session: AsyncSession
    ):
        """Test that soft-deleted builds don't appear in list_by_user."""
        # Create builds
        builds = [
            SavedBuild(
                user_id=1, name=f"Build {i}", visibility="private", share_token=uuid.uuid4().hex
            )
            for i in range(3)
        ]
        session.add_all(builds)
        await session.commit()

        # Soft delete one build
        await repository.soft_delete(builds[1].id, user_id=1)
        await session.commit()

        # List should only show 2 active builds
        retrieved = await repository.list_by_user(user_id=1)
        assert len(retrieved) == 2
        assert builds[1].id not in [b.id for b in retrieved]
