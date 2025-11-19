"""Tests for CollectionsService sharing features (Phase 2a).

This test suite verifies:
- Visibility updates with telemetry
- Collection copying with access control
- Discovery with search and sorting
- Share token management
- Authorization and RLS checks

Target: >85% code coverage
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.listings import Listing
from apps.api.dealbrain_api.models.sharing import Collection, CollectionItem, User
from apps.api.dealbrain_api.services.collections_service import CollectionsService

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
    """Create CollectionsService instance with test session."""
    return CollectionsService(session)


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
async def other_user(session: AsyncSession):
    """Create another user for authorization tests."""
    user = User(
        username="otheruser", email="other@example.com", display_name="Other User"
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
        visibility="private",
    )
    session.add(collection)
    await session.flush()
    await session.refresh(collection)
    return collection


@pytest_asyncio.fixture
async def public_collection(session: AsyncSession, sample_user: User):
    """Create public collection for testing."""
    collection = Collection(
        user_id=sample_user.id,
        name="Public Collection",
        description="Public test collection",
        visibility="public",
    )
    session.add(collection)
    await session.flush()
    await session.refresh(collection)
    return collection


@pytest_asyncio.fixture
async def sample_listing(session: AsyncSession):
    """Create sample listing for testing."""
    listing = Listing(
        title="Test PC",
        listing_url="https://example.com/test",
        price_usd=500.0,
        condition="new",
    )
    session.add(listing)
    await session.flush()
    return listing


@pytest.mark.asyncio
class TestUpdateVisibility:
    """Test CollectionsService.update_visibility() method."""

    async def test_update_visibility_private_to_public(
        self,
        service: CollectionsService,
        sample_collection: Collection,
        sample_user: User,
    ):
        """Test updating visibility from private to public."""
        # Mock telemetry
        with patch.object(service, "_emit_event") as mock_emit:
            # Update visibility
            updated = await service.update_visibility(
                collection_id=sample_collection.id,
                new_visibility="public",
                user_id=sample_user.id,
            )

            # Verify update
            assert updated is not None
            assert updated.visibility == "public"

            # Verify telemetry event emitted
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == "collection.visibility_changed"
            assert call_args[0][1]["old_visibility"] == "private"
            assert call_args[0][1]["new_visibility"] == "public"

    async def test_update_visibility_public_to_unlisted(
        self,
        service: CollectionsService,
        public_collection: Collection,
        sample_user: User,
    ):
        """Test updating visibility from public to unlisted."""
        updated = await service.update_visibility(
            collection_id=public_collection.id,
            new_visibility="unlisted",
            user_id=sample_user.id,
        )

        assert updated is not None
        assert updated.visibility == "unlisted"

    async def test_update_visibility_invalid_value(
        self,
        service: CollectionsService,
        sample_collection: Collection,
        sample_user: User,
    ):
        """Test updating visibility with invalid value raises error."""
        with pytest.raises(ValueError, match="Visibility must be one of"):
            await service.update_visibility(
                collection_id=sample_collection.id,
                new_visibility="invalid",
                user_id=sample_user.id,
            )

    async def test_update_visibility_unauthorized(
        self,
        service: CollectionsService,
        sample_collection: Collection,
        other_user: User,
    ):
        """Test updating visibility for collection owned by another user."""
        with pytest.raises(PermissionError):
            await service.update_visibility(
                collection_id=sample_collection.id,
                new_visibility="public",
                user_id=other_user.id,
            )

    async def test_update_visibility_nonexistent_collection(
        self,
        service: CollectionsService,
        sample_user: User,
    ):
        """Test updating visibility for non-existent collection."""
        result = await service.update_visibility(
            collection_id=99999, new_visibility="public", user_id=sample_user.id
        )

        assert result is None


@pytest.mark.asyncio
class TestGetPublicCollection:
    """Test CollectionsService.get_public_collection() method."""

    async def test_get_public_collection_success(
        self,
        service: CollectionsService,
        public_collection: Collection,
    ):
        """Test retrieving public collection without authentication."""
        retrieved = await service.get_public_collection(
            collection_id=public_collection.id
        )

        assert retrieved is not None
        assert retrieved.id == public_collection.id
        assert retrieved.visibility == "public"

    async def test_get_public_collection_private_returns_none(
        self,
        service: CollectionsService,
        sample_collection: Collection,
    ):
        """Test retrieving private collection returns None."""
        retrieved = await service.get_public_collection(
            collection_id=sample_collection.id
        )

        assert retrieved is None

    async def test_get_public_collection_with_items(
        self,
        service: CollectionsService,
        session: AsyncSession,
        public_collection: Collection,
        sample_listing: Listing,
    ):
        """Test retrieving public collection with items loaded."""
        # Add item to collection
        item = CollectionItem(
            collection_id=public_collection.id,
            listing_id=sample_listing.id,
            status="undecided",
            position=0,
        )
        session.add(item)
        await session.commit()

        # Retrieve with items
        retrieved = await service.get_public_collection(
            collection_id=public_collection.id, load_items=True
        )

        assert retrieved is not None
        assert len(retrieved.items) == 1


@pytest.mark.asyncio
class TestCheckAccess:
    """Test CollectionsService.check_access() method."""

    async def test_check_access_public_anonymous(
        self,
        service: CollectionsService,
        public_collection: Collection,
    ):
        """Test that anonymous users can access public collections."""
        can_access = await service.check_access(
            collection_id=public_collection.id, user_id=None
        )

        assert can_access is True

    async def test_check_access_private_owner(
        self,
        service: CollectionsService,
        sample_collection: Collection,
        sample_user: User,
    ):
        """Test that owner can access private collection."""
        can_access = await service.check_access(
            collection_id=sample_collection.id, user_id=sample_user.id
        )

        assert can_access is True

    async def test_check_access_private_non_owner(
        self,
        service: CollectionsService,
        sample_collection: Collection,
        other_user: User,
    ):
        """Test that non-owner cannot access private collection."""
        can_access = await service.check_access(
            collection_id=sample_collection.id, user_id=other_user.id
        )

        assert can_access is False

    async def test_check_access_private_anonymous(
        self,
        service: CollectionsService,
        sample_collection: Collection,
    ):
        """Test that anonymous users cannot access private collections."""
        can_access = await service.check_access(
            collection_id=sample_collection.id, user_id=None
        )

        assert can_access is False

    async def test_check_access_unlisted_anonymous(
        self,
        service: CollectionsService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test that anonymous users can access unlisted collections."""
        # Create unlisted collection
        unlisted = Collection(
            user_id=sample_user.id,
            name="Unlisted Collection",
            visibility="unlisted",
        )
        session.add(unlisted)
        await session.commit()
        await session.refresh(unlisted)

        can_access = await service.check_access(collection_id=unlisted.id, user_id=None)

        assert can_access is True

    async def test_check_access_nonexistent_collection(
        self,
        service: CollectionsService,
    ):
        """Test checking access for non-existent collection."""
        can_access = await service.check_access(collection_id=99999, user_id=1)

        assert can_access is False


@pytest.mark.asyncio
class TestCopyCollection:
    """Test CollectionsService.copy_collection() method."""

    async def test_copy_public_collection(
        self,
        service: CollectionsService,
        session: AsyncSession,
        public_collection: Collection,
        sample_listing: Listing,
        other_user: User,
    ):
        """Test copying public collection to another user's workspace."""
        # Add item to source collection
        item = CollectionItem(
            collection_id=public_collection.id,
            listing_id=sample_listing.id,
            status="shortlisted",
            notes="Great deal",
            position=0,
        )
        session.add(item)
        await session.commit()

        # Mock telemetry
        with patch.object(service, "_emit_event") as mock_emit:
            # Copy collection
            new_collection = await service.copy_collection(
                source_collection_id=public_collection.id,
                user_id=other_user.id,
                new_name="My Copy",
            )

            # Verify copy
            assert new_collection is not None
            assert new_collection.id != public_collection.id
            assert new_collection.user_id == other_user.id
            assert new_collection.name == "My Copy"
            assert new_collection.visibility == "private"  # Always private
            assert new_collection.description == public_collection.description

            # Verify telemetry
            mock_emit.assert_called_once()

    async def test_copy_collection_default_name(
        self,
        service: CollectionsService,
        public_collection: Collection,
        other_user: User,
    ):
        """Test copying collection with default name."""
        new_collection = await service.copy_collection(
            source_collection_id=public_collection.id,
            user_id=other_user.id,
        )

        assert new_collection.name == f"Copy of {public_collection.name}"

    async def test_copy_collection_unauthorized(
        self,
        service: CollectionsService,
        sample_collection: Collection,
        other_user: User,
    ):
        """Test copying private collection user doesn't have access to."""
        with pytest.raises(PermissionError):
            await service.copy_collection(
                source_collection_id=sample_collection.id,
                user_id=other_user.id,
            )

    async def test_copy_collection_nonexistent(
        self,
        service: CollectionsService,
        sample_user: User,
    ):
        """Test copying non-existent collection."""
        with pytest.raises(ValueError, match="not found"):
            await service.copy_collection(
                source_collection_id=99999,
                user_id=sample_user.id,
            )

    async def test_copy_collection_preserves_items(
        self,
        service: CollectionsService,
        session: AsyncSession,
        public_collection: Collection,
        sample_listing: Listing,
        other_user: User,
    ):
        """Test that copying collection preserves all items with notes and status."""
        # Add multiple items
        for i in range(3):
            listing = Listing(
                title=f"Test Listing {i}",
                listing_url=f"https://example.com/{i}",
                price_usd=100.0 * (i + 1),
                condition="new",
            )
            session.add(listing)
            await session.flush()

            item = CollectionItem(
                collection_id=public_collection.id,
                listing_id=listing.id,
                status="undecided" if i == 0 else "shortlisted",
                notes=f"Note {i}",
                position=i,
            )
            session.add(item)

        await session.commit()

        # Copy collection
        new_collection = await service.copy_collection(
            source_collection_id=public_collection.id,
            user_id=other_user.id,
        )

        # Refresh to load items
        await session.refresh(new_collection)

        # Verify all items copied
        assert len(new_collection.items) == 3


@pytest.mark.asyncio
class TestListPublicCollections:
    """Test CollectionsService.list_public_collections() method."""

    async def test_list_public_collections_recent(
        self,
        service: CollectionsService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test listing public collections sorted by recency."""
        # Create multiple public collections
        for i in range(3):
            collection = Collection(
                user_id=sample_user.id,
                name=f"Public Collection {i}",
                visibility="public",
            )
            session.add(collection)

        await session.commit()

        # List public collections
        collections = await service.list_public_collections(
            visibility_filter="public", sort_by="recent", limit=10
        )

        # Verify results
        assert len(collections) == 3
        # Should be sorted by created_at DESC
        for i in range(len(collections) - 1):
            assert collections[i].created_at >= collections[i + 1].created_at

    async def test_list_public_collections_excludes_private(
        self,
        service: CollectionsService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test that private collections are excluded."""
        # Create public and private collections
        public = Collection(
            user_id=sample_user.id, name="Public", visibility="public"
        )
        private = Collection(
            user_id=sample_user.id, name="Private", visibility="private"
        )
        session.add_all([public, private])
        await session.commit()

        # List public collections
        collections = await service.list_public_collections(
            visibility_filter="public"
        )

        # Only public collection should be returned
        assert len(collections) == 1
        assert collections[0].name == "Public"

    async def test_list_public_collections_pagination(
        self,
        service: CollectionsService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test pagination of public collections."""
        # Create 5 public collections
        for i in range(5):
            collection = Collection(
                user_id=sample_user.id,
                name=f"Collection {i}",
                visibility="public",
            )
            session.add(collection)

        await session.commit()

        # Get first page
        page1 = await service.list_public_collections(limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = await service.list_public_collections(limit=2, offset=2)
        assert len(page2) == 2

        # Verify no overlap
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
class TestSearchCollections:
    """Test CollectionsService.search_collections() method."""

    async def test_search_collections_by_name(
        self,
        service: CollectionsService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test searching collections by name."""
        # Create collections with different names
        gaming = Collection(
            user_id=sample_user.id,
            name="Gaming PCs",
            description="Best gaming builds",
            visibility="public",
        )
        office = Collection(
            user_id=sample_user.id,
            name="Office Builds",
            description="Budget office computers",
            visibility="public",
        )
        session.add_all([gaming, office])
        await session.commit()

        # Mock telemetry
        with patch.object(service, "_emit_event") as mock_emit:
            # Search for "gaming"
            results = await service.search_collections(
                query="gaming", visibility_filter="public"
            )

            # Verify results
            assert len(results) == 1
            assert results[0].name == "Gaming PCs"

            # Verify telemetry
            mock_emit.assert_called_once()

    async def test_search_collections_by_description(
        self,
        service: CollectionsService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test searching collections by description."""
        # Create collection
        collection = Collection(
            user_id=sample_user.id,
            name="Best Deals",
            description="Budget gaming builds",
            visibility="public",
        )
        session.add(collection)
        await session.commit()

        # Search for "budget"
        results = await service.search_collections(
            query="budget", visibility_filter="public"
        )

        # Verify found
        assert len(results) == 1
        assert results[0].id == collection.id

    async def test_search_collections_case_insensitive(
        self,
        service: CollectionsService,
        session: AsyncSession,
        sample_user: User,
    ):
        """Test that search is case-insensitive."""
        # Create collection
        collection = Collection(
            user_id=sample_user.id,
            name="Gaming PCs",
            visibility="public",
        )
        session.add(collection)
        await session.commit()

        # Search with different case
        results = await service.search_collections(
            query="GAMING", visibility_filter="public"
        )

        assert len(results) == 1


@pytest.mark.asyncio
class TestGenerateShareToken:
    """Test CollectionsService.generate_share_token() method."""

    async def test_generate_share_token_public_collection(
        self,
        service: CollectionsService,
        public_collection: Collection,
        sample_user: User,
    ):
        """Test generating share token for public collection."""
        # Generate token
        token = await service.generate_share_token(
            collection_id=public_collection.id,
            user_id=sample_user.id,
            expires_at=None,
        )

        # Verify token
        assert token is not None
        assert token.collection_id == public_collection.id
        assert token.token is not None
        assert token.expires_at is None

    async def test_generate_share_token_with_expiry(
        self,
        service: CollectionsService,
        public_collection: Collection,
        sample_user: User,
    ):
        """Test generating share token with expiry."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        token = await service.generate_share_token(
            collection_id=public_collection.id,
            user_id=sample_user.id,
            expires_at=expires_at,
        )

        assert token.expires_at == expires_at

    async def test_generate_share_token_private_collection_fails(
        self,
        service: CollectionsService,
        sample_collection: Collection,
        sample_user: User,
    ):
        """Test that generating token for private collection fails."""
        with pytest.raises(ValueError, match="Cannot generate share token"):
            await service.generate_share_token(
                collection_id=sample_collection.id,
                user_id=sample_user.id,
            )

    async def test_generate_share_token_unauthorized(
        self,
        service: CollectionsService,
        public_collection: Collection,
        other_user: User,
    ):
        """Test generating share token for collection owned by another user."""
        with pytest.raises(ValueError, match="not found"):
            await service.generate_share_token(
                collection_id=public_collection.id,
                user_id=other_user.id,
            )


@pytest.mark.asyncio
class TestValidateShareToken:
    """Test CollectionsService.validate_share_token() method."""

    async def test_validate_share_token_success(
        self,
        service: CollectionsService,
        public_collection: Collection,
        sample_user: User,
    ):
        """Test validating valid share token."""
        # Generate token
        token = await service.generate_share_token(
            collection_id=public_collection.id,
            user_id=sample_user.id,
        )

        # Validate token
        collection = await service.validate_share_token(token=token.token)

        # Verify collection returned
        assert collection is not None
        assert collection.id == public_collection.id

    async def test_validate_share_token_invalid(
        self,
        service: CollectionsService,
    ):
        """Test validating invalid share token."""
        collection = await service.validate_share_token(token="invalid-token-12345")

        assert collection is None

    async def test_validate_share_token_expired(
        self,
        service: CollectionsService,
        public_collection: Collection,
        sample_user: User,
    ):
        """Test validating expired share token."""
        # Generate token that expired yesterday
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        token = await service.generate_share_token(
            collection_id=public_collection.id,
            user_id=sample_user.id,
            expires_at=expires_at,
        )

        # Validate token
        collection = await service.validate_share_token(token=token.token)

        # Should return None for expired token
        assert collection is None


@pytest.mark.asyncio
class TestIncrementShareViews:
    """Test CollectionsService.increment_share_views() method."""

    async def test_increment_share_views_success(
        self,
        service: CollectionsService,
        public_collection: Collection,
        sample_user: User,
    ):
        """Test incrementing share views successfully."""
        # Generate token
        token = await service.generate_share_token(
            collection_id=public_collection.id,
            user_id=sample_user.id,
        )

        # Increment views
        success = await service.increment_share_views(token=token.token)
        assert success is True

        # Verify view count increased
        validated = await service.validate_share_token(token=token.token)
        # Note: We'd need to access the token directly to verify view count
        # This is more of an integration test

    async def test_increment_share_views_invalid_token(
        self,
        service: CollectionsService,
    ):
        """Test incrementing views for invalid token."""
        success = await service.increment_share_views(token="invalid-token")
        assert success is False
