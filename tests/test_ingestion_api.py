"""Tests for URL ingestion API endpoints.

This module tests the FastAPI endpoints for single URL import:
- POST /api/v1/ingest/single - Create import job
- GET /api/v1/ingest/{job_id} - Get job status
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from dealbrain_api.db import Base
from dealbrain_api.models.core import ImportSession
from dealbrain_core.enums import SourceType
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
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
        pytest.skip("aiosqlite is not installed; skipping ingestion API tests")

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
# POST /api/v1/ingest/single Tests
# ============================================================================


def test_create_single_url_import_success(client, db_session):
    """Test successful single URL import creation."""
    test_url = "https://www.ebay.com/itm/123456789012"

    with patch("dealbrain_api.api.ingestion.ingest_url_task") as mock_task:
        response = client.post(
            "/v1/ingest/single",
            json={"url": test_url, "priority": "normal"},
        )

    # Assert 202 Accepted
    assert response.status_code == 202

    # Assert response structure
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert data["listing_id"] is None
    assert data["provenance"] is None
    assert data["quality"] is None
    assert data["errors"] == []

    # Validate job_id is valid UUID
    job_id = UUID(data["job_id"])
    assert isinstance(job_id, UUID)

    # Assert Celery task was queued
    mock_task.delay.assert_called_once()
    call_args = mock_task.delay.call_args
    assert call_args.kwargs["job_id"] == data["job_id"]
    assert call_args.kwargs["url"] == test_url


def test_create_single_url_import_invalid_url(client):
    """Test single URL import with invalid URL format."""
    response = client.post(
        "/v1/ingest/single",
        json={"url": "not-a-valid-url", "priority": "normal"},
    )

    # Pydantic validation should return 422
    assert response.status_code == 422


def test_create_single_url_import_missing_url(client):
    """Test single URL import without URL field."""
    response = client.post(
        "/v1/ingest/single",
        json={"priority": "normal"},
    )

    # Missing required field should return 422
    assert response.status_code == 422


def test_create_single_url_import_invalid_priority(client):
    """Test single URL import with invalid priority."""
    test_url = "https://www.ebay.com/itm/123456789012"

    response = client.post(
        "/v1/ingest/single",
        json={"url": test_url, "priority": "invalid_priority"},
    )

    # Invalid priority pattern should return 422
    assert response.status_code == 422


def test_create_single_url_import_default_priority(client, db_session):
    """Test single URL import with default priority."""
    test_url = "https://www.ebay.com/itm/123456789012"

    with patch("dealbrain_api.api.ingestion.ingest_url_task") as mock_task:
        response = client.post(
            "/v1/ingest/single",
            json={"url": test_url},  # No priority specified
        )

    # Should succeed with default priority
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"

    # Task should be queued
    mock_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_create_single_url_import_creates_import_session(client, db_session):
    """Test that ImportSession record is created in database."""
    test_url = "https://www.ebay.com/itm/123456789012"

    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response = client.post(
            "/v1/ingest/single",
            json={"url": test_url, "priority": "high"},
        )

    assert response.status_code == 202
    job_id = UUID(response.json()["job_id"])

    # Verify ImportSession exists in database
    stmt = select(ImportSession).where(ImportSession.id == job_id)
    result = await db_session.execute(stmt)
    import_session = result.scalar_one_or_none()

    assert import_session is not None
    assert import_session.id == job_id
    assert import_session.url == test_url
    assert import_session.source_type == SourceType.URL_SINGLE.value
    assert import_session.status == "queued"
    assert import_session.adapter_config.get("priority") == "high"


# ============================================================================
# GET /api/v1/ingest/{job_id} Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_ingestion_status_queued(client, db_session):
    """Test getting status of queued job."""
    # Create ImportSession in queued state
    job_id = uuid4()
    import_session = ImportSession(
        id=job_id,
        filename=f"url_import_{job_id.hex[:8]}",
        upload_path="https://example.com/item/123",
        source_type=SourceType.URL_SINGLE.value,
        url="https://example.com/item/123",
        status="queued",
        sheet_meta_json={},
        mappings_json={},
        conflicts_json={},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(import_session)
    await db_session.commit()

    # Get status
    response = client.get(f"/v1/ingest/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == "queued"
    assert data["listing_id"] is None
    assert data["provenance"] is None
    assert data["quality"] is None
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_get_ingestion_status_complete(client, db_session):
    """Test getting status of completed job with listing created."""
    # Create ImportSession in complete state with result data
    job_id = uuid4()
    import_session = ImportSession(
        id=job_id,
        filename=f"url_import_{job_id.hex[:8]}",
        upload_path="https://example.com/item/123",
        source_type=SourceType.URL_SINGLE.value,
        url="https://example.com/item/123",
        status="complete",
        sheet_meta_json={},
        mappings_json={},
        conflicts_json={
            "listing_id": 456,
            "provenance": "ebay_api",
            "quality": "full",
            "title": "Gaming PC Intel i7",
            "price": 599.99,
            "vendor_item_id": "123456789012",
            "marketplace": "ebay",
        },
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(import_session)
    await db_session.commit()

    # Get status
    response = client.get(f"/v1/ingest/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == "complete"
    assert data["listing_id"] == 456
    assert data["provenance"] == "ebay_api"
    assert data["quality"] == "full"
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_get_ingestion_status_partial(client, db_session):
    """Test getting status of partially successful job."""
    # Create ImportSession in partial state
    job_id = uuid4()
    import_session = ImportSession(
        id=job_id,
        filename=f"url_import_{job_id.hex[:8]}",
        upload_path="https://example.com/item/123",
        source_type=SourceType.URL_SINGLE.value,
        url="https://example.com/item/123",
        status="partial",
        sheet_meta_json={},
        mappings_json={},
        conflicts_json={
            "listing_id": 789,
            "provenance": "scraper",
            "quality": "partial",
            "title": "Used PC",
            "price": 299.99,
        },
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(import_session)
    await db_session.commit()

    # Get status
    response = client.get(f"/v1/ingest/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == "partial"
    assert data["listing_id"] == 789
    assert data["provenance"] == "scraper"
    assert data["quality"] == "partial"


@pytest.mark.asyncio
async def test_get_ingestion_status_failed(client, db_session):
    """Test getting status of failed job with error details."""
    # Create ImportSession in failed state with error
    job_id = uuid4()
    import_session = ImportSession(
        id=job_id,
        filename=f"url_import_{job_id.hex[:8]}",
        upload_path="https://example.com/item/123",
        source_type=SourceType.URL_SINGLE.value,
        url="https://example.com/item/123",
        status="failed",
        sheet_meta_json={},
        mappings_json={},
        conflicts_json={
            "error": "Failed to fetch URL: Connection timeout",
        },
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(import_session)
    await db_session.commit()

    # Get status
    response = client.get(f"/v1/ingest/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == "failed"
    assert data["listing_id"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0]["type"] == "ingestion_error"
    assert "Connection timeout" in data["errors"][0]["message"]


def test_get_ingestion_status_not_found(client):
    """Test getting status of non-existent job."""
    fake_job_id = uuid4()

    response = client.get(f"/v1/ingest/{fake_job_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_ingestion_status_invalid_uuid(client):
    """Test getting status with invalid UUID format."""
    response = client.get("/v1/ingest/not-a-valid-uuid")

    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_ingestion_status_running(client, db_session):
    """Test getting status of job currently running."""
    # Create ImportSession in running state
    job_id = uuid4()
    import_session = ImportSession(
        id=job_id,
        filename=f"url_import_{job_id.hex[:8]}",
        upload_path="https://example.com/item/123",
        source_type=SourceType.URL_SINGLE.value,
        url="https://example.com/item/123",
        status="running",
        sheet_meta_json={},
        mappings_json={},
        conflicts_json={},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(import_session)
    await db_session.commit()

    # Get status
    response = client.get(f"/v1/ingest/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["status"] == "running"
    assert data["listing_id"] is None


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_and_retrieve_workflow(client, db_session):
    """Test complete workflow: create job -> retrieve status."""
    test_url = "https://www.ebay.com/itm/999888777666"

    # Step 1: Create import job
    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        create_response = client.post(
            "/v1/ingest/single",
            json={"url": test_url, "priority": "normal"},
        )

    assert create_response.status_code == 202
    job_id = create_response.json()["job_id"]

    # Step 2: Retrieve job status
    status_response = client.get(f"/v1/ingest/{job_id}")

    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "queued"

    # Step 3: Simulate task completion by updating ImportSession
    job_uuid = UUID(job_id)
    stmt = select(ImportSession).where(ImportSession.id == job_uuid)
    result = await db_session.execute(stmt)
    import_session = result.scalar_one()

    import_session.status = "complete"
    import_session.conflicts_json = {
        "listing_id": 123,
        "provenance": "ebay_api",
        "quality": "full",
    }
    await db_session.commit()

    # Step 4: Retrieve updated status
    final_response = client.get(f"/v1/ingest/{job_id}")

    assert final_response.status_code == 200
    final_data = final_response.json()
    assert final_data["status"] == "complete"
    assert final_data["listing_id"] == 123
    assert final_data["provenance"] == "ebay_api"
    assert final_data["quality"] == "full"
