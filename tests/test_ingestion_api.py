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
            "/api/v1/ingest/single",
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
        "/api/v1/ingest/single",
        json={"url": "not-a-valid-url", "priority": "normal"},
    )

    # Pydantic validation should return 422
    assert response.status_code == 422


def test_create_single_url_import_missing_url(client):
    """Test single URL import without URL field."""
    response = client.post(
        "/api/v1/ingest/single",
        json={"priority": "normal"},
    )

    # Missing required field should return 422
    assert response.status_code == 422


def test_create_single_url_import_invalid_priority(client):
    """Test single URL import with invalid priority."""
    test_url = "https://www.ebay.com/itm/123456789012"

    response = client.post(
        "/api/v1/ingest/single",
        json={"url": test_url, "priority": "invalid_priority"},
    )

    # Invalid priority pattern should return 422
    assert response.status_code == 422


def test_create_single_url_import_default_priority(client, db_session):
    """Test single URL import with default priority."""
    test_url = "https://www.ebay.com/itm/123456789012"

    with patch("dealbrain_api.api.ingestion.ingest_url_task") as mock_task:
        response = client.post(
            "/api/v1/ingest/single",
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
            "/api/v1/ingest/single",
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
    response = client.get(f"/api/v1/ingest/{job_id}")

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
    response = client.get(f"/api/v1/ingest/{job_id}")

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
    response = client.get(f"/api/v1/ingest/{job_id}")

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
    response = client.get(f"/api/v1/ingest/{job_id}")

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

    response = client.get(f"/api/v1/ingest/{fake_job_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_ingestion_status_invalid_uuid(client):
    """Test getting status with invalid UUID format."""
    response = client.get("/api/v1/ingest/not-a-valid-uuid")

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
    response = client.get(f"/api/v1/ingest/{job_id}")

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
            "/api/v1/ingest/single",
            json={"url": test_url, "priority": "normal"},
        )

    assert create_response.status_code == 202
    job_id = create_response.json()["job_id"]

    # Step 2: Retrieve job status
    status_response = client.get(f"/api/v1/ingest/{job_id}")

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
    final_response = client.get(f"/api/v1/ingest/{job_id}")

    assert final_response.status_code == 200
    final_data = final_response.json()
    assert final_data["status"] == "complete"
    assert final_data["listing_id"] == 123
    assert final_data["provenance"] == "ebay_api"
    assert final_data["quality"] == "full"


# ============================================================================
# POST /api/v1/ingest/bulk Tests
# ============================================================================


def test_create_bulk_import_csv_success(client, db_session):
    """Test successful bulk import with CSV file."""
    csv_content = b"url\nhttps://www.ebay.com/itm/111\nhttps://www.ebay.com/itm/222\nhttps://www.ebay.com/itm/333"

    with patch("dealbrain_api.api.ingestion.ingest_url_task") as mock_task:
        response = client.post(
            "/api/v1/ingest/bulk",
            files={"file": ("urls.csv", csv_content, "text/csv")},
        )

    # Assert 202 Accepted
    assert response.status_code == 202

    # Assert response structure
    data = response.json()
    assert "bulk_job_id" in data
    assert data["total_urls"] == 3

    # Validate bulk_job_id is valid UUID
    bulk_job_id = UUID(data["bulk_job_id"])
    assert isinstance(bulk_job_id, UUID)

    # Assert 3 Celery tasks were queued
    assert mock_task.delay.call_count == 3


def test_create_bulk_import_json_success(client, db_session):
    """Test successful bulk import with JSON file."""
    json_content = (
        b'[{"url": "https://www.amazon.com/dp/A111"},{"url": "https://www.amazon.com/dp/A222"}]'
    )

    with patch("dealbrain_api.api.ingestion.ingest_url_task") as mock_task:
        response = client.post(
            "/api/v1/ingest/bulk",
            files={"file": ("urls.json", json_content, "application/json")},
        )

    # Assert 202 Accepted
    assert response.status_code == 202

    # Assert response structure
    data = response.json()
    assert "bulk_job_id" in data
    assert data["total_urls"] == 2

    # Assert 2 Celery tasks were queued
    assert mock_task.delay.call_count == 2


def test_create_bulk_import_empty_file(client):
    """Test bulk import with empty file returns 400."""
    empty_content = b""

    response = client.post(
        "/api/v1/ingest/bulk",
        files={"file": ("empty.csv", empty_content, "text/csv")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_create_bulk_import_too_many_urls(client):
    """Test bulk import with more than 1000 URLs returns 413."""
    # Generate CSV with 1001 URLs
    urls = ["url\n"] + [f"https://example.com/item/{i}\n" for i in range(1001)]
    csv_content = "".join(urls).encode("utf-8")

    response = client.post(
        "/api/v1/ingest/bulk",
        files={"file": ("too_many.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 413
    assert "1000" in response.json()["detail"]


def test_create_bulk_import_invalid_csv(client):
    """Test bulk import with invalid CSV format returns 400."""
    invalid_csv = b"not,a,valid,csv\nwithout,proper,headers"

    response = client.post(
        "/api/v1/ingest/bulk",
        files={"file": ("invalid.csv", invalid_csv, "text/csv")},
    )

    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_create_bulk_import_invalid_json(client):
    """Test bulk import with invalid JSON format returns 400."""
    invalid_json = b'{"not": "an array"}'

    response = client.post(
        "/api/v1/ingest/bulk",
        files={"file": ("invalid.json", invalid_json, "application/json")},
    )

    assert response.status_code == 400
    assert "json" in response.json()["detail"].lower()


def test_create_bulk_import_invalid_urls(client):
    """Test bulk import with invalid URLs returns 422."""
    csv_content = b"url\nnot-a-valid-url\nhttp://valid.com\ninvalid-url-2"

    response = client.post(
        "/api/v1/ingest/bulk",
        files={"file": ("bad_urls.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()


def test_create_bulk_import_deduplicates_urls(client, db_session):
    """Test bulk import deduplicates URLs."""
    # CSV with duplicate URLs
    csv_content = b"url\nhttps://www.ebay.com/itm/111\nhttps://www.ebay.com/itm/222\nhttps://www.ebay.com/itm/111\nhttps://www.ebay.com/itm/222"

    with patch("dealbrain_api.api.ingestion.ingest_url_task") as mock_task:
        response = client.post(
            "/api/v1/ingest/bulk",
            files={"file": ("duplicates.csv", csv_content, "text/csv")},
        )

    # Assert success with deduplicated count
    assert response.status_code == 202
    data = response.json()
    assert data["total_urls"] == 2  # Only 2 unique URLs

    # Assert only 2 tasks queued
    assert mock_task.delay.call_count == 2


@pytest.mark.asyncio
async def test_create_bulk_import_creates_parent_child_sessions(client, db_session):
    """Test bulk import creates parent and child ImportSession records."""
    csv_content = b"url\nhttps://www.ebay.com/itm/111\nhttps://www.ebay.com/itm/222"

    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response = client.post(
            "/api/v1/ingest/bulk",
            files={"file": ("urls.csv", csv_content, "text/csv")},
        )

    assert response.status_code == 202
    bulk_job_id = UUID(response.json()["bulk_job_id"])

    # Verify parent ImportSession exists
    stmt = select(ImportSession).where(ImportSession.id == bulk_job_id)
    result = await db_session.execute(stmt)
    parent_session = result.scalar_one_or_none()

    assert parent_session is not None
    assert parent_session.id == bulk_job_id
    assert parent_session.source_type == SourceType.URL_BULK.value
    assert parent_session.url is None
    assert parent_session.status == "queued"
    assert parent_session.conflicts_json.get("total_urls") == 2
    assert parent_session.conflicts_json.get("file_format") == "csv"

    # Verify child ImportSession records exist
    stmt = select(ImportSession).where(ImportSession.source_type == SourceType.URL_SINGLE.value)
    result = await db_session.execute(stmt)
    child_sessions = result.scalars().all()

    assert len(child_sessions) == 2
    for child in child_sessions:
        assert child.url in ["https://www.ebay.com/itm/111", "https://www.ebay.com/itm/222"]
        assert child.source_type == SourceType.URL_SINGLE.value
        assert child.status == "queued"
        assert child.conflicts_json.get("parent_job_id") == str(bulk_job_id)


@pytest.mark.asyncio
async def test_create_bulk_import_queues_celery_tasks(client, db_session):
    """Test bulk import queues Celery tasks for each URL."""
    csv_content = b"url\nhttps://www.ebay.com/itm/111\nhttps://www.ebay.com/itm/222\nhttps://www.ebay.com/itm/333"

    with patch("dealbrain_api.api.ingestion.ingest_url_task") as mock_task:
        response = client.post(
            "/api/v1/ingest/bulk",
            files={"file": ("urls.csv", csv_content, "text/csv")},
        )

    assert response.status_code == 202

    # Verify 3 tasks were queued
    assert mock_task.delay.call_count == 3

    # Verify each call has job_id and url
    for call in mock_task.delay.call_args_list:
        assert "job_id" in call.kwargs
        assert "url" in call.kwargs
        # Verify job_id is valid UUID string
        UUID(call.kwargs["job_id"])
        # Verify URL is valid
        assert call.kwargs["url"].startswith("https://www.ebay.com/itm/")


def test_create_bulk_import_no_valid_urls(client):
    """Test bulk import with only empty rows returns 400."""
    csv_content = b"url\n\n\n"

    response = client.post(
        "/api/v1/ingest/bulk",
        files={"file": ("empty_rows.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 400
    assert "no valid urls" in response.json()["detail"].lower()


# ============================================================================
# GET /api/v1/ingest/bulk/{bulk_job_id} Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_bulk_status_all_queued(client, db_session):
    """Test bulk status when all children are queued."""
    # Create parent bulk job
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
        conflicts_json={"total_urls": 3, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create 3 child jobs (all queued)
    urls = [
        "https://www.ebay.com/itm/111",
        "https://www.ebay.com/itm/222",
        "https://www.ebay.com/itm/333",
    ]
    for url in urls:
        child_id = uuid4()
        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=url,
            source_type=SourceType.URL_SINGLE.value,
            url=url,
            status="queued",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={"parent_job_id": str(bulk_job_id)},
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Get bulk status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["bulk_job_id"] == str(bulk_job_id)
    assert data["status"] == "queued"
    assert data["total_urls"] == 3
    assert data["completed"] == 0
    assert data["success"] == 0
    assert data["partial"] == 0
    assert data["failed"] == 0
    assert data["running"] == 0
    assert data["queued"] == 3
    assert len(data["per_row_status"]) == 3
    assert data["offset"] == 0
    assert data["limit"] == 100
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_get_bulk_status_running(client, db_session):
    """Test bulk status when some jobs are running/queued."""
    # Create parent bulk job
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
        conflicts_json={"total_urls": 5, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create 5 child jobs with mixed statuses
    child_statuses = ["complete", "complete", "running", "running", "queued"]
    for idx, child_status in enumerate(child_statuses):
        url = f"https://www.ebay.com/itm/{idx+1}00"
        child_id = uuid4()
        conflicts_json = {"parent_job_id": str(bulk_job_id)}
        if child_status == "complete":
            conflicts_json["listing_id"] = idx + 100
            conflicts_json["provenance"] = "ebay_api"
            conflicts_json["quality"] = "full"

        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=url,
            source_type=SourceType.URL_SINGLE.value,
            url=url,
            status=child_status,
            sheet_meta_json={},
            mappings_json={},
            conflicts_json=conflicts_json,
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Get bulk status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["bulk_job_id"] == str(bulk_job_id)
    assert data["status"] == "running"  # Some running/queued
    assert data["total_urls"] == 5
    assert data["completed"] == 2  # complete only
    assert data["success"] == 2
    assert data["partial"] == 0
    assert data["failed"] == 0
    assert data["running"] == 2
    assert data["queued"] == 1
    assert len(data["per_row_status"]) == 5


@pytest.mark.asyncio
async def test_get_bulk_status_complete(client, db_session):
    """Test bulk status when all jobs are complete (100% done)."""
    # Create parent bulk job
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
        conflicts_json={"total_urls": 3, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create 3 child jobs (all complete)
    for idx in range(3):
        url = f"https://www.ebay.com/itm/{idx+1}00"
        child_id = uuid4()
        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=url,
            source_type=SourceType.URL_SINGLE.value,
            url=url,
            status="complete",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={
                "parent_job_id": str(bulk_job_id),
                "listing_id": idx + 100,
                "provenance": "ebay_api",
                "quality": "full",
            },
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Get bulk status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["bulk_job_id"] == str(bulk_job_id)
    assert data["status"] == "complete"  # All done
    assert data["total_urls"] == 3
    assert data["completed"] == 3
    assert data["success"] == 3
    assert data["partial"] == 0
    assert data["failed"] == 0
    assert data["running"] == 0
    assert data["queued"] == 0
    assert len(data["per_row_status"]) == 3
    # Verify listing_id is included in per_row_status
    assert all(row["listing_id"] is not None for row in data["per_row_status"])


@pytest.mark.asyncio
async def test_get_bulk_status_partial(client, db_session):
    """Test bulk status with mixed success and failure."""
    # Create parent bulk job
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
        conflicts_json={"total_urls": 5, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create child jobs: 3 complete, 1 partial, 1 failed
    child_configs = [
        ("complete", 100, None),
        ("complete", 101, None),
        ("complete", 102, None),
        ("partial", 103, None),
        ("failed", None, "Adapter timeout"),
    ]
    for idx, (child_status, listing_id, error) in enumerate(child_configs):
        url = f"https://www.ebay.com/itm/{idx+1}00"
        child_id = uuid4()
        conflicts_json = {"parent_job_id": str(bulk_job_id)}
        if listing_id:
            conflicts_json["listing_id"] = listing_id
            conflicts_json["provenance"] = "scraper"
            conflicts_json["quality"] = "full" if child_status == "complete" else "partial"
        if error:
            conflicts_json["error"] = error

        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=url,
            source_type=SourceType.URL_SINGLE.value,
            url=url,
            status=child_status,
            sheet_meta_json={},
            mappings_json={},
            conflicts_json=conflicts_json,
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Get bulk status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["bulk_job_id"] == str(bulk_job_id)
    assert data["status"] == "partial"  # Mixed success and failure
    assert data["total_urls"] == 5
    assert data["completed"] == 5  # All done
    assert data["success"] == 3
    assert data["partial"] == 1
    assert data["failed"] == 1
    assert data["running"] == 0
    assert data["queued"] == 0
    assert len(data["per_row_status"]) == 5
    # Verify error is included for failed job
    failed_row = [row for row in data["per_row_status"] if row["status"] == "failed"][0]
    assert failed_row["error"] == "Adapter timeout"


@pytest.mark.asyncio
async def test_get_bulk_status_failed(client, db_session):
    """Test bulk status when all children failed."""
    # Create parent bulk job
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
        conflicts_json={"total_urls": 3, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create 3 child jobs (all failed)
    for idx in range(3):
        url = f"https://www.ebay.com/itm/{idx+1}00"
        child_id = uuid4()
        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=url,
            source_type=SourceType.URL_SINGLE.value,
            url=url,
            status="failed",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={
                "parent_job_id": str(bulk_job_id),
                "error": "Connection timeout",
            },
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Get bulk status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["bulk_job_id"] == str(bulk_job_id)
    assert data["status"] == "failed"  # All failed
    assert data["total_urls"] == 3
    assert data["completed"] == 3
    assert data["success"] == 0
    assert data["partial"] == 0
    assert data["failed"] == 3
    assert data["running"] == 0
    assert data["queued"] == 0


def test_get_bulk_status_not_found(client):
    """Test bulk status retrieval for non-existent bulk job."""
    fake_bulk_job_id = uuid4()

    response = client.get(f"/api/v1/ingest/bulk/{fake_bulk_job_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_bulk_status_invalid_uuid(client):
    """Test bulk status retrieval with invalid UUID format."""
    response = client.get("/api/v1/ingest/bulk/not-a-valid-uuid")

    assert response.status_code == 422
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_bulk_status_pagination(client, db_session):
    """Test bulk status with pagination (offset/limit)."""
    # Create parent bulk job
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
        conflicts_json={"total_urls": 10, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create 10 child jobs
    for idx in range(10):
        url = f"https://www.ebay.com/itm/{idx+1}00"
        child_id = uuid4()
        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=url,
            source_type=SourceType.URL_SINGLE.value,
            url=url,
            status="complete",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={
                "parent_job_id": str(bulk_job_id),
                "listing_id": idx + 100,
            },
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Test pagination: Get first 5 results (offset=0, limit=5)
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}?offset=0&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert data["total_urls"] == 10  # Total is always 10
    assert len(data["per_row_status"]) == 5  # Only 5 returned
    assert data["offset"] == 0
    assert data["limit"] == 5
    assert data["has_more"] is True  # More results available

    # Test pagination: Get next 5 results (offset=5, limit=5)
    response2 = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}?offset=5&limit=5")

    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total_urls"] == 10
    assert len(data2["per_row_status"]) == 5
    assert data2["offset"] == 5
    assert data2["limit"] == 5
    assert data2["has_more"] is False  # No more results


@pytest.mark.asyncio
async def test_get_bulk_status_has_more_flag(client, db_session):
    """Test has_more flag calculation."""
    # Create parent bulk job
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
        conflicts_json={"total_urls": 7, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create 7 child jobs
    for idx in range(7):
        url = f"https://www.ebay.com/itm/{idx+1}00"
        child_id = uuid4()
        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=url,
            source_type=SourceType.URL_SINGLE.value,
            url=url,
            status="queued",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={"parent_job_id": str(bulk_job_id)},
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Test 1: offset=0, limit=5 -> has_more=True (7 > 0+5)
    response1 = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}?offset=0&limit=5")
    assert response1.json()["has_more"] is True

    # Test 2: offset=0, limit=10 -> has_more=False (7 <= 0+10)
    response2 = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}?offset=0&limit=10")
    assert response2.json()["has_more"] is False

    # Test 3: offset=5, limit=3 -> has_more=False (7 <= 5+3)
    response3 = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}?offset=5&limit=3")
    assert response3.json()["has_more"] is False
