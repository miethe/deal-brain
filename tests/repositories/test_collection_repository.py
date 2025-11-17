"""Tests for CollectionRepository (Phase 1.3: Repository Layer).

This test suite verifies:
- Collection CRUD operations with ownership validation
- Collection item management with deduplication
- Position-based ordering
- Query optimization (eager loading)
- Access control and authorization
- Error handling and edge cases

Target: >90% code coverage
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.dealbrain_api.db import Base
from apps.api.dealbrain_api.models.listings import Listing
from apps.api.dealbrain_api.models.sharing import Collection, CollectionItem, User
from apps.api.dealbrain_api.repositories.collection_repository import CollectionRepository

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
    """Create CollectionRepository instance with test session."""
    return CollectionRepository(session)


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
class TestCreateCollection:
    """Test CollectionRepository.create_collection() method."""

    async def test_create_minimal_collection(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test creating collection with minimal fields."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="My Collection"
        )
        await session.commit()

        assert collection.id is not None
        assert collection.user_id == sample_user.id
        assert collection.name == "My Collection"
        assert collection.description is None
        assert collection.visibility == "private"
        assert collection.created_at is not None
        assert collection.updated_at is not None

    async def test_create_collection_with_all_fields(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test creating collection with all optional fields."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Public Collection",
            description="A collection of great deals",
            visibility="public"
        )
        await session.commit()

        assert collection.name == "Public Collection"
        assert collection.description == "A collection of great deals"
        assert collection.visibility == "public"


@pytest.mark.asyncio
class TestGetCollectionById:
    """Test CollectionRepository.get_collection_by_id() method."""

    async def test_get_existing_collection(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test retrieving existing collection by ID."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        retrieved = await repository.get_collection_by_id(collection.id)

        assert retrieved is not None
        assert retrieved.id == collection.id
        assert retrieved.name == "Test Collection"
        # Verify user eager loaded
        assert retrieved.user is not None
        assert retrieved.user.id == sample_user.id

    async def test_get_collection_nonexistent(
        self,
        repository: CollectionRepository
    ):
        """Test getting collection that doesn't exist."""
        retrieved = await repository.get_collection_by_id(99999)
        assert retrieved is None

    async def test_get_collection_with_items(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test getting collection with eager-loaded items."""
        # Create collection
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        # Add items
        for i in range(3):
            await repository.add_item(
                collection_id=collection.id,
                listing_id=sample_listing.id
            )
        await session.commit()

        # Get with items loaded
        retrieved = await repository.get_collection_by_id(
            collection.id,
            load_items=True
        )

        assert retrieved is not None
        assert len(retrieved.items) == 3

    async def test_get_collection_access_control(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test access control for private collections."""
        # Create collection owned by user 1
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Private Collection"
        )
        await session.commit()

        # Owner can access
        retrieved = await repository.get_collection_by_id(
            collection.id,
            user_id=sample_user.id
        )
        assert retrieved is not None

        # Non-owner cannot access
        retrieved = await repository.get_collection_by_id(
            collection.id,
            user_id=999  # Different user
        )
        assert retrieved is None


@pytest.mark.asyncio
class TestUpdateCollection:
    """Test CollectionRepository.update_collection() method."""

    async def test_update_collection_name(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test updating collection name."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Original Name"
        )
        await session.commit()

        updated = await repository.update_collection(
            collection_id=collection.id,
            user_id=sample_user.id,
            name="Updated Name"
        )
        await session.commit()

        assert updated.name == "Updated Name"

    async def test_update_collection_all_fields(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test updating all collection fields."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Original Name",
            description="Original description",
            visibility="private"
        )
        await session.commit()

        updated = await repository.update_collection(
            collection_id=collection.id,
            user_id=sample_user.id,
            name="Updated Name",
            description="Updated description",
            visibility="public"
        )
        await session.commit()

        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.visibility == "public"

    async def test_update_collection_access_denied(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test that non-owners cannot update collections."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="User 1 Collection"
        )
        await session.commit()

        # User 2 attempts to update
        with pytest.raises(ValueError, match="not found or access denied"):
            await repository.update_collection(
                collection_id=collection.id,
                user_id=999,  # Different user
                name="Hacked Name"
            )

    async def test_update_nonexistent_collection(
        self,
        repository: CollectionRepository
    ):
        """Test error when updating non-existent collection."""
        with pytest.raises(ValueError, match="not found or access denied"):
            await repository.update_collection(
                collection_id=99999,
                user_id=1,
                name="New Name"
            )


@pytest.mark.asyncio
class TestDeleteCollection:
    """Test CollectionRepository.delete_collection() method."""

    async def test_delete_collection(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test deleting collection."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Collection to Delete"
        )
        await session.commit()

        collection_id = collection.id

        # Delete collection
        result = await repository.delete_collection(collection_id, sample_user.id)
        await session.commit()

        assert result is True

        # Verify collection is deleted
        retrieved = await repository.get_collection_by_id(collection_id)
        assert retrieved is None

    async def test_delete_collection_cascade_deletes_items(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test that deleting collection also deletes items."""
        # Create collection
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Collection to Delete"
        )
        await session.commit()

        # Add items
        for i in range(3):
            await repository.add_item(
                collection_id=collection.id,
                listing_id=sample_listing.id
            )
        await session.commit()

        # Delete collection
        await repository.delete_collection(collection.id, sample_user.id)
        await session.commit()

        # Verify items are deleted
        items = await repository.get_collection_items(collection.id)
        assert len(items) == 0

    async def test_delete_collection_access_denied(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test that non-owners cannot delete collections."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="User 1 Collection"
        )
        await session.commit()

        # User 2 attempts to delete
        with pytest.raises(ValueError, match="not found or access denied"):
            await repository.delete_collection(collection.id, user_id=999)


@pytest.mark.asyncio
class TestFindUserCollections:
    """Test CollectionRepository.find_user_collections() method."""

    async def test_find_user_collections(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test finding collections for a user."""
        # Create multiple collections
        for i in range(5):
            await repository.create_collection(
                user_id=sample_user.id,
                name=f"Collection {i}"
            )
        await session.commit()

        # Find collections
        collections = await repository.find_user_collections(sample_user.id)

        assert len(collections) == 5
        # Verify ordering (newest first)
        for i in range(len(collections) - 1):
            assert collections[i].created_at >= collections[i + 1].created_at

    async def test_find_user_collections_with_pagination(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test pagination for user collections."""
        # Create 10 collections
        for i in range(10):
            await repository.create_collection(
                user_id=sample_user.id,
                name=f"Collection {i}"
            )
        await session.commit()

        # Get first page
        page1 = await repository.find_user_collections(sample_user.id, limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await repository.find_user_collections(sample_user.id, limit=5, offset=5)
        assert len(page2) == 5

        # Verify no overlap
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert len(page1_ids & page2_ids) == 0

    async def test_find_user_collections_empty(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test finding collections for user with no collections."""
        collections = await repository.find_user_collections(sample_user.id)
        assert len(collections) == 0


@pytest.mark.asyncio
class TestAddItem:
    """Test CollectionRepository.add_item() method."""

    async def test_add_item_to_collection(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test adding item to collection."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        item = await repository.add_item(
            collection_id=collection.id,
            listing_id=sample_listing.id
        )
        await session.commit()

        assert item.id is not None
        assert item.collection_id == collection.id
        assert item.listing_id == sample_listing.id
        assert item.status == "undecided"
        assert item.notes is None
        assert item.position == 0  # First item

    async def test_add_item_with_all_fields(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test adding item with all optional fields."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        item = await repository.add_item(
            collection_id=collection.id,
            listing_id=sample_listing.id,
            status="shortlisted",
            notes="Great deal!",
            position=5
        )
        await session.commit()

        assert item.status == "shortlisted"
        assert item.notes == "Great deal!"
        assert item.position == 5

    async def test_add_item_deduplication(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test that duplicate items are prevented."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        # Add item
        await repository.add_item(
            collection_id=collection.id,
            listing_id=sample_listing.id
        )
        await session.commit()

        # Attempt to add duplicate
        with pytest.raises(ValueError, match="already exists in collection"):
            await repository.add_item(
                collection_id=collection.id,
                listing_id=sample_listing.id
            )

    async def test_add_item_auto_position(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test automatic position assignment."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        # Add multiple items
        item1 = await repository.add_item(collection.id, sample_listing.id)
        await session.commit()

        # Create another listing for second item
        listing2 = Listing(name="PC Build 2", base_price=1200.0, adjusted_price=1150.0)
        session.add(listing2)
        await session.flush()

        item2 = await repository.add_item(collection.id, listing2.id)
        await session.commit()

        assert item1.position == 0
        assert item2.position == 1


@pytest.mark.asyncio
class TestUpdateItem:
    """Test CollectionRepository.update_item() method."""

    async def test_update_item_status(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test updating item status."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        item = await repository.add_item(collection.id, sample_listing.id)
        await session.commit()

        updated = await repository.update_item(
            item_id=item.id,
            status="shortlisted"
        )
        await session.commit()

        assert updated.status == "shortlisted"

    async def test_update_item_notes(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test updating item notes."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        item = await repository.add_item(collection.id, sample_listing.id)
        await session.commit()

        updated = await repository.update_item(
            item_id=item.id,
            notes="This is a great deal!"
        )
        await session.commit()

        assert updated.notes == "This is a great deal!"

    async def test_update_item_position(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test updating item position."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        item = await repository.add_item(collection.id, sample_listing.id)
        await session.commit()

        updated = await repository.update_item(
            item_id=item.id,
            position=10
        )
        await session.commit()

        assert updated.position == 10

    async def test_update_nonexistent_item(
        self,
        repository: CollectionRepository
    ):
        """Test updating non-existent item."""
        updated = await repository.update_item(
            item_id=99999,
            status="shortlisted"
        )
        assert updated is None


@pytest.mark.asyncio
class TestRemoveItem:
    """Test CollectionRepository.remove_item() method."""

    async def test_remove_item(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test removing item from collection."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        item = await repository.add_item(collection.id, sample_listing.id)
        await session.commit()

        item_id = item.id

        # Remove item
        result = await repository.remove_item(item_id)
        await session.commit()

        assert result is True

        # Verify item is deleted
        from sqlalchemy import select
        stmt = select(CollectionItem).where(CollectionItem.id == item_id)
        result = await session.execute(stmt)
        assert result.scalar_one_or_none() is None

    async def test_remove_nonexistent_item(
        self,
        repository: CollectionRepository
    ):
        """Test removing non-existent item."""
        result = await repository.remove_item(99999)
        assert result is False


@pytest.mark.asyncio
class TestGetCollectionItems:
    """Test CollectionRepository.get_collection_items() method."""

    async def test_get_collection_items(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test getting all items in collection."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        # Add items
        for i in range(3):
            await repository.add_item(collection.id, sample_listing.id)
            # Create new listing for next iteration
            if i < 2:
                listing = Listing(
                    name=f"PC Build {i+2}",
                    base_price=1000.0 + i * 100,
                    adjusted_price=950.0 + i * 100
                )
                session.add(listing)
                await session.flush()
                sample_listing = listing

        await session.commit()

        # Get items
        items = await repository.get_collection_items(collection.id)

        assert len(items) == 3
        # Verify ordering by position
        for i in range(len(items)):
            assert items[i].position == i

    async def test_get_collection_items_with_listings(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test eager loading of listings."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        await repository.add_item(collection.id, sample_listing.id)
        await session.commit()

        # Get items with listings loaded
        items = await repository.get_collection_items(
            collection.id,
            load_listings=True
        )

        assert len(items) == 1
        # Verify eager loading worked
        assert items[0].listing is not None
        assert items[0].listing.name == "Test PC Build"


@pytest.mark.asyncio
class TestCheckItemExists:
    """Test CollectionRepository.check_item_exists() method."""

    async def test_check_item_exists_true(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test checking if item exists returns True."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        await repository.add_item(collection.id, sample_listing.id)
        await session.commit()

        exists = await repository.check_item_exists(collection.id, sample_listing.id)
        assert exists is True

    async def test_check_item_exists_false(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test checking if item exists returns False."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        exists = await repository.check_item_exists(collection.id, sample_listing.id)
        assert exists is False


@pytest.mark.asyncio
class TestGetNextPosition:
    """Test CollectionRepository.get_next_position() method."""

    async def test_get_next_position_empty_collection(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User
    ):
        """Test getting next position for empty collection."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        next_pos = await repository.get_next_position(collection.id)
        assert next_pos == 0

    async def test_get_next_position_with_items(
        self,
        repository: CollectionRepository,
        session: AsyncSession,
        sample_user: User,
        sample_listing: Listing
    ):
        """Test getting next position with existing items."""
        collection = await repository.create_collection(
            user_id=sample_user.id,
            name="Test Collection"
        )
        await session.commit()

        # Add items
        for i in range(3):
            await repository.add_item(collection.id, sample_listing.id)
            # Create new listing for next iteration
            if i < 2:
                listing = Listing(
                    name=f"PC Build {i+2}",
                    base_price=1000.0 + i * 100,
                    adjusted_price=950.0 + i * 100
                )
                session.add(listing)
                await session.flush()
                sample_listing = listing

        await session.commit()

        next_pos = await repository.get_next_position(collection.id)
        assert next_pos == 3  # 0, 1, 2 exist, next is 3
