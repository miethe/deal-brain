"""Normalizes and enriches listing data from adapters.

This module performs the following transformations:
1. Currency conversion to USD using fixed exchange rates
2. Condition string normalization to standard enum values
3. Spec extraction from descriptions (CPU/RAM/storage)
4. CPU canonicalization against catalog with benchmark enrichment
5. Data quality assessment (full/partial based on field coverage)
"""

from typing import Any

from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...telemetry import get_logger
from .converters import convert_to_usd, normalize_condition
from .quality import assess_quality as assess_quality_impl
from .quality import extract_specs, parse_brand_and_model

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

    def __init__(self, session: AsyncSession):
        """Initialize listing normalizer.

        Args:
            session: Async SQLAlchemy session for database queries
        """
        self.session = session

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
        price_usd = convert_to_usd(raw_data.price, raw_data.currency)

        # 2. Normalize condition
        condition = normalize_condition(raw_data.condition)

        # 3. Extract specs if not already present
        specs = extract_specs(raw_data)

        # 4. Canonicalize CPU
        cpu_model = specs.get("cpu_model") or raw_data.cpu_model
        cpu_info = await self._canonicalize_cpu(cpu_model)

        # 5. Parse brand and model from title if not already set
        manufacturer = raw_data.manufacturer
        model_number = raw_data.model_number
        if not manufacturer or not model_number:
            brand, model = parse_brand_and_model(raw_data.title)
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
        return assess_quality_impl(normalized)

    # Backward-compatible proxy methods for tests
    def _convert_to_usd(self, price, currency):
        """Proxy to converters.convert_to_usd for backward compatibility."""
        return convert_to_usd(price, currency)

    def _normalize_condition(self, condition):
        """Proxy to converters.normalize_condition for backward compatibility."""
        return normalize_condition(condition)

    def _extract_specs(self, data):
        """Proxy to quality.extract_specs for backward compatibility."""
        return extract_specs(data)

    def _parse_brand_and_model(self, title):
        """Proxy to quality.parse_brand_and_model for backward compatibility."""
        return parse_brand_and_model(title)


__all__ = [
    "ListingNormalizer",
]
