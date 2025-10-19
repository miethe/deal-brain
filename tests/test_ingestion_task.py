"""Tests for URL ingestion Celery tasks."""

from __future__ import annotations

import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - optional dependency check
    import aiosqlite  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - skip when unavailable
    aiosqlite = None

from dealbrain_api.db import Base
from dealbrain_api.models.core import ImportSession
from dealbrain_api.services.ingestion import IngestionResult
from dealbrain_api.tasks.ingestion import _ingest_url_async, ingest_url_task
from dealbrain_core.enums import SourceType


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
