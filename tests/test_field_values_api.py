"""Tests for field values autocomplete endpoint."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

try:
    import aiosqlite  # type: ignore  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import Cpu, Gpu, Listing
from apps.api.dealbrain_api.services.field_values import get_field_distinct_values


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio("asyncio")
async def test_get_listing_condition_values():
    """Test getting distinct values for listing.condition field."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create test listings with different conditions
        listings = [
            Listing(title="Test 1", price_usd=100.0, condition="New"),
            Listing(title="Test 2", price_usd=200.0, condition="Like New"),
            Listing(title="Test 3", price_usd=150.0, condition="Good"),
            Listing(title="Test 4", price_usd=120.0, condition="New"),  # Duplicate
        ]
        for listing in listings:
            session.add(listing)
        await session.commit()

        # Get distinct condition values
        values = await get_field_distinct_values(
            session=session,
            field_name="listing.condition",
            limit=100,
        )

        assert len(values) == 3  # Should have 3 distinct values
        assert set(values) == {"Good", "Like New", "New"}


@pytest.mark.anyio("asyncio")
async def test_get_listing_manufacturer_values():
    """Test getting distinct values for listing.manufacturer field."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create test listings with different manufacturers
        listings = [
            Listing(title="Test 1", price_usd=100.0, manufacturer="Dell"),
            Listing(title="Test 2", price_usd=200.0, manufacturer="HP"),
            Listing(title="Test 3", price_usd=150.0, manufacturer="Lenovo"),
            Listing(title="Test 4", price_usd=120.0, manufacturer="Dell"),  # Duplicate
        ]
        for listing in listings:
            session.add(listing)
        await session.commit()

        # Get distinct manufacturer values
        values = await get_field_distinct_values(
            session=session,
            field_name="listing.manufacturer",
            limit=100,
        )

        assert len(values) == 3
        assert set(values) == {"Dell", "HP", "Lenovo"}


@pytest.mark.anyio("asyncio")
async def test_get_cpu_manufacturer_values():
    """Test getting distinct values for cpu.manufacturer field."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create test CPUs with different manufacturers
        cpus = [
            Cpu(name="Intel Core i5-12400", manufacturer="Intel"),
            Cpu(name="AMD Ryzen 5 5600X", manufacturer="AMD"),
            Cpu(name="Intel Core i7-13700", manufacturer="Intel"),  # Duplicate
        ]
        for cpu in cpus:
            session.add(cpu)
        await session.commit()

        # Get distinct manufacturer values
        values = await get_field_distinct_values(
            session=session,
            field_name="cpu.manufacturer",
            limit=100,
        )

        assert len(values) == 2
        assert set(values) == {"AMD", "Intel"}


@pytest.mark.anyio("asyncio")
async def test_get_gpu_manufacturer_values():
    """Test getting distinct values for gpu.manufacturer field."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create test GPUs with different manufacturers
        gpus = [
            Gpu(name="RTX 3060", manufacturer="NVIDIA"),
            Gpu(name="RX 6700 XT", manufacturer="AMD"),
            Gpu(name="RTX 4070", manufacturer="NVIDIA"),  # Duplicate
        ]
        for gpu in gpus:
            session.add(gpu)
        await session.commit()

        # Get distinct manufacturer values
        values = await get_field_distinct_values(
            session=session,
            field_name="gpu.manufacturer",
            limit=100,
        )

        assert len(values) == 2
        assert set(values) == {"AMD", "NVIDIA"}


@pytest.mark.anyio("asyncio")
async def test_limit_parameter():
    """Test that limit parameter works correctly."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create 10 manufacturers
        for i in range(10):
            session.add(
                Listing(title=f"Test {i}", price_usd=100.0, manufacturer=f"Manufacturer_{i}")
            )
        await session.commit()

        # Get only 5 values
        values = await get_field_distinct_values(
            session=session,
            field_name="listing.manufacturer",
            limit=5,
        )

        assert len(values) == 5


@pytest.mark.anyio("asyncio")
async def test_search_filter():
    """Test that search filter works correctly."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create listings with different sellers
        listings = [
            Listing(title="Test 1", price_usd=100.0, seller="ebay_seller_1"),
            Listing(title="Test 2", price_usd=200.0, seller="amazon_seller_1"),
            Listing(title="Test 3", price_usd=150.0, seller="ebay_seller_2"),
            Listing(title="Test 4", price_usd=120.0, seller="newegg_seller_1"),
        ]
        for listing in listings:
            session.add(listing)
        await session.commit()

        # Search for "ebay"
        values = await get_field_distinct_values(
            session=session,
            field_name="listing.seller",
            search="ebay",
        )

        assert len(values) == 2
        assert all("ebay" in v for v in values)


@pytest.mark.anyio("asyncio")
async def test_invalid_field_format():
    """Test that invalid field name format raises ValueError."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        with pytest.raises(ValueError, match="Invalid field name format"):
            await get_field_distinct_values(
                session=session,
                field_name="invalid_field",  # Missing dot separator
            )


@pytest.mark.anyio("asyncio")
async def test_unknown_entity():
    """Test that unknown entity raises ValueError."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        with pytest.raises(ValueError, match="Unknown entity"):
            await get_field_distinct_values(
                session=session,
                field_name="unknown_entity.field",
            )


@pytest.mark.anyio("asyncio")
async def test_unknown_field():
    """Test that unknown field raises ValueError."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        with pytest.raises(ValueError, match="Unknown field"):
            await get_field_distinct_values(
                session=session,
                field_name="listing.nonexistent_field",
            )


@pytest.mark.anyio("asyncio")
async def test_null_values_filtered():
    """Test that null values are filtered out."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create listings with some null manufacturers
        listings = [
            Listing(title="Test 1", price_usd=100.0, manufacturer="Dell"),
            Listing(title="Test 2", price_usd=200.0, manufacturer=None),  # Null
            Listing(title="Test 3", price_usd=150.0, manufacturer="HP"),
            Listing(title="Test 4", price_usd=120.0, manufacturer=None),  # Null
        ]
        for listing in listings:
            session.add(listing)
        await session.commit()

        # Get distinct manufacturer values
        values = await get_field_distinct_values(
            session=session,
            field_name="listing.manufacturer",
            limit=100,
        )

        # Should only return non-null values
        assert len(values) == 2
        assert set(values) == {"Dell", "HP"}
        assert None not in values
