"""E2E tests for export/import workflows (Phase 2c).

This test suite verifies end-to-end workflows:
- Export deal → Import deal → Verify data preserved
- Export collection → Import collection → Verify all items
- Share collection → Copy collection → Import copy
- Round-trip fidelity tests

Target: Critical path coverage
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.catalog import Cpu
from apps.api.dealbrain_api.models.core import Listing
from apps.api.dealbrain_api.models.sharing import Collection, CollectionItem, User
from apps.api.dealbrain_api.services.collections_service import CollectionsService
from apps.api.dealbrain_api.services.export_import import ExportImportService
from dealbrain_core.enums import Condition, ListingStatus

AIOSQLITE_AVAILABLE = True
try:
    import aiosqlite  # type: ignore
except ImportError:
    AIOSQLITE_AVAILABLE = False


@pytest.fixture
def anyio_backend():
    """Configure async backend for tests."""
    return "asyncio"


@pytest_asyncio.fixture
async def session():
    """Create an in-memory async database session for testing."""
    if not AIOSQLITE_AVAILABLE:
        pytest.skip("aiosqlite is not installed; skipping async integration test")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            yield session
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def export_service(session: AsyncSession):
    """Create ExportImportService instance."""
    return ExportImportService(session)


@pytest_asyncio.fixture
async def collection_service(session: AsyncSession):
    """Create CollectionsService instance."""
    return CollectionsService(session)


@pytest_asyncio.fixture
async def sample_user(session: AsyncSession):
    """Create sample user."""
    user = User(
        username="testuser", email="test@example.com", display_name="Test User"
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def other_user(session: AsyncSession):
    """Create another user for multi-user tests."""
    user = User(
        username="otheruser", email="other@example.com", display_name="Other User"
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def sample_listing_with_cpu(session: AsyncSession):
    """Create sample listing with CPU for testing."""
    # Create CPU
    cpu = Cpu(
        name="Intel Core i7-7700T",
        manufacturer="Intel",
        cores=4,
        threads=8,
        tdp_w=35,
        cpu_mark_multi=8542,
        cpu_mark_single=2234,
    )
    session.add(cpu)
    await session.flush()

    # Create listing
    listing = Listing(
        title="Dell OptiPlex 7050 Micro",
        listing_url="https://example.com/listing/1",
        seller="TechDeals Inc",
        price_usd=299.99,
        adjusted_price_usd=289.99,
        condition=Condition.REFURB.value,
        status=ListingStatus.ACTIVE.value,
        device_model="OptiPlex 7050 Micro",
        notes="Excellent condition",
        manufacturer="Dell",
        series="OptiPlex",
        model_number="7050",
        form_factor="Micro",
        cpu_id=cpu.id,
    )
    session.add(listing)
    await session.flush()
    await session.refresh(listing)
    return listing


# ==================== Deal Export/Import E2E Tests ====================


@pytest.mark.asyncio
class TestDealExportImportE2E:
    """End-to-end tests for deal export/import workflow."""

    async def test_export_import_deal_round_trip(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_listing_with_cpu: Listing,
    ):
        """Test exporting and importing a deal preserves all data."""
        # 1. Export listing
        export = await export_service.export_listing_as_json(
            listing_id=sample_listing_with_cpu.id
        )

        # 2. Verify export is valid JSON
        json_str = export.model_dump_json(indent=2)
        export_data = json.loads(json_str)

        assert export_data["deal_brain_export"]["version"] == "1.0.0"
        assert export_data["data"]["listing"]["title"] == "Dell OptiPlex 7050 Micro"

        # 3. Import listing
        preview_id = await export_service.import_listing_from_json(export_data)

        # 4. Confirm import
        imported_listing = await export_service.confirm_import_listing(
            preview_id=preview_id, merge_strategy="create_new"
        )

        # 5. Verify imported listing matches original
        assert imported_listing is not None
        assert imported_listing.title == sample_listing_with_cpu.title
        assert imported_listing.price_usd == sample_listing_with_cpu.price_usd
        assert imported_listing.seller == sample_listing_with_cpu.seller
        assert imported_listing.manufacturer == sample_listing_with_cpu.manufacturer

    async def test_export_import_preserves_cpu_relationship(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_listing_with_cpu: Listing,
    ):
        """Test that CPU relationship is preserved during export/import."""
        # Export
        export = await export_service.export_listing_as_json(
            listing_id=sample_listing_with_cpu.id
        )

        # Verify CPU in export
        assert export.data.performance.cpu is not None
        assert export.data.performance.cpu.name == "Intel Core i7-7700T"

        # Import
        json_data = json.loads(export.model_dump_json())
        preview_id = await export_service.import_listing_from_json(json_data)
        imported = await export_service.confirm_import_listing(
            preview_id=preview_id, merge_strategy="create_new"
        )

        # Verify CPU relationship recreated
        await session.refresh(imported)
        assert imported.cpu is not None
        assert imported.cpu.name == "Intel Core i7-7700T"

    async def test_export_import_preserves_valuation(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_listing_with_cpu: Listing,
    ):
        """Test that valuation data is preserved during export/import."""
        # Export
        export = await export_service.export_listing_as_json(
            listing_id=sample_listing_with_cpu.id
        )

        # Verify valuation in export
        assert export.data.valuation is not None
        assert export.data.valuation.base_price_usd == 299.99
        assert export.data.valuation.adjusted_price_usd == 289.99

        # Import
        json_data = json.loads(export.model_dump_json())
        preview_id = await export_service.import_listing_from_json(json_data)
        imported = await export_service.confirm_import_listing(
            preview_id=preview_id, merge_strategy="create_new"
        )

        # Verify valuation preserved
        assert imported.price_usd == 299.99
        assert imported.adjusted_price_usd == 289.99

    async def test_import_detects_duplicates(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_listing_with_cpu: Listing,
    ):
        """Test that import detects duplicate listings."""
        # Export
        export = await export_service.export_listing_as_json(
            listing_id=sample_listing_with_cpu.id
        )

        # Import (this should detect the original as a duplicate)
        json_data = json.loads(export.model_dump_json())
        preview_id = await export_service.import_listing_from_json(json_data)

        # Get preview from cache to check duplicates
        from apps.api.dealbrain_api.services.export_import import _preview_cache

        preview = _preview_cache.get(preview_id)

        # Verify duplicates detected
        assert preview is not None
        assert len(preview.duplicates) > 0

        # Clean up preview
        _preview_cache.remove(preview_id)


# ==================== Collection Export/Import E2E Tests ====================


@pytest.mark.asyncio
class TestCollectionExportImportE2E:
    """End-to-end tests for collection export/import workflow."""

    async def test_export_import_collection_round_trip(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_user: User,
        sample_listing_with_cpu: Listing,
    ):
        """Test exporting and importing a collection preserves all data."""
        # 1. Create collection with items
        collection = Collection(
            user_id=sample_user.id,
            name="Gaming Builds",
            description="Best gaming PC deals",
            visibility="public",
        )
        session.add(collection)
        await session.flush()

        item = CollectionItem(
            collection_id=collection.id,
            listing_id=sample_listing_with_cpu.id,
            status="shortlisted",
            notes="Top pick",
            position=0,
        )
        session.add(item)
        await session.commit()
        await session.refresh(collection)

        # 2. Export collection
        export = await export_service.export_collection_as_json(
            collection_id=collection.id, user_id=sample_user.id
        )

        # 3. Verify export is valid
        json_str = export.model_dump_json(indent=2)
        export_data = json.loads(json_str)

        assert export_data["deal_brain_export"]["type"] == "collection"
        assert export_data["data"]["collection"]["name"] == "Gaming Builds"
        assert len(export_data["data"]["items"]) == 1

        # 4. Import collection
        preview_id = await export_service.import_collection_from_json(
            export_data, user_id=sample_user.id
        )

        # 5. Confirm import
        imported_collection = await export_service.confirm_import_collection(
            preview_id=preview_id,
            merge_strategy="create_new",
            user_id=sample_user.id,
        )

        # 6. Verify imported collection matches original
        assert imported_collection is not None
        assert imported_collection.name == collection.name
        assert imported_collection.description == collection.description

    async def test_export_import_collection_preserves_items(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_user: User,
        sample_listing_with_cpu: Listing,
    ):
        """Test that collection items are preserved during export/import."""
        # Create collection with multiple items
        collection = Collection(
            user_id=sample_user.id,
            name="Test Collection",
            visibility="public",
        )
        session.add(collection)
        await session.flush()

        # Add multiple listings
        for i in range(3):
            listing = Listing(
                title=f"Test Listing {i}",
                listing_url=f"https://example.com/{i}",
                price_usd=100.0 * (i + 1),
                condition=Condition.NEW.value,
                status=ListingStatus.ACTIVE.value,
            )
            session.add(listing)
            await session.flush()

            item = CollectionItem(
                collection_id=collection.id,
                listing_id=listing.id,
                status="undecided" if i == 0 else "shortlisted",
                notes=f"Note {i}",
                position=i,
            )
            session.add(item)

        await session.commit()
        await session.refresh(collection)

        # Export
        export = await export_service.export_collection_as_json(
            collection_id=collection.id, user_id=sample_user.id
        )

        # Verify all items in export
        assert len(export.data.items) == 3

        # Import
        json_data = json.loads(export.model_dump_json())
        preview_id = await export_service.import_collection_from_json(
            json_data, user_id=sample_user.id
        )
        imported = await export_service.confirm_import_collection(
            preview_id=preview_id,
            merge_strategy="create_new",
            user_id=sample_user.id,
        )

        # Verify all items imported
        await session.refresh(imported)
        assert len(imported.items) == 3


# ==================== Share → Copy → Export E2E Tests ====================


@pytest.mark.asyncio
class TestShareCopyExportE2E:
    """End-to-end tests for share, copy, and export workflows."""

    async def test_share_copy_export_workflow(
        self,
        collection_service: CollectionsService,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_user: User,
        other_user: User,
        sample_listing_with_cpu: Listing,
    ):
        """Test full workflow: create → share → copy → export."""
        # 1. Create public collection
        collection = await collection_service.create_collection(
            user_id=sample_user.id,
            name="Shared Gaming Builds",
            description="Public collection",
            visibility="private",
        )

        # Add item
        await collection_service.add_item_to_collection(
            collection_id=collection.id,
            listing_id=sample_listing_with_cpu.id,
            user_id=sample_user.id,
            status="shortlisted",
        )

        # 2. Update visibility to public
        await collection_service.update_visibility(
            collection_id=collection.id,
            new_visibility="public",
            user_id=sample_user.id,
        )

        # 3. Generate share token
        token = await collection_service.generate_share_token(
            collection_id=collection.id,
            user_id=sample_user.id,
        )

        # 4. Validate share token
        shared_collection = await collection_service.validate_share_token(
            token=token.token
        )

        assert shared_collection is not None
        assert shared_collection.id == collection.id

        # 5. Copy collection to other user's workspace
        copied = await collection_service.copy_collection(
            source_collection_id=collection.id,
            user_id=other_user.id,
            new_name="My Copy of Gaming Builds",
        )

        # Verify copy
        assert copied is not None
        assert copied.user_id == other_user.id
        assert copied.name == "My Copy of Gaming Builds"
        assert copied.visibility == "private"  # Always private

        # 6. Export the copied collection
        export = await export_service.export_collection_as_json(
            collection_id=copied.id, user_id=other_user.id
        )

        # Verify export
        assert export.data.collection.name == "My Copy of Gaming Builds"


# ==================== Import Validation E2E Tests ====================


@pytest.mark.asyncio
class TestImportValidationE2E:
    """End-to-end tests for import validation."""

    async def test_import_rejects_invalid_schema_version(
        self,
        export_service: ExportImportService,
    ):
        """Test that import rejects incompatible schema versions."""
        # Create export with wrong version
        invalid_export = {
            "deal_brain_export": {
                "version": "2.0.0",  # Invalid version
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {
                "listing": {
                    "id": 1,
                    "title": "Test",
                    "price_usd": 100.0,
                    "condition": "used",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        }

        # Verify import fails
        with pytest.raises(ValueError, match="Incompatible schema version"):
            await export_service.import_listing_from_json(invalid_export)

    async def test_import_rejects_malformed_data(
        self,
        export_service: ExportImportService,
    ):
        """Test that import rejects malformed data."""
        # Create export with missing required fields
        malformed_export = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {
                "listing": {
                    "id": 1,
                    "title": "Test",
                    # Missing required fields like price_usd, condition, etc.
                }
            },
        }

        # Verify import fails
        with pytest.raises(ValueError, match="Invalid export schema"):
            await export_service.import_listing_from_json(malformed_export)


# ==================== Performance E2E Tests ====================


@pytest.mark.asyncio
class TestExportImportPerformanceE2E:
    """End-to-end performance tests for export/import."""

    async def test_export_large_collection(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test exporting collection with many items."""
        # Create collection
        collection = Collection(
            user_id=sample_user.id,
            name="Large Collection",
            visibility="public",
        )
        session.add(collection)
        await session.flush()

        # Add 50 listings
        for i in range(50):
            listing = Listing(
                title=f"Listing {i}",
                listing_url=f"https://example.com/{i}",
                price_usd=100.0,
                condition=Condition.NEW.value,
                status=ListingStatus.ACTIVE.value,
            )
            session.add(listing)
            await session.flush()

            item = CollectionItem(
                collection_id=collection.id,
                listing_id=listing.id,
                status="undecided",
                position=i,
            )
            session.add(item)

        await session.commit()

        # Export collection (should complete without timeout)
        export = await export_service.export_collection_as_json(
            collection_id=collection.id, user_id=sample_user.id
        )

        # Verify all items exported
        assert len(export.data.items) == 50

    async def test_import_with_many_duplicates(
        self,
        export_service: ExportImportService,
        session: AsyncSession,
    ):
        """Test import duplicate detection with many existing listings."""
        # Create 100 existing listings
        for i in range(100):
            listing = Listing(
                title=f"Existing Listing {i}",
                listing_url=f"https://example.com/existing/{i}",
                price_usd=100.0 * (i + 1),
                condition=Condition.NEW.value,
                status=ListingStatus.ACTIVE.value,
            )
            session.add(listing)

        await session.commit()

        # Create export to import
        export_data = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {
                "listing": {
                    "id": 1,
                    "title": "Existing Listing 50",  # Should match existing
                    "listing_url": "https://example.com/existing/50",
                    "price_usd": 5100.0,
                    "condition": "new",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        }

        # Import (should detect duplicates efficiently)
        preview_id = await export_service.import_listing_from_json(export_data)

        # Verify preview created
        assert preview_id is not None
