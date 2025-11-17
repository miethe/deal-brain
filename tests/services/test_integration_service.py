"""Unit tests for IntegrationService.

Tests cover:
- Import from public shares (ListingShare)
- Import from user shares (UserShare)
- Default collection creation
- Duplicate prevention
- Bulk import
- Authorization checks
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.listings import Listing
from dealbrain_api.models.sharing import Collection, CollectionItem, User
from dealbrain_api.services.integration_service import IntegrationService
from dealbrain_api.services.sharing_service import SharingService


try:
    import aiosqlite  # noqa: F401
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not AIOSQLITE_AVAILABLE,
    reason="aiosqlite not installed"
)


@pytest_asyncio.fixture
async def session():
    """Create async in-memory SQLite session for testing."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from dealbrain_api.db import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession):
    """Create sample user."""
    user = User(
        username="testuser",
        email="test@example.com",
        display_name="Test User"
    )
    session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def recipient_user(db_session: AsyncSession):
    """Create recipient user."""
    user = User(
        username="recipient",
        email="recipient@example.com",
        display_name="Recipient User"
    )
    session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def sample_listing(db_session: AsyncSession):
    """Create sample listing."""
    listing = Listing(
        name="Test PC",
        url="https://example.com/test",
        price=500.0,
        condition="new",
        cpu_id=None,
        gpu_id=None,
        form_factor="tower"
    )
    session.add(listing)
    await db_session.flush()
    return listing


@pytest_asyncio.fixture
async def another_listing(db_session: AsyncSession):
    """Create another listing for multi-item tests."""
    listing = Listing(
        name="Another PC",
        url="https://example.com/another",
        price=600.0,
        condition="used",
        cpu_id=None,
        gpu_id=None,
        form_factor="sff"
    )
    session.add(listing)
    await db_session.flush()
    return listing


@pytest.fixture
def service(db_session: AsyncSession):
    """Create IntegrationService instance."""
    return IntegrationService(session)


@pytest.fixture
def sharing_service(db_session: AsyncSession):
    """Create SharingService instance for setup."""
    return SharingService(session)


# ==================== Import Shared Deal Tests ====================


class TestImportSharedDeal:
    """Tests for import_shared_deal method."""

    @pytest.mark.asyncio
    async def test_import_listing_share(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test importing public listing share."""
        # Create public listing share
        listing_share = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            user_id=sample_user.id,
            ttl_days=30
        )

        # Import to collection (will create default collection)
        item, collection = await service.import_shared_deal(
            share_token=listing_share.share_token,
            user_id=sample_user.id
        )

        assert item.id is not None
        assert item.listing_id == sample_listing.id
        assert item.collection_id == collection.id
        assert collection.name == "My Deals"

    @pytest.mark.asyncio
    async def test_import_user_share(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        recipient_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test importing user share."""
        # Create user share
        user_share = await sharing_service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=recipient_user.id,
            listing_id=sample_listing.id,
            message="Great deal!"
        )

        # Import as recipient
        item, collection = await service.import_shared_deal(
            share_token=user_share.share_token,
            user_id=recipient_user.id
        )

        assert item.id is not None
        assert item.listing_id == sample_listing.id
        assert "Great deal!" in item.notes

    @pytest.mark.asyncio
    async def test_import_to_specific_collection(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test importing to specific collection."""
        # Create collection
        from dealbrain_api.services.collections_service import CollectionsService
        collections_service = CollectionsService(session)
        collection = await collections_service.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )

        # Create share
        listing_share = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            ttl_days=30
        )

        # Import to specific collection
        item, imported_collection = await service.import_shared_deal(
            share_token=listing_share.share_token,
            user_id=sample_user.id,
            collection_id=collection.id
        )

        assert item.collection_id == collection.id
        assert imported_collection.id == collection.id

    @pytest.mark.asyncio
    async def test_import_invalid_token(
        self, service: IntegrationService, sample_user: User, db_session: AsyncSession
    ):
        """Test importing with invalid token."""
        with pytest.raises(ValueError, match="not found"):
            await service.import_shared_deal(
                share_token="invalid_token",
                user_id=sample_user.id
            )

    @pytest.mark.asyncio
    async def test_import_expired_listing_share(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test importing expired listing share."""
        # Create expired share
        listing_share = await sharing_service.share_repo.create_listing_share(
            listing_id=sample_listing.id,
            created_by=sample_user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        await db_session.commit()

        # Try to import (should fail)
        with pytest.raises(ValueError, match="has expired"):
            await service.import_shared_deal(
                share_token=listing_share.share_token,
                user_id=sample_user.id
            )

    @pytest.mark.asyncio
    async def test_import_user_share_wrong_recipient(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        recipient_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test importing user share by wrong user."""
        # Create user share
        user_share = await sharing_service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=recipient_user.id,
            listing_id=sample_listing.id
        )

        # Try to import as wrong user (sender instead of recipient)
        with pytest.raises(PermissionError, match="is not the recipient"):
            await service.import_shared_deal(
                share_token=user_share.share_token,
                user_id=sample_user.id  # Wrong user!
            )

    @pytest.mark.asyncio
    async def test_import_duplicate(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test importing same share twice (duplicate)."""
        # Create share
        listing_share = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            ttl_days=30
        )

        # Import first time
        await service.import_shared_deal(
            share_token=listing_share.share_token,
            user_id=sample_user.id
        )

        # Try to import again (should fail - duplicate)
        with pytest.raises(ValueError, match="already exists in collection"):
            await service.import_shared_deal(
                share_token=listing_share.share_token,
                user_id=sample_user.id
            )


# ==================== Duplicate Detection Tests ====================


class TestCheckDuplicateInCollection:
    """Tests for check_duplicate_in_collection method."""

    @pytest.mark.asyncio
    async def test_check_duplicate_not_exists(
        self,
        service: IntegrationService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test checking duplicate when item doesn't exist."""
        from dealbrain_api.services.collections_service import CollectionsService
        collections_service = CollectionsService(session)
        collection = await collections_service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        is_duplicate = await service.check_duplicate_in_collection(
            listing_id=sample_listing.id,
            collection_id=collection.id
        )

        assert is_duplicate is False

    @pytest.mark.asyncio
    async def test_check_duplicate_exists(
        self,
        service: IntegrationService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test checking duplicate when item exists."""
        from dealbrain_api.services.collections_service import CollectionsService
        collections_service = CollectionsService(session)
        collection = await collections_service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        # Add item
        await collections_service.add_item_to_collection(
            collection_id=collection.id,
            listing_id=sample_listing.id,
            user_id=sample_user.id
        )

        # Check duplicate
        is_duplicate = await service.check_duplicate_in_collection(
            listing_id=sample_listing.id,
            collection_id=collection.id
        )

        assert is_duplicate is True


# ==================== Bulk Import Tests ====================


class TestBulkImportShares:
    """Tests for bulk_import_shares method."""

    @pytest.mark.asyncio
    async def test_bulk_import_all_success(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        another_listing: Listing,
        db_session: AsyncSession
    ):
        """Test bulk import with all successful imports."""
        # Create 2 shares
        share1 = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            ttl_days=30
        )
        share2 = await sharing_service.generate_listing_share_token(
            listing_id=another_listing.id,
            ttl_days=30
        )

        # Bulk import
        results = await service.bulk_import_shares(
            share_tokens=[share1.share_token, share2.share_token],
            user_id=sample_user.id
        )

        assert len(results) == 2
        assert isinstance(results[share1.share_token], CollectionItem)
        assert isinstance(results[share2.share_token], CollectionItem)

    @pytest.mark.asyncio
    async def test_bulk_import_partial_success(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test bulk import with partial success (some invalid tokens)."""
        # Create 1 valid share
        share1 = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            ttl_days=30
        )

        # Bulk import with 1 valid, 1 invalid
        results = await service.bulk_import_shares(
            share_tokens=[share1.share_token, "invalid_token"],
            user_id=sample_user.id
        )

        assert len(results) == 2
        assert isinstance(results[share1.share_token], CollectionItem)
        assert isinstance(results["invalid_token"], str)  # Error message
        assert "not found" in results["invalid_token"]

    @pytest.mark.asyncio
    async def test_bulk_import_skip_duplicates(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test bulk import skips duplicates."""
        # Create share
        share = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            ttl_days=30
        )

        # Import once
        await service.import_shared_deal(
            share_token=share.share_token,
            user_id=sample_user.id
        )

        # Try to bulk import same token again
        results = await service.bulk_import_shares(
            share_tokens=[share.share_token],
            user_id=sample_user.id
        )

        assert len(results) == 1
        assert isinstance(results[share.share_token], str)  # Error message
        assert "already exists" in results[share.share_token]

    @pytest.mark.asyncio
    async def test_bulk_import_to_specific_collection(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        another_listing: Listing,
        db_session: AsyncSession
    ):
        """Test bulk import to specific collection."""
        from dealbrain_api.services.collections_service import CollectionsService
        collections_service = CollectionsService(session)
        collection = await collections_service.create_collection(
            user_id=sample_user.id,
            name="Bulk Import Collection"
        )

        # Create shares
        share1 = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            ttl_days=30
        )
        share2 = await sharing_service.generate_listing_share_token(
            listing_id=another_listing.id,
            ttl_days=30
        )

        # Bulk import to specific collection
        results = await service.bulk_import_shares(
            share_tokens=[share1.share_token, share2.share_token],
            user_id=sample_user.id,
            collection_id=collection.id
        )

        # Verify both items in same collection
        assert isinstance(results[share1.share_token], CollectionItem)
        assert isinstance(results[share2.share_token], CollectionItem)
        assert results[share1.share_token].collection_id == collection.id
        assert results[share2.share_token].collection_id == collection.id

    @pytest.mark.asyncio
    async def test_bulk_import_empty_list(
        self, service: IntegrationService, sample_user: User, db_session: AsyncSession
    ):
        """Test bulk import with empty list."""
        results = await service.bulk_import_shares(
            share_tokens=[],
            user_id=sample_user.id
        )

        assert results == {}

    @pytest.mark.asyncio
    async def test_bulk_import_user_shares(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        recipient_user: User,
        sample_listing: Listing,
        another_listing: Listing,
        db_session: AsyncSession
    ):
        """Test bulk import with user shares."""
        # Create user shares
        share1 = await sharing_service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=recipient_user.id,
            listing_id=sample_listing.id,
            message="Share 1"
        )
        share2 = await sharing_service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=recipient_user.id,
            listing_id=another_listing.id,
            message="Share 2"
        )

        # Bulk import as recipient
        results = await service.bulk_import_shares(
            share_tokens=[share1.share_token, share2.share_token],
            user_id=recipient_user.id
        )

        assert len(results) == 2
        assert isinstance(results[share1.share_token], CollectionItem)
        assert isinstance(results[share2.share_token], CollectionItem)

        # Verify messages preserved in notes
        item1 = results[share1.share_token]
        item2 = results[share2.share_token]
        assert "Share 1" in item1.notes
        assert "Share 2" in item2.notes

    @pytest.mark.asyncio
    async def test_bulk_import_mixed_share_types(
        self,
        service: IntegrationService,
        sharing_service: SharingService,
        sample_user: User,
        recipient_user: User,
        sample_listing: Listing,
        another_listing: Listing,
        db_session: AsyncSession
    ):
        """Test bulk import with mixed share types (listing + user shares)."""
        # Create listing share (public)
        listing_share = await sharing_service.generate_listing_share_token(
            listing_id=sample_listing.id,
            ttl_days=30
        )

        # Create user share
        user_share = await sharing_service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=recipient_user.id,
            listing_id=another_listing.id
        )

        # Bulk import as recipient
        results = await service.bulk_import_shares(
            share_tokens=[listing_share.share_token, user_share.share_token],
            user_id=recipient_user.id
        )

        assert len(results) == 2
        assert isinstance(results[listing_share.share_token], CollectionItem)
        assert isinstance(results[user_share.share_token], CollectionItem)
