"""Tests for ExportImportService (Phase 2c).

This test suite verifies:
- Deal export with all relationships
- Deal import with validation and duplicate detection
- Collection export with items
- Collection import with merge strategies
- Schema version validation
- Preview system with TTL
- Duplicate detection algorithms

Target: >85% code coverage
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.catalog import Cpu, Gpu, RamSpec, StorageProfile
from apps.api.dealbrain_api.models.core import Listing
from apps.api.dealbrain_api.models.ports import PortsProfile
from apps.api.dealbrain_api.models.sharing import Collection, CollectionItem, User
from apps.api.dealbrain_api.services.export_import import (
    ExportImportService,
    PreviewCache,
)
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
async def service(session: AsyncSession):
    """Create ExportImportService instance with test session."""
    return ExportImportService(session)


@pytest_asyncio.fixture
async def sample_user(session: AsyncSession):
    """Create sample user for testing."""
    user = User(
        username="testuser", email="test@example.com", display_name="Test User"
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def sample_cpu(session: AsyncSession):
    """Create sample CPU for testing."""
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
    return cpu


@pytest_asyncio.fixture
async def sample_gpu(session: AsyncSession):
    """Create sample GPU for testing."""
    gpu = Gpu(
        name="Intel HD Graphics 630",
        manufacturer="Intel",
        gpu_mark=1153,
    )
    session.add(gpu)
    await session.flush()
    return gpu


@pytest_asyncio.fixture
async def sample_listing(session: AsyncSession, sample_cpu: Cpu):
    """Create sample listing with relationships for testing."""
    listing = Listing(
        title="Dell OptiPlex 7050 Micro",
        listing_url="https://example.com/listing",
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
        cpu_id=sample_cpu.id,
    )
    session.add(listing)
    await session.flush()
    await session.refresh(listing)
    return listing


@pytest_asyncio.fixture
async def sample_collection(
    session: AsyncSession, sample_user: User, sample_listing: Listing
):
    """Create sample collection with items for testing."""
    collection = Collection(
        user_id=sample_user.id,
        name="Test Collection",
        description="Test description",
        visibility="public",
    )
    session.add(collection)
    await session.flush()

    item = CollectionItem(
        collection_id=collection.id,
        listing_id=sample_listing.id,
        status="shortlisted",
        notes="Great deal",
        position=0,
    )
    session.add(item)
    await session.flush()
    await session.refresh(collection)
    return collection


# ==================== Deal Export Tests ====================


@pytest.mark.asyncio
class TestExportListing:
    """Test ExportImportService.export_listing_as_json() method."""

    async def test_export_listing_minimal(
        self,
        service: ExportImportService,
        session: AsyncSession,
    ):
        """Test exporting listing with minimal fields."""
        # Create minimal listing
        listing = Listing(
            title="Test PC",
            listing_url="https://example.com",
            price_usd=100.0,
            condition=Condition.USED.value,
            status=ListingStatus.ACTIVE.value,
        )
        session.add(listing)
        await session.flush()

        # Export listing
        export = await service.export_listing_as_json(listing_id=listing.id)

        # Verify export metadata
        assert export.deal_brain_export.version == "1.0.0"
        assert export.deal_brain_export.type == "deal"

        # Verify listing data
        assert export.data.listing.id == listing.id
        assert export.data.listing.title == "Test PC"
        assert export.data.listing.price_usd == 100.0

    async def test_export_listing_with_cpu(
        self,
        service: ExportImportService,
        sample_listing: Listing,
    ):
        """Test exporting listing with CPU relationship."""
        export = await service.export_listing_as_json(listing_id=sample_listing.id)

        # Verify CPU data exported
        assert export.data.performance is not None
        assert export.data.performance.cpu is not None
        assert export.data.performance.cpu.name == "Intel Core i7-7700T"
        assert export.data.performance.cpu.cores == 4

    async def test_export_listing_with_valuation(
        self,
        service: ExportImportService,
        sample_listing: Listing,
    ):
        """Test exporting listing with valuation data."""
        export = await service.export_listing_as_json(listing_id=sample_listing.id)

        # Verify valuation data
        assert export.data.valuation is not None
        assert export.data.valuation.base_price_usd == 299.99
        assert export.data.valuation.adjusted_price_usd == 289.99

    async def test_export_listing_with_metadata(
        self,
        service: ExportImportService,
        sample_listing: Listing,
    ):
        """Test exporting listing with product metadata."""
        export = await service.export_listing_as_json(listing_id=sample_listing.id)

        # Verify metadata
        assert export.data.metadata is not None
        assert export.data.metadata.manufacturer == "Dell"
        assert export.data.metadata.series == "OptiPlex"
        assert export.data.metadata.model_number == "7050"

    async def test_export_listing_not_found(
        self,
        service: ExportImportService,
    ):
        """Test exporting non-existent listing raises error."""
        with pytest.raises(ValueError, match="not found"):
            await service.export_listing_as_json(listing_id=99999)

    async def test_export_listing_serializable(
        self,
        service: ExportImportService,
        sample_listing: Listing,
    ):
        """Test that exported listing can be serialized to JSON."""
        export = await service.export_listing_as_json(listing_id=sample_listing.id)

        # Verify can serialize to JSON
        json_str = export.model_dump_json(indent=2)
        assert json_str is not None

        # Verify can deserialize back
        data = json.loads(json_str)
        assert data["deal_brain_export"]["version"] == "1.0.0"


# ==================== Deal Import Tests ====================


@pytest.mark.asyncio
class TestImportListing:
    """Test ExportImportService.import_listing_from_json() method."""

    async def test_import_listing_creates_preview(
        self,
        service: ExportImportService,
    ):
        """Test that import creates preview for confirmation."""
        # Create valid export JSON
        export_json = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {
                "listing": {
                    "id": 1,
                    "title": "Test PC",
                    "price_usd": 100.0,
                    "condition": "used",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        }

        # Import listing
        preview_id = await service.import_listing_from_json(export_json)

        # Verify preview ID returned
        assert preview_id is not None
        assert len(preview_id) > 0

    async def test_import_listing_invalid_schema(
        self,
        service: ExportImportService,
    ):
        """Test importing with invalid schema raises error."""
        # Invalid export JSON (missing required fields)
        invalid_json = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {
                "listing": {
                    "title": "Test PC",
                    # Missing required fields
                }
            },
        }

        with pytest.raises(ValueError, match="Invalid export schema"):
            await service.import_listing_from_json(invalid_json)

    async def test_import_listing_wrong_version(
        self,
        service: ExportImportService,
    ):
        """Test importing with wrong schema version raises error."""
        invalid_version = {
            "deal_brain_export": {
                "version": "2.0.0",  # Wrong version
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {"listing": {}},
        }

        with pytest.raises(ValueError, match="Incompatible schema version"):
            await service.import_listing_from_json(invalid_version)

    async def test_confirm_import_create_new(
        self,
        service: ExportImportService,
        session: AsyncSession,
    ):
        """Test confirming import with create_new strategy."""
        # Create and import listing
        export_json = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {
                "listing": {
                    "id": 1,
                    "title": "Imported PC",
                    "price_usd": 100.0,
                    "condition": "used",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        }

        preview_id = await service.import_listing_from_json(export_json)

        # Confirm import
        listing = await service.confirm_import_listing(
            preview_id=preview_id, merge_strategy="create_new"
        )

        # Verify listing created
        assert listing is not None
        assert listing.id is not None
        assert listing.title == "Imported PC"
        assert listing.price_usd == 100.0

    async def test_confirm_import_expired_preview(
        self,
        service: ExportImportService,
    ):
        """Test confirming import with expired preview raises error."""
        with pytest.raises(ValueError, match="Preview not found or expired"):
            await service.confirm_import_listing(
                preview_id="invalid-preview-id", merge_strategy="create_new"
            )

    async def test_confirm_import_skip_strategy(
        self,
        service: ExportImportService,
    ):
        """Test confirming import with skip strategy raises error."""
        # Create preview
        export_json = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            },
            "data": {
                "listing": {
                    "id": 1,
                    "title": "Test PC",
                    "price_usd": 100.0,
                    "condition": "used",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        }

        preview_id = await service.import_listing_from_json(export_json)

        # Try to confirm with skip strategy
        with pytest.raises(ValueError, match="Import skipped"):
            await service.confirm_import_listing(
                preview_id=preview_id, merge_strategy="skip"
            )


# ==================== Collection Export Tests ====================


@pytest.mark.asyncio
class TestExportCollection:
    """Test ExportImportService.export_collection_as_json() method."""

    async def test_export_collection_with_items(
        self,
        service: ExportImportService,
        sample_collection: Collection,
        sample_user: User,
    ):
        """Test exporting collection with items."""
        export = await service.export_collection_as_json(
            collection_id=sample_collection.id, user_id=sample_user.id
        )

        # Verify export metadata
        assert export.deal_brain_export.version == "1.0.0"
        assert export.deal_brain_export.type == "collection"

        # Verify collection data
        assert export.data.collection.id == sample_collection.id
        assert export.data.collection.name == "Test Collection"

        # Verify items
        assert len(export.data.items) == 1
        assert export.data.items[0].status == "shortlisted"
        assert export.data.items[0].notes == "Great deal"

    async def test_export_collection_unauthorized(
        self,
        service: ExportImportService,
        sample_collection: Collection,
    ):
        """Test exporting collection owned by another user raises error."""
        with pytest.raises(ValueError, match="not found or access denied"):
            await service.export_collection_as_json(
                collection_id=sample_collection.id, user_id=99999
            )

    async def test_export_collection_serializable(
        self,
        service: ExportImportService,
        sample_collection: Collection,
        sample_user: User,
    ):
        """Test that exported collection can be serialized to JSON."""
        export = await service.export_collection_as_json(
            collection_id=sample_collection.id, user_id=sample_user.id
        )

        # Verify can serialize
        json_str = export.model_dump_json(indent=2)
        assert json_str is not None

        # Verify can deserialize
        data = json.loads(json_str)
        assert data["deal_brain_export"]["type"] == "collection"


# ==================== Collection Import Tests ====================


@pytest.mark.asyncio
class TestImportCollection:
    """Test ExportImportService.import_collection_from_json() method."""

    async def test_import_collection_creates_preview(
        self,
        service: ExportImportService,
        sample_user: User,
    ):
        """Test that collection import creates preview."""
        # Create valid export JSON
        export_json = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "collection",
            },
            "data": {
                "collection": {
                    "id": 1,
                    "name": "Test Collection",
                    "visibility": "private",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
                "items": [],
            },
        }

        # Import collection
        preview_id = await service.import_collection_from_json(
            export_json, user_id=sample_user.id
        )

        # Verify preview ID returned
        assert preview_id is not None
        assert len(preview_id) > 0


# ==================== Duplicate Detection Tests ====================


@pytest.mark.asyncio
class TestDuplicateDetection:
    """Test duplicate detection algorithms."""

    async def test_find_duplicate_listings_exact_match(
        self,
        service: ExportImportService,
        session: AsyncSession,
    ):
        """Test finding duplicate listings by exact title and seller."""
        # Create existing listing
        existing = Listing(
            title="Dell OptiPlex 7050",
            seller="TechDeals Inc",
            listing_url="https://example.com",
            price_usd=100.0,
            condition=Condition.USED.value,
            status=ListingStatus.ACTIVE.value,
        )
        session.add(existing)
        await session.flush()

        # Create export with same title and seller
        from apps.api.dealbrain_api.schemas.export_import import ListingExport

        listing_export = ListingExport(
            id=1,
            title="Dell OptiPlex 7050",
            seller="TechDeals Inc",
            price_usd=100.0,
            condition=Condition.USED,
            status=ListingStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Find duplicates
        duplicates = await service._find_duplicate_listings(listing_export)

        # Should find exact match
        assert len(duplicates) > 0
        assert duplicates[0].entity_id == existing.id
        assert duplicates[0].match_score == 1.0

    async def test_find_duplicate_listings_url_match(
        self,
        service: ExportImportService,
        session: AsyncSession,
    ):
        """Test finding duplicate listings by URL."""
        # Create existing listing
        existing = Listing(
            title="Different Title",
            listing_url="https://example.com/unique-listing",
            price_usd=100.0,
            condition=Condition.USED.value,
            status=ListingStatus.ACTIVE.value,
        )
        session.add(existing)
        await session.flush()

        # Create export with same URL
        from apps.api.dealbrain_api.schemas.export_import import ListingExport

        listing_export = ListingExport(
            id=1,
            title="Another Title",
            listing_url="https://example.com/unique-listing",
            price_usd=100.0,
            condition=Condition.USED,
            status=ListingStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Find duplicates
        duplicates = await service._find_duplicate_listings(listing_export)

        # Should find URL match
        assert len(duplicates) > 0
        assert duplicates[0].match_score == 1.0

    async def test_find_duplicate_collections_exact_name(
        self,
        service: ExportImportService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test finding duplicate collections by exact name."""
        # Create existing collection
        existing = Collection(
            user_id=sample_user.id,
            name="My Gaming PCs",
            visibility="private",
        )
        session.add(existing)
        await session.flush()

        # Create export with same name
        from apps.api.dealbrain_api.schemas.export_import import CollectionExport

        collection_export = CollectionExport(
            id=1,
            name="My Gaming PCs",
            visibility="private",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Find duplicates
        duplicates = await service._find_duplicate_collections(
            collection_export, user_id=sample_user.id
        )

        # Should find exact match
        assert len(duplicates) > 0
        assert duplicates[0].entity_id == existing.id
        assert duplicates[0].match_score == 1.0


# ==================== Schema Validation Tests ====================


@pytest.mark.asyncio
class TestSchemaValidation:
    """Test schema version validation."""

    def test_validate_schema_version_valid(
        self,
        service: ExportImportService,
    ):
        """Test validating correct schema version."""
        json_data = {
            "deal_brain_export": {
                "version": "1.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            }
        }

        version = service.validate_schema_version(json_data)
        assert version == "1.0.0"

    def test_validate_schema_version_invalid(
        self,
        service: ExportImportService,
    ):
        """Test validating incorrect schema version raises error."""
        json_data = {
            "deal_brain_export": {
                "version": "2.0.0",
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            }
        }

        with pytest.raises(ValueError, match="Incompatible schema version"):
            service.validate_schema_version(json_data)

    def test_validate_schema_version_missing(
        self,
        service: ExportImportService,
    ):
        """Test validating missing schema version raises error."""
        json_data = {
            "deal_brain_export": {
                "exported_at": datetime.utcnow().isoformat(),
                "type": "deal",
            }
        }

        with pytest.raises(ValueError, match="Missing 'version'"):
            service.validate_schema_version(json_data)


# ==================== Preview Cache Tests ====================


@pytest.mark.asyncio
class TestPreviewCache:
    """Test PreviewCache functionality."""

    def test_preview_cache_store_and_retrieve(self):
        """Test storing and retrieving preview."""
        from apps.api.dealbrain_api.services.export_import import (
            ImportPreview,
            PreviewCache,
        )
        from apps.api.dealbrain_api.schemas.export_import import (
            PortableDealExport,
            ExportMetadata,
            DealDataExport,
            ListingExport,
        )

        cache = PreviewCache()

        # Create preview
        preview = ImportPreview(
            preview_id="test-preview-123",
            type="deal",
            data=PortableDealExport(
                deal_brain_export=ExportMetadata(
                    version="1.0.0",
                    exported_at=datetime.utcnow(),
                    type="deal",
                ),
                data=DealDataExport(
                    listing=ListingExport(
                        id=1,
                        title="Test",
                        price_usd=100.0,
                        condition=Condition.USED,
                        status=ListingStatus.ACTIVE,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                ),
            ),
            duplicates=[],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )

        # Store preview
        preview_id = cache.store(preview)

        # Retrieve preview
        retrieved = cache.get(preview_id)

        assert retrieved is not None
        assert retrieved.preview_id == "test-preview-123"

    def test_preview_cache_expired_returns_none(self):
        """Test that expired previews return None."""
        from apps.api.dealbrain_api.services.export_import import (
            ImportPreview,
            PreviewCache,
        )
        from apps.api.dealbrain_api.schemas.export_import import (
            PortableDealExport,
            ExportMetadata,
            DealDataExport,
            ListingExport,
        )

        cache = PreviewCache()

        # Create expired preview
        preview = ImportPreview(
            preview_id="expired-preview",
            type="deal",
            data=PortableDealExport(
                deal_brain_export=ExportMetadata(
                    version="1.0.0",
                    exported_at=datetime.utcnow(),
                    type="deal",
                ),
                data=DealDataExport(
                    listing=ListingExport(
                        id=1,
                        title="Test",
                        price_usd=100.0,
                        condition=Condition.USED,
                        status=ListingStatus.ACTIVE,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                ),
            ),
            duplicates=[],
            created_at=datetime.utcnow() - timedelta(hours=1),
            expires_at=datetime.utcnow() - timedelta(minutes=30),  # Expired
        )

        # Store preview
        preview_id = cache.store(preview)

        # Try to retrieve expired preview
        retrieved = cache.get(preview_id)

        assert retrieved is None

    def test_preview_cache_remove(self):
        """Test removing preview from cache."""
        from apps.api.dealbrain_api.services.export_import import (
            ImportPreview,
            PreviewCache,
        )
        from apps.api.dealbrain_api.schemas.export_import import (
            PortableDealExport,
            ExportMetadata,
            DealDataExport,
            ListingExport,
        )

        cache = PreviewCache()

        # Create and store preview
        preview = ImportPreview(
            preview_id="remove-test",
            type="deal",
            data=PortableDealExport(
                deal_brain_export=ExportMetadata(
                    version="1.0.0",
                    exported_at=datetime.utcnow(),
                    type="deal",
                ),
                data=DealDataExport(
                    listing=ListingExport(
                        id=1,
                        title="Test",
                        price_usd=100.0,
                        condition=Condition.USED,
                        status=ListingStatus.ACTIVE,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                ),
            ),
            duplicates=[],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )

        preview_id = cache.store(preview)

        # Remove preview
        cache.remove(preview_id)

        # Try to retrieve
        retrieved = cache.get(preview_id)
        assert retrieved is None
