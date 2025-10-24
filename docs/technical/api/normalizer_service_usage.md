# ListingNormalizer Service Usage Guide

## Overview

The `ListingNormalizer` service standardizes and enriches listing data from various adapters (eBay API, JSON-LD, scrapers). It performs:

1. **Currency conversion** - Converts prices to USD using fixed exchange rates
2. **Condition normalization** - Maps various condition strings to standard enum values
3. **Spec extraction** - Extracts CPU/RAM/storage from descriptions using regex
4. **CPU canonicalization** - Matches CPUs against catalog and enriches with benchmark data
5. **Quality assessment** - Determines data completeness (full/partial)

## Installation

The service is located at:
```
apps/api/dealbrain_api/services/ingestion.py
```

## Basic Usage

```python
from dealbrain_api.services.ingestion import ListingNormalizer
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from decimal import Decimal

async with session_scope() as session:
    normalizer = ListingNormalizer(session)

    # Raw data from adapter
    raw_data = NormalizedListingSchema(
        title="Gaming PC",
        price=Decimal("500"),
        currency="EUR",
        condition="Brand New",
        description="PC with Intel Core i7-12700K, 16GB RAM, 512GB SSD",
        marketplace="other",
        seller="TechStore",
    )

    # Normalize and enrich
    enriched = await normalizer.normalize(raw_data)

    # Check quality
    quality = normalizer.assess_quality(enriched)

    print(f"Price: ${enriched.price} USD")  # Converted from EUR
    print(f"Condition: {enriched.condition}")  # Normalized to 'new'
    print(f"CPU: {enriched.cpu_model}")  # Canonicalized against catalog
    print(f"RAM: {enriched.ram_gb}GB")  # Extracted from description
    print(f"Storage: {enriched.storage_gb}GB")  # Extracted from description
    print(f"Quality: {quality}")  # 'full' or 'partial'
```

## Currency Conversion

The service supports fixed exchange rates for Phase 2:

```python
CURRENCY_RATES = {
    "USD": 1.0,
    "EUR": 1.08,   # 1 EUR = 1.08 USD
    "GBP": 1.27,   # 1 GBP = 1.27 USD
    "CAD": 0.74,   # 1 CAD = 0.74 USD
}
```

**Examples:**
```python
# EUR to USD
normalizer._convert_to_usd(Decimal("500"), "EUR")
# Result: Decimal("540.00")

# GBP to USD
normalizer._convert_to_usd(Decimal("400"), "GBP")
# Result: Decimal("508.00")

# Unknown currency defaults to USD
normalizer._convert_to_usd(Decimal("599.99"), "JPY")
# Result: Decimal("599.99")
```

## Condition Normalization

Maps various condition strings to standard enum values:

```python
CONDITION_MAPPING = {
    "new": "new",
    "brand new": "new",
    "refurb": "refurb",
    "seller refurbished": "refurb",
    "manufacturer refurbished": "refurb",
    "refurbished": "refurb",
    "used": "used",
    "pre-owned": "used",
    "open box": "used",
    "for parts": "used",
}
```

**Examples:**
```python
normalizer._normalize_condition("Brand New")  # "new"
normalizer._normalize_condition("Seller refurbished")  # "refurb"
normalizer._normalize_condition("Pre-Owned")  # "used"
normalizer._normalize_condition("unknown")  # "used" (default)
```

## Spec Extraction

Extracts hardware specs from product descriptions using regex:

### CPU Extraction
```python
# Pattern matches Intel Core i3/i5/i7/i9 and AMD Ryzen 3/5/7/9
CPU_PATTERN = r"(?:Intel|AMD)?\s*(?:Core)?\s*(i[3579]|Ryzen\s*[3579])\s*-?\s*(\d{4,5}[A-Z0-9]*)"

# Examples:
"Intel Core i7-12700K" → "i7-12700K"
"AMD Ryzen 7 5800X3D" → "Ryzen 7-5800X3D"
"i5-13600K processor" → "i5-13600K"
```

### RAM Extraction
```python
# Pattern matches GB amounts with optional qualifiers
RAM_PATTERN = r"(\d+)\s*GB(?:\s+(?:RAM|DDR[345]|Memory))?"

# Examples:
"16GB DDR4 RAM" → 16
"32 GB Memory" → 32
"8GB" → 8
```

### Storage Extraction
```python
# Pattern matches GB/TB amounts with storage qualifiers
STORAGE_PATTERN = r"(\d+)\s*(GB|TB)\s*(?:SSD|NVMe|HDD|Storage)"

# Examples:
"512GB NVMe SSD" → 512
"1TB HDD" → 1024 (converted to GB)
"256 GB SSD Storage" → 256
```

## CPU Canonicalization

Matches extracted CPU strings against the CPU catalog and enriches with benchmark data:

```python
# Example: Match "i7-12700K" to catalog
cpu_info = await normalizer._canonicalize_cpu("i7-12700K")

# Returns:
{
    "name": "Intel Core i7-12700K 12-Core 3.6 GHz",
    "cpu_mark_multi": 30000,
    "cpu_mark_single": 4000,
    "igpu_mark": 2500,
}
```

**Matching Strategy:**
1. Case-insensitive LIKE match on `Cpu.name`
2. Returns first match found
3. Returns `None` if no match

## Quality Assessment

Determines data completeness based on field coverage:

**Quality Levels:**
- **Full** - 4+ optional fields present (condition, CPU, RAM, storage, images)
- **Partial** - <4 optional fields present

**Required fields:** title, price

**Optional fields:** condition, cpu_model, ram_gb, storage_gb, images

**Examples:**
```python
# Full quality - all optional fields present
data_full = NormalizedListingSchema(
    title="PC",
    price=Decimal("599.99"),
    condition="new",
    cpu_model="i7-12700K",
    ram_gb=16,
    storage_gb=512,
    images=["http://example.com/img.jpg"],
    marketplace="other",
)
normalizer.assess_quality(data_full)  # "full"

# Partial quality - only 2 optional fields
data_partial = NormalizedListingSchema(
    title="PC",
    price=Decimal("599.99"),
    condition="new",
    images=["http://example.com/img.jpg"],
    marketplace="other",
)
normalizer.assess_quality(data_partial)  # "partial"
```

## End-to-End Example

```python
from dealbrain_api.services.ingestion import ListingNormalizer
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from dealbrain_api.db import session_scope
from decimal import Decimal

async def process_listing(raw_data: NormalizedListingSchema):
    """Process a listing through normalization pipeline."""
    async with session_scope() as session:
        normalizer = ListingNormalizer(session)

        # 1. Normalize and enrich
        enriched = await normalizer.normalize(raw_data)

        # 2. Assess quality
        quality = normalizer.assess_quality(enriched)

        # 3. Return processed data
        return {
            "enriched_data": enriched,
            "quality": quality,
        }

# Example usage
raw = NormalizedListingSchema(
    title="Gaming PC",
    price=Decimal("500"),  # EUR
    currency="EUR",
    condition="new",
    description="PC with Intel Core i7-12700K, 16GB DDR4 RAM, 512GB SSD",
    marketplace="other",
    seller="TechStore",
    images=["http://example.com/image1.jpg"],
)

result = await process_listing(raw)
# {
#     "enriched_data": {
#         "title": "Gaming PC",
#         "price": Decimal("540.00"),  # Converted to USD
#         "currency": "USD",
#         "condition": "new",
#         "cpu_model": "Intel Core i7-12700K 12-Core 3.6 GHz",  # Canonicalized
#         "ram_gb": 16,  # Extracted
#         "storage_gb": 512,  # Extracted
#         ...
#     },
#     "quality": "full"
# }
```

## Testing

Comprehensive test suite with 41 tests covering:
- Currency conversion (7 tests)
- Condition normalization (7 tests)
- Spec extraction (11 tests)
- CPU canonicalization (6 tests)
- Quality assessment (5 tests)
- End-to-end normalization (5 tests)

Run tests:
```bash
poetry run pytest tests/test_normalizer_service.py -v
```

Coverage: 77% overall (ListingNormalizer class has >95% coverage)

## Future Enhancements (Phase 3+)

1. **Live currency rates** - Replace fixed rates with live API (e.g., exchangerate-api.com)
2. **Advanced CPU fuzzy matching** - Use difflib or fuzzywuzzy for better partial matches
3. **GPU extraction** - Add regex patterns for GPU model extraction
4. **Form factor detection** - Extract form factor (SFF, USFF, Tower) from descriptions
5. **Manufacturer detection** - Extract manufacturer (HP, Dell, Lenovo) from titles
6. **Confidence scoring** - Add confidence scores for extracted specs
7. **Multi-language support** - Handle non-English descriptions

## Related Services

- **DeduplicationService** - Prevents duplicate listings (same file)
- **ListingsService** - Creates/updates listings in database
- **Adapter Services** - Extract raw data (eBay API, JSON-LD, scrapers)

## Architecture Notes

- **Async-first** - All database operations use `async`/`await`
- **Type-safe** - Full type hints throughout (mypy compatible)
- **Immutable patterns** - Returns new schemas rather than mutating input
- **Separation of concerns** - Pure functions for normalization, async methods for I/O
- **Comprehensive logging** - Uses docstrings with examples for documentation
