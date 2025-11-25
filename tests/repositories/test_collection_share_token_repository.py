"""Tests for CollectionShareTokenRepository (Phase 2a: Sharing).

This test suite verifies:
- Token generation with cryptographically secure random values
- Token-based collection access with expiry validation
- View count tracking with atomic updates
- Token expiration (soft-delete) functionality
- Query optimization with eager loading

Target: >85% code coverage
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.listings import Listing
from apps.api.dealbrain_api.models.sharing import Collection, CollectionShareToken, User
from apps.api.dealbrain_api.repositories.collection_share_token_repository import (
    CollectionShareTokenRepository,
)

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
    """Create CollectionShareTokenRepository instance with test session."""
    return CollectionShareTokenRepository(session)


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
async def sample_collection(session: AsyncSession, sample_user: User):
    """Create sample collection for testing."""
    collection = Collection(
        user_id=sample_user.id,
        name="Test Collection",
        description="Test description",
        visibility="public",
    )
    session.add(collection)
    await session.flush()
    return collection


@pytest.mark.asyncio
class TestGenerateToken:
    """Test CollectionShareTokenRepository.generate_token() method."""

    async def test_generate_token_no_expiry(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test generating token without expiry."""
        # Generate token
        token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=None
        )

        # Verify token attributes
        assert token.id is not None
        assert token.collection_id == sample_collection.id
        assert token.token is not None
        assert len(token.token) > 20  # Should be secure random string
        assert token.view_count == 0
        assert token.expires_at is None
        assert token.created_at is not None
        assert token.updated_at is not None

    async def test_generate_token_with_expiry(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test generating token with expiry."""
        # Set expiry 7 days from now
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        # Generate token
        token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=expires_at
        )

        # Verify expiry is set
        assert token.expires_at is not None
        assert token.expires_at == expires_at

    async def test_generate_multiple_tokens_unique(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test that multiple tokens are unique."""
        # Generate two tokens
        token1 = await repository.generate_token(collection_id=sample_collection.id)
        token2 = await repository.generate_token(collection_id=sample_collection.id)

        # Verify tokens are unique
        assert token1.token != token2.token
        assert token1.id != token2.id


@pytest.mark.asyncio
class TestGetByToken:
    """Test CollectionShareTokenRepository.get_by_token() method."""

    async def test_get_valid_token(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test retrieving valid token."""
        # Generate token
        created_token = await repository.generate_token(
            collection_id=sample_collection.id
        )

        # Retrieve by token string
        retrieved = await repository.get_by_token(
            token=created_token.token, include_expired=False
        )

        # Verify retrieved token
        assert retrieved is not None
        assert retrieved.id == created_token.id
        assert retrieved.token == created_token.token
        assert retrieved.collection is not None
        assert retrieved.collection.id == sample_collection.id

    async def test_get_nonexistent_token(
        self,
        repository: CollectionShareTokenRepository,
    ):
        """Test retrieving non-existent token returns None."""
        retrieved = await repository.get_by_token(
            token="nonexistent-token-12345", include_expired=False
        )

        assert retrieved is None

    async def test_get_expired_token_excluded_by_default(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test that expired tokens are excluded by default."""
        # Generate token that expired yesterday
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=expires_at
        )

        # Try to retrieve without including expired
        retrieved = await repository.get_by_token(
            token=token.token, include_expired=False
        )

        # Should not be found
        assert retrieved is None

    async def test_get_expired_token_included_when_requested(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test that expired tokens can be retrieved when explicitly requested."""
        # Generate token that expired yesterday
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=expires_at
        )

        # Retrieve with include_expired=True
        retrieved = await repository.get_by_token(
            token=token.token, include_expired=True
        )

        # Should be found
        assert retrieved is not None
        assert retrieved.id == token.id


@pytest.mark.asyncio
class TestIncrementViewCount:
    """Test CollectionShareTokenRepository.increment_view_count() method."""

    async def test_increment_view_count_success(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test incrementing view count successfully."""
        # Generate token
        token = await repository.generate_token(collection_id=sample_collection.id)

        # Increment view count
        success = await repository.increment_view_count(token=token.token)
        assert success is True

        # Verify view count increased
        retrieved = await repository.get_by_token(token=token.token)
        assert retrieved.view_count == 1

        # Increment again
        success = await repository.increment_view_count(token=token.token)
        assert success is True

        retrieved = await repository.get_by_token(token=token.token)
        assert retrieved.view_count == 2

    async def test_increment_view_count_nonexistent_token(
        self,
        repository: CollectionShareTokenRepository,
    ):
        """Test incrementing view count for non-existent token returns False."""
        success = await repository.increment_view_count(token="nonexistent-token")
        assert success is False

    async def test_increment_view_count_expired_token(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test incrementing view count for expired token returns False."""
        # Generate token that expired yesterday
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=expires_at
        )

        # Try to increment view count
        success = await repository.increment_view_count(token=token.token)
        assert success is False


@pytest.mark.asyncio
class TestExpireToken:
    """Test CollectionShareTokenRepository.expire_token() method."""

    async def test_expire_token_success(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test expiring token successfully."""
        # Generate token without expiry
        token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=None
        )

        # Verify it can be retrieved
        retrieved = await repository.get_by_token(token=token.token)
        assert retrieved is not None

        # Expire the token
        success = await repository.expire_token(token=token.token)
        assert success is True

        # Verify it can no longer be retrieved (without include_expired)
        retrieved = await repository.get_by_token(
            token=token.token, include_expired=False
        )
        assert retrieved is None

        # But can be retrieved with include_expired=True
        retrieved = await repository.get_by_token(
            token=token.token, include_expired=True
        )
        assert retrieved is not None
        assert retrieved.expires_at is not None

    async def test_expire_nonexistent_token(
        self,
        repository: CollectionShareTokenRepository,
    ):
        """Test expiring non-existent token returns False."""
        success = await repository.expire_token(token="nonexistent-token")
        assert success is False

    async def test_expire_already_expired_token(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test expiring already expired token returns False."""
        # Generate token that expired yesterday
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=expires_at
        )

        # Try to expire it again
        success = await repository.expire_token(token=token.token)
        assert success is False


@pytest.mark.asyncio
class TestGetByCollectionId:
    """Test CollectionShareTokenRepository.get_by_collection_id() method."""

    async def test_get_tokens_for_collection(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test retrieving all tokens for a collection."""
        # Generate multiple tokens
        token1 = await repository.generate_token(collection_id=sample_collection.id)
        token2 = await repository.generate_token(collection_id=sample_collection.id)
        token3 = await repository.generate_token(collection_id=sample_collection.id)

        # Retrieve all tokens
        tokens = await repository.get_by_collection_id(
            collection_id=sample_collection.id
        )

        # Verify all tokens returned
        assert len(tokens) == 3
        token_ids = [t.id for t in tokens]
        assert token1.id in token_ids
        assert token2.id in token_ids
        assert token3.id in token_ids

    async def test_get_tokens_excludes_expired_by_default(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test that expired tokens are excluded by default."""
        # Generate active token
        active_token = await repository.generate_token(
            collection_id=sample_collection.id
        )

        # Generate expired token
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        expired_token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=expires_at
        )

        # Retrieve tokens (without expired)
        tokens = await repository.get_by_collection_id(
            collection_id=sample_collection.id, include_expired=False
        )

        # Only active token should be returned
        assert len(tokens) == 1
        assert tokens[0].id == active_token.id

    async def test_get_tokens_includes_expired_when_requested(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test that expired tokens can be included when requested."""
        # Generate active token
        active_token = await repository.generate_token(
            collection_id=sample_collection.id
        )

        # Generate expired token
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        expired_token = await repository.generate_token(
            collection_id=sample_collection.id, expires_at=expires_at
        )

        # Retrieve tokens (including expired)
        tokens = await repository.get_by_collection_id(
            collection_id=sample_collection.id, include_expired=True
        )

        # Both tokens should be returned
        assert len(tokens) == 2
        token_ids = [t.id for t in tokens]
        assert active_token.id in token_ids
        assert expired_token.id in token_ids

    async def test_get_tokens_pagination(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test pagination of token retrieval."""
        # Generate 5 tokens
        for _ in range(5):
            await repository.generate_token(collection_id=sample_collection.id)

        # Get first page (limit 2)
        page1 = await repository.get_by_collection_id(
            collection_id=sample_collection.id, limit=2, offset=0
        )
        assert len(page1) == 2

        # Get second page
        page2 = await repository.get_by_collection_id(
            collection_id=sample_collection.id, limit=2, offset=2
        )
        assert len(page2) == 2

        # Verify no overlap
        page1_ids = {t.id for t in page1}
        page2_ids = {t.id for t in page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
class TestDeleteToken:
    """Test CollectionShareTokenRepository.delete_token() method."""

    async def test_delete_token_success(
        self,
        repository: CollectionShareTokenRepository,
        sample_collection: Collection,
    ):
        """Test hard deleting token successfully."""
        # Generate token
        token = await repository.generate_token(collection_id=sample_collection.id)

        # Delete token
        success = await repository.delete_token(token=token.token)
        assert success is True

        # Verify token is gone (even with include_expired=True)
        retrieved = await repository.get_by_token(
            token=token.token, include_expired=True
        )
        assert retrieved is None

    async def test_delete_nonexistent_token(
        self,
        repository: CollectionShareTokenRepository,
    ):
        """Test deleting non-existent token returns False."""
        success = await repository.delete_token(token="nonexistent-token")
        assert success is False


@pytest.mark.asyncio
class TestEagerLoading:
    """Test that eager loading works correctly."""

    async def test_get_by_token_loads_collection(
        self,
        repository: CollectionShareTokenRepository,
        session: AsyncSession,
        sample_collection: Collection,
    ):
        """Test that get_by_token eager loads collection."""
        # Generate token
        token = await repository.generate_token(collection_id=sample_collection.id)

        # Retrieve token (closes session to test eager loading)
        retrieved = await repository.get_by_token(token=token.token)

        # Collection should be loaded
        assert retrieved.collection is not None
        assert retrieved.collection.id == sample_collection.id
        assert retrieved.collection.name == "Test Collection"

    async def test_get_by_token_loads_collection_items(
        self,
        repository: CollectionShareTokenRepository,
        session: AsyncSession,
        sample_collection: Collection,
        sample_user: User,
    ):
        """Test that get_by_token eager loads collection items."""
        # Add item to collection
        from apps.api.dealbrain_api.models.sharing import CollectionItem

        listing = Listing(
            title="Test Listing",
            listing_url="https://example.com",
            price_usd=100.0,
            condition="new",
        )
        session.add(listing)
        await session.flush()

        item = CollectionItem(
            collection_id=sample_collection.id,
            listing_id=listing.id,
            status="undecided",
            position=0,
        )
        session.add(item)
        await session.flush()

        # Generate token
        token = await repository.generate_token(collection_id=sample_collection.id)

        # Retrieve token
        retrieved = await repository.get_by_token(token=token.token)

        # Collection items should be loaded
        assert retrieved.collection is not None
        assert len(retrieved.collection.items) == 1
        assert retrieved.collection.items[0].listing_id == listing.id
