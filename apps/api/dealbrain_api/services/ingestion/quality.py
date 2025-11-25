"""Quality assessment and spec extraction utilities for ingestion.

This module provides utilities for:
- Extracting hardware specs (CPU, RAM, storage) from descriptions
- Parsing brand and model information from titles
- Assessing data quality based on field completeness
"""

import re
from typing import Any

from dealbrain_core.schemas.ingestion import NormalizedListingSchema

from ...telemetry import get_logger

logger = get_logger("dealbrain.ingestion.quality")

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


def extract_specs(data: NormalizedListingSchema) -> dict[str, Any]:
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
        >>> specs = extract_specs(data)
        >>> print(specs)
        {'cpu_model': 'i7-12700K', 'ram_gb': 16, 'storage_gb': 512}
    """
    specs: dict[str, Any] = {}

    if not data.description:
        return specs

    description = data.description

    # Extract CPU if not already present
    if not data.cpu_model:
        cpu_match = CPU_PATTERN.search(description)
        if cpu_match:
            # Combine matched groups (e.g., "i7" + "-" + "12700K")
            cpu_model = f"{cpu_match.group(1)}-{cpu_match.group(2)}"
            specs["cpu_model"] = cpu_model.strip()

    # Extract RAM if not already present
    if not data.ram_gb:
        ram_match = RAM_PATTERN.search(description)
        if ram_match:
            specs["ram_gb"] = int(ram_match.group(1))

    # Extract storage if not already present
    if not data.storage_gb:
        storage_match = STORAGE_PATTERN.search(description)
        if storage_match:
            capacity = int(storage_match.group(1))
            unit = storage_match.group(2).upper()

            # Convert to GB
            if unit == "TB":
                capacity *= 1024

            specs["storage_gb"] = capacity

    return specs


def parse_brand_and_model(title: str) -> tuple[str | None, str | None]:
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


def assess_quality(normalized: NormalizedListingSchema) -> str:
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
        >>> assess_quality(data)
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


__all__ = [
    "CPU_PATTERN",
    "RAM_PATTERN",
    "STORAGE_PATTERN",
    "extract_specs",
    "parse_brand_and_model",
    "assess_quality",
]
