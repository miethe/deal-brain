"""Tests for URL ingestion Celery tasks."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - optional dependency check
    import aiosqlite  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - skip when unavailable
    aiosqlite = None

from dealbrain_api.db import Base
from dealbrain_api.models.core import ImportSession, Listing, RawPayload
from dealbrain_api.services.ingestion import IngestionResult
from dealbrain_api.tasks.ingestion import (
    _cleanup_expired_payloads_async,
    _ingest_url_async,
    cleanup_expired_payloads_task,
)
from dealbrain_core.enums import Condition, SourceType


@pytest_asyncio.fixture
async def db_session():
    """Provide an isolated in-memory database session for task tests."""
    if aiosqlite is None:
        pytest.skip("aiosqlite is not installed; skipping ingestion task tests")
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


@pytest.mark.asyncio
async def test_successful_ingestion_complete_quality(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task should update ImportSession to 'complete' for full quality ingestion."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create test ImportSession
    import_session = ImportSession(
        id=uuid4(),
        filename="test_url_import",
        upload_path="/tmp/test",
        status="queued",
        source_type=SourceType.URL_SINGLE.value,
        url="https://ebay.com/itm/123456789012",
    )
    db_session.add(import_session)
    await db_session.commit()

    # Mock IngestionService.ingest_single_url
    mock_result = IngestionResult(
        success=True,
        listing_id=1,
        status="created",
        provenance="ebay_api",
        quality="full",
        url="https://ebay.com/itm/123456789012",
        title="Gaming PC",
        price=Decimal("599.99"),
        vendor_item_id="123456789012",
        marketplace="ebay",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service_instance

        # Execute task async function directly
        result = await _ingest_url_async(
            job_id=str(import_session.id),
            url="https://ebay.com/itm/123456789012",
        )

    # Verify result
    assert result["success"] is True
    assert result["listing_id"] == 1
    assert result["status"] == "complete"  # full quality → complete
    assert result["provenance"] == "ebay_api"
    assert result["quality"] == "full"

    # Verify ImportSession updated
    await db_session.refresh(import_session)
    assert import_session.status == "complete"
    assert import_session.conflicts_json["listing_id"] == 1
    assert import_session.conflicts_json["provenance"] == "ebay_api"
    assert import_session.conflicts_json["quality"] == "full"
    assert import_session.conflicts_json["title"] == "Gaming PC"
    assert import_session.conflicts_json["price"] == 599.99


@pytest.mark.asyncio
async def test_successful_ingestion_partial_quality(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task should update ImportSession to 'partial' for partial quality ingestion."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create test ImportSession
    import_session = ImportSession(
        id=uuid4(),
        filename="test_url_import",
        upload_path="/tmp/test",
        status="queued",
        source_type=SourceType.URL_SINGLE.value,
        url="https://example.com/product",
    )
    db_session.add(import_session)
    await db_session.commit()

    # Mock IngestionService.ingest_single_url with partial quality
    mock_result = IngestionResult(
        success=True,
        listing_id=2,
        status="created",
        provenance="jsonld",
        quality="partial",  # Partial quality
        url="https://example.com/product",
        title="PC",
        price=Decimal("399.99"),
        vendor_item_id=None,
        marketplace="other",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service_instance

        # Execute task async function directly
        result = await _ingest_url_async(
            job_id=str(import_session.id),
            url="https://example.com/product",
        )

    # Verify result
    assert result["success"] is True
    assert result["status"] == "partial"  # partial quality → partial status
    assert result["quality"] == "partial"

    # Verify ImportSession updated
    await db_session.refresh(import_session)
    assert import_session.status == "partial"
    assert import_session.conflicts_json["quality"] == "partial"


@pytest.mark.asyncio
async def test_failed_ingestion(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task should update ImportSession to 'failed' when ingestion fails."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create test ImportSession
    import_session = ImportSession(
        id=uuid4(),
        filename="test_url_import",
        upload_path="/tmp/test",
        status="queued",
        source_type=SourceType.URL_SINGLE.value,
        url="https://invalid.com/item",
    )
    db_session.add(import_session)
    await db_session.commit()

    # Mock IngestionService.ingest_single_url with failure
    mock_result = IngestionResult(
        success=False,
        listing_id=None,
        status="failed",
        provenance="unknown",
        quality="partial",
        url="https://invalid.com/item",
        error="Adapter not found for domain",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service_instance

        # Execute task
        result = await _ingest_url_async(
            job_id=str(import_session.id),
            url="https://invalid.com/item",
        )

    # Verify result
    assert result["success"] is False
    assert result["status"] == "failed"
    assert result["error"] == "Adapter not found for domain"

    # Verify ImportSession updated
    await db_session.refresh(import_session)
    assert import_session.status == "failed"
    assert import_session.conflicts_json["error"] == "Adapter not found for domain"


@pytest.mark.asyncio
async def test_import_session_not_found(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task should return failure when ImportSession not found."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Use non-existent UUID
    fake_job_id = str(uuid4())

    # Execute task - should raise ValueError for missing session
    with pytest.raises(ValueError, match="not found"):
        await _ingest_url_async(
            job_id=fake_job_id,
            url="https://ebay.com/itm/123",
        )


@pytest.mark.asyncio
async def test_transient_error_propagates(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task async function should propagate transient errors for retry handling."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create test ImportSession
    import_session = ImportSession(
        id=uuid4(),
        filename="test_url_import",
        upload_path="/tmp/test",
        status="queued",
        source_type=SourceType.URL_SINGLE.value,
        url="https://ebay.com/itm/timeout",
    )
    db_session.add(import_session)
    await db_session.commit()

    # Mock IngestionService to raise TimeoutError
    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_single_url.side_effect = TimeoutError("Request timed out")
        MockService.return_value = mock_service_instance

        # Execute task async function - should propagate exception
        with pytest.raises(TimeoutError, match="Request timed out"):
            await _ingest_url_async(
                job_id=str(import_session.id),
                url="https://ebay.com/itm/timeout",
            )


@pytest.mark.asyncio
async def test_permanent_error_propagates(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task async function should propagate permanent errors (ValueError)."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create test ImportSession
    import_session = ImportSession(
        id=uuid4(),
        filename="test_url_import",
        upload_path="/tmp/test",
        status="queued",
        source_type=SourceType.URL_SINGLE.value,
        url="invalid-url",
    )
    db_session.add(import_session)
    await db_session.commit()

    # Mock IngestionService to raise ValueError (permanent error)
    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_single_url.side_effect = ValueError("Invalid URL format")
        MockService.return_value = mock_service_instance

        # Execute task async function - should propagate exception
        with pytest.raises(ValueError, match="Invalid URL format"):
            await _ingest_url_async(
                job_id=str(import_session.id),
                url="invalid-url",
            )


@pytest.mark.asyncio
async def test_status_transition_queued_to_running(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task should transition ImportSession status from queued to running."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create test ImportSession with status=queued
    import_session = ImportSession(
        id=uuid4(),
        filename="test_url_import",
        upload_path="/tmp/test",
        status="queued",  # Initial status
        source_type=SourceType.URL_SINGLE.value,
        url="https://ebay.com/itm/123",
    )
    db_session.add(import_session)
    await db_session.commit()

    # Mock successful ingestion
    mock_result = IngestionResult(
        success=True,
        listing_id=1,
        status="created",
        provenance="ebay_api",
        quality="full",
        url="https://ebay.com/itm/123",
        title="PC",
        price=Decimal("500"),
        vendor_item_id="123",
        marketplace="ebay",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service_instance

        # Execute task
        await _ingest_url_async(
            job_id=str(import_session.id),
            url="https://ebay.com/itm/123",
        )

    # Verify final status is complete (not running)
    await db_session.refresh(import_session)
    assert import_session.status == "complete"  # Ended in terminal state


@pytest.mark.asyncio
async def test_result_storage_in_conflicts_json(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Task should store result details in ImportSession.conflicts_json."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create test ImportSession
    import_session = ImportSession(
        id=uuid4(),
        filename="test_url_import",
        upload_path="/tmp/test",
        status="queued",
        source_type=SourceType.URL_SINGLE.value,
        url="https://ebay.com/itm/999",
    )
    db_session.add(import_session)
    await db_session.commit()

    # Mock successful ingestion with all fields
    mock_result = IngestionResult(
        success=True,
        listing_id=99,
        status="created",
        provenance="ebay_api",
        quality="full",
        url="https://ebay.com/itm/999",
        title="Dell OptiPlex 7000",
        price=Decimal("749.99"),
        vendor_item_id="999",
        marketplace="ebay",
    )

    with patch("dealbrain_api.tasks.ingestion.IngestionService") as MockService:
        mock_service_instance = AsyncMock()
        mock_service_instance.ingest_single_url.return_value = mock_result
        MockService.return_value = mock_service_instance

        # Execute task
        await _ingest_url_async(
            job_id=str(import_session.id),
            url="https://ebay.com/itm/999",
        )

    # Verify all result fields stored in conflicts_json
    await db_session.refresh(import_session)
    stored = import_session.conflicts_json

    assert stored["listing_id"] == 99
    assert stored["provenance"] == "ebay_api"
    assert stored["quality"] == "full"
    assert stored["title"] == "Dell OptiPlex 7000"
    assert stored["price"] == 749.99
    assert stored["vendor_item_id"] == "999"
    assert stored["marketplace"] == "ebay"


# ========================================
# Raw Payload Cleanup Tests
# ========================================


@pytest_asyncio.fixture
async def sample_listing(db_session: AsyncSession):
    """Create a sample listing for RawPayload tests."""
    listing = Listing(
        title="Test PC",
        price_usd=599.99,
        condition=Condition.USED.value,
        marketplace="other",
        seller="TestSeller",
        dedup_hash="test_hash_123",
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


@pytest.mark.asyncio
async def test_cleanup_expired_payloads_deletes_old_records(
    db_session: AsyncSession,
    sample_listing: Listing,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test cleanup deletes records older than TTL."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create old payload (35 days ago) - should be deleted
    old_date = datetime.utcnow() - timedelta(days=35)
    old_payload = RawPayload(
        listing_id=sample_listing.id,
        adapter="ebay",
        source_type="json",
        payload={"old": "data"},
        ttl_days=30,
    )
    old_payload.created_at = old_date
    db_session.add(old_payload)

    # Create recent payload (10 days ago) - should be preserved
    recent_date = datetime.utcnow() - timedelta(days=10)
    recent_payload = RawPayload(
        listing_id=sample_listing.id,
        adapter="jsonld",
        source_type="json",
        payload={"recent": "data"},
        ttl_days=30,
    )
    recent_payload.created_at = recent_date
    db_session.add(recent_payload)
    await db_session.commit()

    # Run cleanup
    result = await _cleanup_expired_payloads_async()

    # Verify result
    assert result["deleted_count"] == 1
    assert result["ttl_days"] == 30
    assert "cutoff_date" in result

    # Check DB state - only recent payload should remain
    from sqlalchemy import select

    stmt = select(RawPayload)
    db_result = await db_session.execute(stmt)
    payloads = db_result.scalars().all()

    assert len(payloads) == 1
    assert payloads[0].id == recent_payload.id
    assert payloads[0].adapter == "jsonld"


@pytest.mark.asyncio
async def test_cleanup_expired_payloads_preserves_recent_records(
    db_session: AsyncSession,
    sample_listing: Listing,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test cleanup preserves records newer than TTL."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create recent payloads (all within TTL)
    for i in range(3):
        recent_date = datetime.utcnow() - timedelta(days=i)
        payload = RawPayload(
            listing_id=sample_listing.id,
            adapter=f"adapter_{i}",
            source_type="json",
            payload={"data": f"test_{i}"},
            ttl_days=30,
        )
        payload.created_at = recent_date
        db_session.add(payload)

    await db_session.commit()

    # Run cleanup
    result = await _cleanup_expired_payloads_async()

    # Verify no deletions
    assert result["deleted_count"] == 0

    # Check DB state - all payloads should remain
    from sqlalchemy import select

    stmt = select(RawPayload)
    db_result = await db_session.execute(stmt)
    payloads = db_result.scalars().all()

    assert len(payloads) == 3


@pytest.mark.asyncio
async def test_cleanup_expired_payloads_empty_table(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test cleanup handles empty table gracefully."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Run cleanup on empty table
    result = await _cleanup_expired_payloads_async()

    # Verify no errors, zero deletions
    assert result["deleted_count"] == 0
    assert result["ttl_days"] == 30
    assert "cutoff_date" in result


@pytest.mark.asyncio
async def test_cleanup_expired_payloads_returns_statistics(
    db_session: AsyncSession,
    sample_listing: Listing,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test cleanup returns accurate statistics."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create multiple old payloads (40 days ago)
    old_date = datetime.utcnow() - timedelta(days=40)
    for i in range(5):
        payload = RawPayload(
            listing_id=sample_listing.id,
            adapter=f"adapter_{i}",
            source_type="json",
            payload={"data": f"old_{i}"},
            ttl_days=30,
        )
        payload.created_at = old_date
        db_session.add(payload)

    await db_session.commit()

    # Run cleanup
    result = await _cleanup_expired_payloads_async()

    # Verify statistics
    assert result["deleted_count"] == 5
    assert result["ttl_days"] == 30
    assert "cutoff_date" in result

    # Verify cutoff_date is valid ISO format
    cutoff = datetime.fromisoformat(result["cutoff_date"])
    assert isinstance(cutoff, datetime)


def test_cleanup_task_error_handling(monkeypatch: pytest.MonkeyPatch):
    """Test cleanup task handles errors gracefully without crashing beat schedule."""

    # Mock _cleanup_expired_payloads_async to raise exception
    async def _mock_cleanup_error():
        raise RuntimeError("Database connection failed")

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion._cleanup_expired_payloads_async",
        _mock_cleanup_error,
    )

    # Run task - should not raise, should return error result
    result = cleanup_expired_payloads_task()

    # Verify error result returned (not raised)
    assert result["deleted_count"] == 0
    assert result["ttl_days"] == 0
    assert result["cutoff_date"] is None
    assert "error" in result
    assert "Database connection failed" in result["error"]


@pytest.mark.asyncio
async def test_cleanup_respects_ttl_boundary(
    db_session: AsyncSession,
    sample_listing: Listing,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test cleanup respects exact TTL boundary (30 days)."""
    engine = db_session.bind
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _session_scope_override():
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(
        "dealbrain_api.tasks.ingestion.session_scope",
        _session_scope_override,
    )

    # Create payload exactly at TTL boundary (30 days + 1 hour ago - should be deleted)
    boundary_old = datetime.utcnow() - timedelta(days=30, hours=1)
    old_payload = RawPayload(
        listing_id=sample_listing.id,
        adapter="ebay",
        source_type="json",
        payload={"boundary": "old"},
        ttl_days=30,
    )
    old_payload.created_at = boundary_old
    db_session.add(old_payload)

    # Create payload just inside TTL (29 days ago - should be preserved)
    boundary_new = datetime.utcnow() - timedelta(days=29)
    new_payload = RawPayload(
        listing_id=sample_listing.id,
        adapter="jsonld",
        source_type="json",
        payload={"boundary": "new"},
        ttl_days=30,
    )
    new_payload.created_at = boundary_new
    db_session.add(new_payload)
    await db_session.commit()

    # Run cleanup
    result = await _cleanup_expired_payloads_async()

    # Verify only old payload deleted
    assert result["deleted_count"] == 1

    # Check DB state
    from sqlalchemy import select

    stmt = select(RawPayload)
    db_result = await db_session.execute(stmt)
    payloads = db_result.scalars().all()

    assert len(payloads) == 1
    assert payloads[0].id == new_payload.id
