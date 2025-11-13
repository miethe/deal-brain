"""Tests for catalog usage count service methods."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import Base first
from apps.api.dealbrain_api.db import Base

# Import all models to ensure they're registered with Base.metadata
from apps.api.dealbrain_api.models.core import (
    Cpu,
    Gpu,
    Listing,
    PortsProfile,
    Profile,
    RamSpec,
    StorageProfile,
)
from apps.api.dealbrain_api.services.catalog import (
    get_cpu_usage_count,
    get_gpu_usage_count,
    get_ports_profile_usage_count,
    get_ram_spec_usage_count,
    get_scoring_profile_usage_count,
    get_storage_profile_usage_count,
)

try:
    import aiosqlite  # type: ignore  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def session():
    """Create an in-memory async database session for testing."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
class TestGetCpuUsageCount:
    """Test get_cpu_usage_count function."""

    async def test_count_zero_when_no_listings(self, session: AsyncSession):
        """Test count is 0 when CPU has no listings."""
        cpu = Cpu(name="Intel Core i7-12700K", manufacturer="Intel")
        session.add(cpu)
        await session.commit()

        count = await get_cpu_usage_count(session, cpu.id)
        assert count == 0

    async def test_count_single_listing(self, session: AsyncSession):
        """Test count is 1 when CPU has one listing."""
        cpu = Cpu(name="Intel Core i7-12700K", manufacturer="Intel")
        session.add(cpu)
        await session.flush()

        listing = Listing(
            title="Test PC",
            price_usd=500,
            condition="used",
            cpu_id=cpu.id,
        )
        session.add(listing)
        await session.commit()

        count = await get_cpu_usage_count(session, cpu.id)
        assert count == 1

    async def test_count_multiple_listings(self, session: AsyncSession):
        """Test count with multiple listings using same CPU."""
        cpu = Cpu(name="Intel Core i7-12700K", manufacturer="Intel")
        session.add(cpu)
        await session.flush()

        for i in range(5):
            listing = Listing(
                title=f"Test PC {i}",
                price_usd=500 + i * 100,
                condition="used",
                cpu_id=cpu.id,
            )
            session.add(listing)
        await session.commit()

        count = await get_cpu_usage_count(session, cpu.id)
        assert count == 5

    async def test_count_nonexistent_cpu(self, session: AsyncSession):
        """Test count is 0 for non-existent CPU ID."""
        count = await get_cpu_usage_count(session, 99999)
        assert count == 0


@pytest.mark.asyncio
class TestGetGpuUsageCount:
    """Test get_gpu_usage_count function."""

    async def test_count_zero_when_no_listings(self, session: AsyncSession):
        """Test count is 0 when GPU has no listings."""
        gpu = Gpu(name="NVIDIA RTX 3080", manufacturer="NVIDIA")
        session.add(gpu)
        await session.commit()

        count = await get_gpu_usage_count(session, gpu.id)
        assert count == 0

    async def test_count_single_listing(self, session: AsyncSession):
        """Test count is 1 when GPU has one listing."""
        gpu = Gpu(name="NVIDIA RTX 3080", manufacturer="NVIDIA")
        session.add(gpu)
        await session.flush()

        listing = Listing(
            title="Test PC",
            price_usd=1200,
            condition="used",
            gpu_id=gpu.id,
        )
        session.add(listing)
        await session.commit()

        count = await get_gpu_usage_count(session, gpu.id)
        assert count == 1

    async def test_count_multiple_listings(self, session: AsyncSession):
        """Test count with multiple listings using same GPU."""
        gpu = Gpu(name="NVIDIA RTX 3080", manufacturer="NVIDIA")
        session.add(gpu)
        await session.flush()

        for i in range(3):
            listing = Listing(
                title=f"Gaming PC {i}",
                price_usd=1200 + i * 50,
                condition="used",
                gpu_id=gpu.id,
            )
            session.add(listing)
        await session.commit()

        count = await get_gpu_usage_count(session, gpu.id)
        assert count == 3


@pytest.mark.asyncio
class TestGetRamSpecUsageCount:
    """Test get_ram_spec_usage_count function."""

    async def test_count_zero_when_no_listings(self, session: AsyncSession):
        """Test count is 0 when RAM spec has no listings."""
        from dealbrain_core.enums import RamGeneration

        ram_spec = RamSpec(
            label="DDR4-3200 16GB (2x8GB)",
            ddr_generation=RamGeneration.DDR4,
            speed_mhz=3200,
            module_count=2,
            capacity_per_module_gb=8,
            total_capacity_gb=16,
        )
        session.add(ram_spec)
        await session.commit()

        count = await get_ram_spec_usage_count(session, ram_spec.id)
        assert count == 0

    async def test_count_single_listing(self, session: AsyncSession):
        """Test count is 1 when RAM spec is used by one listing."""
        from dealbrain_core.enums import RamGeneration

        ram_spec = RamSpec(
            label="DDR4-3200 16GB (2x8GB)",
            ddr_generation=RamGeneration.DDR4,
            speed_mhz=3200,
            module_count=2,
            capacity_per_module_gb=8,
            total_capacity_gb=16,
        )
        session.add(ram_spec)
        await session.flush()

        listing = Listing(
            title="Test PC",
            price_usd=700,
            condition="used",
            ram_spec_id=ram_spec.id,
        )
        session.add(listing)
        await session.commit()

        count = await get_ram_spec_usage_count(session, ram_spec.id)
        assert count == 1

    async def test_count_multiple_listings(self, session: AsyncSession):
        """Test count with multiple listings using same RAM spec."""
        from dealbrain_core.enums import RamGeneration

        ram_spec = RamSpec(
            label="DDR4-3200 32GB (2x16GB)",
            ddr_generation=RamGeneration.DDR4,
            speed_mhz=3200,
            module_count=2,
            capacity_per_module_gb=16,
            total_capacity_gb=32,
        )
        session.add(ram_spec)
        await session.flush()

        for i in range(4):
            listing = Listing(
                title=f"Workstation {i}",
                price_usd=900 + i * 100,
                condition="used",
                ram_spec_id=ram_spec.id,
            )
            session.add(listing)
        await session.commit()

        count = await get_ram_spec_usage_count(session, ram_spec.id)
        assert count == 4


@pytest.mark.asyncio
class TestGetStorageProfileUsageCount:
    """Test get_storage_profile_usage_count function."""

    async def test_count_zero_when_no_listings(self, session: AsyncSession):
        """Test count is 0 when storage profile has no listings."""
        from dealbrain_core.enums import StorageMedium

        storage = StorageProfile(
            label="512GB NVMe SSD",
            medium=StorageMedium.NVME,
            interface="NVMe",
            form_factor="M.2",
            capacity_gb=512,
            performance_tier="high",
        )
        session.add(storage)
        await session.commit()

        count = await get_storage_profile_usage_count(session, storage.id)
        assert count == 0

    async def test_count_primary_storage_only(self, session: AsyncSession):
        """Test count when storage is used as primary storage."""
        from dealbrain_core.enums import StorageMedium

        storage = StorageProfile(
            label="512GB NVMe SSD",
            medium=StorageMedium.NVME,
            interface="NVMe",
            form_factor="M.2",
            capacity_gb=512,
            performance_tier="high",
        )
        session.add(storage)
        await session.flush()

        listing = Listing(
            title="Test PC",
            price_usd=800,
            condition="used",
            primary_storage_profile_id=storage.id,
        )
        session.add(listing)
        await session.commit()

        count = await get_storage_profile_usage_count(session, storage.id)
        assert count == 1

    async def test_count_secondary_storage_only(self, session: AsyncSession):
        """Test count when storage is used as secondary storage."""
        from dealbrain_core.enums import StorageMedium

        storage = StorageProfile(
            label="2TB HDD",
            medium=StorageMedium.HDD,
            interface="SATA",
            form_factor='3.5"',
            capacity_gb=2000,
            performance_tier="standard",
        )
        session.add(storage)
        await session.flush()

        listing = Listing(
            title="Test PC",
            price_usd=600,
            condition="used",
            secondary_storage_profile_id=storage.id,
        )
        session.add(listing)
        await session.commit()

        count = await get_storage_profile_usage_count(session, storage.id)
        assert count == 1

    async def test_count_both_primary_and_secondary(self, session: AsyncSession):
        """Test count when storage is used as both primary and secondary."""
        from dealbrain_core.enums import StorageMedium

        storage = StorageProfile(
            label="512GB SSD",
            medium=StorageMedium.SATA_SSD,
            interface="SATA",
            form_factor='2.5"',
            capacity_gb=512,
            performance_tier="standard",
        )
        session.add(storage)
        await session.flush()

        # Listing 1: primary storage
        listing1 = Listing(
            title="PC 1",
            price_usd=700,
            condition="used",
            primary_storage_profile_id=storage.id,
        )
        session.add(listing1)

        # Listing 2: secondary storage
        listing2 = Listing(
            title="PC 2",
            price_usd=750,
            condition="used",
            secondary_storage_profile_id=storage.id,
        )
        session.add(listing2)

        # Listing 3: both primary and secondary (edge case)
        listing3 = Listing(
            title="PC 3",
            price_usd=800,
            condition="used",
            primary_storage_profile_id=storage.id,
            secondary_storage_profile_id=storage.id,
        )
        session.add(listing3)

        await session.commit()

        # Should count 3 listings (listing3 counted once even though it uses it twice)
        count = await get_storage_profile_usage_count(session, storage.id)
        assert count == 3


@pytest.mark.asyncio
class TestGetPortsProfileUsageCount:
    """Test get_ports_profile_usage_count function."""

    async def test_count_zero_when_no_listings(self, session: AsyncSession):
        """Test count is 0 when ports profile has no listings."""
        profile = PortsProfile(name="Standard Ports")
        session.add(profile)
        await session.commit()

        count = await get_ports_profile_usage_count(session, profile.id)
        assert count == 0

    async def test_count_single_listing(self, session: AsyncSession):
        """Test count is 1 when ports profile is used by one listing."""
        profile = PortsProfile(name="Gaming Ports")
        session.add(profile)
        await session.flush()

        listing = Listing(
            title="Gaming PC",
            price_usd=1500,
            condition="used",
            ports_profile_id=profile.id,
        )
        session.add(listing)
        await session.commit()

        count = await get_ports_profile_usage_count(session, profile.id)
        assert count == 1

    async def test_count_multiple_listings(self, session: AsyncSession):
        """Test count with multiple listings using same ports profile."""
        profile = PortsProfile(name="Office Ports")
        session.add(profile)
        await session.flush()

        for i in range(7):
            listing = Listing(
                title=f"Office PC {i}",
                price_usd=500 + i * 50,
                condition="used",
                ports_profile_id=profile.id,
            )
            session.add(listing)
        await session.commit()

        count = await get_ports_profile_usage_count(session, profile.id)
        assert count == 7


@pytest.mark.asyncio
class TestGetScoringProfileUsageCount:
    """Test get_scoring_profile_usage_count function."""

    async def test_count_zero_when_no_listings(self, session: AsyncSession):
        """Test count is 0 when scoring profile has no listings."""
        profile = Profile(name="Gaming Profile", weights_json={}, rule_group_weights={})
        session.add(profile)
        await session.commit()

        count = await get_scoring_profile_usage_count(session, profile.id)
        assert count == 0

    async def test_count_single_listing(self, session: AsyncSession):
        """Test count is 1 when scoring profile is used by one listing."""
        profile = Profile(name="Workstation Profile", weights_json={}, rule_group_weights={})
        session.add(profile)
        await session.flush()

        listing = Listing(
            title="Workstation PC",
            price_usd=2000,
            condition="new",
            active_profile_id=profile.id,
        )
        session.add(listing)
        await session.commit()

        count = await get_scoring_profile_usage_count(session, profile.id)
        assert count == 1

    async def test_count_multiple_listings(self, session: AsyncSession):
        """Test count with multiple listings using same scoring profile."""
        profile = Profile(name="Budget Profile", weights_json={}, rule_group_weights={})
        session.add(profile)
        await session.flush()

        for i in range(10):
            listing = Listing(
                title=f"Budget PC {i}",
                price_usd=400 + i * 30,
                condition="refurbished",
                active_profile_id=profile.id,
            )
            session.add(listing)
        await session.commit()

        count = await get_scoring_profile_usage_count(session, profile.id)
        assert count == 10


@pytest.mark.asyncio
class TestPerformance:
    """Test query performance of usage count methods."""

    async def test_count_performance_large_dataset(self, session: AsyncSession):
        """Test that counts complete quickly even with many listings."""
        import time

        # Create CPU with many listings
        cpu = Cpu(name="Intel Core i5-12400", manufacturer="Intel")
        session.add(cpu)
        await session.flush()

        # Add 100 listings
        for i in range(100):
            listing = Listing(
                title=f"PC {i}",
                price_usd=500,
                condition="used",
                cpu_id=cpu.id,
            )
            session.add(listing)
        await session.commit()

        # Measure query time
        start = time.time()
        count = await get_cpu_usage_count(session, cpu.id)
        elapsed = time.time() - start

        assert count == 100
        # Should complete well under 500ms even with 100 listings
        # In practice, this should be < 10ms for in-memory SQLite
        assert elapsed < 0.5, f"Query took {elapsed:.3f}s, expected < 500ms"
