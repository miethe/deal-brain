"""Integration tests for computed properties in API responses."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

try:
    import aiosqlite  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import Cpu, Gpu, Listing
from dealbrain_core.schemas.listing import ListingRead


@pytest.mark.anyio("asyncio")
async def test_listing_read_schema_includes_computed_properties():
    """Test that ListingRead schema serializes computed properties correctly."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create CPU and GPU
        cpu = Cpu(
            name="Intel Core i7-12700K",
            manufacturer="Intel",
            cores=12,
            threads=20,
        )
        gpu = Gpu(
            name="NVIDIA GeForce RTX 3070",
            manufacturer="NVIDIA",
            gpu_mark=22000,
        )
        session.add_all([cpu, gpu])
        await session.flush()

        # Create listing with all computed properties
        listing = Listing(
            title="Gaming PC",
            price_usd=1500.0,
            condition="new",
            raw_listing_json={
                "imageUrl": "https://example.com/gaming-pc.jpg",
                "marketplace_id": "ebay-123456",
            },
        )
        listing.cpu = cpu
        listing.gpu = gpu
        session.add(listing)
        await session.commit()

        # Refresh to ensure relationships are loaded
        await session.refresh(listing)

        # Serialize using Pydantic schema (simulates API response)
        listing_read = ListingRead.model_validate(listing)

        # Verify computed properties are present in serialized response
        assert listing_read.cpu_name == "Intel Core i7-12700K"
        assert listing_read.gpu_name == "NVIDIA GeForce RTX 3070"
        assert listing_read.thumbnail_url == "https://example.com/gaming-pc.jpg"

        # Verify nested objects are still present
        assert listing_read.cpu is not None
        assert listing_read.cpu.name == "Intel Core i7-12700K"
        assert listing_read.gpu is not None
        assert listing_read.gpu.name == "NVIDIA GeForce RTX 3070"

        # Verify serialization to dict (final API response format)
        response_dict = listing_read.model_dump()
        assert response_dict["cpu_name"] == "Intel Core i7-12700K"
        assert response_dict["gpu_name"] == "NVIDIA GeForce RTX 3070"
        assert response_dict["thumbnail_url"] == "https://example.com/gaming-pc.jpg"


@pytest.mark.anyio("asyncio")
async def test_listing_read_schema_handles_missing_computed_properties():
    """Test that ListingRead schema handles None values for computed properties."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Create listing without CPU, GPU, or image
        listing = Listing(
            title="Barebones PC",
            price_usd=300.0,
            condition="used",
        )
        session.add(listing)
        await session.commit()

        await session.refresh(listing)

        # Serialize using Pydantic schema
        listing_read = ListingRead.model_validate(listing)

        # Verify computed properties return None gracefully
        assert listing_read.cpu_name is None
        assert listing_read.gpu_name is None
        assert listing_read.thumbnail_url is None

        # Verify serialization to dict
        response_dict = listing_read.model_dump()
        assert response_dict["cpu_name"] is None
        assert response_dict["gpu_name"] is None
        assert response_dict["thumbnail_url"] is None
