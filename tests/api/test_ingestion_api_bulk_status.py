"""Tests for bulk URL ingestion status polling endpoint.

This module tests the FastAPI endpoint for bulk import status:
- GET /api/v1/ingest/bulk/{bulk_job_id}/status - Poll bulk job status with pagination
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from dealbrain_api.db import Base
from dealbrain_api.models.core import ImportSession
from dealbrain_core.enums import SourceType
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Try to import aiosqlite
AIOSQLITE_AVAILABLE = False
try:
    import aiosqlite  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:
    pass


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide an isolated in-memory database session for tests."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping bulk status API tests")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
def app(db_session):
    """Create FastAPI test app with ingestion router."""
    from dealbrain_api.api.ingestion import router
    from dealbrain_api.db import session_dependency

    test_app = FastAPI()
    test_app.include_router(router)

    # Override session dependency
    async def override_session_dependency():
        yield db_session

    test_app.dependency_overrides[session_dependency] = override_session_dependency

    return test_app


@pytest.fixture
def client(app):
    """Create test client for FastAPI app."""
    return TestClient(app)


# ============================================================================
# Helper Functions
# ============================================================================


async def create_bulk_job(
    session: AsyncSession,
    bulk_job_id: UUID | None = None,
) -> ImportSession:
    """Create a parent bulk import session."""
    if bulk_job_id is None:
        bulk_job_id = uuid4()

    parent_session = ImportSession(
        id=bulk_job_id,
        filename=f"bulk_import_{bulk_job_id.hex[:8]}",
        upload_path=f"bulk_upload_{bulk_job_id.hex[:8]}",
        source_type=SourceType.URL_BULK.value,
        url=None,
        status="queued",
        sheet_meta_json={},
        mappings_json={},
        conflicts_json={"total_urls": 0},
        preview_json={},
        declared_entities_json={},
        adapter_config={},
    )

    session.add(parent_session)
    await session.commit()
    await session.refresh(parent_session)

    return parent_session


async def create_child_import_session(
    session: AsyncSession,
    bulk_job_id: UUID,
    url: str,
    status: str = "queued",
    quality: str | None = None,
    listing_id: int | None = None,
    error: str | None = None,
) -> ImportSession:
    """Create a child import session for a bulk job."""
    child_job_id = uuid4()

    conflicts = {"parent_job_id": str(bulk_job_id)}
    if listing_id is not None:
        conflicts["listing_id"] = listing_id
    if error is not None:
        conflicts["error"] = error

    child_session = ImportSession(
        id=child_job_id,
        filename=f"url_import_{child_job_id.hex[:8]}",
        upload_path=url,
        source_type=SourceType.URL_SINGLE.value,
        url=url,
        status=status,
        quality=quality,
        listing_id=listing_id,
        sheet_meta_json={},
        mappings_json={},
        conflicts_json=conflicts,
        preview_json={},
        declared_entities_json={},
        adapter_config={},
    )

    session.add(child_session)
    await session.commit()
    await session.refresh(child_session)

    return child_session


# ============================================================================
# GET /api/v1/ingest/bulk/{bulk_job_id}/status Tests
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_status_empty_job(client, db_session):
    """Test bulk status endpoint with no child sessions."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Request status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert response structure
    data = response.json()
    assert data["bulk_job_id"] == str(bulk_job.id)
    assert data["status"] == "queued"
    assert data["total_urls"] == 0
    assert data["completed"] == 0
    assert data["success"] == 0
    assert data["partial"] == 0
    assert data["failed"] == 0
    assert data["running"] == 0
    assert data["queued"] == 0
    assert data["per_row_status"] == []
    assert data["offset"] == 0
    assert data["limit"] == 20
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_bulk_status_running(client, db_session):
    """Test bulk status with mixed statuses."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create child sessions with mixed statuses
    await create_child_import_session(
        db_session, bulk_job.id, "https://ebay.com/itm/1", status="queued"
    )
    await create_child_import_session(
        db_session, bulk_job.id, "https://ebay.com/itm/2", status="running"
    )
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/3",
        status="complete",
        quality="full",
        listing_id=123,
    )
    await create_child_import_session(
        db_session, bulk_job.id, "https://ebay.com/itm/4", status="failed", error="Timeout"
    )

    # Request status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert aggregates
    data = response.json()
    assert data["status"] == "running"  # Mixed statuses
    assert data["total_urls"] == 4
    assert data["completed"] == 2  # complete + failed
    assert data["success"] == 1  # complete with quality=full
    assert data["partial"] == 0
    assert data["failed"] == 1
    assert data["running"] == 1
    assert data["queued"] == 1


@pytest.mark.asyncio
async def test_bulk_status_all_complete(client, db_session):
    """Test bulk status when all URLs are complete."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create child sessions - all complete
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/1",
        status="complete",
        quality="full",
        listing_id=101,
    )
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/2",
        status="complete",
        quality="full",
        listing_id=102,
    )

    # Request status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert aggregates
    data = response.json()
    assert data["status"] == "complete"  # All complete
    assert data["total_urls"] == 2
    assert data["completed"] == 2
    assert data["success"] == 2
    assert data["partial"] == 0
    assert data["failed"] == 0
    assert data["running"] == 0
    assert data["queued"] == 0


@pytest.mark.asyncio
async def test_bulk_status_with_partials(client, db_session):
    """Test bulk status with partial quality imports."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create child sessions with partial quality
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/1",
        status="complete",
        quality="full",
        listing_id=101,
    )
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/2",
        status="complete",
        quality="partial",  # Partial quality
        listing_id=102,
    )
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/3",
        status="complete",
        quality="partial",  # Partial quality
        listing_id=103,
    )

    # Request status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert aggregates
    data = response.json()
    assert data["status"] == "complete"  # All finished
    assert data["total_urls"] == 3
    assert data["completed"] == 3
    assert data["success"] == 1  # Only full quality
    assert data["partial"] == 2  # Partial quality
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_bulk_status_pagination(client, db_session):
    """Test bulk status pagination."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create 25 child sessions
    for i in range(25):
        await create_child_import_session(
            db_session,
            bulk_job.id,
            f"https://ebay.com/itm/{i}",
            status="complete",
            quality="full",
            listing_id=100 + i,
        )

    # Request first page (default limit=20)
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert pagination
    data = response.json()
    assert data["total_urls"] == 25
    assert data["offset"] == 0
    assert data["limit"] == 20
    assert len(data["per_row_status"]) == 20
    assert data["has_more"] is True  # More results available


@pytest.mark.asyncio
async def test_bulk_status_pagination_has_more(client, db_session):
    """Test bulk status pagination with offset."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create 25 child sessions
    for i in range(25):
        await create_child_import_session(
            db_session,
            bulk_job.id,
            f"https://ebay.com/itm/{i}",
            status="complete",
            quality="full",
            listing_id=100 + i,
        )

    # Request second page (offset=20, limit=10)
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status?offset=20&limit=10")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert pagination
    data = response.json()
    assert data["total_urls"] == 25
    assert data["offset"] == 20
    assert data["limit"] == 10
    assert len(data["per_row_status"]) == 5  # Only 5 remaining
    assert data["has_more"] is False  # No more results


@pytest.mark.asyncio
async def test_bulk_status_aggregates_correct(client, db_session):
    """Test bulk status aggregates are calculated correctly."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create comprehensive mix of statuses and qualities
    # 5 queued
    for i in range(5):
        await create_child_import_session(
            db_session, bulk_job.id, f"https://ebay.com/itm/q{i}", status="queued"
        )

    # 3 running
    for i in range(3):
        await create_child_import_session(
            db_session, bulk_job.id, f"https://ebay.com/itm/r{i}", status="running"
        )

    # 10 complete with full quality
    for i in range(10):
        await create_child_import_session(
            db_session,
            bulk_job.id,
            f"https://ebay.com/itm/cf{i}",
            status="complete",
            quality="full",
            listing_id=200 + i,
        )

    # 4 complete with partial quality
    for i in range(4):
        await create_child_import_session(
            db_session,
            bulk_job.id,
            f"https://ebay.com/itm/cp{i}",
            status="complete",
            quality="partial",
            listing_id=300 + i,
        )

    # 2 failed
    for i in range(2):
        await create_child_import_session(
            db_session,
            bulk_job.id,
            f"https://ebay.com/itm/f{i}",
            status="failed",
            error=f"Error {i}",
        )

    # Request status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert detailed aggregates
    data = response.json()
    assert data["status"] == "running"  # Has queued and running
    assert data["total_urls"] == 24  # 5+3+10+4+2
    assert data["queued"] == 5
    assert data["running"] == 3
    assert data["success"] == 10  # Complete with quality=full
    assert data["partial"] == 4  # Complete with quality=partial
    assert data["failed"] == 2
    assert data["completed"] == 16  # success + partial + failed (10+4+2)

    # Verify per_row_status contains quality field
    assert len(data["per_row_status"]) == 20  # Default limit
    for row in data["per_row_status"]:
        assert "url" in row
        assert "status" in row
        assert "quality" in row  # Quality field present
        if row["status"] == "complete":
            assert row["quality"] in ["full", "partial"]
            assert row["listing_id"] is not None


def test_bulk_status_not_found(client, db_session):
    """Test bulk status with non-existent job ID."""
    fake_job_id = uuid4()

    response = client.get(f"/api/v1/ingest/bulk/{fake_job_id}/status")

    # Assert 404 Not Found
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_bulk_status_invalid_uuid(client, db_session):
    """Test bulk status with invalid UUID format."""
    response = client.get("/api/v1/ingest/bulk/invalid-uuid-format/status")

    # Assert 422 Unprocessable Entity
    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bulk_status_overall_partial_status(client, db_session):
    """Test overall status is 'partial' when some complete and some failed."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create mixed complete and failed
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/1",
        status="complete",
        quality="full",
        listing_id=101,
    )
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/2",
        status="failed",
        error="Extraction failed",
    )

    # Request status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert overall status is partial
    data = response.json()
    assert data["status"] == "partial"  # Mixed success and failure
    assert data["total_urls"] == 2
    assert data["success"] == 1
    assert data["failed"] == 1


@pytest.mark.asyncio
async def test_bulk_status_overall_failed_status(client, db_session):
    """Test overall status is 'failed' when all URLs failed."""
    # Create parent bulk job
    bulk_job = await create_bulk_job(db_session)

    # Create all failed
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/1",
        status="failed",
        error="Error 1",
    )
    await create_child_import_session(
        db_session,
        bulk_job.id,
        "https://ebay.com/itm/2",
        status="failed",
        error="Error 2",
    )

    # Request status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job.id}/status")

    # Assert 200 OK
    assert response.status_code == 200

    # Assert overall status is failed
    data = response.json()
    assert data["status"] == "failed"  # All failed
    assert data["total_urls"] == 2
    assert data["failed"] == 2
    assert data["success"] == 0
