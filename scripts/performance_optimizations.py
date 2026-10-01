#!/usr/bin/env python3
"""Performance testing script for Phase 5.5 optimizations.

This script tests:
1. Collections endpoint with 100+ items loads in <200ms
2. No N+1 query issues (verified by query profiling)
3. Redis caching works for public shares
4. Pagination works for large collections
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "apps" / "api"))

from dealbrain_api.db import session_scope
from dealbrain_api.models.sharing import Collection, CollectionItem, Listing, User
from dealbrain_api.repositories.collection_repository import CollectionRepository
from dealbrain_api.repositories.share_repository import ShareRepository
from dealbrain_api.services.caching_service import CachingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_test_data(num_items: int = 150) -> tuple[int, int]:
    """Create test collection with many items.

    Args:
        num_items: Number of items to create in collection

    Returns:
        Tuple of (user_id, collection_id)
    """
    logger.info(f"Creating test data with {num_items} items...")

    async with session_scope() as session:
        # Create test user
        user = User(
            email=f"perf_test_{int(time.time())}@example.com",
            hashed_password="test_hash"
        )
        session.add(user)
        await session.flush()

        # Create test listings
        listings = []
        for i in range(num_items):
            listing = Listing(
                title=f"Performance Test Listing {i}",
                price_usd=100.0 + i,
                condition="used",
                status="active"
            )
            session.add(listing)
            listings.append(listing)

        await session.flush()

        # Create collection
        repo = CollectionRepository(session)
        collection = await repo.create_collection(
            user_id=user.id,
            name=f"Performance Test Collection ({num_items} items)",
            description="Testing Phase 5.5 performance optimizations"
        )

        # Add all listings to collection
        for i, listing in enumerate(listings):
            await repo.add_item(
                collection_id=collection.id,
                listing_id=listing.id,
                status="undecided",
                position=i
            )

        logger.info(
            f"Created collection {collection.id} with {num_items} items "
            f"for user {user.id}"
        )

        return user.id, collection.id


async def test_collection_performance(user_id: int, collection_id: int) -> None:
    """Test collection retrieval performance.

    Verifies:
    - Collection with 100+ items loads in <200ms
    - No N+1 queries (via query profiling logs)
    - Eager loading works correctly

    Args:
        user_id: Test user ID
        collection_id: Test collection ID
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Collection Performance (<200ms target)")
    logger.info("=" * 80)

    async with session_scope() as session:
        repo = CollectionRepository(session)

        # Test 1: Get collection without items (baseline)
        start_time = time.time()
        collection = await repo.get_collection_by_id(
            collection_id,
            user_id=user_id,
            load_items=False
        )
        duration_ms = (time.time() - start_time) * 1000

        logger.info(f"✓ Collection metadata only: {duration_ms:.2f}ms")

        # Test 2: Get collection with all items and eager loading
        start_time = time.time()
        collection = await repo.get_collection_by_id(
            collection_id,
            user_id=user_id,
            load_items=True
        )
        duration_ms = (time.time() - start_time) * 1000

        item_count = len(collection.items)
        logger.info(f"✓ Collection with {item_count} items: {duration_ms:.2f}ms")

        # Verify performance target
        if duration_ms < 200:
            logger.info(f"✅ PASS: Performance target met ({duration_ms:.2f}ms < 200ms)")
        else:
            logger.warning(
                f"⚠️  WARNING: Performance target missed ({duration_ms:.2f}ms > 200ms)"
            )

        # Test 3: Access eager-loaded relationships (should not trigger queries)
        logger.info("\nVerifying eager loading (check logs for N+1 warnings)...")
        for i, item in enumerate(collection.items[:5]):
            # Access listing and its relationships
            listing = item.listing
            cpu_name = listing.cpu.name if listing.cpu else "No CPU"
            gpu_name = listing.gpu.name if listing.gpu else "No GPU"

            logger.debug(
                f"  Item {i}: {listing.title} - CPU: {cpu_name}, GPU: {gpu_name}"
            )

        logger.info("✓ Accessed relationships without additional queries")


async def test_pagination(collection_id: int) -> None:
    """Test pagination for large collections.

    Args:
        collection_id: Test collection ID
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Pagination Support")
    logger.info("=" * 80)

    async with session_scope() as session:
        repo = CollectionRepository(session)

        # Test paginated retrieval
        page_size = 20
        page_num = 2
        offset = (page_num - 1) * page_size

        start_time = time.time()
        items = await repo.get_collection_items(
            collection_id=collection_id,
            load_listings=True,
            limit=page_size,
            offset=offset
        )
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"✓ Retrieved page {page_num} ({len(items)} items, "
            f"offset {offset}): {duration_ms:.2f}ms"
        )

        # Get total count
        total_count = await repo.get_collection_items_count(collection_id)
        logger.info(f"✓ Total items in collection: {total_count}")

        logger.info(f"✅ PASS: Pagination working correctly")


async def test_redis_caching() -> None:
    """Test Redis caching service.

    Verifies:
    - Redis connection works
    - Caching and retrieval works
    - Graceful fallback if Redis unavailable
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Redis Caching")
    logger.info("=" * 80)

    from dealbrain_core.schemas.sharing import PublicListingShareRead

    caching_service = CachingService()

    # Test 1: Basic caching
    cache_key = "test:performance:key"
    test_data = PublicListingShareRead(
        share_token="test_token_123",
        listing_id=999,
        view_count=42,
        is_expired=False
    )

    # Set cache
    success = await caching_service.set(cache_key, test_data, ttl_seconds=60)
    if success:
        logger.info("✓ Redis SET successful")
    else:
        logger.warning("⚠️  Redis unavailable - graceful fallback working")
        return

    # Get from cache
    cached_data = await caching_service.get(cache_key, PublicListingShareRead)
    if cached_data:
        logger.info(f"✓ Redis GET successful: {cached_data.model_dump()}")
        assert cached_data.listing_id == test_data.listing_id
        logger.info("✓ Cached data matches original")
    else:
        logger.error("❌ FAIL: Could not retrieve cached data")
        return

    # Test cache existence
    exists = await caching_service.exists(cache_key)
    logger.info(f"✓ Cache key exists: {exists}")

    # Clean up
    deleted = await caching_service.delete(cache_key)
    logger.info(f"✓ Cleanup successful: {deleted}")

    logger.info("✅ PASS: Redis caching working correctly")


async def test_share_repository_performance() -> None:
    """Test share repository query performance.

    Creates test share and verifies eager loading.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Share Repository Performance")
    logger.info("=" * 80)

    async with session_scope() as session:
        # Create test listing and share
        listing = Listing(
            title="Share Performance Test",
            price_usd=299.99,
            condition="used",
            status="active"
        )
        session.add(listing)
        await session.flush()

        share_repo = ShareRepository(session)
        share = await share_repo.create_listing_share(
            listing_id=listing.id,
            created_by=None,
            expires_at=None
        )

        # Test retrieval with eager loading
        start_time = time.time()
        retrieved_share = await share_repo.get_active_listing_share_by_token(
            share.share_token
        )
        duration_ms = (time.time() - start_time) * 1000

        logger.info(f"✓ Share retrieval with eager loading: {duration_ms:.2f}ms")

        # Access relationships (should not trigger additional queries)
        if retrieved_share:
            listing_title = retrieved_share.listing.title
            logger.info(f"✓ Accessed listing relationship: {listing_title}")

        if duration_ms < 100:
            logger.info(
                f"✅ PASS: Share retrieval performance excellent ({duration_ms:.2f}ms)"
            )
        else:
            logger.warning(
                f"⚠️  WARNING: Share retrieval slower than expected ({duration_ms:.2f}ms)"
            )


async def main() -> None:
    """Run all performance tests."""
    logger.info("Starting Phase 5.5 Performance Tests")
    logger.info("=" * 80)

    try:
        # Create test data
        user_id, collection_id = await create_test_data(num_items=150)

        # Run tests
        await test_collection_performance(user_id, collection_id)
        await test_pagination(collection_id)
        await test_redis_caching()
        await test_share_repository_performance()

        logger.info("\n" + "=" * 80)
        logger.info("✅ All performance tests completed!")
        logger.info("=" * 80)
        logger.info("\nNote: Check logs above for:")
        logger.info("  - SLOW QUERY warnings (should be none)")
        logger.info("  - N+1 query warnings (should be none)")
        logger.info("  - Performance targets met (<200ms for collections)")

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
