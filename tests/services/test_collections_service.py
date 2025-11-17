"""Unit tests for CollectionsService.

Tests cover:
- Collection CRUD with ownership validation
- Item management with deduplication
- Status validation
- Position management
- Filtering and sorting
- Authorization checks
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dealbrain_api.models.listings import Listing
from dealbrain_api.models.sharing import Collection, CollectionItem, User
from dealbrain_api.services.collections_service import CollectionsService


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
    user = User(
        username="testuser",
        email="test@example.com",
        display_name="Test User"
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession):
    """Create another user for authorization tests."""
    user = User(
        username="otheruser",
        email="other@example.com",
        display_name="Other User"
    )
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
        form_factor="tower"
    )
    db_session.add(listing)
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
    db_session.add(listing)
    await db_session.flush()
    return listing


@pytest.fixture
def service(db_session: AsyncSession):
    """Create CollectionsService instance."""
    return CollectionsService(db_session)


# ==================== Collection CRUD Tests ====================


class TestCreateCollection:
    """Tests for create_collection method."""

    @pytest.mark.asyncio
    async def test_create_collection_success(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test creating collection successfully."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test Collection",
            description="A test collection",
            visibility="private"
        )

        assert collection.id is not None
        assert collection.user_id == sample_user.id
        assert collection.name == "Test Collection"
        assert collection.description == "A test collection"
        assert collection.visibility == "private"
        assert collection.created_at is not None

    @pytest.mark.asyncio
    async def test_create_collection_default_visibility(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test creating collection with default visibility."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )

        assert collection.visibility == "private"

    @pytest.mark.asyncio
    async def test_create_collection_invalid_name_empty(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test creating collection with empty name."""
        with pytest.raises(ValueError, match="name must be 1-100 characters"):
            await service.create_collection(
                user_id=sample_user.id,
                name=""
            )

    @pytest.mark.asyncio
    async def test_create_collection_invalid_name_too_long(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test creating collection with name too long."""
        with pytest.raises(ValueError, match="name must be 1-100 characters"):
            await service.create_collection(
                user_id=sample_user.id,
                name="x" * 101
            )

    @pytest.mark.asyncio
    async def test_create_collection_invalid_visibility(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test creating collection with invalid visibility."""
        with pytest.raises(ValueError, match="Visibility must be one of"):
            await service.create_collection(
                user_id=sample_user.id,
                name="Test",
                visibility="invalid"
            )


class TestGetCollection:
    """Tests for get_collection method."""

    @pytest.mark.asyncio
    async def test_get_collection_success(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test getting collection successfully."""
        # Create collection
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )

        # Get collection
        retrieved = await service.get_collection(
            collection_id=collection.id,
            user_id=sample_user.id
        )

        assert retrieved is not None
        assert retrieved.id == collection.id
        assert retrieved.name == "Test Collection"

    @pytest.mark.asyncio
    async def test_get_collection_not_found(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test getting non-existent collection."""
        retrieved = await service.get_collection(
            collection_id=999,
            user_id=sample_user.id
        )

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_collection_unauthorized(
        self,
        service: CollectionsService,
        sample_user: User,
        other_user: User,
        db_session: AsyncSession
    ):
        """Test getting collection owned by another user."""
        # Create collection as sample_user
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )

        # Try to get as other_user (should raise PermissionError)
        with pytest.raises(PermissionError, match="does not own collection"):
            await service.get_collection(
                collection_id=collection.id,
                user_id=other_user.id
            )


class TestUpdateCollection:
    """Tests for update_collection method."""

    @pytest.mark.asyncio
    async def test_update_collection_name(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test updating collection name."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Original Name"
        )

        updated = await service.update_collection(
            collection_id=collection.id,
            user_id=sample_user.id,
            name="New Name"
        )

        assert updated is not None
        assert updated.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_collection_description(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test updating collection description."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        updated = await service.update_collection(
            collection_id=collection.id,
            user_id=sample_user.id,
            description="New description"
        )

        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_update_collection_visibility(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test updating collection visibility."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test",
            visibility="private"
        )

        updated = await service.update_collection(
            collection_id=collection.id,
            user_id=sample_user.id,
            visibility="public"
        )

        assert updated.visibility == "public"

    @pytest.mark.asyncio
    async def test_update_collection_invalid_name(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test updating collection with invalid name."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        with pytest.raises(ValueError, match="name must be 1-100 characters"):
            await service.update_collection(
                collection_id=collection.id,
                user_id=sample_user.id,
                name=""
            )

    @pytest.mark.asyncio
    async def test_update_collection_unauthorized(
        self,
        service: CollectionsService,
        sample_user: User,
        other_user: User,
        db_session: AsyncSession
    ):
        """Test updating collection by non-owner."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        with pytest.raises(PermissionError, match="does not own collection"):
            await service.update_collection(
                collection_id=collection.id,
                user_id=other_user.id,
                name="Hacked"
            )


class TestDeleteCollection:
    """Tests for delete_collection method."""

    @pytest.mark.asyncio
    async def test_delete_collection_success(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test deleting collection successfully."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        success = await service.delete_collection(
            collection_id=collection.id,
            user_id=sample_user.id
        )

        assert success is True

        # Verify deleted
        result = await db_session.execute(
            select(Collection).where(Collection.id == collection.id)
        )
        deleted = result.scalar_one_or_none()
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_collection_not_found(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test deleting non-existent collection."""
        success = await service.delete_collection(
            collection_id=999,
            user_id=sample_user.id
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_delete_collection_unauthorized(
        self,
        service: CollectionsService,
        sample_user: User,
        other_user: User,
        db_session: AsyncSession
    ):
        """Test deleting collection by non-owner."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        with pytest.raises(PermissionError, match="does not own collection"):
            await service.delete_collection(
                collection_id=collection.id,
                user_id=other_user.id
            )


class TestListUserCollections:
    """Tests for list_user_collections method."""

    @pytest.mark.asyncio
    async def test_list_collections_empty(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test listing collections when user has none."""
        collections = await service.list_user_collections(user_id=sample_user.id)

        assert collections == []

    @pytest.mark.asyncio
    async def test_list_collections_multiple(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test listing multiple collections."""
        # Create 3 collections
        c1 = await service.create_collection(sample_user.id, "Collection 1")
        c2 = await service.create_collection(sample_user.id, "Collection 2")
        c3 = await service.create_collection(sample_user.id, "Collection 3")

        collections = await service.list_user_collections(user_id=sample_user.id)

        assert len(collections) == 3
        ids = {c.id for c in collections}
        assert c1.id in ids
        assert c2.id in ids
        assert c3.id in ids

    @pytest.mark.asyncio
    async def test_list_collections_pagination(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test listing collections with pagination."""
        # Create 5 collections
        for i in range(5):
            await service.create_collection(sample_user.id, f"Collection {i}")

        # Get first 2
        page1 = await service.list_user_collections(
            user_id=sample_user.id,
            limit=2,
            offset=0
        )
        assert len(page1) == 2

        # Get next 2
        page2 = await service.list_user_collections(
            user_id=sample_user.id,
            limit=2,
            offset=2
        )
        assert len(page2) == 2

        # Verify no overlap
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert page1_ids.isdisjoint(page2_ids)


# ==================== Item Management Tests ====================


class TestAddItemToCollection:
    """Tests for add_item_to_collection method."""

    @pytest.mark.asyncio
    async def test_add_item_success(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test adding item to collection."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        item = await service.add_item_to_collection(
            collection_id=collection.id,
            listing_id=sample_listing.id,
            user_id=sample_user.id,
            status="undecided",
            notes="Great deal"
        )

        assert item.id is not None
        assert item.collection_id == collection.id
        assert item.listing_id == sample_listing.id
        assert item.status == "undecided"
        assert item.notes == "Great deal"
        assert item.position is not None

    @pytest.mark.asyncio
    async def test_add_item_duplicate(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test adding duplicate item to collection."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        # Add item first time
        await service.add_item_to_collection(
            collection_id=collection.id,
            listing_id=sample_listing.id,
            user_id=sample_user.id
        )

        # Try to add same item again
        with pytest.raises(ValueError, match="already exists in collection"):
            await service.add_item_to_collection(
                collection_id=collection.id,
                listing_id=sample_listing.id,
                user_id=sample_user.id
            )

    @pytest.mark.asyncio
    async def test_add_item_invalid_status(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test adding item with invalid status."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        with pytest.raises(ValueError, match="Status must be one of"):
            await service.add_item_to_collection(
                collection_id=collection.id,
                listing_id=sample_listing.id,
                user_id=sample_user.id,
                status="invalid_status"
            )

    @pytest.mark.asyncio
    async def test_add_item_unauthorized(
        self,
        service: CollectionsService,
        sample_user: User,
        other_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test adding item to collection by non-owner."""
        collection = await service.create_collection(
            user_id=sample_user.id,
            name="Test"
        )

        with pytest.raises(ValueError, match="not found"):
            await service.add_item_to_collection(
                collection_id=collection.id,
                listing_id=sample_listing.id,
                user_id=other_user.id  # Wrong user!
            )


class TestUpdateCollectionItem:
    """Tests for update_collection_item method."""

    @pytest.mark.asyncio
    async def test_update_item_status(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test updating item status."""
        collection = await service.create_collection(sample_user.id, "Test")
        item = await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )

        updated = await service.update_collection_item(
            item_id=item.id,
            user_id=sample_user.id,
            status="shortlisted"
        )

        assert updated is not None
        assert updated.status == "shortlisted"

    @pytest.mark.asyncio
    async def test_update_item_notes(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test updating item notes."""
        collection = await service.create_collection(sample_user.id, "Test")
        item = await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )

        updated = await service.update_collection_item(
            item_id=item.id,
            user_id=sample_user.id,
            notes="Updated notes"
        )

        assert updated.notes == "Updated notes"

    @pytest.mark.asyncio
    async def test_update_item_position(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test updating item position."""
        collection = await service.create_collection(sample_user.id, "Test")
        item = await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )

        updated = await service.update_collection_item(
            item_id=item.id,
            user_id=sample_user.id,
            position=99
        )

        assert updated.position == 99

    @pytest.mark.asyncio
    async def test_update_item_invalid_status(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test updating item with invalid status."""
        collection = await service.create_collection(sample_user.id, "Test")
        item = await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )

        with pytest.raises(ValueError, match="Status must be one of"):
            await service.update_collection_item(
                item_id=item.id,
                user_id=sample_user.id,
                status="invalid"
            )

    @pytest.mark.asyncio
    async def test_update_item_unauthorized(
        self,
        service: CollectionsService,
        sample_user: User,
        other_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test updating item by non-owner."""
        collection = await service.create_collection(sample_user.id, "Test")
        item = await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )

        with pytest.raises(PermissionError, match="does not own collection"):
            await service.update_collection_item(
                item_id=item.id,
                user_id=other_user.id,
                status="bought"
            )


class TestRemoveItemFromCollection:
    """Tests for remove_item_from_collection method."""

    @pytest.mark.asyncio
    async def test_remove_item_success(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test removing item from collection."""
        collection = await service.create_collection(sample_user.id, "Test")
        item = await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )

        success = await service.remove_item_from_collection(
            item_id=item.id,
            user_id=sample_user.id
        )

        assert success is True

        # Verify removed
        result = await db_session.execute(
            select(CollectionItem).where(CollectionItem.id == item.id)
        )
        removed = result.scalar_one_or_none()
        assert removed is None

    @pytest.mark.asyncio
    async def test_remove_item_not_found(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test removing non-existent item."""
        success = await service.remove_item_from_collection(
            item_id=999,
            user_id=sample_user.id
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_remove_item_unauthorized(
        self,
        service: CollectionsService,
        sample_user: User,
        other_user: User,
        sample_listing: Listing,
        db_session: AsyncSession
    ):
        """Test removing item by non-owner."""
        collection = await service.create_collection(sample_user.id, "Test")
        item = await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )

        with pytest.raises(PermissionError, match="does not own collection"):
            await service.remove_item_from_collection(
                item_id=item.id,
                user_id=other_user.id
            )


# ==================== Queries & Filtering Tests ====================


class TestGetCollectionItems:
    """Tests for get_collection_items method."""

    @pytest.mark.asyncio
    async def test_get_items_empty(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test getting items from empty collection."""
        collection = await service.create_collection(sample_user.id, "Test")

        items = await service.get_collection_items(
            collection_id=collection.id,
            user_id=sample_user.id
        )

        assert items == []

    @pytest.mark.asyncio
    async def test_get_items_multiple(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        another_listing: Listing,
        db_session: AsyncSession
    ):
        """Test getting multiple items."""
        collection = await service.create_collection(sample_user.id, "Test")

        # Add 2 items
        await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id
        )
        await service.add_item_to_collection(
            collection.id,
            another_listing.id,
            sample_user.id
        )

        items = await service.get_collection_items(
            collection_id=collection.id,
            user_id=sample_user.id
        )

        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_get_items_filter_by_status(
        self,
        service: CollectionsService,
        sample_user: User,
        sample_listing: Listing,
        another_listing: Listing,
        db_session: AsyncSession
    ):
        """Test filtering items by status."""
        collection = await service.create_collection(sample_user.id, "Test")

        # Add items with different statuses
        await service.add_item_to_collection(
            collection.id,
            sample_listing.id,
            sample_user.id,
            status="undecided"
        )
        await service.add_item_to_collection(
            collection.id,
            another_listing.id,
            sample_user.id,
            status="shortlisted"
        )

        # Get only shortlisted items
        shortlisted = await service.get_collection_items(
            collection_id=collection.id,
            user_id=sample_user.id,
            status_filter="shortlisted"
        )

        assert len(shortlisted) == 1
        assert shortlisted[0].status == "shortlisted"

    @pytest.mark.asyncio
    async def test_get_items_unauthorized(
        self,
        service: CollectionsService,
        sample_user: User,
        other_user: User,
        db_session: AsyncSession
    ):
        """Test getting items by non-owner."""
        collection = await service.create_collection(sample_user.id, "Test")

        with pytest.raises(PermissionError, match="does not own collection"):
            await service.get_collection_items(
                collection_id=collection.id,
                user_id=other_user.id
            )


class TestGetOrCreateDefaultCollection:
    """Tests for get_or_create_default_collection method."""

    @pytest.mark.asyncio
    async def test_create_default_collection(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test creating default collection when none exists."""
        collection = await service.get_or_create_default_collection(sample_user.id)

        assert collection.id is not None
        assert collection.name == "My Deals"
        assert collection.visibility == "private"

    @pytest.mark.asyncio
    async def test_get_existing_default_collection(
        self, service: CollectionsService, sample_user: User, db_session: AsyncSession
    ):
        """Test getting existing default collection."""
        # Create default collection
        first = await service.get_or_create_default_collection(sample_user.id)

        # Get it again (should return same one)
        second = await service.get_or_create_default_collection(sample_user.id)

        assert first.id == second.id
