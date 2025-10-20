"""Integration tests for URL ingestion job lifecycle (Phase 4, Task ID-027).

This module tests complete end-to-end workflows for URL ingestion, including:
- Single URL flow: endpoint → Celery task → ImportSession update
- Bulk import: file upload → parse → queue jobs → poll completion
- Re-import same URL: verify same listing_id returned (no duplicate)
- Price change workflow: verify price updated in ImportSession
- Adapter disabled error handling: verify ADAPTER_DISABLED error handling

These tests use real database (via transactional fixtures) and mock IngestionService
for consistent, fast test execution focused on job lifecycle tracking.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from dealbrain_api.db import Base
from dealbrain_api.models.core import ImportSession
from dealbrain_api.services.ingestion import IngestionResult
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
        pytest.skip("aiosqlite is not installed; skipping ingestion integration tests")

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
# Test 1: Single URL Flow
# ============================================================================


@pytest.mark.asyncio
async def test_single_url_complete_flow(client, db_session, monkeypatch):
    """Test complete single URL ingestion workflow from API to ImportSession update.

    Workflow:
    1. POST /api/v1/ingest/single → creates ImportSession with status=queued
    2. Celery task executes → calls IngestionService.ingest_single_url (mocked)
    3. ImportSession updated → status=complete with result data
    4. Verify ImportSession reflects successful ingestion
    """
    test_url = "https://www.ebay.com/itm/123456789012"

    # Step 1: Create import job via API
    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response = client.post(
            "/api/v1/ingest/single",
            json={"url": test_url, "priority": "normal"},
        )

    assert response.status_code == 202
    job_id = UUID(response.json()["job_id"])

    # Verify ImportSession created
    stmt = select(ImportSession).where(ImportSession.id == job_id)
    result = await db_session.execute(stmt)
    import_session = result.scalar_one()

    assert import_session.status == "queued"
    assert import_session.url == test_url

    # Step 2: Simulate task execution
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr("dealbrain_api.tasks.ingestion.session_scope", _session_scope_override)

    # Mock IngestionService
    mock_result = IngestionResult(
        success=True,
        listing_id=1,
        status="created",
        provenance="ebay_api",
        quality="full",
        url=test_url,
        title="Gaming PC Intel i7",
        price=Decimal("599.99"),
        vendor_item_id="123456789012",
        marketplace="ebay",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service = AsyncMock()
        mock_service.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service

        from dealbrain_api.tasks.ingestion import _ingest_url_async

        task_result = await _ingest_url_async(job_id=str(job_id), url=test_url)

    # Step 3: Verify task result
    assert task_result["success"] is True
    assert task_result["status"] == "complete"
    assert task_result["listing_id"] == 1

    # Step 4: Verify ImportSession updated
    await db_session.refresh(import_session)
    assert import_session.status == "complete"
    assert import_session.conflicts_json["listing_id"] == 1
    assert import_session.conflicts_json["quality"] == "full"


# ============================================================================
# Test 2: Bulk Import Flow
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_import_complete_flow(client, db_session, monkeypatch):
    """Test complete bulk import workflow.

    Workflow:
    1. POST /api/v1/ingest/bulk with CSV → creates parent + child ImportSessions
    2. Each child job executes (mocked)
    3. GET /api/v1/ingest/bulk/{id} → poll status until all complete
    """
    csv_content = b"url\nhttps://www.ebay.com/itm/111\nhttps://www.ebay.com/itm/222"

    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response = client.post(
            "/api/v1/ingest/bulk",
            files={"file": ("urls.csv", csv_content, "text/csv")},
        )

    assert response.status_code == 202
    bulk_job_id = UUID(response.json()["bulk_job_id"])

    # Verify child sessions created
    stmt = select(ImportSession).where(ImportSession.source_type == SourceType.URL_SINGLE.value)
    result = await db_session.execute(stmt)
    child_sessions = result.scalars().all()

    assert len(child_sessions) == 2

    # Simulate task completion by directly updating child sessions
    # (This tests the bulk status aggregation logic, not the actual task execution)
    urls = ["https://www.ebay.com/itm/111", "https://www.ebay.com/itm/222"]

    for idx, (child, url) in enumerate(zip(child_sessions, urls)):
        child.status = "complete"
        child.conflicts_json = {
            "parent_job_id": str(bulk_job_id),
            "listing_id": idx + 100,
            "provenance": "ebay_api",
            "quality": "full",
            "title": f"PC {idx+1}",
            "price": float((idx + 1) * 100),
            "vendor_item_id": f"vendor_{idx+1}",
            "marketplace": "ebay",
        }

    await db_session.commit()

    # Poll bulk status
    response = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}")
    assert response.status_code == 200
    bulk_status = response.json()

    assert bulk_status["status"] == "complete"
    assert bulk_status["total_urls"] == 2
    assert bulk_status["success"] == 2
    assert len(bulk_status["per_row_status"]) == 2


# ============================================================================
# Test 3: Re-import Same URL
# ============================================================================


@pytest.mark.asyncio
async def test_reimport_same_url_no_duplicate(client, db_session, monkeypatch):
    """Test re-importing same URL returns same listing_id (no duplicate).

    Workflow:
    1. Import URL → listing_id=999, price=$100
    2. Re-import same URL → listing_id=999 (same), price=$105
    """
    test_url = "https://www.ebay.com/itm/123"

    # Setup
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr("dealbrain_api.tasks.ingestion.session_scope", _session_scope_override)

    # First import
    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response1 = client.post("/api/v1/ingest/single", json={"url": test_url})
    job_id_1 = UUID(response1.json()["job_id"])

    mock_result_1 = IngestionResult(
        success=True,
        listing_id=999,
        status="created",
        provenance="ebay_api",
        quality="full",
        url=test_url,
        title="PC",
        price=Decimal("100.00"),
        vendor_item_id="123",
        marketplace="ebay",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service = AsyncMock()
        mock_service.ingest_single_url.return_value = mock_result_1
        MockService.return_value = mock_service

        from dealbrain_api.tasks.ingestion import _ingest_url_async

        result1 = await _ingest_url_async(job_id=str(job_id_1), url=test_url)

    assert result1["listing_id"] == 999

    # Second import (re-import)
    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response2 = client.post("/api/v1/ingest/single", json={"url": test_url})
    job_id_2 = UUID(response2.json()["job_id"])

    mock_result_2 = IngestionResult(
        success=True,
        listing_id=999,  # SAME listing_id
        status="updated",
        provenance="ebay_api",
        quality="full",
        url=test_url,
        title="PC",
        price=Decimal("105.00"),
        vendor_item_id="123",
        marketplace="ebay",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service = AsyncMock()
        mock_service.ingest_single_url.return_value = mock_result_2
        MockService.return_value = mock_service

        result2 = await _ingest_url_async(job_id=str(job_id_2), url=test_url)

    # Verify same listing_id (no duplicate)
    assert result2["listing_id"] == 999
    assert result2["status"] == "complete"


# ============================================================================
# Test 4: Price Change Event (workflow tracking)
# ============================================================================


@pytest.mark.asyncio
async def test_price_change_workflow_tracking(client, db_session, monkeypatch):
    """Test price change workflow tracking in ImportSession.

    Note: Actual event emission is tested in test_event_service.py.
    This test verifies the ImportSession tracks price changes correctly.
    """
    test_url = "https://www.ebay.com/itm/456"

    # Setup
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr("dealbrain_api.tasks.ingestion.session_scope", _session_scope_override)

    # First import (price $100)
    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response1 = client.post("/api/v1/ingest/single", json={"url": test_url})
    job_id_1 = UUID(response1.json()["job_id"])

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service = AsyncMock()
        mock_service.ingest_single_url.return_value = IngestionResult(
            success=True,
            listing_id=888,
            status="created",
            provenance="ebay_api",
            quality="full",
            url=test_url,
            title="PC",
            price=Decimal("100.00"),
            vendor_item_id="456",
            marketplace="ebay",
        )
        MockService.return_value = mock_service

        from dealbrain_api.tasks.ingestion import _ingest_url_async

        await _ingest_url_async(job_id=str(job_id_1), url=test_url)

    # Second import (price $105 - significant change)
    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response2 = client.post("/api/v1/ingest/single", json={"url": test_url})
    job_id_2 = UUID(response2.json()["job_id"])

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service = AsyncMock()
        mock_service.ingest_single_url.return_value = IngestionResult(
            success=True,
            listing_id=888,
            status="updated",
            provenance="ebay_api",
            quality="full",
            url=test_url,
            title="PC",
            price=Decimal("105.00"),  # Price changed
            vendor_item_id="456",
            marketplace="ebay",
        )
        MockService.return_value = mock_service

        await _ingest_url_async(job_id=str(job_id_2), url=test_url)

    # Verify ImportSession reflects price change
    stmt = select(ImportSession).where(ImportSession.id == job_id_2)
    result = await db_session.execute(stmt)
    session_2 = result.scalar_one()

    assert session_2.conflicts_json["price"] == 105.0  # Updated price


# ============================================================================
# Test 5: Adapter Disabled Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_adapter_disabled_error_handling(client, db_session, monkeypatch):
    """Test error handling when adapter fails or is disabled.

    Workflow:
    1. Import job created
    2. IngestionService returns failure result
    3. ImportSession status = failed with error message
    """
    test_url = "https://www.ebay.com/itm/disabled"

    # Setup
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr("dealbrain_api.tasks.ingestion.session_scope", _session_scope_override)

    # Create import job
    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response = client.post("/api/v1/ingest/single", json={"url": test_url})

    job_id = UUID(response.json()["job_id"])

    # Mock IngestionService to return failure
    mock_result = IngestionResult(
        success=False,
        listing_id=None,
        status="failed",
        provenance="unknown",
        quality="partial",
        url=test_url,
        error="ADAPTER_DISABLED: eBay adapter is disabled in settings",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service = AsyncMock()
        mock_service.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service

        from dealbrain_api.tasks.ingestion import _ingest_url_async

        result = await _ingest_url_async(job_id=str(job_id), url=test_url)

    # Verify failure result
    assert result["success"] is False
    assert result["status"] == "failed"
    assert "ADAPTER_DISABLED" in result["error"]

    # Verify ImportSession updated to failed
    stmt = select(ImportSession).where(ImportSession.id == job_id)
    result_db = await db_session.execute(stmt)
    import_session = result_db.scalar_one()

    assert import_session.status == "failed"
    assert "ADAPTER_DISABLED" in import_session.conflicts_json["error"]


# ============================================================================
# Test 6: Bulk Import Pagination
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_import_pagination_works(client, db_session):
    """Test that pagination works for bulk status endpoint."""
    # Create parent bulk job with 15 child jobs
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
        conflicts_json={"total_urls": 15, "file_format": "csv"},
        preview_json={},
        declared_entities_json={},
    )
    db_session.add(parent_session)

    # Create 15 child jobs
    for i in range(15):
        child_id = uuid4()
        child_session = ImportSession(
            id=child_id,
            filename=f"url_import_{child_id.hex[:8]}",
            upload_path=f"https://example.com/item/{i}",
            source_type=SourceType.URL_SINGLE.value,
            url=f"https://example.com/item/{i}",
            status="complete",
            sheet_meta_json={},
            mappings_json={},
            conflicts_json={"parent_job_id": str(bulk_job_id), "listing_id": i + 100},
            preview_json={},
            declared_entities_json={},
        )
        db_session.add(child_session)

    await db_session.commit()

    # Test pagination: First page (limit=10)
    response1 = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}?offset=0&limit=10")
    assert response1.status_code == 200
    data1 = response1.json()

    assert data1["total_urls"] == 15
    assert len(data1["per_row_status"]) == 10
    assert data1["has_more"] is True

    # Test pagination: Second page
    response2 = client.get(f"/api/v1/ingest/bulk/{bulk_job_id}?offset=10&limit=10")
    assert response2.status_code == 200
    data2 = response2.json()

    assert len(data2["per_row_status"]) == 5  # Only 5 remaining
    assert data2["has_more"] is False


# ============================================================================
# Test 7: Partial Quality Ingestion
# ============================================================================


@pytest.mark.asyncio
async def test_single_url_partial_quality(client, db_session, monkeypatch):
    """Test single URL import with partial quality data."""
    test_url = "https://example.com/partial"

    # Setup
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr("dealbrain_api.tasks.ingestion.session_scope", _session_scope_override)

    with patch("dealbrain_api.api.ingestion.ingest_url_task"):
        response = client.post("/api/v1/ingest/single", json={"url": test_url})

    job_id = UUID(response.json()["job_id"])

    # Mock partial quality result
    mock_result = IngestionResult(
        success=True,
        listing_id=2,
        status="created",
        provenance="jsonld",
        quality="partial",  # Partial quality
        url=test_url,
        title="PC",
        price=Decimal("399.99"),
        marketplace="other",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service = AsyncMock()
        mock_service.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service

        from dealbrain_api.tasks.ingestion import _ingest_url_async

        result = await _ingest_url_async(job_id=str(job_id), url=test_url)

    # Verify partial quality status
    assert result["success"] is True
    assert result["status"] == "partial"  # Partial status
    assert result["quality"] == "partial"

    # Verify ImportSession reflects partial status
    stmt = select(ImportSession).where(ImportSession.id == job_id)
    result_db = await db_session.execute(stmt)
    import_session = result_db.scalar_one()

    assert import_session.status == "partial"
    assert import_session.conflicts_json["quality"] == "partial"
