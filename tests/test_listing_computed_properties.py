"""Tests for Listing computed properties (cpu_name, gpu_name, thumbnail_url)."""

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


class TestCpuNameProperty:
    """Test cpu_name computed property."""

    @pytest.mark.anyio("asyncio")
    async def test_cpu_name_with_cpu_attached(self):
        """Test cpu_name returns correct value when CPU is attached."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            cpu = Cpu(
                name="Intel Core i5-12400",
                manufacturer="Intel",
                cores=6,
                threads=12,
                cpu_mark_single=3500,
                cpu_mark_multi=21000,
            )
            session.add(cpu)
            await session.flush()

            listing = Listing(
                title="Test PC with CPU",
                price_usd=500.0,
                condition="used",
            )
            listing.cpu = cpu
            session.add(listing)
            await session.commit()

            # Refresh to ensure relationships are loaded
            await session.refresh(listing)

            assert listing.cpu_name == "Intel Core i5-12400"

    @pytest.mark.anyio("asyncio")
    async def test_cpu_name_returns_none_when_no_cpu(self):
        """Test cpu_name returns None when no CPU is attached."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC without CPU",
                price_usd=500.0,
                condition="used",
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.cpu_name is None


class TestGpuNameProperty:
    """Test gpu_name computed property."""

    @pytest.mark.anyio("asyncio")
    async def test_gpu_name_with_gpu_attached(self):
        """Test gpu_name returns correct value when GPU is attached."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            gpu = Gpu(
                name="NVIDIA GeForce RTX 3060",
                manufacturer="NVIDIA",
                gpu_mark=15000,
            )
            session.add(gpu)
            await session.flush()

            listing = Listing(
                title="Test PC with GPU",
                price_usd=800.0,
                condition="new",
            )
            listing.gpu = gpu
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.gpu_name == "NVIDIA GeForce RTX 3060"

    @pytest.mark.anyio("asyncio")
    async def test_gpu_name_returns_none_when_no_gpu(self):
        """Test gpu_name returns None when no GPU is attached."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC without GPU",
                price_usd=500.0,
                condition="used",
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.gpu_name is None


class TestThumbnailUrlProperty:
    """Test thumbnail_url computed property."""

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_from_raw_listing_json_image_url(self):
        """Test thumbnail_url extraction from raw_listing_json with 'image_url' key."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC with image",
                price_usd=500.0,
                condition="used",
                raw_listing_json={"image_url": "https://example.com/image1.jpg"},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.thumbnail_url == "https://example.com/image1.jpg"

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_from_raw_listing_json_thumbnail_url(self):
        """Test thumbnail_url extraction from raw_listing_json with 'thumbnail_url' key."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC with thumbnail",
                price_usd=500.0,
                condition="used",
                raw_listing_json={"thumbnail_url": "https://example.com/thumb.jpg"},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.thumbnail_url == "https://example.com/thumb.jpg"

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_from_raw_listing_json_camel_case(self):
        """Test thumbnail_url extraction from raw_listing_json with camelCase keys."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC with camelCase image",
                price_usd=500.0,
                condition="used",
                raw_listing_json={"imageUrl": "https://example.com/imageUrl.jpg"},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.thumbnail_url == "https://example.com/imageUrl.jpg"

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_fallback_to_attributes_json(self):
        """Test thumbnail_url falls back to attributes_json when not in raw_listing_json."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC with attributes image",
                price_usd=500.0,
                condition="used",
                raw_listing_json={},
                attributes_json={"image_url": "https://example.com/attributes_image.jpg"},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.thumbnail_url == "https://example.com/attributes_image.jpg"

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_prefers_raw_listing_json_over_attributes(self):
        """Test thumbnail_url prioritizes raw_listing_json over attributes_json."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC with both image sources",
                price_usd=500.0,
                condition="used",
                raw_listing_json={"image_url": "https://example.com/raw.jpg"},
                attributes_json={"image_url": "https://example.com/attributes.jpg"},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            # Should use raw_listing_json, not attributes_json
            assert listing.thumbnail_url == "https://example.com/raw.jpg"

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_returns_none_when_no_image_data(self):
        """Test thumbnail_url returns None when no image data is present."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC without image",
                price_usd=500.0,
                condition="used",
                raw_listing_json={},
                attributes_json={},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.thumbnail_url is None

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_returns_none_when_empty_string(self):
        """Test thumbnail_url returns None when image URL is empty string."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC with empty image URL",
                price_usd=500.0,
                condition="used",
                raw_listing_json={"image_url": ""},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            assert listing.thumbnail_url is None

    @pytest.mark.anyio("asyncio")
    async def test_thumbnail_url_handles_none_raw_listing_json(self):
        """Test thumbnail_url handles None raw_listing_json gracefully."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            listing = Listing(
                title="Test PC with None raw_listing_json",
                price_usd=500.0,
                condition="used",
                raw_listing_json=None,
                attributes_json={"image_url": "https://example.com/fallback.jpg"},
            )
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            # Should fall back to attributes_json
            assert listing.thumbnail_url == "https://example.com/fallback.jpg"


class TestCombinedComputedProperties:
    """Test multiple computed properties together."""

    @pytest.mark.anyio("asyncio")
    async def test_all_computed_properties_together(self):
        """Test all computed properties work together on a single listing."""
        if not AIOSQLITE_AVAILABLE:
            pytest.skip("aiosqlite is not installed; skipping async integration test")

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            cpu = Cpu(
                name="AMD Ryzen 7 5800X",
                manufacturer="AMD",
                cores=8,
                threads=16,
            )
            gpu = Gpu(
                name="AMD Radeon RX 6700 XT",
                manufacturer="AMD",
                gpu_mark=20000,
            )
            session.add_all([cpu, gpu])
            await session.flush()

            listing = Listing(
                title="Complete Test PC",
                price_usd=1200.0,
                condition="refurb",
                raw_listing_json={
                    "imageUrl": "https://example.com/complete-pc.jpg",
                    "seller_id": "12345",
                },
            )
            listing.cpu = cpu
            listing.gpu = gpu
            session.add(listing)
            await session.commit()

            await session.refresh(listing)

            # All computed properties should work
            assert listing.cpu_name == "AMD Ryzen 7 5800X"
            assert listing.gpu_name == "AMD Radeon RX 6700 XT"
            assert listing.thumbnail_url == "https://example.com/complete-pc.jpg"
