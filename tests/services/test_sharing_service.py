"""Unit tests for SharingService.

Tests cover:
- Token generation and security
- Share creation (listing and user shares)
- Validation (expired, invalid tokens)
- Rate limiting enforcement
- Authorization (prevent cross-user access)
- View tracking
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.listings import Listing
from dealbrain_api.models.sharing import Collection, ListingShare, User, UserShare
from dealbrain_api.services.sharing_service import SharingService


try:
    import aiosqlite  # noqa: F401

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False


pytestmark = pytest.mark.skipif(not AIOSQLITE_AVAILABLE, reason="aiosqlite not installed")


@pytest_asyncio.fixture
async def db_session():
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
    user = User(username="testuser", email="test@example.com", display_name="Test User")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def sample_recipient(db_session: AsyncSession):
    """Create sample recipient user."""
    user = User(username="recipient", email="recipient@example.com", display_name="Recipient User")
    db_session.add(user)
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
        form_factor="tower",
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


@pytest.fixture
def service(db_session: AsyncSession):
    """Create SharingService instance."""
    return SharingService(db_session)


# ==================== ListingShare Tests ====================


class TestGenerateListingShareToken:
    """Tests for generate_listing_share_token method."""

    @pytest.mark.asyncio
    async def test_generate_share_with_expiry(
        self,
        service: SharingService,
        sample_listing: Listing,
        sample_user: User,
        db_session: AsyncSession,
    ):
        """Test generating share with expiry."""
        share = await service.generate_listing_share_token(
            listing_id=sample_listing.id, user_id=sample_user.id, ttl_days=30
        )

        assert share.id is not None
        assert share.listing_id == sample_listing.id
        assert share.created_by == sample_user.id
        assert share.share_token is not None
        assert len(share.share_token) == 64
        assert share.expires_at is not None
        assert share.view_count == 0

        # Check expiry is approximately 30 days from now
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        time_diff = abs((share.expires_at - expected_expiry).total_seconds())
        assert time_diff < 10  # Within 10 seconds

    @pytest.mark.asyncio
    async def test_generate_share_without_expiry(
        self, service: SharingService, sample_listing: Listing, db_session: AsyncSession
    ):
        """Test generating share without expiry (ttl_days=0)."""
        share = await service.generate_listing_share_token(
            listing_id=sample_listing.id, user_id=None, ttl_days=0
        )

        assert share.id is not None
        assert share.listing_id == sample_listing.id
        assert share.created_by is None
        assert share.expires_at is None

    @pytest.mark.asyncio
    async def test_generate_share_invalid_listing(
        self, service: SharingService, db_session: AsyncSession
    ):
        """Test generating share for non-existent listing."""
        with pytest.raises(ValueError, match="Listing 999 not found"):
            await service.generate_listing_share_token(listing_id=999, user_id=None)

    @pytest.mark.asyncio
    async def test_token_uniqueness(
        self, service: SharingService, sample_listing: Listing, db_session: AsyncSession
    ):
        """Test that generated tokens are unique."""
        share1 = await service.generate_listing_share_token(listing_id=sample_listing.id)
        share2 = await service.generate_listing_share_token(listing_id=sample_listing.id)

        assert share1.share_token != share2.share_token


class TestValidateListingShareToken:
    """Tests for validate_listing_share_token method."""

    @pytest.mark.asyncio
    async def test_validate_active_share(
        self, service: SharingService, sample_listing: Listing, db_session: AsyncSession
    ):
        """Test validating active (non-expired) share."""
        share = await service.generate_listing_share_token(
            listing_id=sample_listing.id, ttl_days=30
        )

        share_obj, is_valid = await service.validate_listing_share_token(share.share_token)

        assert share_obj is not None
        assert share_obj.id == share.id
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_expired_share(
        self, service: SharingService, sample_listing: Listing, db_session: AsyncSession
    ):
        """Test validating expired share."""
        # Create share that expired 1 day ago
        share = await service.share_repo.create_listing_share(
            listing_id=sample_listing.id,
            created_by=None,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await db_session.commit()

        share_obj, is_valid = await service.validate_listing_share_token(share.share_token)

        assert share_obj is not None
        assert share_obj.id == share.id
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_invalid_token(self, service: SharingService, db_session: AsyncSession):
        """Test validating non-existent token."""
        share_obj, is_valid = await service.validate_listing_share_token(
            "invalid_token_that_doesnt_exist"
        )

        assert share_obj is None
        assert is_valid is False


class TestIncrementShareView:
    """Tests for increment_share_view method."""

    @pytest.mark.asyncio
    async def test_increment_view_active_share(
        self, service: SharingService, sample_listing: Listing, db_session: AsyncSession
    ):
        """Test incrementing view count for active share."""
        share = await service.generate_listing_share_token(
            listing_id=sample_listing.id, ttl_days=30
        )

        initial_count = share.view_count

        success = await service.increment_share_view(share.share_token)

        assert success is True

        # Verify count incremented
        result = await db_session.execute(select(ListingShare).where(ListingShare.id == share.id))
        updated_share = result.scalar_one()
        assert updated_share.view_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_increment_view_expired_share(
        self, service: SharingService, sample_listing: Listing, db_session: AsyncSession
    ):
        """Test incrementing view count for expired share (should fail)."""
        share = await service.share_repo.create_listing_share(
            listing_id=sample_listing.id,
            created_by=None,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await db_session.commit()

        success = await service.increment_share_view(share.share_token)

        assert success is False

    @pytest.mark.asyncio
    async def test_increment_view_invalid_token(
        self, service: SharingService, db_session: AsyncSession
    ):
        """Test incrementing view count for invalid token."""
        success = await service.increment_share_view("invalid_token")

        assert success is False


# ==================== UserShare Tests ====================


class TestCreateUserShare:
    """Tests for create_user_share method."""

    @pytest.mark.asyncio
    async def test_create_user_share_success(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test creating user share successfully."""
        share = await service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=sample_recipient.id,
            listing_id=sample_listing.id,
            message="Check this out!",
        )

        assert share.id is not None
        assert share.sender_id == sample_user.id
        assert share.recipient_id == sample_recipient.id
        assert share.listing_id == sample_listing.id
        assert share.message == "Check this out!"
        assert share.share_token is not None
        assert len(share.share_token) == 64
        assert share.expires_at is not None

        # Check expiry is approximately 30 days from now
        expected_expiry = datetime.now(timezone.utc) + timedelta(days=30)
        time_diff = abs((share.expires_at - expected_expiry).total_seconds())
        assert time_diff < 10

    @pytest.mark.asyncio
    async def test_create_user_share_custom_ttl(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test creating user share with custom TTL."""
        share = await service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=sample_recipient.id,
            listing_id=sample_listing.id,
            ttl_days=7,
        )

        expected_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        time_diff = abs((share.expires_at - expected_expiry).total_seconds())
        assert time_diff < 10

    @pytest.mark.asyncio
    async def test_create_user_share_invalid_sender(
        self,
        service: SharingService,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test creating share with invalid sender."""
        with pytest.raises(ValueError, match="Sender user 999 not found"):
            await service.create_user_share(
                sender_id=999, recipient_id=sample_recipient.id, listing_id=sample_listing.id
            )

    @pytest.mark.asyncio
    async def test_create_user_share_invalid_recipient(
        self,
        service: SharingService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test creating share with invalid recipient."""
        with pytest.raises(ValueError, match="Recipient user 999 not found"):
            await service.create_user_share(
                sender_id=sample_user.id, recipient_id=999, listing_id=sample_listing.id
            )

    @pytest.mark.asyncio
    async def test_create_user_share_invalid_listing(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        db_session: AsyncSession,
    ):
        """Test creating share with invalid listing."""
        with pytest.raises(ValueError, match="Listing 999 not found"):
            await service.create_user_share(
                sender_id=sample_user.id, recipient_id=sample_recipient.id, listing_id=999
            )


class TestGetUserInbox:
    """Tests for get_user_inbox method."""

    @pytest.mark.asyncio
    async def test_get_inbox_empty(
        self, service: SharingService, sample_user: User, db_session: AsyncSession
    ):
        """Test getting empty inbox."""
        shares = await service.get_user_inbox(user_id=sample_user.id)

        assert shares == []

    @pytest.mark.asyncio
    async def test_get_inbox_with_shares(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test getting inbox with shares."""
        # Create 2 shares
        share1 = await service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=sample_recipient.id,
            listing_id=sample_listing.id,
            message="Share 1",
        )
        share2 = await service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=sample_recipient.id,
            listing_id=sample_listing.id,
            message="Share 2",
        )

        # Get recipient's inbox
        shares = await service.get_user_inbox(user_id=sample_recipient.id)

        assert len(shares) == 2
        assert any(s.id == share1.id for s in shares)
        assert any(s.id == share2.id for s in shares)

    @pytest.mark.asyncio
    async def test_get_inbox_filter_expired(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test getting inbox excludes expired shares by default."""
        # Create active share
        await service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=sample_recipient.id,
            listing_id=sample_listing.id,
            message="Active",
        )

        # Create expired share
        await service.share_repo.create_user_share(
            sender_id=sample_user.id,
            recipient_id=sample_recipient.id,
            listing_id=sample_listing.id,
            message="Expired",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        await db_session.commit()

        # Get inbox (exclude expired by default)
        shares = await service.get_user_inbox(user_id=sample_recipient.id)

        assert len(shares) == 1
        assert shares[0].message == "Active"

        # Get inbox including expired
        all_shares = await service.get_user_inbox(user_id=sample_recipient.id, include_expired=True)

        assert len(all_shares) == 2


class TestMarkShareAsViewed:
    """Tests for mark_share_as_viewed method."""

    @pytest.mark.asyncio
    async def test_mark_share_viewed_success(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test marking share as viewed."""
        share = await service.create_user_share(
            sender_id=sample_user.id, recipient_id=sample_recipient.id, listing_id=sample_listing.id
        )

        success = await service.mark_share_as_viewed(share_id=share.id, user_id=sample_recipient.id)

        assert success is True

        # Verify viewed_at is set
        result = await db_session.execute(select(UserShare).where(UserShare.id == share.id))
        updated_share = result.scalar_one()
        assert updated_share.viewed_at is not None

    @pytest.mark.asyncio
    async def test_mark_share_viewed_unauthorized(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test marking share viewed by non-recipient (should fail)."""
        share = await service.create_user_share(
            sender_id=sample_user.id, recipient_id=sample_recipient.id, listing_id=sample_listing.id
        )

        # Try to mark viewed as sender (not recipient)
        with pytest.raises(PermissionError, match="is not the recipient"):
            await service.mark_share_as_viewed(share_id=share.id, user_id=sample_user.id)

    @pytest.mark.asyncio
    async def test_mark_share_viewed_invalid_id(
        self, service: SharingService, db_session: AsyncSession
    ):
        """Test marking non-existent share as viewed."""
        success = await service.mark_share_as_viewed(share_id=999, user_id=1)

        assert success is False


# ==================== Rate Limiting Tests ====================


class TestCheckShareRateLimit:
    """Tests for check_share_rate_limit method."""

    @pytest.mark.asyncio
    async def test_rate_limit_under_limit(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test rate limit check when under limit."""
        # Create 5 shares (under limit of 10)
        for _ in range(5):
            await service.create_user_share(
                sender_id=sample_user.id,
                recipient_id=sample_recipient.id,
                listing_id=sample_listing.id,
            )

        # Check rate limit
        ok = await service.check_share_rate_limit(sample_user.id)

        assert ok is True

    @pytest.mark.asyncio
    async def test_rate_limit_at_limit(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test rate limit check when at limit."""
        # Create 10 shares (at limit)
        for _ in range(10):
            await service.create_user_share(
                sender_id=sample_user.id,
                recipient_id=sample_recipient.id,
                listing_id=sample_listing.id,
            )

        # Check rate limit (should fail)
        ok = await service.check_share_rate_limit(sample_user.id)

        assert ok is False

    @pytest.mark.asyncio
    async def test_rate_limit_create_share_blocked(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test that creating share is blocked when rate limit exceeded."""
        # Create 10 shares (at limit)
        for _ in range(10):
            await service.create_user_share(
                sender_id=sample_user.id,
                recipient_id=sample_recipient.id,
                listing_id=sample_listing.id,
            )

        # Try to create 11th share (should fail)
        with pytest.raises(PermissionError, match="exceeded share rate limit"):
            await service.create_user_share(
                sender_id=sample_user.id,
                recipient_id=sample_recipient.id,
                listing_id=sample_listing.id,
            )


# ==================== Import to Collection Tests ====================


class TestImportShareToCollection:
    """Tests for import_share_to_collection method."""

    @pytest.mark.asyncio
    async def test_import_share_to_collection(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test importing share to collection."""
        # Create user share
        share = await service.create_user_share(
            sender_id=sample_user.id,
            recipient_id=sample_recipient.id,
            listing_id=sample_listing.id,
            message="Great deal!",
        )

        # Import to collection (will create default collection)
        item = await service.import_share_to_collection(
            share_token=share.share_token, user_id=sample_recipient.id
        )

        assert item.id is not None
        assert item.listing_id == sample_listing.id
        assert "Great deal!" in item.notes

        # Verify share marked as imported
        result = await db_session.execute(select(UserShare).where(UserShare.id == share.id))
        updated_share = result.scalar_one()
        assert updated_share.imported_at is not None

    @pytest.mark.asyncio
    async def test_import_share_to_specific_collection(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test importing share to specific collection."""
        # Create collection
        collection = Collection(
            user_id=sample_recipient.id, name="Test Collection", visibility="private"
        )
        db_session.add(collection)
        await db_session.flush()

        # Create share
        share = await service.create_user_share(
            sender_id=sample_user.id, recipient_id=sample_recipient.id, listing_id=sample_listing.id
        )

        # Import to specific collection
        item = await service.import_share_to_collection(
            share_token=share.share_token, user_id=sample_recipient.id, collection_id=collection.id
        )

        assert item.collection_id == collection.id

    @pytest.mark.asyncio
    async def test_import_share_unauthorized(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test importing share by non-recipient."""
        # Create share
        share = await service.create_user_share(
            sender_id=sample_user.id, recipient_id=sample_recipient.id, listing_id=sample_listing.id
        )

        # Try to import as wrong user
        with pytest.raises(PermissionError, match="is not the recipient"):
            await service.import_share_to_collection(
                share_token=share.share_token, user_id=sample_user.id  # Wrong user!
            )

    @pytest.mark.asyncio
    async def test_import_share_duplicate(
        self,
        service: SharingService,
        sample_user: User,
        sample_recipient: User,
        sample_listing: Listing,
        db_session: AsyncSession,
    ):
        """Test importing same share twice (should fail)."""
        # Create share
        share = await service.create_user_share(
            sender_id=sample_user.id, recipient_id=sample_recipient.id, listing_id=sample_listing.id
        )

        # Import first time
        await service.import_share_to_collection(
            share_token=share.share_token, user_id=sample_recipient.id
        )

        # Try to import again (should fail - duplicate)
        with pytest.raises(ValueError, match="already in collection"):
            await service.import_share_to_collection(
                share_token=share.share_token, user_id=sample_recipient.id
            )
