"""Normalization and enrichment logic for listing data.

This module normalizes and enriches listing data from adapters, performing:
1. Currency conversion to USD using fixed exchange rates
2. Condition string normalization to standard enum values
3. Spec extraction from descriptions (CPU/RAM/storage)
4. CPU canonicalization against catalog with benchmark enrichment
5. Data quality assessment (full/partial based on field coverage)
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from dealbrain_api.models.core import Cpu
from dealbrain_api.telemetry import get_logger
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("dealbrain.ingestion.normalizer")


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
        price: Decimal,
        currency: str | None,
    ) -> Decimal:
        """Convert price to USD using fixed exchange rates.

        Args:
            price: Original price amount
            currency: ISO currency code (USD|EUR|GBP|CAD)

        Returns:
            Price converted to USD (2 decimal places)

        Example:
            >>> normalizer._convert_to_usd(Decimal("500"), "EUR")
            Decimal('540.00')
            >>> normalizer._convert_to_usd(Decimal("599.99"), "USD")
            Decimal('599.99')
            >>> normalizer._convert_to_usd(Decimal("599.99"), "JPY")
            Decimal('599.99')  # Unknown currency defaults to USD
        """
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
        - Partial: missing one or more optional fields (<4 optional fields)

        Args:
            normalized: Normalized listing schema

        Returns:
            Quality level: "full" or "partial"

        Raises:
            ValueError: If required fields (title, price) are missing

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
        # Check required fields
        required_fields = [
            normalized.title,
            normalized.price,
        ]

        if not all(required_fields):
            raise ValueError("Missing required fields (title, price)")

        # Count optional fields
        optional_fields = [
            normalized.condition,
            normalized.cpu_model,
            normalized.ram_gb,
            normalized.storage_gb,
            normalized.images,
        ]

        coverage = sum(1 for field in optional_fields if field)

        return "full" if coverage >= 4 else "partial"
