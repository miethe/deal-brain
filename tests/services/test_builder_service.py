"""Tests for BuilderService (Phase 3: Service Layer).

This test suite verifies:
- calculate_build_valuation() with component validation and price calculation
- calculate_build_metrics() using CPU benchmark data
- save_build() with snapshot generation and persistence
- get_user_builds() pagination and ordering
- get_build_by_id() with access control
- compare_build_to_listings() similarity matching
- Performance targets (<300ms calculate, <500ms save)
- Integration with existing domain logic

Target: >85% code coverage
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import TypeDecorator

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.builds import SavedBuild
from apps.api.dealbrain_api.models.catalog import Cpu, Gpu
from apps.api.dealbrain_api.models.listings import Listing
from apps.api.dealbrain_api.services.builder_service import BuilderService

try:
    import aiosqlite  # type: ignore  # noqa: F401
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


class JSONEncodedList(TypeDecorator):
    """Represents a list as JSON-encoded string for SQLite compatibility."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JSONEncodedDict(TypeDecorator):
    """Represents a dict as JSON-encoded string for SQLite compatibility."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


@pytest.fixture
def anyio_backend():
    """Configure async backend for tests."""
    return "asyncio"


@pytest_asyncio.fixture
async def session():
    """Create an in-memory async database session for testing."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    # Patch SavedBuild PostgreSQL-specific columns for SQLite compatibility
    original_types = {}
    patches = {
        "tags": JSONEncodedList(),
        "pricing_snapshot": JSONEncodedDict(),
        "metrics_snapshot": JSONEncodedDict(),
        "valuation_breakdown": JSONEncodedDict()
    }

    for col_name, new_type in patches.items():
        column = SavedBuild.__table__.c[col_name]
        original_types[col_name] = column.type
        column.type = new_type

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

        # Restore original types
        for col_name, original_type in original_types.items():
            column = SavedBuild.__table__.c[col_name]
            column.type = original_type


@pytest_asyncio.fixture
async def cpu_sample(session: AsyncSession) -> Cpu:
    """Create a sample CPU with benchmark data."""
    cpu = Cpu(
        name="Intel Core i7-12700K",
        manufacturer="Intel",
        socket="LGA1700",
        cores=12,
        threads=20,
        tdp_w=125,
        cpu_mark_multi=35000,
        cpu_mark_single=4200,
        igpu_mark=2500,
        release_year=2021,
    )
    session.add(cpu)
    await session.commit()
    await session.refresh(cpu)
    return cpu


@pytest_asyncio.fixture
async def cpu_no_benchmarks(session: AsyncSession) -> Cpu:
    """Create a CPU without benchmark data."""
    cpu = Cpu(
        name="AMD Ryzen 5 5600G",
        manufacturer="AMD",
        socket="AM4",
        cores=6,
        threads=12,
        tdp_w=65,
        cpu_mark_multi=None,  # No benchmark data
        cpu_mark_single=None,
        release_year=2021,
    )
    session.add(cpu)
    await session.commit()
    await session.refresh(cpu)
    return cpu


@pytest_asyncio.fixture
async def gpu_sample(session: AsyncSession) -> Gpu:
    """Create a sample GPU."""
    gpu = Gpu(
        name="NVIDIA RTX 3060",
        manufacturer="NVIDIA",
        gpu_mark=15000,
    )
    session.add(gpu)
    await session.commit()
    await session.refresh(gpu)
    return gpu


@pytest_asyncio.fixture
async def listing_sample(session: AsyncSession, cpu_sample: Cpu) -> Listing:
    """Create a sample listing for comparison tests."""
    listing = Listing(
        title="Dell OptiPlex 7080 - i7-12700K",
        cpu_id=cpu_sample.id,
        ram_gb=32,
        primary_storage_gb=512,
        primary_storage_type="SSD",
        price_usd=899.99,
        adjusted_price_usd=849.99,
        condition="used",
        status="active",
        valuation_breakdown={
            "listing_price": 899.99,
            "adjusted_price": 849.99,
            "total_adjustment": -50.0,
        },
    )
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


# =============================================================================
# calculate_build_valuation() Tests
# =============================================================================


@pytest.mark.asyncio
async def test_calculate_build_valuation_cpu_only(
    session: AsyncSession, cpu_sample: Cpu
):
    """Test valuation calculation with CPU only."""
    service = BuilderService(session)

    components = {"cpu_id": cpu_sample.id}
    result = await service.calculate_build_valuation(components)

    # Verify result structure
    assert "base_price" in result
    assert "adjusted_price" in result
    assert "delta_amount" in result
    assert "delta_percentage" in result
    assert "breakdown" in result

    # Verify base_price is Decimal
    assert isinstance(result["base_price"], Decimal)
    assert result["base_price"] > 0

    # Verify adjusted_price equals base_price (no adjustments in Phase 3)
    assert result["adjusted_price"] == result["base_price"]
    assert result["delta_amount"] == Decimal("0.00")

    # Verify breakdown structure
    breakdown = result["breakdown"]
    assert "components" in breakdown
    assert "adjustments" in breakdown
    assert len(breakdown["components"]) == 1  # CPU only
    assert breakdown["components"][0]["type"] == "CPU"
    assert breakdown["components"][0]["name"] == cpu_sample.name


@pytest.mark.asyncio
async def test_calculate_build_valuation_full_build(
    session: AsyncSession, cpu_sample: Cpu, gpu_sample: Gpu
):
    """Test valuation calculation with CPU + GPU."""
    service = BuilderService(session)

    components = {
        "cpu_id": cpu_sample.id,
        "gpu_id": gpu_sample.id,
    }
    result = await service.calculate_build_valuation(components)

    # Verify base_price includes both components
    assert result["base_price"] > 0
    breakdown = result["breakdown"]
    assert len(breakdown["components"]) == 2  # CPU + GPU

    # Verify component breakdown
    component_types = [c["type"] for c in breakdown["components"]]
    assert "CPU" in component_types
    assert "GPU" in component_types


@pytest.mark.asyncio
async def test_calculate_build_valuation_cpu_required_error(session: AsyncSession):
    """Test that CPU is required for valuation."""
    service = BuilderService(session)

    components = {}  # No CPU
    with pytest.raises(ValueError, match="CPU is required"):
        await service.calculate_build_valuation(components)


@pytest.mark.asyncio
async def test_calculate_build_valuation_invalid_cpu_id(session: AsyncSession):
    """Test error handling for invalid CPU ID."""
    service = BuilderService(session)

    components = {"cpu_id": 99999}  # Non-existent CPU ID
    with pytest.raises(ValueError, match="Invalid CPU ID"):
        await service.calculate_build_valuation(components)


@pytest.mark.asyncio
async def test_calculate_build_valuation_invalid_gpu_id(
    session: AsyncSession, cpu_sample: Cpu
):
    """Test error handling for invalid GPU ID."""
    service = BuilderService(session)

    components = {
        "cpu_id": cpu_sample.id,
        "gpu_id": 99999,  # Non-existent GPU ID
    }
    with pytest.raises(ValueError, match="Invalid GPU ID"):
        await service.calculate_build_valuation(components)


@pytest.mark.asyncio
async def test_calculate_build_valuation_performance(
    session: AsyncSession, cpu_sample: Cpu, gpu_sample: Gpu
):
    """Test that valuation calculation completes in <300ms."""
    service = BuilderService(session)

    components = {
        "cpu_id": cpu_sample.id,
        "gpu_id": gpu_sample.id,
    }

    start = time.time()
    await service.calculate_build_valuation(components)
    duration_ms = (time.time() - start) * 1000

    # Performance target: <300ms
    assert duration_ms < 300, f"Valuation took {duration_ms:.2f}ms (target: <300ms)"


# =============================================================================
# calculate_build_metrics() Tests
# =============================================================================


@pytest.mark.asyncio
async def test_calculate_build_metrics_with_benchmarks(
    session: AsyncSession, cpu_sample: Cpu
):
    """Test metrics calculation with CPU benchmark data."""
    service = BuilderService(session)

    adjusted_price = Decimal("899.99")
    result = await service.calculate_build_metrics(cpu_sample.id, adjusted_price)

    # Verify result structure
    assert "dollar_per_cpu_mark_multi" in result
    assert "dollar_per_cpu_mark_single" in result
    assert "composite_score" in result
    assert "cpu_mark_multi" in result
    assert "cpu_mark_single" in result

    # Verify metrics calculated correctly
    assert result["cpu_mark_multi"] == cpu_sample.cpu_mark_multi
    assert result["cpu_mark_single"] == cpu_sample.cpu_mark_single
    assert result["dollar_per_cpu_mark_multi"] is not None
    assert result["dollar_per_cpu_mark_single"] is not None

    # Verify dollar_per_cpu_mark calculation
    expected_multi = float(adjusted_price) / cpu_sample.cpu_mark_multi
    assert abs(float(result["dollar_per_cpu_mark_multi"]) - expected_multi) < 0.0001


@pytest.mark.asyncio
async def test_calculate_build_metrics_no_benchmarks(
    session: AsyncSession, cpu_no_benchmarks: Cpu
):
    """Test metrics calculation with CPU lacking benchmark data."""
    service = BuilderService(session)

    adjusted_price = Decimal("599.99")
    result = await service.calculate_build_metrics(cpu_no_benchmarks.id, adjusted_price)

    # Verify metrics are None when no benchmark data
    assert result["cpu_mark_multi"] is None
    assert result["cpu_mark_single"] is None
    assert result["dollar_per_cpu_mark_multi"] is None
    assert result["dollar_per_cpu_mark_single"] is None
    assert result["composite_score"] is None


@pytest.mark.asyncio
async def test_calculate_build_metrics_invalid_cpu_id(session: AsyncSession):
    """Test error handling for invalid CPU ID."""
    service = BuilderService(session)

    with pytest.raises(ValueError, match="Invalid CPU ID"):
        await service.calculate_build_metrics(99999, Decimal("899.99"))


# =============================================================================
# save_build() Tests
# =============================================================================


@pytest.mark.asyncio
async def test_save_build_success(session: AsyncSession, cpu_sample: Cpu):
    """Test successful build save with snapshots."""
    service = BuilderService(session)

    request = {
        "name": "My Gaming Build",
        "description": "High-performance gaming PC",
        "tags": ["gaming", "high-end"],
        "visibility": "public",
        "components": {"cpu_id": cpu_sample.id},
    }

    build = await service.save_build(request, user_id=1)

    # Verify build created
    assert build.id is not None
    assert build.name == "My Gaming Build"
    assert build.description == "High-performance gaming PC"
    assert build.tags == ["gaming", "high-end"]
    assert build.visibility == "public"
    assert build.user_id == 1
    assert build.cpu_id == cpu_sample.id

    # Verify share_token generated (32 chars hex)
    assert len(build.share_token) == 32
    assert all(c in "0123456789abcdef" for c in build.share_token)

    # Verify pricing_snapshot structure
    assert build.pricing_snapshot is not None
    assert "base_price" in build.pricing_snapshot
    assert "adjusted_price" in build.pricing_snapshot
    assert "delta_amount" in build.pricing_snapshot
    assert "delta_percentage" in build.pricing_snapshot
    assert "breakdown" in build.pricing_snapshot
    assert "calculated_at" in build.pricing_snapshot

    # Verify metrics_snapshot structure
    assert build.metrics_snapshot is not None
    assert "dollar_per_cpu_mark_multi" in build.metrics_snapshot
    assert "dollar_per_cpu_mark_single" in build.metrics_snapshot
    assert "composite_score" in build.metrics_snapshot
    assert "calculated_at" in build.metrics_snapshot

    # Verify valuation_breakdown
    assert build.valuation_breakdown is not None
    assert "components" in build.valuation_breakdown
    assert "adjustments" in build.valuation_breakdown


@pytest.mark.asyncio
async def test_save_build_name_required(session: AsyncSession, cpu_sample: Cpu):
    """Test that build name is required."""
    service = BuilderService(session)

    request = {
        "name": "",  # Empty name
        "visibility": "private",
        "components": {"cpu_id": cpu_sample.id},
    }

    with pytest.raises(ValueError, match="Build name is required"):
        await service.save_build(request)


@pytest.mark.asyncio
async def test_save_build_invalid_visibility(session: AsyncSession, cpu_sample: Cpu):
    """Test validation of visibility enum."""
    service = BuilderService(session)

    request = {
        "name": "Test Build",
        "visibility": "invalid",  # Invalid visibility
        "components": {"cpu_id": cpu_sample.id},
    }

    with pytest.raises(ValueError, match="Invalid visibility"):
        await service.save_build(request)


@pytest.mark.asyncio
async def test_save_build_cpu_required_in_components(session: AsyncSession):
    """Test that CPU is required in components."""
    service = BuilderService(session)

    request = {
        "name": "Test Build",
        "visibility": "private",
        "components": {},  # No CPU
    }

    with pytest.raises(ValueError, match="CPU is required"):
        await service.save_build(request)


@pytest.mark.asyncio
async def test_save_build_snapshot_values_match_calculation(
    session: AsyncSession, cpu_sample: Cpu
):
    """Test that snapshot values match current calculation."""
    service = BuilderService(session)

    request = {
        "name": "Snapshot Test Build",
        "visibility": "private",
        "components": {"cpu_id": cpu_sample.id},
    }

    # Calculate valuation separately
    valuation = await service.calculate_build_valuation(request["components"])

    # Save build
    build = await service.save_build(request)

    # Verify snapshot values match calculation
    assert build.pricing_snapshot["base_price"] == str(valuation["base_price"])
    assert build.pricing_snapshot["adjusted_price"] == str(valuation["adjusted_price"])


@pytest.mark.asyncio
async def test_save_build_performance(
    session: AsyncSession, cpu_sample: Cpu, gpu_sample: Gpu
):
    """Test that save_build completes in <500ms."""
    service = BuilderService(session)

    request = {
        "name": "Performance Test Build",
        "visibility": "private",
        "components": {
            "cpu_id": cpu_sample.id,
            "gpu_id": gpu_sample.id,
        },
    }

    start = time.time()
    await service.save_build(request, user_id=1)
    duration_ms = (time.time() - start) * 1000

    # Performance target: <500ms
    assert duration_ms < 500, f"Save took {duration_ms:.2f}ms (target: <500ms)"


# =============================================================================
# get_user_builds() Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_user_builds_pagination(session: AsyncSession, cpu_sample: Cpu):
    """Test pagination of user builds."""
    service = BuilderService(session)

    # Create 5 builds for user 1
    for i in range(5):
        request = {
            "name": f"Build {i+1}",
            "visibility": "private",
            "components": {"cpu_id": cpu_sample.id},
        }
        await service.save_build(request, user_id=1)

    # Test limit
    builds = await service.get_user_builds(user_id=1, limit=3, offset=0)
    assert len(builds) == 3

    # Test offset
    builds_offset = await service.get_user_builds(user_id=1, limit=3, offset=3)
    assert len(builds_offset) == 2


@pytest.mark.asyncio
async def test_get_user_builds_ordering(session: AsyncSession, cpu_sample: Cpu):
    """Test that builds are ordered by created_at DESC (newest first)."""
    service = BuilderService(session)

    # Create multiple builds
    build_ids = []
    for i in range(3):
        build = await service.save_build(
            {
                "name": f"Build {i+1}",
                "visibility": "private",
                "components": {"cpu_id": cpu_sample.id},
            },
            user_id=1,
        )
        build_ids.append(build.id)

    # Get builds
    builds = await service.get_user_builds(user_id=1, limit=10, offset=0)

    # Verify we got all builds
    assert len(builds) == 3

    # Verify builds are ordered by created_at DESC
    # Since created_at should be non-increasing
    for i in range(len(builds) - 1):
        assert builds[i].created_at >= builds[i + 1].created_at


@pytest.mark.asyncio
async def test_get_user_builds_empty_result(session: AsyncSession):
    """Test empty result when user has no builds."""
    service = BuilderService(session)

    builds = await service.get_user_builds(user_id=999, limit=10, offset=0)
    assert len(builds) == 0


# =============================================================================
# get_build_by_id() Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_build_by_id_public_build(session: AsyncSession, cpu_sample: Cpu):
    """Test getting a public build."""
    service = BuilderService(session)

    # Create public build
    build = await service.save_build(
        {
            "name": "Public Build",
            "visibility": "public",
            "components": {"cpu_id": cpu_sample.id},
        },
        user_id=1,
    )

    # Get build without user_id (anonymous access)
    result = await service.get_build_by_id(build.id)
    assert result is not None
    assert result.id == build.id


@pytest.mark.asyncio
async def test_get_build_by_id_private_build_access_control(
    session: AsyncSession, cpu_sample: Cpu
):
    """Test access control for private builds."""
    service = BuilderService(session)

    # Create private build for user 1
    build = await service.save_build(
        {
            "name": "Private Build",
            "visibility": "private",
            "components": {"cpu_id": cpu_sample.id},
        },
        user_id=1,
    )

    # Owner can access
    result_owner = await service.get_build_by_id(build.id, user_id=1)
    assert result_owner is not None
    assert result_owner.id == build.id

    # Other user cannot access
    result_other = await service.get_build_by_id(build.id, user_id=2)
    assert result_other is None


@pytest.mark.asyncio
async def test_get_build_by_id_not_found(session: AsyncSession):
    """Test that non-existent build returns None."""
    service = BuilderService(session)

    result = await service.get_build_by_id(99999)
    assert result is None


# =============================================================================
# compare_build_to_listings() Tests
# =============================================================================


@pytest.mark.asyncio
async def test_compare_build_to_listings_same_cpu(
    session: AsyncSession, cpu_sample: Cpu, listing_sample: Listing
):
    """Test finding listings with same CPU."""
    service = BuilderService(session)

    results = await service.compare_build_to_listings(
        cpu_id=cpu_sample.id,
        ram_gb=32,
        storage_gb=512,
        limit=5,
    )

    # Verify results
    assert len(results) == 1
    assert results[0]["listing_id"] == listing_sample.id
    assert results[0]["name"] == listing_sample.title
    assert results[0]["similarity_score"] > 0.8  # High similarity (same CPU, similar specs)


@pytest.mark.asyncio
async def test_compare_build_to_listings_similarity_scoring(
    session: AsyncSession, cpu_sample: Cpu
):
    """Test similarity scoring based on specs."""
    service = BuilderService(session)

    # Create listing with different RAM/storage
    listing = Listing(
        title="Dell OptiPlex - Different Specs",
        cpu_id=cpu_sample.id,
        ram_gb=16,  # Different RAM (32 vs 16 = 16GB diff)
        primary_storage_gb=256,  # Different storage (512 vs 256 = 256GB diff)
        price_usd=699.99,
        adjusted_price_usd=649.99,
        condition="used",
        status="active",
    )
    session.add(listing)
    await session.commit()

    results = await service.compare_build_to_listings(
        cpu_id=cpu_sample.id,
        ram_gb=32,
        storage_gb=512,
        limit=5,
    )

    # Verify similarity score is lower due to spec differences
    assert len(results) == 1
    assert results[0]["similarity_score"] < 1.0
    assert results[0]["similarity_score"] > 0.7  # Still reasonably similar


@pytest.mark.asyncio
async def test_compare_build_to_listings_limit(
    session: AsyncSession, cpu_sample: Cpu
):
    """Test limit parameter."""
    service = BuilderService(session)

    # Create 10 listings
    for i in range(10):
        listing = Listing(
            title=f"Listing {i+1}",
            cpu_id=cpu_sample.id,
            ram_gb=32,
            primary_storage_gb=512,
            price_usd=899.99,
            adjusted_price_usd=849.99,
            condition="used",
            status="active",
        )
        session.add(listing)
    await session.commit()

    # Request only 5
    results = await service.compare_build_to_listings(
        cpu_id=cpu_sample.id,
        ram_gb=32,
        storage_gb=512,
        limit=5,
    )

    # Verify limit enforced
    assert len(results) <= 5


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_end_to_end_build_workflow(
    session: AsyncSession, cpu_sample: Cpu, gpu_sample: Gpu
):
    """Test end-to-end: calculate → save → retrieve → compare."""
    service = BuilderService(session)

    # Step 1: Calculate valuation
    components = {
        "cpu_id": cpu_sample.id,
        "gpu_id": gpu_sample.id,
    }
    valuation = await service.calculate_build_valuation(components)
    assert valuation["base_price"] > 0

    # Step 2: Calculate metrics
    metrics = await service.calculate_build_metrics(
        cpu_sample.id, valuation["adjusted_price"]
    )
    assert metrics["dollar_per_cpu_mark_multi"] is not None

    # Step 3: Save build
    request = {
        "name": "E2E Test Build",
        "description": "End-to-end test",
        "tags": ["test"],
        "visibility": "public",
        "components": components,
    }
    build = await service.save_build(request, user_id=1)
    assert build.id is not None

    # Step 4: Retrieve build
    retrieved = await service.get_build_by_id(build.id, user_id=1)
    assert retrieved is not None
    assert retrieved.name == "E2E Test Build"

    # Step 5: Compare to listings
    # Create a sample listing
    listing = Listing(
        title="Similar Listing",
        cpu_id=cpu_sample.id,
        gpu_id=gpu_sample.id,
        ram_gb=32,
        primary_storage_gb=512,
        price_usd=999.99,
        adjusted_price_usd=949.99,
        condition="used",
        status="active",
    )
    session.add(listing)
    await session.commit()

    comparisons = await service.compare_build_to_listings(
        cpu_id=cpu_sample.id,
        ram_gb=32,
        storage_gb=512,
        limit=5,
    )
    assert len(comparisons) == 1
    assert comparisons[0]["listing_id"] == listing.id


@pytest.mark.asyncio
async def test_snapshot_consistency(session: AsyncSession, cpu_sample: Cpu):
    """Test that saved snapshot values match current calculation."""
    service = BuilderService(session)

    request = {
        "name": "Snapshot Consistency Test",
        "visibility": "private",
        "components": {"cpu_id": cpu_sample.id},
    }

    # Save build (creates snapshots)
    build = await service.save_build(request, user_id=1)

    # Calculate current values
    current_valuation = await service.calculate_build_valuation(request["components"])
    current_metrics = await service.calculate_build_metrics(
        cpu_sample.id, current_valuation["adjusted_price"]
    )

    # Verify snapshot matches current calculation
    assert build.pricing_snapshot["base_price"] == str(current_valuation["base_price"])
    assert build.pricing_snapshot["adjusted_price"] == str(
        current_valuation["adjusted_price"]
    )

    # Verify metrics snapshot
    if current_metrics["dollar_per_cpu_mark_multi"] is not None:
        assert build.metrics_snapshot["dollar_per_cpu_mark_multi"] == str(
            current_metrics["dollar_per_cpu_mark_multi"]
        )
