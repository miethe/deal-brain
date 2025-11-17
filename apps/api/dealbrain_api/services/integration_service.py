"""Business logic for integrating shares with collections.

This module provides the service layer for share-to-collection workflows including:
- Importing shared deals to collections
- Duplicate detection and prevention
- Bulk import operations
- Cross-service coordination between sharing and collections
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sharing import Collection, CollectionItem, ListingShare, UserShare
from .collections_service import CollectionsService
from .sharing_service import SharingService

logger = logging.getLogger(__name__)


class IntegrationService:
    """Business logic for integrating shares with collections.

    Coordinates between SharingService and CollectionsService to provide
    seamless workflows for importing shared deals into collections.

    Args:
        session: Async SQLAlchemy session for database operations
    """

    def __init__(self, session: AsyncSession):
        """Initialize service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.sharing_service = SharingService(session)
        self.collections_service = CollectionsService(session)

    async def import_shared_deal(
        self,
        share_token: str,
        user_id: int,
        collection_id: Optional[int] = None
    ) -> tuple[CollectionItem, Collection]:
        """Import shared deal to collection.

        Imports a shared listing (either public ListingShare or UserShare)
        into a user's collection. If no collection is specified, uses or
        creates a default collection.

        Args:
            share_token: Share token (ListingShare or UserShare)
            user_id: User ID importing the deal
            collection_id: Optional collection ID (creates default if None)

        Returns:
            Tuple of (CollectionItem, Collection)

        Raises:
            ValueError: If share not found, expired, or duplicate
            PermissionError: If user not authorized for UserShare

        Example:
            # Import public share
            item, collection = await service.import_shared_deal(
                share_token="abc123...",
                user_id=1,
                collection_id=5
            )

            # Import to default collection
            item, collection = await service.import_shared_deal(
                share_token="xyz789...",
                user_id=2
            )
        """
        # 1. Try to find share (could be ListingShare or UserShare)
        listing_share = await self.sharing_service.share_repo.get_listing_share_by_token(
            share_token
        )
        user_share = await self.sharing_service.share_repo.get_user_share_by_token(
            share_token
        )

        # Determine which type of share this is
        if user_share:
            # UserShare - verify user is recipient
            if user_share.recipient_id != user_id:
                raise PermissionError(
                    f"User {user_id} is not the recipient of this share"
                )

            if user_share.is_expired():
                raise ValueError("This share has expired")

            listing_id = user_share.listing_id
            share_type = "user_share"

        elif listing_share:
            # ListingShare - anyone can import
            if listing_share.is_expired():
                raise ValueError("This share has expired")

            listing_id = listing_share.listing_id
            share_type = "listing_share"

        else:
            raise ValueError(f"Share with token '{share_token}' not found")

        # 2. Get or create collection
        if collection_id is None:
            collection = await self.collections_service.get_or_create_default_collection(
                user_id
            )
            collection_id = collection.id
        else:
            # Verify ownership
            collection = await self.collections_service.get_collection(
                collection_id=collection_id,
                user_id=user_id,
                load_items=False
            )
            if not collection:
                raise ValueError(f"Collection {collection_id} not found")

        # 3. Check for duplicate
        duplicate = await self.check_duplicate_in_collection(
            listing_id=listing_id,
            collection_id=collection_id
        )

        if duplicate:
            raise ValueError(
                f"Listing {listing_id} already exists in collection {collection_id}"
            )

        # 4. Add item to collection
        notes = None
        if share_type == "user_share" and user_share.message:
            notes = f"Shared: {user_share.message}"

        item = await self.collections_service.add_item_to_collection(
            collection_id=collection_id,
            listing_id=listing_id,
            user_id=user_id,
            status="undecided",
            notes=notes
        )

        # 5. Mark share as imported (if UserShare)
        if share_type == "user_share":
            await self.sharing_service.share_repo.mark_share_imported(user_share.id)

        await self.session.commit()

        logger.info(
            f"Imported {share_type} {share_token[:8]}... (listing {listing_id}) "
            f"to collection {collection_id} for user {user_id}"
        )

        return (item, collection)

    async def check_duplicate_in_collection(
        self,
        listing_id: int,
        collection_id: int
    ) -> bool:
        """Check if listing already exists in collection.

        Args:
            listing_id: Listing ID
            collection_id: Collection ID

        Returns:
            True if listing exists in collection, False otherwise

        Example:
            is_duplicate = await service.check_duplicate_in_collection(
                listing_id=123,
                collection_id=5
            )
        """
        exists = await self.collections_service.collection_repo.check_item_exists(
            collection_id=collection_id,
            listing_id=listing_id
        )

        return exists

    async def bulk_import_shares(
        self,
        share_tokens: list[str],
        user_id: int,
        collection_id: Optional[int] = None
    ) -> dict[str, CollectionItem | str]:
        """Import multiple shares at once.

        Attempts to import multiple shared deals into a collection. Skips
        duplicates and records errors for invalid shares.

        Args:
            share_tokens: List of share tokens to import
            user_id: User ID importing the deals
            collection_id: Optional collection ID (creates default if None)

        Returns:
            Dictionary mapping token to either:
            - CollectionItem: Successfully imported item
            - str: Error message if import failed

        Example:
            results = await service.bulk_import_shares(
                share_tokens=["abc123", "def456", "ghi789"],
                user_id=1,
                collection_id=5
            )

            for token, result in results.items():
                if isinstance(result, CollectionItem):
                    print(f"{token}: Success")
                else:
                    print(f"{token}: Error - {result}")
        """
        results: dict[str, CollectionItem | str] = {}

        # Get or create collection once
        if collection_id is None:
            collection = await self.collections_service.get_or_create_default_collection(
                user_id
            )
            collection_id = collection.id

        # Process each token
        for token in share_tokens:
            try:
                item, _ = await self.import_shared_deal(
                    share_token=token,
                    user_id=user_id,
                    collection_id=collection_id
                )
                results[token] = item

            except ValueError as e:
                # Invalid token, expired, or duplicate
                results[token] = str(e)

            except PermissionError as e:
                # User not authorized
                results[token] = str(e)

            except Exception as e:
                # Unexpected error
                logger.error(f"Error importing share {token}: {e}")
                results[token] = f"Unexpected error: {str(e)}"

        # Commit all successful imports
        await self.session.commit()

        success_count = sum(
            1 for v in results.values() if isinstance(v, CollectionItem)
        )
        error_count = len(results) - success_count

        logger.info(
            f"Bulk import for user {user_id}: {success_count} success, "
            f"{error_count} errors"
        )

        return results
