"""
Tests for complete_partial_import method in ListingsService.

Tests coverage:
1. Successful completion with price
2. Listing not found error
3. Already complete listing error
4. Invalid price (negative) error
5. Invalid price (non-numeric) error
6. Metrics calculation after completion
7. Metadata tracking for manual price entry
"""

from __future__ import annotations

import sys
import types
from decimal import Decimal

import pytest

try:
    import pytest_asyncio
except ModuleNotFoundError:
    pytest_asyncio = None

# Stub Celery to avoid import errors in test environment
if "celery" not in sys.modules:

    class _DummyTask:
        def __init__(self, func):
            self._func = func

        def __call__(self, *args, **kwargs):
            return self._func(*args, **kwargs)

        def delay(self, *args, **kwargs):
            return self._func(*args, **kwargs)

    class _StubCelery:
        def __init__(self, *args, **kwargs):
            pass

        def config_from_object(self, *args, **kwargs):
            return None

        def task(self, *decorator_args, **decorator_kwargs):
            def _decorator(func):
                return _DummyTask(func)

            return _decorator

    celery_stub = types.ModuleType("celery")
    celery_stub.Celery = _StubCelery
    sys.modules["celery"] = celery_stub

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dealbrain_api.db import Base
from dealbrain_api.models.core import Cpu, Listing, Profile
from dealbrain_api.services.listings import complete_partial_import

try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


pytestmark = pytest.mark.asyncio


if pytest_asyncio:

    @pytest_asyncio.fixture
    async def db_session() -> AsyncSession:
        """Provide an isolated in-memory database session for tests."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping completion tests")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session = async_session()
        try:
            # Create default profile for metrics calculation
            profile = Profile(
                name="Default Profile",
                is_default=True,
                weights_json={
                    "cpu_mark_multi": 0.4,
                    "cpu_mark_single": 0.3,
                    "gpu_score": 0.2,
                    "perf_per_watt": 0.05,
                    "ram_capacity": 0.05,
                },
            )
            session.add(profile)

            # Create sample CPU for metrics calculation
            cpu = Cpu(
                name="Intel Core i5-12400",
                manufacturer="Intel",
                cores=6,
                threads=12,
                cpu_mark_multi=15000,
                cpu_mark_single=3500,
                tdp_w=65,
            )
            session.add(cpu)

            await session.commit()

            yield session
        finally:
            await session.close()
            await engine.dispose()

else:

    @pytest.fixture
    def db_session() -> AsyncSession:
        pytest.skip("pytest-asyncio is not installed; skipping completion tests")


# No need to disable recalculation as listings service doesn't have that function


async def test_complete_partial_import_success(db_session: AsyncSession):
    """Test successful completion of partial import with price."""
    # Create partial listing
    listing = Listing(
        title="Gaming PC - Partial Import",
        quality="partial",
        missing_fields=["price"],
        extraction_metadata={},
        price_usd=None,
        condition="used",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Complete the partial import
    completion_data = {"price": 299.99}
    updated = await complete_partial_import(
        session=db_session,
        listing_id=listing.id,
        completion_data=completion_data,
        user_id="test_user",
    )

    # Verify updates
    assert updated.price_usd == 299.99
    assert updated.quality == "full"
    assert "price" not in updated.missing_fields
    assert updated.extraction_metadata.get("price") == "manual"


async def test_complete_partial_import_not_found(db_session: AsyncSession):
    """Test error when listing not found."""
    with pytest.raises(ValueError, match="Listing 9999 not found"):
        await complete_partial_import(
            session=db_session,
            listing_id=9999,
            completion_data={"price": 299.99},
            user_id="test_user",
        )


async def test_complete_partial_import_already_complete(db_session: AsyncSession):
    """Test error when trying to complete an already complete listing."""
    # Create full listing
    listing = Listing(
        title="Gaming PC - Already Complete",
        quality="full",
        price_usd=499.99,
        condition="used",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Try to complete it again
    with pytest.raises(ValueError, match="is already complete"):
        await complete_partial_import(
            session=db_session,
            listing_id=listing.id,
            completion_data={"price": 599.99},
            user_id="test_user",
        )


async def test_complete_partial_import_invalid_price_negative(db_session: AsyncSession):
    """Test error when price is negative."""
    # Create partial listing
    listing = Listing(
        title="Gaming PC - Partial Import",
        quality="partial",
        missing_fields=["price"],
        price_usd=None,
        condition="used",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Try to complete with negative price
    with pytest.raises(ValueError, match="Price must be greater than 0"):
        await complete_partial_import(
            session=db_session,
            listing_id=listing.id,
            completion_data={"price": -100},
            user_id="test_user",
        )


async def test_complete_partial_import_invalid_price_non_numeric(db_session: AsyncSession):
    """Test error when price is non-numeric."""
    # Create partial listing
    listing = Listing(
        title="Gaming PC - Partial Import",
        quality="partial",
        missing_fields=["price"],
        price_usd=None,
        condition="used",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Try to complete with non-numeric price
    with pytest.raises(ValueError, match="Price must be a numeric value"):
        await complete_partial_import(
            session=db_session,
            listing_id=listing.id,
            completion_data={"price": "not_a_number"},
            user_id="test_user",
        )


async def test_complete_partial_import_metrics_calculated(db_session: AsyncSession):
    """Test that metrics are calculated after completion."""
    # Get CPU for linking
    result = await db_session.execute(select(Cpu))
    cpu = result.scalars().first()

    # Create partial listing with CPU
    listing = Listing(
        title="Gaming PC - With CPU",
        quality="partial",
        missing_fields=["price"],
        price_usd=None,
        condition="used",
        cpu_id=cpu.id,
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Complete the partial import
    completion_data = {"price": 300.0}
    updated = await complete_partial_import(
        session=db_session,
        listing_id=listing.id,
        completion_data=completion_data,
        user_id="test_user",
    )

    # Verify metrics were calculated
    assert updated.adjusted_price_usd is not None
    assert updated.valuation_breakdown is not None
    assert updated.score_cpu_multi is not None
    assert updated.score_cpu_single is not None

    # Verify CPU performance metrics
    assert updated.dollar_per_cpu_mark_single is not None
    assert updated.dollar_per_cpu_mark_multi is not None


async def test_complete_partial_import_metadata_tracking(db_session: AsyncSession):
    """Test that extraction_metadata tracks manual price entry."""
    # Create partial listing with some existing metadata
    listing = Listing(
        title="Gaming PC - Metadata Test",
        quality="partial",
        missing_fields=["price"],
        extraction_metadata={"title": "extracted", "condition": "extracted"},
        price_usd=None,
        condition="used",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Complete the partial import
    completion_data = {"price": 450.0}
    updated = await complete_partial_import(
        session=db_session,
        listing_id=listing.id,
        completion_data=completion_data,
        user_id="test_user",
    )

    # Verify metadata tracking
    assert updated.extraction_metadata.get("price") == "manual"
    assert updated.extraction_metadata.get("title") == "extracted"
    assert updated.extraction_metadata.get("condition") == "extracted"


async def test_complete_partial_import_partial_still_incomplete(db_session: AsyncSession):
    """Test that listing stays partial if other fields are still missing."""
    # Create partial listing with multiple missing fields
    listing = Listing(
        title="Gaming PC - Multiple Missing",
        quality="partial",
        missing_fields=["price", "cpu_model", "ram_gb"],
        extraction_metadata={},
        price_usd=None,
        condition="used",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Only complete price
    completion_data = {"price": 350.0}
    updated = await complete_partial_import(
        session=db_session,
        listing_id=listing.id,
        completion_data=completion_data,
        user_id="test_user",
    )

    # Verify listing is still partial
    assert updated.price_usd == 350.0
    assert updated.quality == "partial"  # Still partial because other fields missing
    assert "price" not in updated.missing_fields
    assert "cpu_model" in updated.missing_fields
    assert "ram_gb" in updated.missing_fields


async def test_complete_partial_import_zero_price(db_session: AsyncSession):
    """Test that zero price is rejected."""
    # Create partial listing
    listing = Listing(
        title="Gaming PC - Zero Price Test",
        quality="partial",
        missing_fields=["price"],
        price_usd=None,
        condition="used",
    )
    db_session.add(listing)
    await db_session.commit()
    await db_session.refresh(listing)

    # Try to complete with zero price
    with pytest.raises(ValueError, match="Price must be greater than 0"):
        await complete_partial_import(
            session=db_session,
            listing_id=listing.id,
            completion_data={"price": 0},
            user_id="test_user",
        )
