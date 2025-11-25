"""Tests for valuation background tasks."""

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from dealbrain_api.db import Base
from dealbrain_core.enums import Condition, ListingStatus
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

try:  # pragma: no cover - optional dependency check
    import aiosqlite  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - skip when unavailable
    aiosqlite = None

from dealbrain_api.models.core import Listing
from dealbrain_api.tasks.valuation import _recalculate_listings_async


@pytest_asyncio.fixture
async def db_session():
    """Provide an isolated in-memory database session for tasks tests."""
    if aiosqlite is None:
        pytest.skip("aiosqlite is not installed; skipping valuation task tests")
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
async def test_recalculate_listings_task_updates_adjusted_price(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    """Background task should recalculate adjusted prices for targeted listings."""
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
        "dealbrain_api.tasks.valuation.session_scope",
        _session_scope_override,
    )

    listing = Listing(
        title="Async Task Listing",
        price_usd=999.0,
        condition=Condition.USED.value,
        status=ListingStatus.ACTIVE.value,
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Ensure adjusted price is stale
    listing.adjusted_price_usd = None
    listing.valuation_breakdown = None
    await db_session.commit()

    # Call the async function directly instead of the Celery wrapper
    # This avoids event loop conflicts in tests
    result = await _recalculate_listings_async(
        listing_ids=[listing.id],
        include_inactive=False,
    )

    assert result["succeeded"] == 1
    await db_session.refresh(listing)
    assert listing.adjusted_price_usd == pytest.approx(listing.price_usd)
    assert listing.valuation_breakdown is not None
