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

## Adapter Fallback Chain

The ingestion service implements an automatic fallback mechanism that tries adapters in priority order, ensuring resilient data extraction across multiple sources.

### How the Fallback Mechanism Works

When a URL is submitted for ingestion, the system attempts adapters sequentially based on priority (lower number = higher priority):

1. **eBay Adapter** (priority: 1) - Try to extract via eBay Browse API
2. **JSON-LD Adapter** (priority: 2) - Fall back to structured data extraction
3. **Generic Scraper** (priority: 3) - Final fallback for unstructured pages

Each adapter is tried in order until one succeeds. If an adapter fails with a recoverable error, the system moves to the next adapter. If all adapters fail, an `ALL_ADAPTERS_FAILED` error is returned.

### Priority-Based Adapter Selection

The adapter priority determines the order of execution:

```python
# Adapter priorities (lower = tried first)
EbayAdapter:     priority=1   # Official API, most reliable
JsonLdAdapter:   priority=2   # Works across 80% of retailers
GenericAdapter:  priority=3   # Last resort fallback
```

### Fallback Scenarios

**Fallback occurs for these recoverable errors:**
- `CONFIGURATION_ERROR` - Missing/invalid API key (try next adapter)
- `TIMEOUT` - Request took too long (try next adapter)
- `NETWORK_ERROR` - Connection issue (try next adapter)
- `RATE_LIMITED` - API quota exceeded (try next adapter)

**Fast-fail (no fallback) for these errors:**
- `ITEM_NOT_FOUND` - URL is valid but item doesn't exist (404 not found)
- `ADAPTER_DISABLED` - Adapter is disabled via feature flag
- `PARSE_ERROR` - URL format is invalid

### Example: eBay URL Without API Key

Demonstrates the fallback mechanism in action:

```python
# User submits eBay URL: https://www.ebay.com/itm/123456789012

# Step 1: Try eBay adapter
adapter = EbayAdapter()
try:
    listing = await adapter.extract("https://www.ebay.com/itm/123456789012")
except AdapterException as e:
    if e.code == "CONFIGURATION_ERROR":  # eBay API key not configured
        # Fall back to next adapter
        logger.info("eBay adapter failed: CONFIGURATION_ERROR, trying JSON-LD adapter")

# Step 2: Try JSON-LD adapter (falls back to public structured data)
adapter = JsonLdAdapter()
listing = await adapter.extract("https://www.ebay.com/itm/123456789012")
# JSON-LD succeeds by extracting public Schema.org data from eBay's page
```

In this scenario, even without eBay API credentials, the system extracts listing data via JSON-LD fallback, ensuring the import succeeds.

### Logging Behavior

All adapter attempts are logged for debugging and monitoring:

```
[2025-10-21 14:32:10] INFO: Attempting adapter: EbayAdapter (priority=1)
[2025-10-21 14:32:11] WARNING: EbayAdapter failed: CONFIGURATION_ERROR (EBAY_API_KEY not set)
[2025-10-21 14:32:11] INFO: Attempting adapter: JsonLdAdapter (priority=2)
[2025-10-21 14:32:12] INFO: JsonLdAdapter succeeded: extracted title, price, condition
```

Log entries include:
- Adapter name and priority being attempted
- Failure reason (code and message)
- Success confirmation with fields extracted
- Adapter attempt index (e.g., "attempt 2 of 3")

### Error Handling

If all adapters fail to extract data:

```python
# Raised when every adapter in the chain fails
raise AdapterException(
    code="ALL_ADAPTERS_FAILED",
    message="No adapter could extract data from this URL",
    context={
        "url": "https://example.com/item/123",
        "attempted_adapters": [
            {"name": "EbayAdapter", "error": "CONFIGURATION_ERROR"},
            {"name": "JsonLdAdapter", "error": "NETWORK_ERROR"},
            {"name": "GenericAdapter", "error": "PARSE_ERROR"}
        ]
    }
)
```

The `context` field provides details about each adapter's failure for debugging.

### Disabling the Fallback

To disable fallback and require a specific adapter to succeed, configure it explicitly:

```python
# Configuration to require only eBay API (no fallback)
class IngestionSettings(BaseModel):
    ebay: AdapterConfig = Field(
        default_factory=lambda: AdapterConfig(
            enabled=True,
            timeout_s=6,
            retries=2,
        )
    )
    jsonld: AdapterConfig = Field(
        default_factory=lambda: AdapterConfig(
            enabled=False,  # Disable fallback to JSON-LD
        )
    )
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
