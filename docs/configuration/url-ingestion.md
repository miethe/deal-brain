# URL Ingestion Environment Variables Configuration

This document provides comprehensive guidance for configuring URL ingestion environment variables in Deal Brain.

## Overview

The URL ingestion system allows Deal Brain to fetch and parse pricing data directly from product URLs across multiple adapters (eBay, JSON-LD structured data, Amazon). The configuration is managed through environment variables that control adapter behavior, timeouts, retries, and price change detection.

## Architecture

### Configuration Structure

The URL ingestion configuration consists of three main components:

1. **IngestionSettings** - Master configuration for the entire ingestion system
2. **AdapterConfig** - Per-adapter configuration (eBay, JSON-LD, Amazon)
3. **Environment Variable Overrides** - API keys injected via top-level environment variables

```
Settings
└── ingestion: IngestionSettings
    ├── ingestion_enabled: bool
    ├── ebay: AdapterConfig
    ├── jsonld: AdapterConfig
    ├── amazon: AdapterConfig
    ├── price_change_threshold_pct: float
    ├── price_change_threshold_abs: Decimal
    ├── raw_payload_ttl_days: int
    └── raw_payload_max_bytes: int

AdapterConfig (used by ebay, jsonld, amazon)
├── enabled: bool
├── timeout_s: int
├── retries: int
└── api_key: str | None
```

## Environment Variables Reference

### Master Control

#### `INGESTION_INGESTION_ENABLED` (Optional)
- **Type**: Boolean
- **Default**: `true`
- **Valid Values**: `true`, `false`
- **Description**: Master switch to enable/disable the entire URL ingestion feature
- **Use Case**: Quickly disable ingestion across all adapters without individual configuration changes

**Examples:**
```bash
INGESTION_INGESTION_ENABLED=false  # Disable all ingestion
INGESTION_INGESTION_ENABLED=true   # Enable all ingestion (default)
```

### API Key Configuration

#### `EBAY_API_KEY` (Optional)
- **Type**: String
- **Default**: None (adapter will fail if authentication is required)
- **Description**: eBay API authentication key for accessing eBay product data
- **Status**: Enabled by default with 6-second timeout and 2 retries
- **Required For**: eBay adapter to function with authentication
- **Security**: Store securely in environment, not in code or version control

**Examples:**
```bash
EBAY_API_KEY=your-ebay-api-key-here
```

#### `AMAZON_API_KEY` (Optional)
- **Type**: String
- **Default**: None (adapter currently disabled - P1 phase)
- **Description**: Amazon API authentication key for accessing Amazon product data
- **Status**: Currently disabled (P1 implementation phase)
- **Required For**: Future Amazon adapter implementation
- **Note**: This variable is reserved for future use; Amazon adapter is not yet functional

**Examples:**
```bash
AMAZON_API_KEY=your-amazon-api-key-here
```

### eBay Adapter Configuration

#### `INGESTION_EBAY_ENABLED` (Optional)
- **Type**: Boolean
- **Default**: `true`
- **Valid Values**: `true`, `false`
- **Description**: Enable/disable the eBay adapter
- **Use Case**: Disable eBay ingestion while keeping other adapters active

**Examples:**
```bash
INGESTION_EBAY_ENABLED=false  # Disable eBay adapter
```

#### `INGESTION_EBAY_TIMEOUT_S` (Optional)
- **Type**: Integer
- **Default**: `6`
- **Valid Range**: 1-60 seconds
- **Description**: Request timeout for eBay API calls
- **Use Case**: Adjust based on network conditions or API response times
- **Recommendation**: Use default (6s) unless experiencing timeouts

**Examples:**
```bash
INGESTION_EBAY_TIMEOUT_S=10  # 10-second timeout
INGESTION_EBAY_TIMEOUT_S=3   # 3-second timeout for fast networks
```

#### `INGESTION_EBAY_RETRIES` (Optional)
- **Type**: Integer
- **Default**: `2`
- **Valid Range**: 0-5 attempts
- **Description**: Maximum number of retry attempts for failed eBay requests
- **Use Case**: Increase for unreliable networks, decrease to fail fast
- **Recommendation**: Use default (2) for balanced reliability

**Examples:**
```bash
INGESTION_EBAY_RETRIES=3  # Retry up to 3 times
INGESTION_EBAY_RETRIES=0  # No retries, fail immediately
```

### JSON-LD Adapter Configuration

#### `INGESTION_JSONLD_ENABLED` (Optional)
- **Type**: Boolean
- **Default**: `true`
- **Valid Values**: `true`, `false`
- **Description**: Enable/disable the JSON-LD structured data adapter
- **Use Case**: Disable for websites without structured data markup

**Examples:**
```bash
INGESTION_JSONLD_ENABLED=false
```

#### `INGESTION_JSONLD_TIMEOUT_S` (Optional)
- **Type**: Integer
- **Default**: `8`
- **Valid Range**: 1-60 seconds
- **Description**: Request timeout for JSON-LD parsing
- **Use Case**: Adjust for sites with slow response times
- **Recommendation**: Use default (8s) for general web scraping

**Examples:**
```bash
INGESTION_JSONLD_TIMEOUT_S=10  # 10-second timeout for slow sites
INGESTION_JSONLD_TIMEOUT_S=5   # 5-second timeout for fast responses
```

#### `INGESTION_JSONLD_RETRIES` (Optional)
- **Type**: Integer
- **Default**: `1`
- **Valid Range**: 0-5 attempts
- **Description**: Maximum retry attempts for failed JSON-LD requests
- **Recommendation**: Default (1) is usually sufficient for public web APIs

**Examples:**
```bash
INGESTION_JSONLD_RETRIES=2  # Retry once more on failure
```

### Amazon Adapter Configuration (Future)

#### `INGESTION_AMAZON_ENABLED` (Optional)
- **Type**: Boolean
- **Default**: `false`
- **Valid Values**: `true`, `false`
- **Description**: Enable/disable the Amazon adapter (currently disabled - P1 phase)
- **Status**: Reserved for future implementation
- **Note**: Amazon adapter is not yet functional; this variable is for future use

**Examples:**
```bash
INGESTION_AMAZON_ENABLED=false  # Keep disabled (P1 implementation)
```

#### `INGESTION_AMAZON_TIMEOUT_S` (Optional)
- **Type**: Integer
- **Default**: `8`
- **Valid Range**: 1-60 seconds
- **Description**: Request timeout for Amazon API calls (future use)

#### `INGESTION_AMAZON_RETRIES` (Optional)
- **Type**: Integer
- **Default**: `1`
- **Valid Range**: 0-5 attempts
- **Description**: Maximum retry attempts for Amazon API calls (future use)

### Price Change Detection

#### `INGESTION_PRICE_CHANGE_THRESHOLD_PCT` (Optional)
- **Type**: Float
- **Default**: `2.0`
- **Valid Range**: 0.0-100.0 (percentage)
- **Description**: Percentage change threshold for triggering price change events
- **Use Case**: Only emit price change events when price changes by this percentage or more
- **Example**: With default 2.0%, a $100 item needs a $2 price change to trigger an event
- **Recommendation**: Use 2.0% for normal operations; adjust based on business requirements

**Examples:**
```bash
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=5.0  # Only alert on 5% price changes
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=0.5  # Alert on small 0.5% changes
```

#### `INGESTION_PRICE_CHANGE_THRESHOLD_ABS` (Optional)
- **Type**: Decimal (string)
- **Default**: `1.0`
- **Valid Range**: Greater than 0
- **Unit**: USD
- **Description**: Absolute dollar amount threshold for triggering price change events
- **Use Case**: Complement percentage threshold with minimum absolute change
- **Logic**: Event fires if EITHER percentage OR absolute threshold is met
- **Recommendation**: Use 1.0 USD for typical price tracking

**Examples:**
```bash
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=2.5  # $2.50 minimum change
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=0.50 # $0.50 minimum change
```

**Example Scenario:**
- Thresholds: 2.0% OR $1.00
- Item: $100
- New price: $102 (2% change, $2 absolute)
- Result: Event fires (meets both thresholds)

- Item: $50
- New price: $50.80 (1.6% change, $0.80 absolute)
- Result: No event (meets neither threshold)

### Raw Payload Management

#### `INGESTION_RAW_PAYLOAD_TTL_DAYS` (Optional)
- **Type**: Integer
- **Default**: `30`
- **Valid Range**: 1-365 days
- **Description**: Time-to-live (TTL) for raw payload data stored in the database
- **Use Case**: Control storage and compliance requirements for ingested payloads
- **Recommendation**: 30 days provides good data retention for debugging
- **Compliance**: Adjust based on data retention policies

**Examples:**
```bash
INGESTION_RAW_PAYLOAD_TTL_DAYS=60  # Keep payloads for 60 days
INGESTION_RAW_PAYLOAD_TTL_DAYS=7   # Only 1 week retention
INGESTION_RAW_PAYLOAD_TTL_DAYS=365 # Full year retention
```

#### `INGESTION_RAW_PAYLOAD_MAX_BYTES` (Optional)
- **Type**: Integer
- **Default**: `524288` (512 KB)
- **Valid Range**: 1,024 - 10,485,760 bytes
- **Min**: 1 KB
- **Max**: 10 MB
- **Description**: Maximum size of stored raw payload data
- **Use Case**: Prevent storage of oversized payloads
- **Unit**: Bytes
- **Recommendation**: 512 KB is sufficient for most product pages

**Examples:**
```bash
INGESTION_RAW_PAYLOAD_MAX_BYTES=262144    # 256 KB limit
INGESTION_RAW_PAYLOAD_MAX_BYTES=1048576   # 1 MB limit
INGESTION_RAW_PAYLOAD_MAX_BYTES=524288    # 512 KB (default)
```

**Size Reference:**
- 256 KB: `262144` bytes - Conservative limit
- 512 KB: `524288` bytes - Default, suitable for typical product pages
- 1 MB: `1048576` bytes - Generous limit for complex pages
- 5 MB: `5242880` bytes - Maximum for very large payloads

## Quick Start Configuration

### Minimal Setup (No URL Ingestion)

```bash
# Master control disabled
INGESTION_INGESTION_ENABLED=false
```

### Basic Setup (Default Settings)

```bash
# All defaults are used - no environment variables needed
# This provides:
# - eBay adapter enabled (6s timeout, 2 retries)
# - JSON-LD adapter enabled (8s timeout, 1 retry)
# - Amazon adapter disabled (P1 phase)
# - Price change detection: 2% or $1.00
# - 30-day payload retention, 512 KB max per payload
```

### Local Development Setup

```bash
# Enable all adapters with conservative timeouts
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=true
INGESTION_EBAY_TIMEOUT_S=10
INGESTION_EBAY_RETRIES=2
INGESTION_JSONLD_ENABLED=true
INGESTION_JSONLD_TIMEOUT_S=10
INGESTION_JSONLD_RETRIES=1

# Price change detection
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=2.0
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=1.0

# Payload management
INGESTION_RAW_PAYLOAD_TTL_DAYS=30
INGESTION_RAW_PAYLOAD_MAX_BYTES=524288
```

### Production Setup

```bash
# Production-grade configuration with API keys
INGESTION_INGESTION_ENABLED=true

# eBay - Production API key with standard settings
EBAY_API_KEY=your-production-ebay-api-key
INGESTION_EBAY_ENABLED=true
INGESTION_EBAY_TIMEOUT_S=8
INGESTION_EBAY_RETRIES=3

# JSON-LD - Fast timeout for reliability
INGESTION_JSONLD_ENABLED=true
INGESTION_JSONLD_TIMEOUT_S=6
INGESTION_JSONLD_RETRIES=2

# Amazon - Keep disabled until P1 implementation complete
INGESTION_AMAZON_ENABLED=false

# Price change detection - Stricter thresholds
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=1.0
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=0.50

# Payload management - Shorter retention, smaller size for storage efficiency
INGESTION_RAW_PAYLOAD_TTL_DAYS=14
INGESTION_RAW_PAYLOAD_MAX_BYTES=262144
```

### Testing Setup

```bash
# Disable ingestion for integration tests
INGESTION_INGESTION_ENABLED=false

# Or enable with fast timeouts for testing
INGESTION_EBAY_TIMEOUT_S=2
INGESTION_EBAY_RETRIES=0
INGESTION_JSONLD_TIMEOUT_S=2
INGESTION_JSONLD_RETRIES=0

# Minimal payload retention for tests
INGESTION_RAW_PAYLOAD_TTL_DAYS=1
INGESTION_RAW_PAYLOAD_MAX_BYTES=1048576
```

## Advanced Configuration

### Performance Tuning

#### Optimizing for Speed

Use shorter timeouts and fewer retries for fast, reliable networks:

```bash
INGESTION_EBAY_TIMEOUT_S=4
INGESTION_EBAY_RETRIES=0
INGESTION_JSONLD_TIMEOUT_S=4
INGESTION_JSONLD_RETRIES=0
```

#### Optimizing for Reliability

Use longer timeouts and more retries for unreliable networks:

```bash
INGESTION_EBAY_TIMEOUT_S=15
INGESTION_EBAY_RETRIES=5
INGESTION_JSONLD_TIMEOUT_S=15
INGESTION_JSONLD_RETRIES=3
```

### Selective Adapter Enablement

#### eBay Only

```bash
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=true
INGESTION_JSONLD_ENABLED=false
INGESTION_AMAZON_ENABLED=false
EBAY_API_KEY=your-api-key
```

#### JSON-LD Only (No API Key Required)

```bash
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=false
INGESTION_JSONLD_ENABLED=true
INGESTION_AMAZON_ENABLED=false
```

### Price Change Detection Strategies

#### Sensitive Detection (Catch All Changes)

Use low thresholds to capture every price change:

```bash
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=0.1   # 0.1% or...
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=0.01  # 1 cent minimum
```

#### Standard Detection (Default)

```bash
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=2.0   # 2% or...
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=1.0   # $1 minimum
```

#### Strict Detection (Only Major Changes)

Ignore minor fluctuations:

```bash
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=5.0    # 5% or...
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=5.0    # $5 minimum
```

### Storage and Compliance Configuration

#### GDPR/Data Minimization

```bash
INGESTION_RAW_PAYLOAD_TTL_DAYS=7            # 1 week only
INGESTION_RAW_PAYLOAD_MAX_BYTES=262144      # 256 KB limit
```

#### Extended Retention (Compliance/Audit)

```bash
INGESTION_RAW_PAYLOAD_TTL_DAYS=365          # Full year
INGESTION_RAW_PAYLOAD_MAX_BYTES=5242880     # 5 MB for archives
```

#### Cost Optimization

```bash
INGESTION_RAW_PAYLOAD_TTL_DAYS=3            # Only 3 days
INGESTION_RAW_PAYLOAD_MAX_BYTES=262144      # 256 KB
```

## Configuration Examples

### Example 1: eBay-Only Setup for Testing

```bash
# Only eBay adapter enabled
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_ENABLED=true
INGESTION_EBAY_TIMEOUT_S=5
INGESTION_EBAY_RETRIES=1
INGESTION_JSONLD_ENABLED=false
INGESTION_AMAZON_ENABLED=false

# Sensitive price detection for testing
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=0.5
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=0.25

# Short-lived payloads for testing
INGESTION_RAW_PAYLOAD_TTL_DAYS=1
INGESTION_RAW_PAYLOAD_MAX_BYTES=1048576
```

### Example 2: Multi-Source Production

```bash
# Multiple adapters enabled for production
INGESTION_INGESTION_ENABLED=true

# eBay with API key
EBAY_API_KEY=prod-ebay-key-12345
INGESTION_EBAY_ENABLED=true
INGESTION_EBAY_TIMEOUT_S=8
INGESTION_EBAY_RETRIES=3

# JSON-LD for fallback
INGESTION_JSONLD_ENABLED=true
INGESTION_JSONLD_TIMEOUT_S=8
INGESTION_JSONLD_RETRIES=2

# Amazon disabled (future)
INGESTION_AMAZON_ENABLED=false

# Balanced price detection
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=2.0
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=1.0

# Standard retention
INGESTION_RAW_PAYLOAD_TTL_DAYS=30
INGESTION_RAW_PAYLOAD_MAX_BYTES=524288
```

### Example 3: Minimal Staging Setup

```bash
# Keep it simple for staging
INGESTION_INGESTION_ENABLED=true
INGESTION_EBAY_TIMEOUT_S=10
INGESTION_JSONLD_TIMEOUT_S=10

# Everything else uses defaults
```

## Validation Rules

### Constraint Validation

The configuration system enforces strict validation on all settings:

| Setting | Constraints |
|---------|-------------|
| `timeout_s` | Must be between 1 and 60 seconds |
| `retries` | Must be between 0 and 5 |
| `price_change_threshold_pct` | Must be between 0.0 and 100.0 |
| `price_change_threshold_abs` | Must be greater than 0 (decimal) |
| `raw_payload_ttl_days` | Must be between 1 and 365 days |
| `raw_payload_max_bytes` | Must be between 1,024 and 10,485,760 bytes |

### Invalid Configuration Examples

```bash
# INVALID: Timeout too short
INGESTION_EBAY_TIMEOUT_S=0  # Must be >= 1

# INVALID: Timeout too long
INGESTION_EBAY_TIMEOUT_S=120  # Must be <= 60

# INVALID: Negative price threshold
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=-1.0  # Must be >= 0.0

# INVALID: Payload size too small
INGESTION_RAW_PAYLOAD_MAX_BYTES=512  # Must be >= 1024

# INVALID: Retention too long
INGESTION_RAW_PAYLOAD_TTL_DAYS=400  # Must be <= 365
```

## Runtime Behavior

### Configuration Application

1. **Initialization**: Settings are loaded from environment variables on application startup
2. **Validation**: Pydantic validates all settings against constraints
3. **Injection**: API keys from environment variables are injected into adapter configs during post-initialization
4. **Caching**: Settings are cached after first load (via `@lru_cache`)

### API Key Handling

- **Environment Override**: `EBAY_API_KEY` and `AMAZON_API_KEY` environment variables override any defaults
- **Injection Point**: API keys are injected into respective `AdapterConfig` objects during `Settings.model_post_init()`
- **Security**: API keys are never logged or exposed in error messages
- **Optional**: Omitting API keys disables authenticated requests for those adapters

### Adapter Interaction

When a URL ingestion request is processed:

1. System checks if `ingestion_enabled` is true
2. For each enabled adapter, validates `adapter.enabled` flag
3. Creates request with adapter's `timeout_s` and `retries` settings
4. Stores raw payload if within `raw_payload_max_bytes` limit
5. Monitors price changes against both percentage and absolute thresholds
6. Automatically cleans up payloads older than `raw_payload_ttl_days`

## Troubleshooting

### Ingestion Not Working

**Problem**: URL ingestion not processing any requests

**Check**:
```bash
# 1. Verify master control is enabled
echo $INGESTION_INGESTION_ENABLED  # Should be true

# 2. Verify at least one adapter is enabled
echo $INGESTION_EBAY_ENABLED      # or check JSONLD
echo $INGESTION_JSONLD_ENABLED

# 3. If eBay enabled, verify API key if required
echo $EBAY_API_KEY
```

### Frequent Timeouts

**Problem**: Adapters frequently timing out

**Solution**: Increase timeout values
```bash
INGESTION_EBAY_TIMEOUT_S=15      # Increase from 6 to 15
INGESTION_JSONLD_TIMEOUT_S=15    # Increase from 8 to 15
```

### Too Many Retries

**Problem**: Slow ingestion due to excessive retry attempts

**Solution**: Reduce retries
```bash
INGESTION_EBAY_RETRIES=0         # Fail immediately on first error
INGESTION_JSONLD_RETRIES=0
```

### Missing Price Change Alerts

**Problem**: Price changes not triggering events

**Check**:
```bash
# Price change thresholds might be too high
# Default: 2% OR $1.00

# Lower thresholds to catch smaller changes
INGESTION_PRICE_CHANGE_THRESHOLD_PCT=0.5   # 0.5% instead of 2%
INGESTION_PRICE_CHANGE_THRESHOLD_ABS=0.10  # $0.10 instead of $1.00
```

### Database Growing Too Large

**Problem**: Raw payload storage consuming too much space

**Solution**: Reduce retention or payload size limits
```bash
INGESTION_RAW_PAYLOAD_TTL_DAYS=7        # 7 days instead of 30
INGESTION_RAW_PAYLOAD_MAX_BYTES=262144  # 256 KB instead of 512 KB
```

## Environment Variable Format

### Naming Convention

All environment variables follow the pattern: `INGESTION_[ADAPTER_NAME]_[SETTING_NAME]`

Examples:
```
INGESTION_INGESTION_ENABLED              # Master control
INGESTION_EBAY_ENABLED                   # eBay-specific
INGESTION_EBAY_TIMEOUT_S                 # eBay timeout
INGESTION_JSONLD_RETRIES                 # JSON-LD retries
INGESTION_PRICE_CHANGE_THRESHOLD_PCT     # Global setting
INGESTION_RAW_PAYLOAD_TTL_DAYS           # Global setting
```

### Type Conversion

- **Boolean**: Converted from `true`/`false` strings
- **Integer**: Parsed as base-10 integers
- **Float**: Parsed with decimal support
- **Decimal**: Parsed as precise decimal numbers (for USD amounts)

### Optional vs Required

- **All ingestion variables are optional**: They have sensible defaults
- **API keys are optional**: Omitting them disables authenticated adapters
- **Only DATABASE_URL is required** (for main application)

## Related Documentation

- [URL Ingestion Architecture](/docs/URL_INGESTION_ARCHITECTURE.md)
- [API Reference](/docs/api/)
- [Development Setup](/docs/setup.md)

## Support

For issues or questions about URL ingestion configuration:

1. Check the Troubleshooting section above
2. Review the URL Ingestion Architecture documentation
3. Examine server logs for validation errors
4. Verify environment variables with `env | grep INGESTION`

