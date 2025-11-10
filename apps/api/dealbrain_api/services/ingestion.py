"""Service for URL ingestion deduplication logic.

This module implements deduplication strategies for preventing duplicate listings
when importing from URLs. It uses a hybrid approach:

1. Primary: (marketplace, vendor_item_id) for API sources (eBay, Amazon)
2. Secondary: Hash-based for JSON-LD sources without vendor IDs
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from dealbrain_api.adapters import AdapterRouter
from dealbrain_api.models.core import Listing, RawPayload
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..telemetry import get_logger

logger = get_logger("dealbrain.ingestion")


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

    def _normalize_price(self, price: Decimal | None) -> str:
        """Normalize price for consistent hashing.

        Formats price as string with exactly 2 decimal places.
        Returns empty string for None prices (partial extractions).

        Args:
            price: Price amount (Decimal or None for partial extractions)

        Returns:
            Price formatted as "XXX.XX" (2 decimal places), or empty string if None

        Example:
            >>> service._normalize_price(Decimal("599.99"))
            '599.99'
            >>> service._normalize_price(Decimal("599.9"))
            '599.90'
            >>> service._normalize_price(Decimal("599"))
            '599.00'
            >>> service._normalize_price(None)
            ''
        """
        if price is None:
            return ""
        return f"{price:.2f}"


class ListingNormalizer:
    """Normalizes and enriches listing data from adapters.

    Performs the following transformations:
    1. Currency conversion to USD using fixed exchange rates
    2. Condition string normalization to standard enum values
    3. Spec extraction from descriptions (CPU/RAM/storage)
    4. CPU canonicalization against catalog with benchmark enrichment
    5. Data quality assessment (full/partial based on field coverage)

    Example:
        >>> async with session_scope() as session:
        ...     normalizer = ListingNormalizer(session)
        ...     enriched = await normalizer.normalize(raw_data)
        ...     quality = normalizer.assess_quality(enriched)
        ...     print(f"Enriched CPU: {enriched.cpu_model}, Quality: {quality}")
    """

    # Currency conversion rates (fixed for Phase 2)
    # TODO: Phase 3+ will use live rates API
    CURRENCY_RATES = {
        "USD": Decimal("1.0"),
        "EUR": Decimal("1.08"),  # 1 EUR = 1.08 USD
        "GBP": Decimal("1.27"),  # 1 GBP = 1.27 USD
        "CAD": Decimal("0.74"),  # 1 CAD = 0.74 USD
    }

    # Condition normalization mapping
    CONDITION_MAPPING = {
        "new": "new",
        "brand new": "new",
        "refurb": "refurb",  # Already normalized value
        "seller refurbished": "refurb",
        "manufacturer refurbished": "refurb",
        "refurbished": "refurb",
        "used": "used",
        "pre-owned": "used",
        "open box": "used",
        "for parts": "used",
    }

    # Regex patterns for spec extraction
    CPU_PATTERN = re.compile(
        r"(?:Intel|AMD)?\s*(?:Core)?\s*(i[3579]|Ryzen\s*[3579])\s*-?\s*(\d{4,5}[A-Z0-9]*)",
        re.IGNORECASE,
    )

    RAM_PATTERN = re.compile(
        r"(\d+)\s*GB(?:\s+(?:RAM|DDR[345]|Memory))?",
        re.IGNORECASE,
    )

    STORAGE_PATTERN = re.compile(
        r"(\d+)\s*(GB|TB)\s*(?:SSD|NVMe|HDD|Storage)",
        re.IGNORECASE,
    )

    def __init__(self, session: AsyncSession):
        """Initialize listing normalizer.

        Args:
            session: Async SQLAlchemy session for database queries
        """
        self.session = session

    def _parse_brand_and_model(self, title: str) -> tuple[str | None, str | None]:
        """
        Parse brand and model from product title.

        Examples:
            "MINISFORUM Venus NAB9 Mini PC..." → ("MINISFORUM", "Venus NAB9")
            "Dell OptiPlex 7090 Desktop..." → ("Dell", "OptiPlex 7090")
            "HP EliteDesk 800 G6..." → ("HP", "EliteDesk 800 G6")

        Returns:
            Tuple of (brand, model) or (None, None) if parsing fails
        """
        if not title:
            return None, None

        # Common brand patterns (case-insensitive)
        brand_patterns = [
            r"^(MINISFORUM|Dell|HP|Lenovo|ASUS|Acer|MSI|Gigabyte|Intel|AMD)\s+",
            r"^(NUC|ThinkCentre|OptiPlex|EliteDesk|Pavilion|Inspiron|Latitude)\s+",
        ]

        brand = None
        model = None

        # Try to match brand at start of title
        for pattern in brand_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                brand = match.group(1)
                # Extract model (next 2-3 words after brand)
                remaining = title[match.end() :].strip()
                model_match = re.match(r"^([\w\-]+(?:\s+[\w\-]+){0,2})", remaining)
                if model_match:
                    model = model_match.group(1).strip()
                break

        # If no brand found, try "Model by Brand" pattern
        if not brand:
            match = re.search(r"([\w\-]+(?:\s+[\w\-]+)?)\s+by\s+([\w]+)", title, re.IGNORECASE)
            if match:
                model = match.group(1).strip()
                brand = match.group(2).strip()

        # Clean up
        if brand:
            brand = brand.strip()
        if model:
            model = model.strip()
            # Remove trailing "Mini PC", "Desktop", etc.
            model = re.sub(
                r"\s+(Mini PC|Desktop|Tower|SFF|USFF|Computer|PC).*$",
                "",
                model,
                flags=re.IGNORECASE,
            )

        logger.debug(
            "ingestion.title.parsed",
            title_preview=f"{title[:50]}..." if len(title) > 50 else title,
            brand=brand,
            model=model,
        )

        return brand, model

    async def normalize(
        self,
        raw_data: NormalizedListingSchema,
    ) -> NormalizedListingSchema:
        """Normalize and enrich listing data.

        Applies currency conversion, condition normalization, spec extraction,
        and CPU canonicalization to produce a standardized, enriched listing.

        Args:
            raw_data: Raw normalized data from adapter

        Returns:
            Enriched NormalizedListingSchema with standardized fields

        Example:
            >>> raw = NormalizedListingSchema(
            ...     title="Gaming PC",
            ...     price=Decimal("500"),
            ...     currency="EUR",
            ...     condition="Brand New",
            ...     description="PC with Intel Core i7-12700K, 16GB RAM, 512GB SSD",
            ...     marketplace="other"
            ... )
            >>> enriched = await normalizer.normalize(raw)
            >>> print(f"Price: ${enriched.price}, CPU: {enriched.cpu_model}")
        """
        # 1. Convert currency
        price_usd = self._convert_to_usd(raw_data.price, raw_data.currency)

        # 2. Normalize condition
        condition = self._normalize_condition(raw_data.condition)

        # 3. Extract specs if not already present
        specs = self._extract_specs(raw_data)

        # 4. Canonicalize CPU
        cpu_model = specs.get("cpu_model") or raw_data.cpu_model
        cpu_info = await self._canonicalize_cpu(cpu_model)

        # 5. Parse brand and model from title if not already set
        manufacturer = raw_data.manufacturer
        model_number = raw_data.model_number
        if not manufacturer or not model_number:
            brand, model = self._parse_brand_and_model(raw_data.title)
            if brand and not manufacturer:
                manufacturer = brand
            if model and not model_number:
                model_number = model

        # 6. Build enriched schema
        enriched = NormalizedListingSchema(
            title=raw_data.title,
            price=price_usd,
            currency="USD",  # Always USD after conversion
            condition=condition,
            images=raw_data.images or [],
            seller=raw_data.seller,
            marketplace=raw_data.marketplace,
            vendor_item_id=raw_data.vendor_item_id,
            description=raw_data.description,
            cpu_model=cpu_info.get("name") if cpu_info else cpu_model,
            ram_gb=specs.get("ram_gb") or raw_data.ram_gb,
            storage_gb=specs.get("storage_gb") or raw_data.storage_gb,
            manufacturer=manufacturer,
            model_number=model_number,
        )

        return enriched

    def _convert_to_usd(
        self,
        price: Decimal | None,
        currency: str | None,
    ) -> Decimal | None:
        """Convert price to USD using fixed exchange rates.

        Args:
            price: Original price amount (may be None for partial extractions)
            currency: ISO currency code (USD|EUR|GBP|CAD)

        Returns:
            Price converted to USD (2 decimal places), or None if price is None

        Example:
            >>> normalizer._convert_to_usd(Decimal("500"), "EUR")
            Decimal('540.00')
            >>> normalizer._convert_to_usd(Decimal("599.99"), "USD")
            Decimal('599.99')
            >>> normalizer._convert_to_usd(Decimal("599.99"), "JPY")
            Decimal('599.99')  # Unknown currency defaults to USD
            >>> normalizer._convert_to_usd(None, "USD")
            None  # Partial extraction without price
        """
        # Handle None price (partial extraction)
        if price is None:
            return None

        if not currency or currency not in self.CURRENCY_RATES:
            # Default to USD if unknown currency
            return price.quantize(Decimal("0.01"))

        rate = self.CURRENCY_RATES[currency]
        converted = price * rate
        return converted.quantize(Decimal("0.01"))

    def _normalize_condition(self, condition: str | None) -> str:
        """Normalize condition string to standard enum value.

        Maps various condition strings to standardized Condition enum values
        (new|refurb|used). Defaults to 'used' if unknown.

        Args:
            condition: Raw condition string from adapter

        Returns:
            Normalized condition enum value

        Example:
            >>> normalizer._normalize_condition("Brand New")
            'new'
            >>> normalizer._normalize_condition("Seller refurbished")
            'refurb'
            >>> normalizer._normalize_condition("unknown")
            'used'  # Default to 'used' if unknown
        """
        if not condition:
            return "used"  # Default to 'used'

        condition_lower = condition.lower().strip()
        return self.CONDITION_MAPPING.get(condition_lower, "used")

    def _extract_specs(
        self,
        data: NormalizedListingSchema,
    ) -> dict[str, Any]:
        """Extract CPU/RAM/storage from description if not already present.

        Uses regex patterns to extract hardware specs from product description.
        Only extracts if the field is not already populated in the raw data.

        Args:
            data: Normalized listing data with description

        Returns:
            Dict with extracted cpu_model, ram_gb, storage_gb (if found)

        Example:
            >>> data = NormalizedListingSchema(
            ...     title="PC",
            ...     price=Decimal("599"),
            ...     description="Gaming PC with Intel Core i7-12700K, 16GB RAM, 512GB SSD",
            ...     marketplace="other",
            ...     condition="used"
            ... )
            >>> specs = normalizer._extract_specs(data)
            >>> print(specs)
            {'cpu_model': 'i7-12700K', 'ram_gb': 16, 'storage_gb': 512}
        """
        specs: dict[str, Any] = {}

        if not data.description:
            return specs

        description = data.description

        # Extract CPU if not already present
        if not data.cpu_model:
            cpu_match = self.CPU_PATTERN.search(description)
            if cpu_match:
                # Combine matched groups (e.g., "i7" + "-" + "12700K")
                cpu_model = f"{cpu_match.group(1)}-{cpu_match.group(2)}"
                specs["cpu_model"] = cpu_model.strip()

        # Extract RAM if not already present
        if not data.ram_gb:
            ram_match = self.RAM_PATTERN.search(description)
            if ram_match:
                specs["ram_gb"] = int(ram_match.group(1))

        # Extract storage if not already present
        if not data.storage_gb:
            storage_match = self.STORAGE_PATTERN.search(description)
            if storage_match:
                capacity = int(storage_match.group(1))
                unit = storage_match.group(2).upper()

                # Convert to GB
                if unit == "TB":
                    capacity *= 1024

                specs["storage_gb"] = capacity

        return specs

    async def _canonicalize_cpu(
        self,
        cpu_model: str | None,
    ) -> dict[str, Any] | None:
        """Match CPU string to catalog and enrich with benchmark data.

        Strategies:
        1. Exact match on CPU.name (case-insensitive LIKE)
        2. Return None if no match

        Args:
            cpu_model: Extracted or provided CPU model string

        Returns:
            Dict with name, cpu_mark_multi, cpu_mark_single, igpu_mark if found,
            None otherwise

        Example:
            >>> cpu_info = await normalizer._canonicalize_cpu("Intel Core i7-12700K")
            >>> print(cpu_info)
            {'name': 'Intel Core i7-12700K', 'cpu_mark_multi': 30000, ...}
        """
        from dealbrain_api.models.core import Cpu

        if not cpu_model:
            return None

        # Try LIKE match on CPU name
        # Note: ILIKE with wildcards can match multiple CPUs (e.g., "i7-12700" matches
        # "i7-12700", "i7-12700K", "i7-12700F"), so use .first() instead of .scalar_one_or_none()
        stmt = select(Cpu).where(Cpu.name.ilike(f"%{cpu_model}%"))
        result = await self.session.execute(stmt)
        cpu = result.scalars().first()

        if cpu:
            return {
                "name": cpu.name,
                "cpu_mark_multi": cpu.cpu_mark_multi,
                "cpu_mark_single": cpu.cpu_mark_single,
                "igpu_mark": cpu.igpu_mark,
            }

        return None

    def assess_quality(self, normalized: NormalizedListingSchema) -> str:
        """Return 'full' or 'partial' based on field completeness.

        Quality assessment:
        - Full: has title, price, condition, CPU, RAM, storage, images (4+ optional fields)
        - Partial: missing price OR missing one or more optional fields (<4 optional fields)

        Args:
            normalized: Normalized listing schema

        Returns:
            Quality level: "full" or "partial"

        Raises:
            ValueError: If required field (title) is missing

        Example:
            >>> data = NormalizedListingSchema(
            ...     title="PC",
            ...     price=Decimal("599.99"),
            ...     condition="new",
            ...     cpu_model="i7-12700K",
            ...     ram_gb=16,
            ...     storage_gb=512,
            ...     images=["http://example.com/img.jpg"],
            ...     marketplace="other"
            ... )
            >>> normalizer.assess_quality(data)
            'full'
        """
        # Check required field (title is now the only truly required field)
        if not normalized.title or not normalized.title.strip():
            raise ValueError("Missing required field: title")

        # If price is missing, automatically mark as partial
        if normalized.price is None:
            return "partial"

        # Count optional fields (only if price is present)
        optional_fields = [
            normalized.condition,
            normalized.cpu_model,
            normalized.ram_gb,
            normalized.storage_gb,
            normalized.images,
        ]

        coverage = sum(1 for field in optional_fields if field)

        return "full" if coverage >= 4 else "partial"


@dataclass
class ListingCreatedEvent:
    """Event emitted when a new listing is created.

    Attributes:
        listing_id: Database ID of the created listing
        title: Listing title
        price: Current price in USD
        marketplace: Marketplace identifier (ebay|amazon|other)
        vendor_item_id: Marketplace-specific item ID (optional)
        provenance: Data source (ebay_api|jsonld)
        quality: Data quality assessment (full|partial)
        created_at: Timestamp when listing was created
    """

    listing_id: int
    title: str
    price: Decimal
    marketplace: str
    vendor_item_id: str | None
    provenance: str
    quality: str
    created_at: datetime


@dataclass
class PriceChangedEvent:
    """Event emitted when a listing's price changes significantly.

    Attributes:
        listing_id: Database ID of the listing
        title: Listing title
        old_price: Previous price in USD
        new_price: Current price in USD
        change_amount: Price difference (new - old, negative = price drop)
        change_percent: Percentage change ((new - old) / old * 100)
        marketplace: Marketplace identifier (ebay|amazon|other)
        vendor_item_id: Marketplace-specific item ID (optional)
        changed_at: Timestamp when price change was detected
    """

    listing_id: int
    title: str
    old_price: Decimal
    new_price: Decimal
    change_amount: Decimal
    change_percent: Decimal
    marketplace: str
    vendor_item_id: str | None
    changed_at: datetime


def should_emit_price_change(
    old_price: Decimal,
    new_price: Decimal,
    threshold_abs: Decimal,
    threshold_pct: Decimal,
) -> bool:
    """Determine if price change is significant enough to emit event.

    Emits if EITHER:
    - Absolute change >= threshold_abs
    - Percent change >= threshold_pct

    Args:
        old_price: Previous price in USD
        new_price: Current price in USD
        threshold_abs: Minimum absolute change threshold (e.g., $1.00)
        threshold_pct: Minimum percent change threshold (e.g., 2.0 for 2%)

    Returns:
        True if price change is significant, False otherwise

    Example:
        >>> should_emit_price_change(
        ...     Decimal("100.00"),
        ...     Decimal("98.00"),
        ...     Decimal("1.00"),
        ...     Decimal("2.0")
        ... )
        True  # $2 change >= $1 threshold AND 2% >= 2% threshold
    """
    change_abs = abs(new_price - old_price)

    # Handle zero old_price edge case
    if old_price == Decimal("0"):
        return change_abs >= threshold_abs

    # Calculate percentage change
    change_pct = abs((new_price - old_price) / old_price * Decimal("100"))

    # Emit if EITHER threshold is met
    return change_abs >= threshold_abs or change_pct >= threshold_pct


class IngestionEventService:
    """Service for emitting ingestion-related events.

    Emits events for:
    - listing.created - When a new listing is imported
    - price.changed - When an existing listing's price changes significantly

    Phase 2 Implementation:
    - Uses in-memory event storage for testing
    - Future phases will integrate with Celery, webhooks, or event bus

    Example:
        >>> event_service = IngestionEventService()
        >>> event_service.emit_listing_created(
        ...     listing=new_listing,
        ...     provenance="ebay_api",
        ...     quality="full"
        ... )
        >>> events = event_service.get_events()
        >>> print(f"Emitted {len(events)} events")
    """

    def __init__(self):
        """Initialize event service with in-memory event storage."""
        self._events: list[ListingCreatedEvent | PriceChangedEvent] = []

    def emit_listing_created(
        self,
        listing: Listing,
        provenance: str,
        quality: str,
    ) -> None:
        """Emit event when new listing is created.

        Args:
            listing: Newly created listing instance
            provenance: Data source (ebay_api|jsonld)
            quality: Data quality assessment (full|partial)

        Example:
            >>> listing = Listing(
            ...     id=1,
            ...     title="Gaming PC",
            ...     price_usd=599.99,
            ...     marketplace="ebay",
            ...     vendor_item_id="123456789012"
            ... )
            >>> event_service.emit_listing_created(listing, "ebay_api", "full")
        """
        event = ListingCreatedEvent(
            listing_id=listing.id,
            title=listing.title,
            price=Decimal(str(listing.price_usd)),
            marketplace=listing.marketplace,
            vendor_item_id=listing.vendor_item_id,
            provenance=provenance,
            quality=quality,
            created_at=listing.created_at,
        )

        self._events.append(event)
        # Future: Send to Celery task, webhook, or event bus

    def emit_price_changed(
        self,
        listing: Listing,
        old_price: Decimal,
        new_price: Decimal,
    ) -> None:
        """Emit event when listing price changes significantly.

        Args:
            listing: Listing instance with updated price
            old_price: Previous price in USD
            new_price: Current price in USD

        Example:
            >>> listing = Listing(
            ...     id=1,
            ...     title="Gaming PC",
            ...     price_usd=549.99,
            ...     marketplace="ebay"
            ... )
            >>> event_service.emit_price_changed(
            ...     listing,
            ...     Decimal("599.99"),
            ...     Decimal("549.99")
            ... )
        """
        change_amount = new_price - old_price

        # Calculate percentage change (handle zero old_price edge case)
        if old_price != Decimal("0"):
            change_percent = (new_price - old_price) / old_price * Decimal("100")
        else:
            change_percent = Decimal("0")

        event = PriceChangedEvent(
            listing_id=listing.id,
            title=listing.title,
            old_price=old_price,
            new_price=new_price,
            change_amount=change_amount,
            change_percent=change_percent,
            marketplace=listing.marketplace,
            vendor_item_id=listing.vendor_item_id,
            changed_at=datetime.utcnow(),
        )

        self._events.append(event)
        # Future: Send to Celery task, webhook, or event bus

    def check_and_emit_price_change(
        self,
        listing: Listing,
        old_price: Decimal,
        new_price: Decimal,
    ) -> bool:
        """Check if price change is significant and emit event if so.

        Reads thresholds from application settings and emits price.changed
        event if either threshold is met.

        Args:
            listing: Listing instance with updated price
            old_price: Previous price in USD
            new_price: Current price in USD

        Returns:
            True if event was emitted, False otherwise

        Example:
            >>> # Assuming settings.ingestion.price_change_threshold_abs = 1.0
            >>> # and settings.ingestion.price_change_threshold_pct = 2.0
            >>> listing = Listing(id=1, title="PC", price_usd=98.00, marketplace="ebay")
            >>> emitted = event_service.check_and_emit_price_change(
            ...     listing,
            ...     Decimal("100.00"),
            ...     Decimal("98.00")
            ... )
            >>> print(f"Event emitted: {emitted}")
            Event emitted: True
        """
        from dealbrain_api.settings import get_settings

        settings = get_settings()

        threshold_abs = Decimal(str(settings.ingestion.price_change_threshold_abs))
        threshold_pct = Decimal(str(settings.ingestion.price_change_threshold_pct))

        if should_emit_price_change(old_price, new_price, threshold_abs, threshold_pct):
            self.emit_price_changed(listing, old_price, new_price)
            return True

        return False

    def get_events(self) -> list[ListingCreatedEvent | PriceChangedEvent]:
        """Get all emitted events (for testing).

        Returns:
            Copy of all emitted events

        Example:
            >>> events = event_service.get_events()
            >>> for event in events:
            ...     if isinstance(event, ListingCreatedEvent):
            ...         print(f"Created: {event.title}")
            ...     elif isinstance(event, PriceChangedEvent):
            ...         print(f"Price changed: {event.title}")
        """
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear all events (for testing).

        Resets the in-memory event storage to empty list.
        Useful for test isolation and cleanup.

        Example:
            >>> event_service.emit_listing_created(listing, "ebay_api", "full")
            >>> len(event_service.get_events())
            1
            >>> event_service.clear_events()
            >>> len(event_service.get_events())
            0
        """
        self._events.clear()


@dataclass
class IngestionResult:
    """Result of ingesting a single URL.

    Attributes:
        success: Whether ingestion completed successfully
        listing_id: Database ID of created/updated listing (None if failed)
        status: Ingestion status (created|updated|failed)
        provenance: Data source used (ebay_api|jsonld)
        quality: Data quality assessment (full|partial)
        url: Source URL that was ingested
        dedup_result: Deduplication check result (optional)
        error: Error message if ingestion failed (optional)
        title: Listing title (optional)
        price: Listing price in USD (optional)
        vendor_item_id: Marketplace-specific item ID (optional)
        marketplace: Marketplace identifier (ebay|amazon|other)
    """

    # Required fields
    success: bool
    listing_id: int | None
    status: str  # "created" | "updated" | "failed"
    provenance: str  # "ebay_api" | "jsonld"
    quality: str  # "full" | "partial"
    url: str

    # Optional fields with defaults
    dedup_result: DeduplicationResult | None = None
    error: str | None = None
    title: str | None = None
    price: Decimal | None = None
    vendor_item_id: str | None = None
    marketplace: str = "other"


class IngestionService:
    """Orchestrates URL ingestion workflow.

    Coordinates the complete ingestion pipeline:
    1. Select adapter (AdapterRouter)
    2. Extract raw data (adapter.extract())
    3. Normalize and enrich (ListingNormalizer)
    4. Check for duplicates (DeduplicationService)
    5. Upsert listing (create or update)
    6. Emit events (IngestionEventService)
    7. Store raw payload (RawPayload model)

    Example:
        >>> async with session_scope() as session:
        ...     service = IngestionService(session)
        ...     result = await service.ingest_single_url("https://ebay.com/itm/123")
        ...     if result.success:
        ...         print(f"Created listing {result.listing_id}")
    """

    def __init__(self, session: AsyncSession):
        """Initialize ingestion service.

        Args:
            session: Async SQLAlchemy session for database operations
        """
        self.session = session
        self.router = AdapterRouter()
        self.dedup_service = DeduplicationService(session)
        self.normalizer = ListingNormalizer(session)
        self.event_service = IngestionEventService()

    async def ingest_single_url(self, url: str) -> IngestionResult:
        """Ingest a single URL through complete workflow.

        Orchestrates the full ingestion pipeline from URL to persisted listing.
        Handles errors gracefully and returns result with detailed status.

        Args:
            url: The URL to ingest

        Returns:
            IngestionResult with outcome details (success/failure, listing_id, etc.)

        Example:
            >>> result = await service.ingest_single_url("https://ebay.com/itm/123")
            >>> if result.success:
            ...     print(f"{result.status}: listing {result.listing_id}")
            ... else:
            ...     print(f"Failed: {result.error}")
        """
        logger.info("ingestion.url.start", url=url)
        try:
            # Step 1: Extract raw data via adapter with fallback chain
            raw_data, adapter_name = await self.router.extract(url)

            # Step 2: Normalize and enrich
            normalized = await self.normalizer.normalize(raw_data)

            # Step 3: Check for duplicates
            dedup_result = await self.dedup_service.find_existing_listing(normalized)

            # Step 4: Upsert listing
            if dedup_result.exists and dedup_result.existing_listing:
                listing = await self._update_listing(dedup_result.existing_listing, normalized)
                status = "updated"
            else:
                listing = await self._create_listing(normalized)
                status = "created"

            # Step 4.5: Calculate performance metrics
            if listing.cpu_id:
                from .listings import apply_listing_metrics

                await apply_listing_metrics(self.session, listing)
                await self.session.refresh(listing)
                logger.info(
                    "ingestion.listing.metrics_applied",
                    listing_id=listing.id,
                    has_adjusted_price=listing.adjusted_price_usd is not None,
                    has_single_thread_metric=listing.dollar_per_cpu_mark_single is not None,
                    has_multi_thread_metric=listing.dollar_per_cpu_mark_multi is not None,
                )

            # Step 5: Emit events
            quality = self.normalizer.assess_quality(normalized)
            if status == "created":
                self.event_service.emit_listing_created(
                    listing, provenance=adapter_name, quality=quality
                )
            elif status == "updated" and dedup_result.existing_listing:
                # Check if price changed significantly
                old_price = Decimal(str(dedup_result.existing_listing.price_usd))
                new_price = normalized.price
                self.event_service.check_and_emit_price_change(listing, old_price, new_price)

            # Step 6: Store raw payload
            await self._store_raw_payload(listing, adapter_name, normalized)

            # Step 7: Return result
            result = IngestionResult(
                success=True,
                listing_id=listing.id,
                status=status,
                provenance=adapter_name,
                quality=quality,
                dedup_result=dedup_result,
                url=url,
                title=listing.title,
                price=Decimal(str(listing.price_usd)),
                vendor_item_id=listing.vendor_item_id,
                marketplace=listing.marketplace,
            )
            logger.info(
                "ingestion.url.completed",
                url=url,
                listing_id=listing.id,
                status=status,
                provenance=adapter_name,
                quality=quality,
                dedup_exists=dedup_result.exists,
                dedup_exact=dedup_result.is_exact_match,
            )
            return result

        except Exception as e:
            logger.exception("ingestion.url.failed", url=url)
            return IngestionResult(
                success=False,
                listing_id=None,
                status="failed",
                provenance="unknown",
                quality="partial",
                error=str(e),
                url=url,
            )

    async def _find_cpu_by_model(self, cpu_model: str) -> int | None:
        """Find CPU by model string using fuzzy matching.

        Args:
            cpu_model: CPU model string to search for

        Returns:
            CPU ID if found, None otherwise
        """
        from dealbrain_api.models.core import Cpu
        from sqlalchemy import func

        if not cpu_model:
            return None

        # Normalize the cpu_model string (lowercase, strip whitespace)
        normalized = cpu_model.lower().strip()

        # Query CPU catalog for exact match first
        stmt = select(Cpu).where(func.lower(Cpu.name).contains(normalized))
        result = await self.session.execute(stmt)
        cpu = result.scalars().first()

        if cpu:
            logger.info(
                "ingestion.cpu.match",
                match_type="model",
                cpu_id=cpu.id,
                cpu_name=cpu.name,
                query=cpu_model,
            )
            return cpu.id

        # Try partial match (e.g., "i9-12900H" matches "Intel Core i9-12900H")
        # Extract key parts (e.g., "12900H" from "Intel Core i9-12900H")
        cpu_keywords = [part for part in normalized.split() if len(part) > 2]
        if cpu_keywords:
            for keyword in cpu_keywords:
                stmt = select(Cpu).where(func.lower(Cpu.name).contains(keyword))
                result = await self.session.execute(stmt)
                cpu = result.scalars().first()
                if cpu:
                    logger.info(
                        "ingestion.cpu.match",
                        match_type="keyword",
                        cpu_id=cpu.id,
                        cpu_name=cpu.name,
                        keyword=keyword,
                        query=cpu_model,
                    )
                    return cpu.id

        logger.warning("ingestion.cpu.not_found", query=cpu_model)
        return None

    async def _create_listing(self, data: NormalizedListingSchema) -> Listing:
        """Create new listing from normalized data.

        Args:
            data: Normalized listing schema from adapter

        Returns:
            Created Listing instance (with ID assigned)

        Raises:
            ValueError: If condition string cannot be mapped to Condition enum
        """
        from dealbrain_core.enums import Condition

        # Generate dedup hash
        dedup_hash = self.dedup_service._generate_hash(data)

        # Map condition string to enum
        condition_map = {
            "new": Condition.NEW,
            "refurb": Condition.REFURB,
            "used": Condition.USED,
        }
        condition = condition_map.get(data.condition.lower(), Condition.USED)

        # Look up CPU if cpu_model is provided
        cpu_id = None
        if data.cpu_model:
            cpu_id = await self._find_cpu_by_model(data.cpu_model)

        # Prepare attributes_json with images
        attributes_json = {}
        if data.images:
            attributes_json["images"] = data.images
            logger.info(
                "ingestion.images.persist",
                count=len(data.images),
                listing_title=data.title,
            )

        # Create listing with all fields
        listing = Listing(
            title=data.title,
            price_usd=float(data.price),
            condition=condition.value,
            marketplace=data.marketplace,
            vendor_item_id=data.vendor_item_id,
            seller=data.seller,
            dedup_hash=dedup_hash,
            # NEW FIELDS
            cpu_id=cpu_id,  # Foreign key to CPU table
            ram_gb=data.ram_gb or 0,  # Default to 0 if not provided
            primary_storage_gb=data.storage_gb or 0,  # Default to 0 if not provided
            notes=data.description,  # Store description in notes field
            attributes_json=attributes_json,  # Store images and other metadata
            manufacturer=data.manufacturer,  # Brand/manufacturer
            model_number=data.model_number,  # Model number
            # last_seen_at is auto-set by default
        )

        logger.info(
            "ingestion.listing.created",
            title=listing.title,
            cpu_id=cpu_id,
            ram_gb=data.ram_gb or 0,
            storage_gb=data.storage_gb or 0,
            image_count=len(data.images) if data.images else 0,
            manufacturer=data.manufacturer,
            model_number=data.model_number,
            condition=condition.value,
        )

        self.session.add(listing)
        await self.session.flush()  # Get ID without committing

        return listing

    async def _update_listing(self, existing: Listing, data: NormalizedListingSchema) -> Listing:
        """Update existing listing with new data.

        Updates mutable fields (price, images) and refreshes last_seen_at.
        Does not update immutable fields like title or vendor_item_id.

        Args:
            existing: Existing listing to update
            data: New normalized data from adapter

        Returns:
            Updated Listing instance
        """
        from dealbrain_core.enums import Condition
        from sqlalchemy.orm.attributes import flag_modified

        # Update price and check for changes
        old_price = existing.price_usd
        existing.price_usd = float(data.price)
        existing.last_seen_at = datetime.utcnow()

        # Update condition if changed
        condition_map = {
            "new": Condition.NEW,
            "refurb": Condition.REFURB,
            "used": Condition.USED,
        }
        condition = condition_map.get(data.condition.lower(), Condition.USED)
        existing.condition = condition.value

        # Update seller if provided
        if data.seller:
            existing.seller = data.seller

        # NEW: Update all extracted fields
        if data.cpu_model:
            cpu_id = await self._find_cpu_by_model(data.cpu_model)
            if cpu_id:
                existing.cpu_id = cpu_id

        if data.ram_gb is not None:
            existing.ram_gb = data.ram_gb

        if data.storage_gb is not None:
            existing.primary_storage_gb = data.storage_gb

        if data.description:
            existing.notes = data.description

        if data.manufacturer:
            existing.manufacturer = data.manufacturer

        if data.model_number:
            existing.model_number = data.model_number

        if data.images:
            # Merge with existing attributes_json
            if not existing.attributes_json:
                existing.attributes_json = {}
            existing.attributes_json["images"] = data.images
            flag_modified(existing, "attributes_json")  # Tell SQLAlchemy JSON changed

        logger.info(
            "ingestion.listing.updated",
            listing_id=existing.id,
            title=existing.title,
            old_price=float(old_price or 0),
            new_price=float(data.price),
            cpu_id=existing.cpu_id,
            ram_gb=data.ram_gb if data.ram_gb is not None else existing.ram_gb,
            storage_gb=(
                data.storage_gb if data.storage_gb is not None else existing.primary_storage_gb
            ),
            manufacturer=data.manufacturer or existing.manufacturer,
            model_number=data.model_number or existing.model_number,
        )

        await self.session.flush()

        return existing

    async def _store_raw_payload(
        self, listing: Listing, adapter_name: str, raw_data: NormalizedListingSchema
    ) -> None:
        """Store raw normalized data as JSON payload.

        Preserves original adapter data for debugging and re-processing.
        Truncates large payloads to stay within 512KB limit.

        Args:
            listing: Listing instance to attach payload to
            adapter_name: Name of adapter used (ebay|jsonld)
            raw_data: Normalized listing schema to serialize
        """
        import json

        # Convert NormalizedListingSchema to dict
        payload_dict = raw_data.model_dump(mode="json")

        # Truncate if too large (512KB limit from plan)
        payload_json = json.dumps(payload_dict)
        max_size = 512 * 1024  # 512KB

        if len(payload_json) > max_size:
            # Truncate description or other large fields
            payload_dict["description"] = payload_dict.get("description", "")[:1000] + "..."
            payload_json = json.dumps(payload_dict)

        # Create RawPayload record
        raw_payload = RawPayload(
            listing_id=listing.id,
            adapter=adapter_name,
            source_type="json",  # NormalizedListingSchema is always JSON
            payload=payload_json,  # Store as JSON string
            ttl_days=30,  # From plan
        )

        self.session.add(raw_payload)


__all__ = [
    "DeduplicationService",
    "DeduplicationResult",
    "ListingNormalizer",
    "IngestionEventService",
    "ListingCreatedEvent",
    "PriceChangedEvent",
    "should_emit_price_change",
    "IngestionResult",
    "IngestionService",
]
