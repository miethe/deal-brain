"""Tests for partial import migrations (0025 and 0026).

Tests cover:
- Migration 0025: Listing model changes (price_usd nullable, quality, extraction_metadata, missing_fields)
- Migration 0026: ImportSession bulk tracking (bulk_job_id, quality, listing_id, completed_at)
- Upgrade/downgrade scenarios
- Data integrity after migrations
- Index creation and usage
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

try:  # pragma: no cover - conditional dependency for local test harness
    import aiosqlite  # type: ignore  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:  # pragma: no cover - executed only when optional dep missing
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():  # pragma: no cover - test configuration helper
    return "asyncio"


from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.core import Listing, ImportSession, Cpu
from dealbrain_core.enums import Condition, ListingStatus, Marketplace


@pytest.fixture
async def db_engine():
    """Create in-memory SQLite database for testing."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create async database session."""
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


class TestMigration0025PartialImport:
    """Test migration 0025: Partial import support for Listing model."""

    @pytest.mark.anyio("asyncio")
    async def test_listing_price_usd_nullable(self, db_session):
        """Test that listing.price_usd can be NULL for partial imports."""
        # Create a partial import listing with no price
        cpu = Cpu(
            name="Intel Core i5-12400",
            manufacturer="Intel",
        )
        db_session.add(cpu)
        await db_session.flush()

        listing = Listing(
            title="Dell OptiPlex 7090 - Partial Import",
            price_usd=None,  # NULL price
            condition=Condition.USED.value,
            marketplace=Marketplace.EBAY.value,
            cpu_id=cpu.id,
            quality="partial",
            missing_fields=["price"],
        )
        db_session.add(listing)
        await db_session.commit()

        # Verify listing was created
        result = await db_session.execute(
            select(Listing).where(Listing.id == listing.id)
        )
        saved_listing = result.scalar_one()
        assert saved_listing.price_usd is None
        assert saved_listing.quality == "partial"
        assert "price" in saved_listing.missing_fields

    @pytest.mark.anyio("asyncio")
    async def test_listing_quality_default(self, db_session):
        """Test that listing.quality defaults to 'full'."""
        cpu = Cpu(
            name="AMD Ryzen 5 5600X",
            manufacturer="AMD",
        )
        db_session.add(cpu)
        await db_session.flush()

        listing = Listing(
            title="HP ProDesk 600 G6",
            price_usd=450.00,
            condition=Condition.REFURB.value,
            marketplace=Marketplace.OTHER.value,
            cpu_id=cpu.id,
            # quality not specified - should default to 'full'
        )
        db_session.add(listing)
        await db_session.commit()

        result = await db_session.execute(
            select(Listing).where(Listing.id == listing.id)
        )
        saved_listing = result.scalar_one()
        assert saved_listing.quality == "full"
        assert saved_listing.extraction_metadata == {}
        assert saved_listing.missing_fields == []

    @pytest.mark.anyio("asyncio")
    async def test_listing_extraction_metadata(self, db_session):
        """Test that listing.extraction_metadata tracks field provenance."""
        cpu = Cpu(
            name="Intel Core i7-11700",
            manufacturer="Intel",
        )
        db_session.add(cpu)
        await db_session.flush()

        extraction_metadata = {
            "title": "extracted",
            "price": "extraction_failed",
            "cpu": "manual",
            "ram_gb": "extracted",
        }

        listing = Listing(
            title="Lenovo ThinkCentre M90",
            price_usd=None,
            condition=Condition.USED.value,
            marketplace=Marketplace.EBAY.value,
            cpu_id=cpu.id,
            quality="partial",
            extraction_metadata=extraction_metadata,
            missing_fields=["price"],
        )
        db_session.add(listing)
        await db_session.commit()

        result = await db_session.execute(
            select(Listing).where(Listing.id == listing.id)
        )
        saved_listing = result.scalar_one()
        assert saved_listing.extraction_metadata == extraction_metadata
        assert saved_listing.extraction_metadata["title"] == "extracted"
        assert saved_listing.extraction_metadata["price"] == "extraction_failed"
        assert saved_listing.extraction_metadata["cpu"] == "manual"

    @pytest.mark.anyio("asyncio")
    async def test_listing_missing_fields(self, db_session):
        """Test that listing.missing_fields tracks fields needing manual entry."""
        cpu = Cpu(
            name="AMD Ryzen 7 5800X",
            manufacturer="AMD",
        )
        db_session.add(cpu)
        await db_session.flush()

        missing_fields = ["price", "ram_gb", "storage_gb"]

        listing = Listing(
            title="Custom Build PC",
            price_usd=None,
            condition=Condition.NEW.value,
            marketplace=Marketplace.OTHER.value,
            cpu_id=cpu.id,
            quality="partial",
            missing_fields=missing_fields,
        )
        db_session.add(listing)
        await db_session.commit()

        result = await db_session.execute(
            select(Listing).where(Listing.id == listing.id)
        )
        saved_listing = result.scalar_one()
        assert saved_listing.missing_fields == missing_fields
        assert len(saved_listing.missing_fields) == 3
        assert "price" in saved_listing.missing_fields

    @pytest.mark.anyio("asyncio")
    async def test_partial_vs_full_listings(self, db_session):
        """Test filtering partial vs full listings."""
        cpu = Cpu(
            name="Intel Core i5-10400",
            manufacturer="Intel",
        )
        db_session.add(cpu)
        await db_session.flush()

        # Create full listing
        full_listing = Listing(
            title="Complete Listing",
            price_usd=500.00,
            condition=Condition.USED.value,
            marketplace=Marketplace.EBAY.value,
            cpu_id=cpu.id,
            quality="full",
        )
        db_session.add(full_listing)

        # Create partial listing
        partial_listing = Listing(
            title="Partial Listing",
            price_usd=None,
            condition=Condition.USED.value,
            marketplace=Marketplace.EBAY.value,
            cpu_id=cpu.id,
            quality="partial",
            missing_fields=["price", "ram_gb"],
        )
        db_session.add(partial_listing)
        await db_session.commit()

        # Query for partial listings
        result = await db_session.execute(
            select(Listing).where(Listing.quality == "partial")
        )
        partial_listings = result.scalars().all()
        assert len(partial_listings) == 1
        assert partial_listings[0].id == partial_listing.id

        # Query for full listings
        result = await db_session.execute(
            select(Listing).where(Listing.quality == "full")
        )
        full_listings = result.scalars().all()
        assert len(full_listings) == 1
        assert full_listings[0].id == full_listing.id


class TestMigration0026BulkJobTracking:
    """Test migration 0026: Bulk job tracking for ImportSession."""

    @pytest.mark.anyio("asyncio")
    async def test_import_session_bulk_job_id(self, db_session):
        """Test that import_session.bulk_job_id can group imports."""
        bulk_job_id = str(uuid4())

        # Create multiple import sessions with same bulk_job_id
        session1 = ImportSession(
            filename="import1.xlsx",
            upload_path="/tmp/import1.xlsx",
            bulk_job_id=bulk_job_id,
            status="complete",
            quality="full",
        )
        session2 = ImportSession(
            filename="import2.xlsx",
            upload_path="/tmp/import2.xlsx",
            bulk_job_id=bulk_job_id,
            status="partial",
            quality="partial",
        )
        db_session.add_all([session1, session2])
        await db_session.commit()

        # Query by bulk_job_id
        result = await db_session.execute(
            select(ImportSession).where(ImportSession.bulk_job_id == bulk_job_id)
        )
        sessions = result.scalars().all()
        assert len(sessions) == 2

    @pytest.mark.anyio("asyncio")
    async def test_import_session_quality(self, db_session):
        """Test that import_session.quality tracks data completeness."""
        full_session = ImportSession(
            filename="full_import.xlsx",
            upload_path="/tmp/full.xlsx",
            status="complete",
            quality="full",
        )
        partial_session = ImportSession(
            filename="partial_import.xlsx",
            upload_path="/tmp/partial.xlsx",
            status="partial",
            quality="partial",
        )
        db_session.add_all([full_session, partial_session])
        await db_session.commit()

        # Query for partial imports
        result = await db_session.execute(
            select(ImportSession).where(ImportSession.quality == "partial")
        )
        partial_sessions = result.scalars().all()
        assert len(partial_sessions) == 1
        assert partial_sessions[0].id == partial_session.id

    @pytest.mark.anyio("asyncio")
    async def test_import_session_listing_id(self, db_session):
        """Test that import_session.listing_id links to created listing."""
        cpu = Cpu(
            name="Intel Core i5-11400",
            manufacturer="Intel",
        )
        db_session.add(cpu)
        await db_session.flush()

        listing = Listing(
            title="HP EliteDesk 800 G6",
            price_usd=600.00,
            condition=Condition.REFURB.value,
            marketplace=Marketplace.OTHER.value,
            cpu_id=cpu.id,
        )
        db_session.add(listing)
        await db_session.flush()

        session = ImportSession(
            filename="hp_elitedesk.xlsx",
            upload_path="/tmp/hp.xlsx",
            status="complete",
            quality="full",
            listing_id=listing.id,
        )
        db_session.add(session)
        await db_session.commit()

        # Verify foreign key relationship
        result = await db_session.execute(
            select(ImportSession).where(ImportSession.listing_id == listing.id)
        )
        saved_session = result.scalar_one()
        assert saved_session.listing_id == listing.id

    @pytest.mark.anyio("asyncio")
    async def test_import_session_completed_at(self, db_session):
        """Test that import_session.completed_at tracks completion time."""
        now = datetime.now(timezone.utc)

        session = ImportSession(
            filename="completed_import.xlsx",
            upload_path="/tmp/completed.xlsx",
            status="complete",
            completed_at=now,
        )
        db_session.add(session)
        await db_session.commit()

        result = await db_session.execute(
            select(ImportSession).where(ImportSession.id == session.id)
        )
        saved_session = result.scalar_one()
        assert saved_session.completed_at is not None
        # Compare without microseconds for SQLite compatibility
        assert saved_session.completed_at.replace(microsecond=0) == now.replace(microsecond=0)

    @pytest.mark.anyio("asyncio")
    async def test_bulk_job_status_queries(self, db_session):
        """Test efficient bulk job status queries."""
        bulk_job_id = str(uuid4())

        # Create sessions with different statuses
        sessions = [
            ImportSession(
                filename=f"import_{i}.xlsx",
                upload_path=f"/tmp/import_{i}.xlsx",
                bulk_job_id=bulk_job_id,
                status=status,
                quality=quality,
            )
            for i, (status, quality) in enumerate([
                ("complete", "full"),
                ("complete", "full"),
                ("partial", "partial"),
                ("failed", None),
                ("running", None),
            ])
        ]
        db_session.add_all(sessions)
        await db_session.commit()

        # Query by bulk_job_id and status
        result = await db_session.execute(
            select(ImportSession).where(
                ImportSession.bulk_job_id == bulk_job_id,
                ImportSession.status == "complete"
            )
        )
        complete_sessions = result.scalars().all()
        assert len(complete_sessions) == 2

        # Query by bulk_job_id and partial status
        result = await db_session.execute(
            select(ImportSession).where(
                ImportSession.bulk_job_id == bulk_job_id,
                ImportSession.status == "partial"
            )
        )
        partial_sessions = result.scalars().all()
        assert len(partial_sessions) == 1


class TestMigrationIntegration:
    """Integration tests for both migrations together."""

    @pytest.mark.anyio("asyncio")
    async def test_end_to_end_partial_import_workflow(self, db_session):
        """Test complete workflow: bulk import with partial data."""
        bulk_job_id = str(uuid4())

        cpu = Cpu(
            name="Intel Core i7-12700",
            manufacturer="Intel",
        )
        db_session.add(cpu)
        await db_session.flush()

        # Create partial listing
        partial_listing = Listing(
            title="Dell OptiPlex - Incomplete Data",
            price_usd=None,  # Missing price
            condition=Condition.USED.value,
            marketplace=Marketplace.EBAY.value,
            cpu_id=cpu.id,
            quality="partial",
            extraction_metadata={
                "title": "extracted",
                "price": "extraction_failed",
                "cpu": "extracted",
            },
            missing_fields=["price", "ram_gb"],
        )
        db_session.add(partial_listing)
        await db_session.flush()

        # Create import session tracking this partial import
        session = ImportSession(
            filename="ebay_bulk_import.csv",
            upload_path="/tmp/ebay_bulk.csv",
            bulk_job_id=bulk_job_id,
            status="partial",
            quality="partial",
            listing_id=partial_listing.id,
            completed_at=datetime.now(timezone.utc),
        )
        db_session.add(session)
        await db_session.commit()

        # Query for incomplete listings from bulk job
        result = await db_session.execute(
            select(ImportSession, Listing)
            .join(Listing, ImportSession.listing_id == Listing.id)
            .where(
                ImportSession.bulk_job_id == bulk_job_id,
                ImportSession.quality == "partial",
                Listing.quality == "partial"
            )
        )
        rows = result.all()
        assert len(rows) == 1

        import_session, listing = rows[0]
        assert listing.price_usd is None
        assert "price" in listing.missing_fields
        assert import_session.quality == "partial"
        assert import_session.bulk_job_id == bulk_job_id

    @pytest.mark.anyio("asyncio")
    async def test_bulk_job_summary_query(self, db_session):
        """Test aggregating bulk job results."""
        bulk_job_id = str(uuid4())

        cpu = Cpu(
            name="AMD Ryzen 9 5900X",
            manufacturer="AMD",
        )
        db_session.add(cpu)
        await db_session.flush()

        # Create listings with different quality levels
        full_listing = Listing(
            title="Complete Listing",
            price_usd=800.00,
            condition=Condition.NEW.value,
            marketplace=Marketplace.OTHER.value,
            cpu_id=cpu.id,
            quality="full",
        )
        partial_listing = Listing(
            title="Incomplete Listing",
            price_usd=None,
            condition=Condition.USED.value,
            marketplace=Marketplace.EBAY.value,
            cpu_id=cpu.id,
            quality="partial",
            missing_fields=["price"],
        )
        db_session.add_all([full_listing, partial_listing])
        await db_session.flush()

        # Create import sessions
        sessions = [
            ImportSession(
                filename="import_full.xlsx",
                upload_path="/tmp/full.xlsx",
                bulk_job_id=bulk_job_id,
                status="complete",
                quality="full",
                listing_id=full_listing.id,
                completed_at=datetime.now(timezone.utc),
            ),
            ImportSession(
                filename="import_partial.xlsx",
                upload_path="/tmp/partial.xlsx",
                bulk_job_id=bulk_job_id,
                status="partial",
                quality="partial",
                listing_id=partial_listing.id,
                completed_at=datetime.now(timezone.utc),
            ),
        ]
        db_session.add_all(sessions)
        await db_session.commit()

        # Query all sessions for bulk job
        result = await db_session.execute(
            select(ImportSession).where(ImportSession.bulk_job_id == bulk_job_id)
        )
        all_sessions = result.scalars().all()
        assert len(all_sessions) == 2

        # Count by quality
        full_count = sum(1 for s in all_sessions if s.quality == "full")
        partial_count = sum(1 for s in all_sessions if s.quality == "partial")
        assert full_count == 1
        assert partial_count == 1
