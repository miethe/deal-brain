# URL Ingestion Adapters

This directory contains adapters for extracting listing data from various online marketplaces and sources. All adapters implement the `BaseAdapter` interface and produce normalized `NormalizedListingSchema` output.

## Overview

The adapter pattern enables Deal Brain to extract listing data from multiple sources while maintaining a consistent interface:

1. **BaseAdapter** (`base.py`) - Abstract base class defining the adapter interface
2. **EbayAdapter** (`ebay.py`) - eBay Browse API integration
3. **JsonLdAdapter** (`jsonld.py`) - JSON-LD structured data extraction (TODO)
4. **GenericAdapter** (`generic.py`) - Fallback scraper for unstructured pages (TODO)

## Architecture

```
┌─────────────┐
│ Ingestion   │
│ Service     │
└──────┬──────┘
       │
       │ Tries adapters in priority order
       ├─────────────────────────────────┐
       │                                 │
┌──────▼─────┐                    ┌─────▼─────┐
│ EbayAdapter│ (priority: 1)      │ JsonLd    │ (priority: 2)
│            │                    │ Adapter   │
└──────┬─────┘                    └─────┬─────┘
       │                                │
       │ Both produce                   │
       └────────────┬───────────────────┘
                    │
             ┌──────▼──────┐
             │ Normalized  │
             │ Listing     │
             │ Schema      │
             └─────────────┘
```

## eBay Adapter

### Features

- Parses eBay item URLs to extract item IDs
- Calls eBay Browse API v1 with OAuth authentication
- Maps API response to `NormalizedListingSchema`
- Implements retry logic with exponential backoff (1s, 2s, 4s)
- Handles rate limiting (60 requests/minute)
- Extracts item specifications (CPU, RAM, storage)
- Normalizes eBay conditions to Deal Brain enums

### Configuration

Configure the eBay adapter in `apps/api/dealbrain_api/settings.py`:

```python
class IngestionSettings(BaseModel):
    ebay: AdapterConfig = Field(
        default_factory=lambda: AdapterConfig(
            enabled=True,
            timeout_s=6,
            retries=2,
        )
    )
```

Set the eBay API key via environment variable:

```bash
export EBAY_API_KEY="your_browse_api_key_here"
```

### URL Formats Supported

The eBay adapter handles various URL formats:

```
https://www.ebay.com/itm/123456789012
https://www.ebay.com/itm/Product-Name/123456789012
https://ebay.com/itm/123456789012?hash=abc
https://www.ebay.com/itm/123456789012#section
```

### Usage Example

```python
from dealbrain_api.adapters.ebay import EbayAdapter

adapter = EbayAdapter()
url = "https://www.ebay.com/itm/123456789012"

# Extract normalized listing data
listing = await adapter.extract(url)

print(listing.title)       # "Gaming PC Intel Core i7..."
print(listing.price)       # Decimal("599.99")
print(listing.cpu_model)   # "Intel Core i7-12700K"
print(listing.ram_gb)      # 16
print(listing.storage_gb)  # 512
```

### Error Handling

The adapter raises `AdapterException` with specific error codes:

- `PARSE_ERROR`: Invalid URL format
- `ITEM_NOT_FOUND`: Item does not exist (404)
- `INVALID_SCHEMA`: Invalid API credentials (401)
- `RATE_LIMITED`: API rate limit exceeded (429)
- `TIMEOUT`: Request timeout
- `NETWORK_ERROR`: Network or server error

### Testing

Run the eBay adapter tests:

```bash
# Run all tests
poetry run pytest tests/test_ebay_adapter.py -v

# Run with coverage
poetry run pytest tests/test_ebay_adapter.py \
  --cov=dealbrain_api.adapters.ebay \
  --cov-report=term-missing

# Run specific test class
poetry run pytest tests/test_ebay_adapter.py::TestSpecExtraction -v
```

Current test coverage: **98%**

### Implementation Details

#### Spec Extraction

The adapter extracts CPU, RAM, and storage from eBay's `localizedAspects` or `itemSpecifics` arrays:

```python
# eBay API response
{
  "localizedAspects": [
    {"name": "Processor", "value": "Intel Core i7-12700K"},
    {"name": "RAM Size", "value": "16 GB"},
    {"name": "SSD Capacity", "value": "512 GB"}
  ]
}

# Extracted data
cpu_model = "Intel Core i7-12700K"
ram_gb = 16
storage_gb = 512
```

Storage values in TB are automatically converted to GB (e.g., "2 TB" → 2048 GB).

#### Condition Normalization

eBay conditions are mapped to Deal Brain's `Condition` enum:

| eBay Condition                | Deal Brain Condition |
|-------------------------------|---------------------|
| "New"                         | `new`               |
| "New other (see details)"     | `new`               |
| "Seller refurbished"          | `refurb`            |
| "Manufacturer refurbished"    | `refurb`            |
| "Used"                        | `used`              |
| "For parts or not working"    | `used`              |

#### Retry Strategy

The adapter uses the `RetryConfig` from `BaseAdapter`:

- **Max retries**: 2 (configurable via settings)
- **Backoff**: Exponential with base 1.0s (1s, 2s, 4s)
- **Retryable errors**: TIMEOUT, NETWORK_ERROR, RATE_LIMITED
- **Non-retryable errors**: ITEM_NOT_FOUND, INVALID_SCHEMA

## Adding New Adapters

To add a new adapter:

1. Create a new file in this directory (e.g., `amazon.py`)
2. Inherit from `BaseAdapter`
3. Implement the `async extract(url: str) -> NormalizedListingSchema` method
4. Set adapter metadata (name, supported_domains, priority)
5. Add configuration to `IngestionSettings` in `settings.py`
6. Write comprehensive tests in `tests/test_{adapter_name}_adapter.py`

### Example Template

```python
from dealbrain_api.adapters.base import BaseAdapter
from dealbrain_core.schemas.ingestion import NormalizedListingSchema
from dealbrain_api.settings import get_settings

class NewAdapter(BaseAdapter):
    def __init__(self) -> None:
        settings = get_settings()
        super().__init__(
            name="new_adapter",
            supported_domains=["example.com"],
            priority=5,
            timeout_s=settings.ingestion.new_adapter.timeout_s,
            max_retries=settings.ingestion.new_adapter.retries,
        )

    async def extract(self, url: str) -> NormalizedListingSchema:
        # 1. Parse URL
        # 2. Fetch data with retry
        # 3. Map to NormalizedListingSchema
        pass
```

## Best Practices

1. **Always use async/await** for I/O operations
2. **Use retry logic** via `self.retry_config.execute_with_retry()`
3. **Implement rate limiting** via `self._check_rate_limit()`
4. **Raise AdapterException** with appropriate error codes
5. **Add comprehensive logging** for debugging
6. **Write thorough tests** with >80% coverage
7. **Use type hints** throughout for mypy compatibility
8. **Mock external APIs** in tests using fixtures

## References

- [BaseAdapter documentation](base.py)
- [NormalizedListingSchema](../../../packages/core/dealbrain_core/schemas/ingestion.py)
- [eBay Browse API docs](https://developer.ebay.com/api-docs/buy/browse/overview.html)
