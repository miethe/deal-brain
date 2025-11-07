"""Deduplication logic for URL ingestion.

This module implements deduplication strategies for preventing duplicate listings
when importing from URLs. It uses a hybrid approach:

1. Primary: (marketplace, vendor_item_id) for API sources (eBay, Amazon)
2. Secondary: Hash-based for JSON-LD sources without vendor IDs
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal

from dealbrain_api.models.core import Listing
from dealbrain_api.telemetry import get_logger
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("dealbrain.ingestion.deduplication")


@dataclass
class DeduplicationResult:
    """Result of deduplication check.

    Attributes:
        exists: Whether listing already exists in database
        existing_listing: The existing listing if found, None otherwise
        is_exact_match: True if vendor ID match, False if hash match
        confidence: Match confidence (1.0 for vendor ID, 0.95 for hash)
        dedup_hash: SHA-256 hash used for deduplication (if applicable)
    """

    exists: bool
    existing_listing: Listing | None
    is_exact_match: bool
    confidence: float
    dedup_hash: str | None = None


class DeduplicationService:
    """Service for detecting duplicate listings.

    Uses a two-tier deduplication strategy:
    1. Vendor ID match (highest priority, 100% confidence)
    2. Hash-based match (fallback, 95% confidence)

    Hash formula: SHA-256(normalize(title) + normalize(seller) + normalize(price))

    Example:
        >>> async with session_scope() as session:
        ...     service = DeduplicationService(session)
        ...     result = await service.find_existing_listing(normalized_data)
        ...     if result.exists:
        ...         print(f"Duplicate found: {result.existing_listing.id}")
    """

    def __init__(self, session: AsyncSession):
        """Initialize deduplication service.

        Args:
            session: Async SQLAlchemy session for database queries
        """
        self.session = session

    async def find_existing_listing(
        self,
        normalized_data: NormalizedListingSchema,
    ) -> DeduplicationResult:
        """Find existing listing using vendor ID or hash-based deduplication.

        Checks for duplicates in the following order:
        1. Vendor ID + marketplace match (if available)
        2. Hash-based match (title + seller + price)

        Args:
            normalized_data: Normalized listing data from adapter

        Returns:
            DeduplicationResult with exists flag and existing listing if found

        Example:
            >>> normalized = NormalizedListingSchema(
            ...     title="Gaming PC",
            ...     price=Decimal("599.99"),
            ...     vendor_item_id="123456789012",
            ...     marketplace="ebay",
            ...     condition="used"
            ... )
            >>> result = await service.find_existing_listing(normalized)
            >>> print(f"Exists: {result.exists}, Confidence: {result.confidence}")
        """
        # 1. Try vendor_item_id match first (if available)
        if normalized_data.vendor_item_id and normalized_data.marketplace:
            result = await self._check_vendor_id(
                normalized_data.vendor_item_id,
                normalized_data.marketplace,
            )
            if result:
                logger.info(
                    "ingestion.dedup.match",
                    strategy="vendor_id",
                    vendor_item_id=normalized_data.vendor_item_id,
                    marketplace=normalized_data.marketplace,
                    listing_id=result.id,
                    title=result.title,
                    exists=True,
                )
                return DeduplicationResult(
                    exists=True,
                    existing_listing=result,
                    is_exact_match=True,
                    confidence=1.0,
                )

        # 2. Fallback to hash-based dedup
        dedup_hash = self._generate_hash(normalized_data)
        result = await self._check_hash(dedup_hash)

        if result:
            logger.info(
                "ingestion.dedup.match",
                strategy="hash",
                dedup_hash=f"{dedup_hash[:16]}...",
                listing_id=result.id,
                title=result.title,
                exists=True,
            )
            return DeduplicationResult(
                exists=True,
                existing_listing=result,
                is_exact_match=False,
                confidence=0.95,
                dedup_hash=dedup_hash,
            )

        # 3. Not found
        logger.info(
            "ingestion.dedup.new_listing",
            strategy="none",
            dedup_hash=f"{dedup_hash[:16]}...",
            title=normalized_data.title,
            exists=False,
        )
        return DeduplicationResult(
            exists=False,
            existing_listing=None,
            is_exact_match=False,
            confidence=0.0,
            dedup_hash=dedup_hash,
        )

    async def _check_vendor_id(
        self,
        vendor_item_id: str,
        marketplace: str,
    ) -> Listing | None:
        """Check for existing listing by vendor_item_id + marketplace.

        Uses the unique constraint on (vendor_item_id, marketplace) from Phase 1.

        Args:
            vendor_item_id: Marketplace-specific item ID
            marketplace: Marketplace identifier (ebay|amazon|other)

        Returns:
            Existing Listing if found, None otherwise
        """
        stmt = select(Listing).where(
            Listing.vendor_item_id == vendor_item_id,
            Listing.marketplace == marketplace,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_hash(self, dedup_hash: str) -> Listing | None:
        """Check for existing listing by dedup hash.

        Uses indexed dedup_hash column for efficient lookups.

        Note: dedup_hash is not unique, so multiple listings may share
        the same hash. This method returns the first match found.

        Args:
            dedup_hash: SHA-256 hash of normalized listing data

        Returns:
            Existing Listing if found (first match if multiple), None otherwise
        """
        stmt = select(Listing).where(Listing.dedup_hash == dedup_hash)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    def _generate_hash(self, data: NormalizedListingSchema) -> str:
        """Generate SHA-256 hash for deduplication.

        Hash formula: SHA-256(normalize(title) + normalize(seller) + normalize(price))

        Normalization rules:
        - Lowercase
        - Remove extra whitespace (multiple spaces → single space)
        - Remove punctuation (except decimals in price)
        - Strip currency symbols from price

        Args:
            data: Normalized listing data

        Returns:
            64-character SHA-256 hash (hexadecimal)

        Example:
            >>> data = NormalizedListingSchema(
            ...     title="Gaming PC Intel i7",
            ...     price=Decimal("599.99"),
            ...     seller="TechStore",
            ...     marketplace="other",
            ...     condition="used"
            ... )
            >>> hash_value = service._generate_hash(data)
            >>> len(hash_value)
            64
        """
        # 1. Normalize components
        title_norm = self._normalize_text(data.title)
        seller_norm = self._normalize_text(data.seller or "")
        price_norm = self._normalize_price(data.price)

        # 2. Combine with pipe separator
        combined = f"{title_norm}|{seller_norm}|{price_norm}"

        # 3. Hash with SHA-256
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent hashing.

        Applies aggressive normalization:
        - Lowercase
        - Trim leading/trailing whitespace
        - Multiple spaces → single space
        - Remove all punctuation

        Args:
            text: Text to normalize

        Returns:
            Normalized text

        Example:
            >>> service._normalize_text("Gaming  PC!")
            'gaming pc'
            >>> service._normalize_text("  HP EliteDesk  ")
            'hp elitedesk'
        """
        # 1. Lowercase and trim
        text = text.lower().strip()

        # 2. Multiple spaces → single space
        text = re.sub(r"\s+", " ", text)

        # 3. Remove all punctuation (keep only alphanumeric and spaces)
        text = re.sub(r"[^\w\s]", "", text)

        return text

    def _normalize_price(self, price: Decimal) -> str:
        """Normalize price for consistent hashing.

        Formats price as string with exactly 2 decimal places.

        Args:
            price: Price amount (Decimal)

        Returns:
            Price formatted as "XXX.XX" (2 decimal places)

        Example:
            >>> service._normalize_price(Decimal("599.99"))
            '599.99'
            >>> service._normalize_price(Decimal("599.9"))
            '599.90'
            >>> service._normalize_price(Decimal("599"))
            '599.00'
        """
        return f"{price:.2f}"
