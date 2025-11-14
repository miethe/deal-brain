"""API integration tests for Deal Builder endpoints.

Tests the following endpoints:
- POST /v1/builder/calculate - Calculate build valuation and metrics
- POST /v1/builder/builds - Save a build
- GET /v1/builder/builds - List user's builds
- GET /v1/builder/builds/{build_id} - Get single build
- PATCH /v1/builder/builds/{build_id} - Update build
- DELETE /v1/builder/builds/{build_id} - Delete build
- GET /v1/builder/builds/shared/{share_token} - Get build by share token
- GET /v1/builder/compare - Compare to listings

Validates:
- Response status codes
- Response schema compliance
- Business logic (valuation, metrics calculation)
- Access control (public/private/unlisted)
- Error handling (400, 403, 404, 500)
- Data integrity and persistence
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.types import TypeDecorator

from dealbrain_api.app import create_app
from dealbrain_api.db import Base
from dealbrain_api.models.builds import SavedBuild
from dealbrain_api.models.catalog import Cpu, Gpu
from dealbrain_api.models.listings import Listing
from dealbrain_core.enums import ListingStatus

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


# --- Fixtures ---


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create async database session for tests using in-memory SQLite."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping API integration tests")

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

    # Use in-memory SQLite for tests to avoid polluting dev database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with async_session_maker() as session:
            yield session

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()
    finally:
        # Restore original types
        for col_name, original_type in original_types.items():
            SavedBuild.__table__.c[col_name].type = original_type


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    """Create async HTTP client for API tests with database dependency override."""
    from dealbrain_api.db import session_dependency

    app = create_app()

    # Override the session_dependency to use our test database session
    async def override_session_dependency():
        yield db_session

    app.dependency_overrides[session_dependency] = override_session_dependency

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_cpu(db_session: AsyncSession) -> Cpu:
    """Create a sample CPU with benchmark data."""
    cpu = Cpu(
        name="Intel Core i5-12400",
        manufacturer="Intel",
        socket="LGA1700",
        cores=6,
        threads=12,
        tdp_w=65,
        cpu_mark_multi=17500,
        cpu_mark_single=3200,
        release_year=2022,
    )
    db_session.add(cpu)
    await db_session.commit()
    await db_session.refresh(cpu)
    return cpu


@pytest_asyncio.fixture
async def sample_gpu(db_session: AsyncSession) -> Gpu:
    """Create a sample GPU with benchmark data."""
    gpu = Gpu(
        name="NVIDIA GTX 1660",
        manufacturer="NVIDIA",
        gpu_mark=12000,
    )
    db_session.add(gpu)
    await db_session.commit()
    await db_session.refresh(gpu)
    return gpu


@pytest_asyncio.fixture
async def sample_build(db_session: AsyncSession, sample_cpu: Cpu) -> SavedBuild:
    """Create a sample saved build.

    Uses user_id=0 to match the default user_id used in API tests
    when no authentication is provided (user_id or 0 = 0).
    """
    build = SavedBuild(
        user_id=0,  # Match default user_id in API (user_id or 0)
        name="Test Build",
        description="Test build description",
        tags=["test", "gaming"],
        visibility="private",
        share_token="test-share-token-123",
        cpu_id=sample_cpu.id,
        pricing_snapshot={
            "base_price": "325.00",
            "adjusted_price": "325.00",
        },
        metrics_snapshot={
            "composite_score": 75,
        },
        valuation_breakdown={
            "components": [],
            "adjustments": [],
        },
    )
    db_session.add(build)
    await db_session.commit()
    await db_session.refresh(build)
    return build


@pytest_asyncio.fixture
async def public_build(db_session: AsyncSession, sample_cpu: Cpu) -> SavedBuild:
    """Create a public saved build.

    Uses user_id=0 to match the default user_id used in API tests.
    """
    build = SavedBuild(
        user_id=0,  # Match default user_id in API
        name="Public Build",
        visibility="public",
        share_token="public-share-token-456",
        cpu_id=sample_cpu.id,
        pricing_snapshot={"base_price": "300.00"},
    )
    db_session.add(build)
    await db_session.commit()
    await db_session.refresh(build)
    return build


@pytest_asyncio.fixture
async def sample_listing(db_session: AsyncSession, sample_cpu: Cpu) -> Listing:
    """Create a sample listing for comparison."""
    listing = Listing(
        title="Intel i5-12400 PC",
        cpu_id=sample_cpu.id,
        price_usd=Decimal("350.00"),
        adjusted_price_usd=Decimal("340.00"),
        condition="refurbished",
        status=ListingStatus.ACTIVE.value,
        marketplace="ebay",
        listing_url="https://ebay.com/item/123",
        ram_gb=16,
        primary_storage_gb=512,
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)
    return listing


# --- Test POST /v1/builder/calculate ---


@pytest.mark.asyncio
async def test_calculate_build_success(
    async_client: AsyncClient,
    sample_cpu: Cpu,
    sample_gpu: Gpu,
):
    """Test successful build calculation with CPU and GPU."""
    response = await async_client.post(
        "/v1/builder/calculate",
        json={
            "cpu_id": sample_cpu.id,
            "gpu_id": sample_gpu.id,
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "valuation" in data
    assert "metrics" in data

    # Validate valuation
    valuation = data["valuation"]
    assert "base_price" in valuation
    assert "adjusted_price" in valuation
    assert "delta_amount" in valuation
    assert "delta_percentage" in valuation
    assert "breakdown" in valuation

    # Validate breakdown
    breakdown = valuation["breakdown"]
    assert "components" in breakdown
    assert "adjustments" in breakdown
    assert len(breakdown["components"]) >= 1  # At least CPU

    # Validate metrics
    metrics = data["metrics"]
    assert "dollar_per_cpu_mark_multi" in metrics
    assert "dollar_per_cpu_mark_single" in metrics
    assert "composite_score" in metrics
    assert "cpu_mark_multi" in metrics
    assert "cpu_mark_single" in metrics

    # Validate CPU benchmark data is included
    assert metrics["cpu_mark_multi"] == sample_cpu.cpu_mark_multi
    assert metrics["cpu_mark_single"] == sample_cpu.cpu_mark_single


@pytest.mark.asyncio
async def test_calculate_build_cpu_only(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test build calculation with CPU only (no GPU)."""
    response = await async_client.post(
        "/v1/builder/calculate",
        json={"cpu_id": sample_cpu.id}
    )

    assert response.status_code == 200
    data = response.json()

    # Should still return valid data
    assert "valuation" in data
    assert "metrics" in data

    # Base price should be > 0
    assert float(data["valuation"]["base_price"]) > 0


@pytest.mark.asyncio
async def test_calculate_build_missing_cpu(async_client: AsyncClient):
    """Test calculation fails without CPU (required)."""
    response = await async_client.post(
        "/v1/builder/calculate",
        json={"gpu_id": 999}  # Missing cpu_id
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_calculate_build_invalid_cpu_id(async_client: AsyncClient):
    """Test calculation fails with invalid CPU ID."""
    response = await async_client.post(
        "/v1/builder/calculate",
        json={"cpu_id": 99999}  # Non-existent CPU
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_calculate_build_invalid_gpu_id(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test calculation fails with invalid GPU ID."""
    response = await async_client.post(
        "/v1/builder/calculate",
        json={
            "cpu_id": sample_cpu.id,
            "gpu_id": 99999,  # Non-existent GPU
        }
    )

    assert response.status_code == 400
    assert "detail" in response.json()


# --- Test POST /v1/builder/builds ---


@pytest.mark.asyncio
async def test_save_build_success(
    async_client: AsyncClient,
    sample_cpu: Cpu,
    sample_gpu: Gpu,
):
    """Test successful build save."""
    response = await async_client.post(
        "/v1/builder/builds",
        json={
            "name": "My Gaming Build",
            "description": "High-performance gaming build",
            "tags": ["gaming", "intel"],
            "visibility": "public",
            "components": {
                "cpu_id": sample_cpu.id,
                "gpu_id": sample_gpu.id,
            }
        }
    )

    assert response.status_code == 201
    data = response.json()

    # Validate response structure
    assert data["name"] == "My Gaming Build"
    assert data["description"] == "High-performance gaming build"
    assert data["tags"] == ["gaming", "intel"]
    assert data["visibility"] == "public"
    assert data["cpu_id"] == sample_cpu.id
    assert data["gpu_id"] == sample_gpu.id

    # Validate share token generated
    assert "share_token" in data
    assert len(data["share_token"]) > 0

    # Validate snapshots created
    assert "pricing_snapshot" in data
    assert data["pricing_snapshot"] is not None
    assert "metrics_snapshot" in data
    assert data["metrics_snapshot"] is not None
    assert "valuation_breakdown" in data

    # Validate timestamps
    assert "created_at" in data
    assert "updated_at" in data
    assert "id" in data
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_save_build_missing_name(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test save fails without name (required)."""
    response = await async_client.post(
        "/v1/builder/builds",
        json={
            "components": {"cpu_id": sample_cpu.id}
            # Missing name
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_save_build_empty_name(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test save fails with empty/whitespace name."""
    response = await async_client.post(
        "/v1/builder/builds",
        json={
            "name": "   ",  # Whitespace only
            "components": {"cpu_id": sample_cpu.id}
        }
    )

    # Pydantic validation returns 422 for validation errors
    assert response.status_code == 422
    assert "name" in str(response.json()).lower()


@pytest.mark.asyncio
async def test_save_build_invalid_visibility(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test save fails with invalid visibility value."""
    response = await async_client.post(
        "/v1/builder/builds",
        json={
            "name": "Test Build",
            "visibility": "invalid",  # Not private/public/unlisted
            "components": {"cpu_id": sample_cpu.id}
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_save_build_default_visibility(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test build saves with default visibility (private)."""
    response = await async_client.post(
        "/v1/builder/builds",
        json={
            "name": "Test Build",
            "components": {"cpu_id": sample_cpu.id}
            # No visibility specified
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["visibility"] == "private"


@pytest.mark.asyncio
async def test_save_build_missing_cpu(async_client: AsyncClient):
    """Test save fails without CPU in components."""
    response = await async_client.post(
        "/v1/builder/builds",
        json={
            "name": "Test Build",
            "components": {}  # Missing cpu_id
        }
    )

    assert response.status_code == 422  # Validation error


# --- Test GET /v1/builder/builds ---


@pytest.mark.asyncio
async def test_list_builds_success(
    async_client: AsyncClient,
    sample_build: SavedBuild,
):
    """Test successful build listing."""
    response = await async_client.get("/v1/builder/builds")

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "builds" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    # Default pagination
    assert data["limit"] == 10
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_builds_pagination(
    async_client: AsyncClient,
    sample_build: SavedBuild,
):
    """Test build listing with pagination parameters."""
    response = await async_client.get(
        "/v1/builder/builds",
        params={"limit": 5, "offset": 0}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["limit"] == 5
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_builds_limit_validation(async_client: AsyncClient):
    """Test list fails with limit > 100."""
    response = await async_client.get(
        "/v1/builder/builds",
        params={"limit": 101}
    )

    # Pydantic/Query validation returns 422 for validation errors
    assert response.status_code == 422
    assert "limit" in str(response.json()).lower()


@pytest.mark.asyncio
async def test_list_builds_empty(async_client: AsyncClient):
    """Test listing with no builds returns empty list."""
    response = await async_client.get("/v1/builder/builds")

    assert response.status_code == 200
    data = response.json()

    assert data["builds"] == []
    assert data["total"] == 0


# --- Test GET /v1/builder/builds/{build_id} ---


@pytest.mark.asyncio
async def test_get_build_success(
    async_client: AsyncClient,
    sample_build: SavedBuild,
):
    """Test successful build retrieval."""
    response = await async_client.get(f"/v1/builder/builds/{sample_build.id}")

    assert response.status_code == 200
    data = response.json()

    # Validate response matches saved build
    assert data["id"] == sample_build.id
    assert data["name"] == sample_build.name
    assert data["description"] == sample_build.description
    assert data["visibility"] == sample_build.visibility
    assert data["share_token"] == sample_build.share_token


@pytest.mark.asyncio
async def test_get_build_public_access(
    async_client: AsyncClient,
    public_build: SavedBuild,
):
    """Test public build accessible without authentication."""
    response = await async_client.get(f"/v1/builder/builds/{public_build.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == public_build.id
    assert data["visibility"] == "public"


@pytest.mark.asyncio
async def test_get_build_not_found(async_client: AsyncClient):
    """Test get build returns 404 for non-existent ID."""
    response = await async_client.get("/v1/builder/builds/99999")

    assert response.status_code == 404
    assert "detail" in response.json()


# --- Test PATCH /v1/builder/builds/{build_id} ---


@pytest.mark.asyncio
async def test_update_build_success(
    async_client: AsyncClient,
    sample_build: SavedBuild,
    sample_cpu: Cpu,
):
    """Test successful build update."""
    response = await async_client.patch(
        f"/v1/builder/builds/{sample_build.id}",
        json={
            "name": "Updated Build Name",
            "description": "Updated description",
            "visibility": "public",
            "components": {"cpu_id": sample_cpu.id}
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Updated Build Name"
    assert data["description"] == "Updated description"
    assert data["visibility"] == "public"


@pytest.mark.asyncio
async def test_update_build_not_found(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test update returns 403 for non-existent build."""
    response = await async_client.patch(
        "/v1/builder/builds/99999",
        json={
            "name": "Updated Name",
            "components": {"cpu_id": sample_cpu.id}
        }
    )

    assert response.status_code == 403
    assert "detail" in response.json()


# --- Test DELETE /v1/builder/builds/{build_id} ---


@pytest.mark.asyncio
async def test_delete_build_success(
    async_client: AsyncClient,
    sample_build: SavedBuild,
):
    """Test successful build deletion."""
    response = await async_client.delete(f"/v1/builder/builds/{sample_build.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True

    # Verify build is soft deleted (no longer accessible)
    get_response = await async_client.get(f"/v1/builder/builds/{sample_build.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_build_not_found(async_client: AsyncClient):
    """Test delete returns 403 for non-existent build."""
    response = await async_client.delete("/v1/builder/builds/99999")

    assert response.status_code == 403
    assert "detail" in response.json()


# --- Test GET /v1/builder/builds/shared/{share_token} ---


@pytest.mark.asyncio
async def test_get_shared_build_success(
    async_client: AsyncClient,
    public_build: SavedBuild,
):
    """Test successful shared build retrieval."""
    response = await async_client.get(
        f"/v1/builder/builds/shared/{public_build.share_token}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == public_build.id
    assert data["share_token"] == public_build.share_token


@pytest.mark.asyncio
async def test_get_shared_build_private_not_accessible(
    async_client: AsyncClient,
    sample_build: SavedBuild,
):
    """Test private build not accessible via share token."""
    # sample_build is private
    response = await async_client.get(
        f"/v1/builder/builds/shared/{sample_build.share_token}"
    )

    # Private builds should return 404 via share link
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_shared_build_not_found(async_client: AsyncClient):
    """Test shared build returns 404 for invalid token."""
    response = await async_client.get(
        "/v1/builder/builds/shared/invalid-token-xyz"
    )

    assert response.status_code == 404
    assert "detail" in response.json()


# --- Test GET /v1/builder/compare ---


@pytest.mark.asyncio
async def test_compare_to_listings_success(
    async_client: AsyncClient,
    sample_cpu: Cpu,
    sample_listing: Listing,
):
    """Test successful comparison to listings."""
    response = await async_client.get(
        "/v1/builder/compare",
        params={
            "cpu_id": sample_cpu.id,
            "ram_gb": 16,
            "storage_gb": 512,
            "limit": 5,
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "listings" in data
    assert isinstance(data["listings"], list)

    # Should find at least one listing
    assert len(data["listings"]) >= 1

    # Validate listing structure
    if data["listings"]:
        listing = data["listings"][0]
        assert "listing_id" in listing
        assert "name" in listing
        assert "price" in listing
        assert "adjusted_price" in listing
        assert "deal_quality" in listing
        assert "price_difference" in listing
        assert "similarity_score" in listing


@pytest.mark.asyncio
async def test_compare_missing_cpu_id(async_client: AsyncClient):
    """Test compare fails without CPU ID."""
    response = await async_client.get("/v1/builder/compare")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_compare_no_matches(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test compare returns empty list when no matches found."""
    response = await async_client.get(
        "/v1/builder/compare",
        params={"cpu_id": sample_cpu.id}
    )

    assert response.status_code == 200
    data = response.json()

    # May return empty list if no listings
    assert "listings" in data
    assert isinstance(data["listings"], list)


# --- Performance Tests ---


@pytest.mark.asyncio
async def test_calculate_performance(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test calculate endpoint meets <300ms performance target."""
    import time

    start = time.time()
    response = await async_client.post(
        "/v1/builder/calculate",
        json={"cpu_id": sample_cpu.id}
    )
    duration = (time.time() - start) * 1000  # Convert to ms

    assert response.status_code == 200
    # Relaxed for SQLite in-memory testing (target <300ms in production)
    assert duration < 1000, f"Calculate took {duration}ms (target: <300ms)"


@pytest.mark.asyncio
async def test_save_build_performance(
    async_client: AsyncClient,
    sample_cpu: Cpu,
):
    """Test save endpoint meets <500ms performance target."""
    import time

    start = time.time()
    response = await async_client.post(
        "/v1/builder/builds",
        json={
            "name": "Performance Test Build",
            "components": {"cpu_id": sample_cpu.id}
        }
    )
    duration = (time.time() - start) * 1000  # Convert to ms

    assert response.status_code == 201
    # Relaxed for SQLite in-memory testing (target <500ms in production)
    assert duration < 1000, f"Save took {duration}ms (target: <500ms)"


# --- End-to-End Test ---


@pytest.mark.asyncio
async def test_end_to_end_flow(
    async_client: AsyncClient,
    sample_cpu: Cpu,
    sample_gpu: Gpu,
):
    """Test complete flow: calculate → save → get → share → delete."""

    # 1. Calculate build
    calc_response = await async_client.post(
        "/v1/builder/calculate",
        json={
            "cpu_id": sample_cpu.id,
            "gpu_id": sample_gpu.id,
        }
    )
    assert calc_response.status_code == 200
    calc_data = calc_response.json()
    assert "valuation" in calc_data
    assert "metrics" in calc_data

    # 2. Save build
    save_response = await async_client.post(
        "/v1/builder/builds",
        json={
            "name": "E2E Test Build",
            "visibility": "public",
            "components": {
                "cpu_id": sample_cpu.id,
                "gpu_id": sample_gpu.id,
            }
        }
    )
    assert save_response.status_code == 201
    build_data = save_response.json()
    build_id = build_data["id"]
    share_token = build_data["share_token"]

    # 3. Get build by ID
    get_response = await async_client.get(f"/v1/builder/builds/{build_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == build_id
    assert get_data["name"] == "E2E Test Build"

    # 4. Get build via share link
    share_response = await async_client.get(
        f"/v1/builder/builds/shared/{share_token}"
    )
    assert share_response.status_code == 200
    share_data = share_response.json()
    assert share_data["id"] == build_id

    # 5. Update build
    update_response = await async_client.patch(
        f"/v1/builder/builds/{build_id}",
        json={
            "name": "Updated E2E Build",
            "components": {"cpu_id": sample_cpu.id}
        }
    )
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["name"] == "Updated E2E Build"

    # 6. Delete build
    delete_response = await async_client.delete(f"/v1/builder/builds/{build_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True

    # 7. Verify deleted (should return 404)
    verify_response = await async_client.get(f"/v1/builder/builds/{build_id}")
    assert verify_response.status_code == 404
