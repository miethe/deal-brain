"""Tests for ShareRepository (Phase 1.3: Repository Layer).

This test suite verifies:
- ListingShare CRUD operations and token management
- UserShare CRUD operations with expiry tracking
- View count incrementation
- Share viewed/imported status tracking
- Query optimization (eager loading)
- Expiry validation and cleanup queries
- Error handling and edge cases

Target: >90% code coverage
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.listings import Listing
from apps.api.dealbrain_api.models.sharing import User, UserShare
from apps.api.dealbrain_api.repositories.share_repository import ShareRepository

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
            await session.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def repository(session: AsyncSession):
    """Create ShareRepository instance with test session."""
    return ShareRepository(session)


@pytest_asyncio.fixture
async def sample_user(session: AsyncSession):
    """Create sample user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        display_name="Test User"
    )
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def sample_listing(session: AsyncSession):
    """Create sample listing for testing."""
    listing = Listing(
        name="Test PC Build",
        base_price=1000.0,
        adjusted_price=950.0
    )
    session.add(listing)
    await session.flush()
    return listing


@pytest.mark.asyncio
class TestCreateListingShare:
    """Test ShareRepository.create_listing_share() method."""

    async def test_create_minimal_listing_share(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test creating listing share with minimal fields."""
        share = await repository.create_listing_share(
            listing_id=sample_listing.id
        )
        await session.commit()

        assert share.id is not None
        assert share.listing_id == sample_listing.id
        assert share.created_by is None
        assert share.expires_at is None
        assert len(share.share_token) == 64
        assert share.view_count == 0
        assert share.created_at is not None

    async def test_create_listing_share_with_creator(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing,
        sample_user: User
    ):
        """Test creating listing share with creator."""
        share = await repository.create_listing_share(
            listing_id=sample_listing.id,
            created_by=sample_user.id
        )
        await session.commit()

        assert share.created_by == sample_user.id

    async def test_create_listing_share_with_expiry(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test creating listing share with expiry."""
        expires_at = datetime.utcnow() + timedelta(days=7)

        share = await repository.create_listing_share(
            listing_id=sample_listing.id,
            expires_at=expires_at
        )
        await session.commit()

        assert share.expires_at is not None
        # Compare timestamps (allowing for small time difference)
        assert abs((share.expires_at - expires_at).total_seconds()) < 1

    async def test_token_generation_uniqueness(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test that share tokens are unique."""
        share1 = await repository.create_listing_share(sample_listing.id)
        share2 = await repository.create_listing_share(sample_listing.id)
        await session.commit()

        assert share1.share_token != share2.share_token


@pytest.mark.asyncio
class TestGetListingShareByToken:
    """Test ShareRepository.get_listing_share_by_token() method."""

    async def test_get_existing_listing_share(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test retrieving existing listing share by token."""
        share = await repository.create_listing_share(sample_listing.id)
        await session.commit()

        retrieved = await repository.get_listing_share_by_token(share.share_token)

        assert retrieved is not None
        assert retrieved.id == share.id
        assert retrieved.share_token == share.share_token
        # Verify eager loading worked
        assert retrieved.listing is not None
        assert retrieved.listing.id == sample_listing.id

    async def test_get_listing_share_invalid_token(
        self,
        repository: ShareRepository
    ):
        """Test getting listing share with invalid token."""
        retrieved = await repository.get_listing_share_by_token("invalid_token_xyz")
        assert retrieved is None

    async def test_get_listing_share_includes_expired(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test that get_listing_share_by_token includes expired shares."""
        # Create expired share
        expires_at = datetime.utcnow() - timedelta(days=1)
        share = await repository.create_listing_share(
            sample_listing.id,
            expires_at=expires_at
        )
        await session.commit()

        # Should still be retrievable
        retrieved = await repository.get_listing_share_by_token(share.share_token)
        assert retrieved is not None
        assert retrieved.is_expired() is True


@pytest.mark.asyncio
class TestGetActiveListingShareByToken:
    """Test ShareRepository.get_active_listing_share_by_token() method."""

    async def test_get_active_listing_share(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test getting active (non-expired) listing share."""
        expires_at = datetime.utcnow() + timedelta(days=7)
        share = await repository.create_listing_share(
            sample_listing.id,
            expires_at=expires_at
        )
        await session.commit()

        retrieved = await repository.get_active_listing_share_by_token(share.share_token)

        assert retrieved is not None
        assert retrieved.id == share.id

    async def test_get_active_listing_share_never_expires(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test getting listing share that never expires."""
        share = await repository.create_listing_share(
            sample_listing.id,
            expires_at=None
        )
        await session.commit()

        retrieved = await repository.get_active_listing_share_by_token(share.share_token)

        assert retrieved is not None
        assert retrieved.expires_at is None

    async def test_get_active_listing_share_expired_returns_none(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test that expired shares are not returned as active."""
        # Create expired share
        expires_at = datetime.utcnow() - timedelta(days=1)
        share = await repository.create_listing_share(
            sample_listing.id,
            expires_at=expires_at
        )
        await session.commit()

        retrieved = await repository.get_active_listing_share_by_token(share.share_token)
        assert retrieved is None


@pytest.mark.asyncio
class TestIncrementViewCount:
    """Test ShareRepository.increment_view_count() method."""

    async def test_increment_view_count(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test incrementing view count."""
        share = await repository.create_listing_share(sample_listing.id)
        await session.commit()

        assert share.view_count == 0

        # Increment view count
        await repository.increment_view_count(share.id)
        await session.commit()

        # Refresh to get updated value
        await session.refresh(share)
        assert share.view_count == 1

    async def test_increment_view_count_multiple_times(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test incrementing view count multiple times."""
        share = await repository.create_listing_share(sample_listing.id)
        await session.commit()

        # Increment 5 times
        for _ in range(5):
            await repository.increment_view_count(share.id)

        await session.commit()

        # Refresh to get updated value
        await session.refresh(share)
        assert share.view_count == 5


@pytest.mark.asyncio
class TestFindExpiredListingShares:
    """Test ShareRepository.find_expired_listing_shares() method."""

    async def test_find_expired_listing_shares(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test finding expired listing shares."""
        # Create expired shares
        for i in range(3):
            expires_at = datetime.utcnow() - timedelta(days=i + 1)
            await repository.create_listing_share(
                sample_listing.id,
                expires_at=expires_at
            )

        # Create active shares
        for i in range(2):
            expires_at = datetime.utcnow() + timedelta(days=i + 1)
            await repository.create_listing_share(
                sample_listing.id,
                expires_at=expires_at
            )

        await session.commit()

        # Find expired shares
        expired = await repository.find_expired_listing_shares()

        assert len(expired) == 3

    async def test_find_expired_listing_shares_with_limit(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test finding expired shares with limit."""
        # Create 5 expired shares
        for i in range(5):
            expires_at = datetime.utcnow() - timedelta(days=i + 1)
            await repository.create_listing_share(
                sample_listing.id,
                expires_at=expires_at
            )

        await session.commit()

        # Find with limit
        expired = await repository.find_expired_listing_shares(limit=2)

        assert len(expired) == 2


@pytest.mark.asyncio
class TestCreateUserShare:
    """Test ShareRepository.create_user_share() method."""

    async def test_create_user_share(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test creating user-to-user share."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        share = await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id
        )
        await session.commit()

        assert share.id is not None
        assert share.sender_id == sender.id
        assert share.recipient_id == recipient.id
        assert share.listing_id == sample_listing.id
        assert len(share.share_token) == 64
        assert share.message is None
        assert share.viewed_at is None
        assert share.imported_at is None
        # Default expiry is 30 days
        expected_expiry = datetime.utcnow() + timedelta(days=30)
        assert abs((share.expires_at - expected_expiry).total_seconds()) < 2

    async def test_create_user_share_with_message(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test creating user share with message."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        message = "Check out this great deal!"
        share = await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id,
            message=message
        )
        await session.commit()

        assert share.message == message

    async def test_create_user_share_custom_expiry(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test creating user share with custom expiry."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        share = await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id,
            expires_in_days=7
        )
        await session.commit()

        expected_expiry = datetime.utcnow() + timedelta(days=7)
        assert abs((share.expires_at - expected_expiry).total_seconds()) < 2


@pytest.mark.asyncio
class TestGetUserShareByToken:
    """Test ShareRepository.get_user_share_by_token() method."""

    async def test_get_user_share_by_token(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test getting user share by token with eager loading."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        share = await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id
        )
        await session.commit()

        retrieved = await repository.get_user_share_by_token(share.share_token)

        assert retrieved is not None
        assert retrieved.id == share.id
        # Verify eager loading
        assert retrieved.sender is not None
        assert retrieved.sender.username == "sender"
        assert retrieved.recipient is not None
        assert retrieved.recipient.username == "recipient"
        assert retrieved.listing is not None


@pytest.mark.asyncio
class TestGetUserReceivedShares:
    """Test ShareRepository.get_user_received_shares() method."""

    async def test_get_user_received_shares(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test getting shares received by user."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        # Create shares
        for i in range(3):
            await repository.create_user_share(
                sender_id=sender.id,
                recipient_id=recipient.id,
                listing_id=sample_listing.id
            )

        await session.commit()

        # Get received shares
        received = await repository.get_user_received_shares(recipient.id)

        assert len(received) == 3

    async def test_get_user_received_shares_excludes_expired(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test that expired shares are excluded by default."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        # Create active share
        await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id,
            expires_in_days=7
        )

        # Create expired share (need to manually set)
        expired_share = UserShare(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id,
            share_token=UserShare.generate_token(),
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        session.add(expired_share)
        await session.commit()

        # Get received shares (exclude expired by default)
        received = await repository.get_user_received_shares(recipient.id)

        assert len(received) == 1

    async def test_get_user_received_shares_with_pagination(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test pagination for received shares."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        # Create 10 shares
        for i in range(10):
            await repository.create_user_share(
                sender_id=sender.id,
                recipient_id=recipient.id,
                listing_id=sample_listing.id
            )

        await session.commit()

        # Get first page
        page1 = await repository.get_user_received_shares(recipient.id, limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await repository.get_user_received_shares(recipient.id, limit=5, offset=5)
        assert len(page2) == 5


@pytest.mark.asyncio
class TestGetUserSentShares:
    """Test ShareRepository.get_user_sent_shares() method."""

    async def test_get_user_sent_shares(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test getting shares sent by user."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        # Create shares
        for i in range(3):
            await repository.create_user_share(
                sender_id=sender.id,
                recipient_id=recipient.id,
                listing_id=sample_listing.id
            )

        await session.commit()

        # Get sent shares
        sent = await repository.get_user_sent_shares(sender.id)

        assert len(sent) == 3


@pytest.mark.asyncio
class TestMarkShareViewed:
    """Test ShareRepository.mark_share_viewed() method."""

    async def test_mark_share_viewed(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test marking share as viewed."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        share = await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id
        )
        await session.commit()

        assert share.viewed_at is None

        # Mark as viewed
        await repository.mark_share_viewed(share.id)
        await session.commit()

        # Refresh to get updated value
        await session.refresh(share)
        assert share.viewed_at is not None


@pytest.mark.asyncio
class TestMarkShareImported:
    """Test ShareRepository.mark_share_imported() method."""

    async def test_mark_share_imported(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test marking share as imported."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        share = await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id
        )
        await session.commit()

        assert share.imported_at is None

        # Mark as imported
        await repository.mark_share_imported(share.id)
        await session.commit()

        # Refresh to get updated value
        await session.refresh(share)
        assert share.imported_at is not None


@pytest.mark.asyncio
class TestFindExpiredUserShares:
    """Test ShareRepository.find_expired_user_shares() method."""

    async def test_find_expired_user_shares(
        self,
        repository: ShareRepository,
        session: AsyncSession,
        sample_listing: Listing
    ):
        """Test finding expired user shares."""
        sender = User(username="sender", email="sender@example.com")
        recipient = User(username="recipient", email="recipient@example.com")
        session.add_all([sender, recipient])
        await session.flush()

        # Create expired shares (need to manually set)
        for i in range(3):
            expired_share = UserShare(
                sender_id=sender.id,
                recipient_id=recipient.id,
                listing_id=sample_listing.id,
                share_token=UserShare.generate_token(),
                expires_at=datetime.utcnow() - timedelta(days=i + 1)
            )
            session.add(expired_share)

        # Create active share
        await repository.create_user_share(
            sender_id=sender.id,
            recipient_id=recipient.id,
            listing_id=sample_listing.id,
            expires_in_days=7
        )

        await session.commit()

        # Find expired shares
        expired = await repository.find_expired_user_shares()

        assert len(expired) == 3
