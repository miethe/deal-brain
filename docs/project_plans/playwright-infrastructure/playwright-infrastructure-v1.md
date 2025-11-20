---
title: "Playwright Infrastructure Optimization and URL Ingestion Enhancement"
description: "A comprehensive two-part enhancement addressing Playwright integration bloat and adding fallback support for JavaScript-rendered marketplace listings through Playwright-based URL scraping."
audience: [ai-agents, developers, pm]
tags: [playwright, docker-optimization, url-ingestion, adapters, infrastructure]
created: 2025-11-20
updated: 2025-11-20
category: "product-planning"
status: published
related:
  - /docs/architecture/playwright-optimization-analysis.md
  - /docs/architecture/URL_INGESTION_ARCHITECTURE.md
---

# Playwright Infrastructure Optimization and URL Ingestion Enhancement

## Executive Summary

This PRD addresses two interconnected infrastructure challenges:

1. **Build Bloat**: Playwright adds 1.58GB to Docker images (1.71GB total) and 2-3 minutes to build time, but is only used for social media card generation (not core functionality).

2. **URL Ingestion Gaps**: Current adapters (eBay API, JSON-LD) succeed on 60-70% of listings, failing on JavaScript-heavy sites like Amazon where product data requires browser rendering.

The solution involves two parallel tracks:
- **Phase 1: Build Optimization** (2-3 hours) — Multi-stage Docker builds to eliminate Playwright from development workflows
- **Phase 2-4: URL Ingestion Enhancement** (4-5 days) — Add Playwright-based adapter as priority-10 fallback with browser pool and anti-detection features

**Success Metrics:**
- Dev build: 5-6min → 2-3min (50% reduction)
- Dev image: 1.71GB → 500MB (65% reduction)
- URL extraction success: 60-70% → 85%+
- Amazon extraction: <20% → 70%+

---

## Problem Statement

### Part 1: Docker Image Bloat

**Current State:**
- API/Worker images: 1.71GB each
- Build time: 5-6 minutes (local + Docker)
- Contains 33 system dependencies + Chromium browser for single use case

**Impact:**
- Slow feedback loop for developers (builds block iteration)
- High CI/CD costs (4-6 minutes per deployment × 10+ builds/day = 40+ minutes overhead)
- Large storage footprint (3.4GB for API + Worker images)
- Developers forced to carry production dependencies in local dev environment

**Root Cause:**
Playwright is installed unconditionally for all environments (dev, CI, prod) even though it's only used for optional card image generation—not core listing data functionality. The system degrades gracefully if card generation is unavailable.

### Part 2: URL Ingestion Success Rate Gaps

**Current State:**
- eBay API adapter: Works when API key configured, fails silently otherwise
- JSON-LD adapter: Extracts structured data from HTML when available (60-70% success rate)
- Amazon/JavaScript sites: Fail entirely (Amazon requires JavaScript rendering for price/specs)
- No fallback mechanism for JavaScript-rendered content

**Impact:**
- Amazon listings (major marketplace) have <20% extraction success
- Users import manually or skip listings, reducing inventory coverage
- Competitive disadvantage vs. scraping-first systems
- Partial imports with missing prices reduce valuation accuracy

**Root Cause:**
Current adapters rely on static HTML parsing. Many modern marketplaces (Amazon, Walmart, etc.) render critical product data with JavaScript, making the data invisible to static parsers. Playwright (available in devDependencies) could render JavaScript to extract complete data.

---

## Goals

### Part 1: Build Optimization
- Reduce development image size from 1.71GB to ~500MB (65% reduction)
- Reduce development build time from 5-6 minutes to 2-3 minutes (50% reduction)
- Zero impact to production deployment process
- Enable faster local iteration for all developers
- Reduce CI/CD overhead by 40-50 minutes per day

### Part 2: URL Ingestion Enhancement
- Increase overall extraction success rate from 60-70% to 85%+
- Achieve 70%+ success rate for Amazon listings (currently <20%)
- Add JavaScript-aware extraction fallback without breaking existing adapters
- Keep extraction latency under 10 seconds for Playwright requests (acceptable for fallback)
- Support both full and partial imports (price-optional for data-rich listings)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PART 1: BUILD OPTIMIZATION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Multi-Stage Dockerfile        Docker Compose Profiles           │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐  │
│  │ FROM python:3.11-slim    │  │ services:                    │  │
│  │                          │  │   api (default profile)      │  │
│  │ stage: development       │  │   → development target       │  │
│  │ └─ NO Playwright         │  │                              │  │
│  │                          │  │   api-prod (prod profile)    │  │
│  │ stage: production        │  │   → production target        │  │
│  │ └─ WITH Playwright       │  │                              │  │
│  └──────────────────────────┘  └──────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                PART 2: URL INGESTION ENHANCEMENT                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Adapter Priority Chain                Browser Pool              │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐  │
│  │ Priority 1: eBay API     │  │ Browser Instance Pool        │  │
│  │ Priority 5: JSON-LD      │  │ ├─ 2-3 browsers max          │  │
│  │ Priority 10: Playwright  │  │ ├─ Reusable instances        │  │
│  │                          │  │ ├─ Anti-detection headers    │  │
│  │ (Fallback for JS sites)  │  │ ├─ Stealth mode              │  │
│  └──────────────────────────┘  └──────────────────────────────┘  │
│                                                                   │
│  Error Handling & Retry                                          │
│  ┌──────────────────────────┐                                    │
│  │ Non-retryable:           │                                    │
│  │ • 404 (item not found)   │                                    │
│  │ • Invalid schema         │                                    │
│  │                          │                                    │
│  │ Retryable (exp backoff): │                                    │
│  │ • Timeout                │                                    │
│  │ • Rate limit             │                                    │
│  │ • Network error          │                                    │
│  └──────────────────────────┘                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requirements & Acceptance Criteria

### Part 1: Build Optimization

| Requirement | Acceptance Criteria | Files Modified |
|------------|-------------------|-----------------|
| **Multi-stage Dockerfile** | Development stage has NO Playwright system deps; Production stage retains all deps; Same base image used for both | `infra/api/Dockerfile` |
| **Development image size** | `docker build --target=development` produces image <600MB | Measurement command provided in docs |
| **Development build time** | Build completes in 2-3 minutes locally (without Docker caching) | Benchmark included in phase progress |
| **Production unchanged** | `docker build --target=production` (or default) is identical to current image | Checksum comparison in tests |
| **Docker Compose profiles** | `docker compose up` uses dev target; `docker compose --profile production up` uses prod target | `docker-compose.yml` |
| **Worker Dockerfile** | Mirrors API optimization (multi-stage, profiles) | `infra/worker/Dockerfile` |
| **Documentation** | New build process documented with examples | `docs/development/docker-optimization.md` |
| **CI/CD integration** | GitHub Actions use correct target; Dev CI uses development target | `.github/workflows/*.yml` |
| **Backward compatibility** | Existing `make up`, `make api`, `make web` commands work without changes | `Makefile` (no changes required) |

### Part 2: URL Ingestion Enhancement

#### Phase 2A: PlaywrightAdapter Implementation

| Requirement | Acceptance Criteria | Files Modified |
|------------|-------------------|-----------------|
| **PlaywrightAdapter class** | Inherits from BaseAdapter; Implements extract() method; Returns NormalizedListingSchema | `apps/api/dealbrain_api/adapters/playwright.py` |
| **Browser pool management** | Maintains 2-3 reusable Chromium instances; Gracefully handles browser crashes; Implements connection pooling | `apps/api/dealbrain_api/adapters/browser_pool.py` |
| **Fallback chain integration** | PlaywrightAdapter registered in router with priority=10; Attempted only after higher-priority adapters fail | `apps/api/dealbrain_api/adapters/router.py` |
| **Anti-detection features** | Uses stealth mode; Includes realistic User-Agent; Disables headless mode (optional); Sets viewport size | `apps/api/dealbrain_api/adapters/playwright.py` |
| **Timeout handling** | 8-10 second timeout per request; Respects Playwright timeout settings; Logs timeout errors | Base configuration |
| **Error handling** | Distinguishes between: timeout, parsing error, selector not found, page error | AdapterError enums |
| **Success metrics** | Extracts title, price, condition from 70%+ of Amazon/JS-heavy sites tested | Test coverage >80% |

#### Phase 2B: Adapter Router Enhancement

| Requirement | Acceptance Criteria | Files Modified |
|------------|-------------------|-----------------|
| **Fallback mechanism** | Router.extract() tries adapters sequentially by priority; Logs each attempt; Stops on success or non-retryable error | `apps/api/dealbrain_api/adapters/router.py` (updated) |
| **Fast-fail conditions** | ITEM_NOT_FOUND, ADAPTER_DISABLED skip remaining adapters; Other errors continue chain | Documented behavior |
| **Adapter enablement** | Settings control which adapters are enabled; PlaywrightAdapter can be toggled via configuration | `apps/api/dealbrain_api/settings.py` |
| **Metrics & monitoring** | Logs adapter name + success/failure for each URL; Tracks fallback chain length; Reports which adapter succeeded | Observability integrated |

#### Phase 3: Production Hardening

| Requirement | Acceptance Criteria | Files Modified |
|------------|-------------------|-----------------|
| **Rate limiting** | PlaywrightAdapter respects rate limits; Default 60 req/min; Configurable per source | Browser pool integration |
| **Retry logic** | Exponential backoff (1s, 2s, 4s) for retryable errors; Max 2 retries | RetryConfig in adapter |
| **Resource cleanup** | Browser instances closed on process shutdown; No hanging processes | Proper async context managers |
| **Memory management** | Browser pool size capped at 3 instances; Old browsers recycled after N requests | Browser pool monitoring |
| **Partial import support** | Listings with missing price marked as "partial"; Extraction metadata tracked; UI handles gracefully | NormalizedListingSchema |
| **Database migration** | No new tables required; Uses existing fields: raw_listing_json, attributes_json, extraction_metadata | No Alembic migration |
| **Observability** | Structured logging for all adapter operations; Metrics for success rate by adapter; Performance breakdown by source | OpenTelemetry integration |

#### Phase 4: Anti-Detection Optimization (Optional)

| Requirement | Acceptance Criteria | Files Modified |
|------------|-------------------|-----------------|
| **Stealth plugin** | Integrates playwright-stealth; Masks browser automation signals | `apps/api/dealbrain_api/adapters/playwright.py` |
| **User-Agent rotation** | Cycles through realistic User-Agent strings; Matches viewport and OS | Browser pool config |
| **JavaScript execution** | Waits for network idle or specific element visibility; Handles dynamic rendering | Selector strategies |
| **Cookie/session handling** | Preserves session cookies across requests; Handles CloudFlare challenges (if needed) | Optional for Phase 4 |

---

## Phased Implementation Plan

### Phase 1: Multi-Stage Docker Optimization (2-3 hours, IMMEDIATE)

**Goal:** Enable fast local development, zero impact to production.

**Tasks:**

1. **Backup current Dockerfiles**
   - Copy `infra/api/Dockerfile` → `infra/api/Dockerfile.backup`
   - Copy `infra/worker/Dockerfile` → `infra/worker/Dockerfile.backup`

2. **Create multi-stage Dockerfile for API**
   - **Development stage:**
     - `FROM python:3.11-slim AS development`
     - Install build-essential, libpq-dev, ca-certificates only
     - Copy dependencies and install with Poetry
     - NO Playwright system packages, NO `playwright install chromium`
     - CMD: `dealbrain-api`

   - **Production stage:**
     - `FROM python:3.11-slim AS production`
     - Install ALL current system dependencies (including Playwright)
     - Copy dependencies and install with Poetry
     - `playwright install chromium`
     - CMD: `dealbrain-api`

3. **Implement Docker Compose profiles**
   - Development service uses `target: development` (default)
   - Add production profile with `target: production`
   - Update example: `docker compose --profile production up`

4. **Mirror optimization to Worker Dockerfile**
   - Identical multi-stage approach for `infra/worker/Dockerfile`

5. **Update Makefile** (optional, for convenience)
   - Add `make up-prod` target: `docker compose --profile production up`
   - Existing `make up` unchanged (uses default development)

6. **Update CI/CD pipelines**
   - GitHub Actions development builds: add `--target development` to build command
   - Production builds: add `--target production` or omit (defaults to latest)

7. **Documentation & testing**
   - Document new build process in `/docs/development/docker-optimization.md`
   - Test: `docker build --target development` produces <600MB image
   - Test: `docker build --target production` produces 1.71GB image (unchanged)
   - Test: `make up` works for development
   - Test: `docker compose --profile production up` works for production

**Deliverables:**
- Modified `infra/api/Dockerfile` (multi-stage)
- Modified `infra/worker/Dockerfile` (multi-stage)
- Updated `docker-compose.yml` with profiles
- `docs/development/docker-optimization.md`
- Build benchmarks (before/after)

**Success Metrics:**
- Dev image size: <600MB (measured with `docker images`)
- Dev build time: 2-3 minutes (without cache)
- Prod image identical to current (verified with checksum or features)
- All existing commands work without changes

---

### Phase 2A: PlaywrightAdapter MVP (1-2 days, HIGH PRIORITY)

**Goal:** Add JavaScript-aware extraction fallback; achieve 70%+ success on Amazon.

**Prerequisites:**
- Phase 1 complete (allows Playwright to be used safely in production)

**Tasks:**

1. **Create browser pool utility**
   - File: `apps/api/dealbrain_api/adapters/browser_pool.py`
   - Class: `BrowserPool`
     - Singleton pattern (reuse across requests)
     - Maintains 2-3 reusable Chromium instances
     - Implements async context manager for browser lifecycle
     - Handles browser crashes (auto-restart)
     - Configurable pool size via settings

   - Methods:
     ```python
     async def acquire_browser() -> Browser
     async def release_browser(browser: Browser) -> None
     async def close_all() -> None  # For shutdown
     ```

2. **Implement PlaywrightAdapter class**
   - File: `apps/api/dealbrain_api/adapters/playwright.py`
   - Inherits from `BaseAdapter`
   - Constructor:
     ```python
     def __init__(self):
         super().__init__(
             name="playwright",
             supported_domains=["*"],  # Wildcard: fallback for any domain
             priority=10,  # Lowest priority (fallback)
             timeout_s=8,
             max_retries=2,
         )
     ```

   - Implement `extract(url: str) -> NormalizedListingSchema`:
     1. Acquire browser from pool
     2. Create new page with User-Agent + viewport
     3. Navigate to URL with timeout
     4. Wait for network idle or dynamic content (configurable)
     5. Extract data using CSS selectors + JavaScript evaluation
     6. Map to NormalizedListingSchema
     7. Return browser to pool
     8. Raise AdapterException on errors (timeout, parse error, etc.)

3. **Add anti-detection features**
   - User-Agent headers: Rotate between realistic agents
   - Viewport: Set to 1920x1080 (desktop)
   - Headless mode: Run as `headless=True` for performance (toggle in settings)
   - Disable automation detection:
     ```python
     browser = await launch_browser(
         args=["--disable-blink-features=AutomationControlled"],
         headless=True,
     )
     await page.add_init_script("""
         Object.defineProperty(navigator, 'webdriver', {
             get: () => undefined
         })
     """)
     ```

4. **Handle JavaScript rendering**
   - Wait strategies:
     - `page.wait_for_load_state("networkidle")` — Wait for network idle
     - `page.wait_for_selector(".price")` — Wait for specific element
     - Fallback: `asyncio.sleep(2)` — Fixed 2-second wait
   - Configurable per domain (e.g., Amazon may need longer waits)

5. **Extract listing data via JavaScript + CSS**
   - Use CSS selectors for common fields:
     - Title: `h1`, `h2`, `.title`, `.product-title`
     - Price: `.price`, `.current-price`, `[data-price]`
     - Condition: `.condition`, `.item-condition`
   - Fallback to JavaScript evaluation:
     ```python
     title = await page.evaluate("""
         () => document.querySelector('h1')?.textContent
     """)
     ```

6. **Map extracted data to NormalizedListingSchema**
   - Handle missing fields gracefully
   - Mark partial imports if price unavailable
   - Track extraction metadata (which fields succeeded)
   - Return schema even if some fields missing

7. **Add PlaywrightAdapter to router**
   - File: `apps/api/dealbrain_api/adapters/router.py`
   - Import PlaywrightAdapter
   - Add to `AVAILABLE_ADAPTERS` list:
     ```python
     AVAILABLE_ADAPTERS: list[type[BaseAdapter]] = [
         EbayAdapter,      # priority 1
         JsonLdAdapter,    # priority 5
         PlaywrightAdapter,  # priority 10
     ]
     ```

8. **Configure settings**
   - File: `apps/api/dealbrain_api/settings.py`
   - Add PlaywrightAdapter configuration:
     ```python
     class PlaywrightAdapterConfig(BaseModel):
         enabled: bool = True  # Can disable if Playwright causes issues
         timeout_s: int = 8
         max_retries: int = 2
         pool_size: int = 3
         headless: bool = True
     ```

9. **Testing**
   - Unit tests:
     - Extract from test HTML pages (mock Playwright responses)
     - Verify NormalizedListingSchema output
     - Test error handling (timeout, parse error)

   - Integration tests (require real URLs):
     - Amazon product page → extract title, price, condition
     - Walmart product page → extract specs
     - Generic site → fallback behavior

   - Metrics:
     - Success rate: 70%+ on test Amazon URLs
     - Latency: <10s per request
     - Error rate: <10% (network issues)

**Deliverables:**
- `apps/api/dealbrain_api/adapters/browser_pool.py`
- `apps/api/dealbrain_api/adapters/playwright.py`
- Updated `apps/api/dealbrain_api/adapters/router.py`
- Updated `apps/api/dealbrain_api/settings.py`
- Unit + integration tests in `tests/adapters/test_playwright.py`

**Success Metrics:**
- 70%+ extraction success on Amazon test URLs
- <10s latency per Playwright request
- Adapter integrates seamlessly into fallback chain
- No impact to existing adapters (eBay, JSON-LD)

---

### Phase 2B: Fallback Chain & Error Handling (½ day)

**Goal:** Ensure robust fallback behavior; proper error handling across all adapters.

**Tasks:**

1. **Enhance AdapterRouter.extract() fallback logic**
   - Already implemented in router (see `URL_INGESTION_ARCHITECTURE.md`)
   - Verify handling of:
     - Non-retryable errors (ITEM_NOT_FOUND, ADAPTER_DISABLED)
     - Retryable errors (TIMEOUT, RATE_LIMITED, NETWORK_ERROR)
     - Adapter initialization failures
   - Ensure ALL errors logged with adapter name

2. **Add adapter enablement via settings**
   - Each adapter can be disabled individually
   - Fallback chain skips disabled adapters
   - Configuration in `apps/api/dealbrain_api/settings.py`:
     ```python
     ingestion:
         ebay:
             enabled: true
             api_key: "..."
         jsonld:
             enabled: true
         playwright:
             enabled: true
             timeout_s: 8
     ```

3. **Enhance error telemetry**
   - Structured logging for each adapter attempt
   - Include: URL, adapter name, error type, error message
   - Example log:
     ```
     [eBay] Trying adapter ebay for https://ebay.com/itm/123
     [eBay] EbayAdapter failed: [configuration_error] eBay Browse API key not configured
     [JSON-LD] Trying adapter jsonld for https://ebay.com/itm/123
     [JSON-LD] JsonLdAdapter failed: [no_structured_data] No JSON-LD found
     [Playwright] Trying adapter playwright for https://ebay.com/itm/123
     [Playwright] Success with playwright adapter
     ```

4. **Test fallback chain**
   - Unit tests for each failure scenario
   - Verify correct adapter is tried next
   - Verify correct error raised when all fail

**Deliverables:**
- Updated `apps/api/dealbrain_api/adapters/router.py` (enhanced logging)
- Updated settings configuration
- Test coverage for fallback chains

**Success Metrics:**
- Fallback chain works correctly for all error types
- Logging is clear and actionable (includes adapter name)
- Disabled adapters are skipped silently

---

### Phase 3: Production Hardening & Observability (1-2 days)

**Goal:** Ensure Playwright adapter is production-ready; add monitoring; handle edge cases.

**Tasks:**

1. **Rate limiting for PlaywrightAdapter**
   - Base class RateLimitConfig already supports per-adapter limits
   - Configure: 60 req/min default (conservative for non-API endpoints)
   - Implement exponential backoff on 429 responses
   - Log rate limit hits

2. **Retry strategy with exponential backoff**
   - Base class RetryConfig already implemented
   - For Playwright: 2 retries, backoff 1s, 2s, 4s
   - Configure retryable errors: TIMEOUT, NETWORK_ERROR, RATE_LIMITED
   - Don't retry: INVALID_SCHEMA, ITEM_NOT_FOUND

3. **Resource cleanup on shutdown**
   - Register BrowserPool cleanup with FastAPI shutdown event
   - Ensure all browser instances closed
   - Log any hanging connections
   - File: `apps/api/dealbrain_api/main.py` (update startup/shutdown handlers)

4. **Memory management**
   - Browser pool size cap: 3 instances max (configurable)
   - Recycle browsers after 50 requests (configurable)
   - Monitor memory usage (optional telemetry)
   - Auto-restart crashed browsers

5. **Partial import support**
   - Existing: NormalizedListingSchema has `quality` field ("full" or "partial")
   - Playwright: Mark as "partial" if price/condition missing
   - Tracking: `extraction_metadata` field records which fields succeeded
   - UI/API: Already handles partial imports gracefully

6. **Observability & monitoring**
   - Structured logging for:
     - Browser pool: acquire/release/recycle
     - Page navigation: URL, timing, status
     - Extraction: title, price, condition success/failure
     - Errors: exception type, message, metadata
   - Metrics (OpenTelemetry):
     - `playwright_extraction_duration_ms` (per URL)
     - `playwright_extraction_success_rate` (success/total)
     - `playwright_browser_pool_size` (active browsers)
     - `playwright_request_latency` (p50, p95, p99)

7. **Testing**
   - Memory tests: Verify browser pool doesn't grow unbounded
   - Shutdown tests: Verify clean browser closure
   - Edge case tests:
     - Very slow pages (8s timeout)
     - Pages with JavaScript errors
     - Redirects (e.g., expired listings)
     - Bot detection (403, 429, etc.)

**Deliverables:**
- Enhanced BrowserPool with memory management
- Updated PlaywrightAdapter with rate limiting + retry
- FastAPI shutdown handlers in `apps/api/dealbrain_api/main.py`
- Observability integration (logging + metrics)
- Edge case test suite

**Success Metrics:**
- Browser pool stable under load (no unbounded growth)
- Clean shutdown: all browsers closed on exit
- Latency metrics tracked and reported
- Error rate <10% for extraction operations

---

### Phase 4: Anti-Detection Optimization (1 day, OPTIONAL)

**Goal:** Improve success rate on sites with anti-bot detection; improve realism.

**Tasks:**

1. **Integrate playwright-stealth plugin**
   - Install dependency: `pip install playwright-stealth`
   - Apply stealth techniques:
     ```python
     from playwright_stealth import stealth_sync

     browser = await launch_browser(...)
     stealth_sync(browser)
     ```
   - Masks webdriver automation signals
   - Reference: https://github.com/easyinsf/playwright_stealth

2. **User-Agent rotation**
   - Maintain list of realistic User-Agents (chrome, firefox, safari variants)
   - Rotate on each request
   - Match viewport size to OS/browser combo
   - Example: Chrome on Windows 1920x1080, Safari on macOS 1440x900

3. **Advanced JavaScript rendering**
   - Wait for dynamic content:
     - `page.wait_for_function()` — Wait for JS to set data attribute
     - `page.wait_for_selector(".price")` — Wait for price element
   - Handle infinite scroll (if needed):
     - Scroll to bottom, wait for more items, repeat
   - Execute custom JavaScript to extract hidden data

4. **Cookie/session handling** (if needed)
   - Preserve cookies across requests in same session
   - Handle CloudFlare challenges (optional, advanced)
   - Manage session state for repeat visits to same domain

5. **Testing on hard targets**
   - Test against: Amazon, Walmart, BestBuy (known for bot detection)
   - Measure success rate before/after stealth mode
   - Verify latency acceptable (<10s)

**Deliverables:**
- Enhanced PlaywrightAdapter with stealth mode
- User-Agent rotation utility
- Advanced JavaScript execution strategies
- Test results against hard targets

**Success Metrics:**
- Success rate on Amazon improves from 70% to 80%+
- Fewer 403/429 responses
- Latency still <10s

---

## Database & Data Model

### No Schema Changes Required

The existing `Listing` model already supports:
- `raw_listing_json` — Stores raw Playwright HTML/data
- `attributes_json` — Flexible JSON for extra fields
- `extraction_metadata` — Tracks which fields extracted successfully
- `quality` field — Marks full vs. partial imports

### Adapter Output Format

All adapters return `NormalizedListingSchema` (existing):
```python
class NormalizedListingSchema(DealBrainModel):
    title: str  # Required
    price: Decimal | None  # Optional (for partial imports)
    currency: str = "USD"
    condition: str  # Condition enum value
    images: list[str] = []
    seller: str | None = None
    marketplace: str  # e.g., "amazon", "ebay", "generic"
    vendor_item_id: str | None = None
    description: str | None = None
    cpu_model: str | None = None
    ram_gb: int | None = None
    storage_gb: int | None = None
    quality: str  # "full" or "partial"
    extraction_metadata: dict[str, str]  # {"title": "extracted", "price": "extraction_failed"}
    missing_fields: list[str]  # ["price"] if not found
```

---

## API Changes

### New Adapter Settings (Non-Breaking)

File: `apps/api/dealbrain_api/settings.py`

```python
class PlaywrightAdapterConfig(BaseModel):
    enabled: bool = True
    timeout_s: int = 8
    max_retries: int = 2
    requests_per_minute: int = 60
    pool_size: int = 3
    headless: bool = True

class IngestionConfig(BaseModel):
    ebay: EbayAdapterConfig
    jsonld: JsonLdAdapterConfig  # New
    playwright: PlaywrightAdapterConfig  # New
```

### No Endpoint Changes

Existing URL ingestion endpoints remain unchanged:
- `POST /v1/url-imports/sessions` — Create session
- `GET /v1/url-imports/sessions/{id}` — Get status
- `GET /v1/url-imports/sessions/{id}/preview` — Get results
- `POST /v1/url-imports/sessions/{id}/commit` — Commit listings

Playwright adapter transparently participates in fallback chain (no client changes needed).

---

## Dependencies

### Part 1: Build Optimization
- No new dependencies (uses existing infrastructure)

### Part 2: URL Ingestion
**Already present in pyproject.toml:**
- `playwright` (in dev dependencies, will move to main dependencies for prod images only)
- `httpx`
- `beautifulsoup4` (if not present, add for additional parsing)
- `pydantic`

**Optional (Phase 4):**
- `playwright-stealth` — For anti-detection features

### Dependency Changes

Update `pyproject.toml`:
```toml
[tool.poetry.dependencies]
# ... existing ...
playwright = "^1.40.0"  # Move from dev-dependencies to main for prod builds

[tool.poetry.group.dev.dependencies]
# ... existing ...
# playwright stays here too for dev/testing
```

**Note:** Playwright will be installed in:
- Production Docker image (multi-stage build)
- Local dev environment (Poetry installs all deps)
- CI/CD production builds

Playwright will NOT be installed in development Docker image (multi-stage build).

---

## Testing Strategy

### Part 1: Build Optimization

| Test | Command | Expected Result |
|------|---------|-----------------|
| Dev build size | `docker build --target=development -t dev-api . && docker images` | Image size <600MB |
| Prod build size | `docker build --target=production -t prod-api . && docker images` | Image size ~1.71GB |
| Build time (dev) | Time `docker build --target=development` | <3 minutes without cache |
| Dev compose up | `docker compose up` (default profile) | API starts, health check passes |
| Prod compose up | `docker compose --profile production up` | API starts, health check passes |
| Playwright absent (dev) | `docker run --rm dev-api which playwright` | Command not found |
| Playwright present (prod) | `docker run --rm prod-api which playwright` | Path to playwright returned |

### Part 2: URL Ingestion

**Unit Tests:** `tests/adapters/test_playwright.py`

```python
def test_extract_from_mock_amazon_page():
    """Extract title, price from mocked Amazon page"""

def test_extract_without_price_partial_import():
    """Handle missing price gracefully"""

def test_timeout_raises_adapter_exception():
    """Timeout raises AdapterError.TIMEOUT"""

def test_browser_pool_acquire_release():
    """Browser pool manages instances correctly"""

def test_rate_limit_enforced():
    """Rate limiter blocks at 60 req/min"""
```

**Integration Tests:** `tests/adapters/test_playwright_integration.py` (real URLs)

```python
@pytest.mark.integration
async def test_extract_from_real_amazon_listing():
    """Extract real Amazon product"""
    # Requires internet connection, optional in CI

@pytest.mark.integration
async def test_playwright_fallback_chain():
    """Fallback chain tries Playwright after JSON-LD fails"""
```

**Adapter Router Tests:** `tests/adapters/test_router.py` (updated)

```python
async def test_fallback_chain_skips_disabled_adapters():
    """Disabled adapters skipped in chain"""

async def test_fallback_chain_stops_on_success():
    """Chain stops after first success"""

async def test_fast_fail_on_item_not_found():
    """404 stops chain immediately"""
```

---

## Deployment & Rollout

### Part 1: Docker Optimization

**Rollout:**
1. Merge multi-stage Dockerfile changes
2. Update CI/CD pipelines to use correct targets
3. All developers pull and benefit immediately (`make up` uses dev target)
4. No user-facing changes

**Rollback:** Switch back to old Dockerfile if issues; multi-stage is backward-compatible

### Part 2: URL Ingestion

**Rollout:**
1. Merge PlaywrightAdapter code (disabled by default)
2. Feature flag: `INGESTION_PLAYWRIGHT_ENABLED=true` to enable in staging
3. Monitor success rates, latency, browser pool health
4. Enable in production after validation (1-2 weeks)
5. Gradual rollout (10% → 50% → 100% of traffic)

**Rollback:** Disable adapter via `INGESTION_PLAYWRIGHT_ENABLED=false`

**Monitoring:**
- Adapter success rate by source
- Latency percentiles (p50, p95, p99)
- Browser pool memory usage
- Error rates by error type

---

## Success Metrics & Monitoring

### Part 1: Build Optimization

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Dev image size | 1.71GB | <600MB | `docker images` |
| Dev build time | 5-6 min | 2-3 min | `time docker build --target=development` |
| Build disk usage | 3.4GB (API+Worker) | 1.2GB (65% reduction) | Sum of image sizes |
| CI/CD overhead reduction | 4-6 min/build | 2-3 min/build | PR merge time before/after |

### Part 2: URL Ingestion

| Metric | Baseline | Target | Measurement | SLA |
|--------|----------|--------|-------------|-----|
| Overall extraction success | 60-70% | 85%+ | (URLs extracted / total) × 100 | Per week |
| Amazon extraction success | <20% | 70%+ | (Amazon URLs / Amazon total) × 100 | Per week |
| Playwright latency | N/A | <10s | p99 request time | Per request |
| Browser pool health | N/A | <3 instances | Active browser count | Continuous |
| Error rate (extraction) | N/A | <10% | (Failed extractions / total) × 100 | Per week |
| Adapter success by source | N/A | Tracked | Breakdown by eBay/Amazon/generic | Per week |

### Monitoring Implementation

**Logging:**
- Structured JSON logs for adapter operations
- Fields: adapter_name, url, status, duration_ms, error_type

**Metrics (OpenTelemetry):**
- Counters: extraction_attempts, extraction_success, extraction_failure
- Histograms: extraction_duration_ms, browser_pool_size
- Gauges: active_browsers, pending_requests

**Dashboards (Grafana):**
- Adapter success rates by source
- Latency percentiles
- Browser pool status
- Error breakdown by type

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Playwright browser crashes in prod | Lost extractions, failed imports | Medium | Auto-restart, pool health checks, monitoring |
| Anti-bot detection blocks Playwright | Success rate doesn't improve | Medium | Implement stealth mode (Phase 4), rotate User-Agents |
| Browser pool memory leak | Unbounded memory growth | Medium | Resource limits, recycle after N requests, monitoring |
| Playwright adds latency to extraction | Timeouts, poor UX | Low | 8s timeout, async operations, separate worker process |
| Docker build breaks existing workflows | Dev friction, CI/CD delays | Low | Multi-stage is backward-compatible, no breaking changes |
| Playwright library updates break code | Runtime errors | Low | Pin versions, regular dependency updates, test coverage |
| Rate limiting overly conservative | Amazon rate-limits us | Low | Start at 60 req/min, monitor, adjust based on feedback |
| Sites behind CloudFlare fail | Reduced success rate | Medium | Implement CF handling (optional Phase 4), fallback for 403 |

---

## Open Questions & Assumptions

### Assumptions

1. **Production deployment includes Playwright** — Production images will have Playwright installed (multi-stage build); development does not.
2. **Fallback chain acceptable** — Multiple adapter attempts per URL acceptable for latency (estimated <15s total).
3. **Partial imports acceptable** — Listings with missing prices acceptable for data-rich sites (marked as "partial").
4. **Browser pool size** — 2-3 concurrent browsers sufficient for current scale; can adjust based on load testing.
5. **Amazon does not block Playwright** — PlaywrightAdapter will succeed on Amazon >70% of time with current anti-detection techniques.
6. **No GDPR/legal issues** — Scraping test sites allowed; production use complies with terms of service.

### Open Questions

1. **Should Playwright be conditional on environment variable in production?**
   - Current: Always installed in production Docker
   - Alternative: Only install if `INGESTION_PLAYWRIGHT_ENABLED=true` at build time
   - Decision: Always install (simpler); disable via settings at runtime if needed

2. **Should browser pool be application-level singleton or per-request?**
   - Current design: Application-level singleton (reused across requests)
   - Alternative: Per-request (fresh browser each time, more overhead)
   - Decision: Application-level singleton (better performance, memory management)

3. **Should stealth mode be enabled by default or optional?**
   - Current: Design allows toggle via settings
   - Recommendation: Default to enabled (Phase 2B); can disable if sites don't require it
   - Decision: Included in Phase 4 (optional); enable based on monitoring

4. **How to handle sites requiring login or session state?**
   - Current: No login support planned
   - Future: May need to support cookie persistence or login flows
   - Decision: Out of scope for MVP; can add in future phase

---

## Timeline & Effort Estimation

| Phase | Duration | Priority | Start Date |
|-------|----------|----------|-----------|
| Phase 1: Docker Optimization | 2-3 hours | IMMEDIATE | Week 1 |
| Phase 2A: PlaywrightAdapter MVP | 1-2 days | HIGH | Week 1-2 |
| Phase 2B: Fallback Chain | ½ day | HIGH | Week 2 |
| Phase 3: Production Hardening | 1-2 days | MEDIUM | Week 2-3 |
| Phase 4: Anti-Detection (Optional) | 1 day | LOW | Week 3-4 |
| **Total (MVP)** | **4-5 days** | — | — |
| **Total (Full)** | **5-6 days** | — | — |

---

## Subagent Assignments

### Backend Architect
- Design PlaywrightAdapter architecture
- Review browser pool implementation
- Plan production hardening (Phase 3)
- Ensure compatibility with existing adapter system

### DevOps Engineer
- Implement multi-stage Dockerfile optimization
- Update Docker Compose and CI/CD pipelines
- Set up monitoring and observability
- Load testing and resource optimization

### QA Engineer
- Create comprehensive test plan
- Execute integration tests against real URLs
- Monitor success rates in staging
- Define rollout strategy and canary deployment

---

## Files to Create/Modify

### Files to Create

| File | Purpose | Phase |
|------|---------|-------|
| `apps/api/dealbrain_api/adapters/browser_pool.py` | Browser pool management | Phase 2A |
| `apps/api/dealbrain_api/adapters/playwright.py` | PlaywrightAdapter implementation | Phase 2A |
| `tests/adapters/test_playwright.py` | Unit + integration tests | Phase 2A |
| `tests/adapters/test_playwright_integration.py` | Real URL tests | Phase 2A |
| `docs/development/docker-optimization.md` | Build process documentation | Phase 1 |
| `docs/adapters/playwright-adapter.md` | Adapter usage guide | Phase 2B |

### Files to Modify

| File | Changes | Phase |
|------|---------|-------|
| `infra/api/Dockerfile` | Multi-stage build (development/production targets) | Phase 1 |
| `infra/worker/Dockerfile` | Multi-stage build (development/production targets) | Phase 1 |
| `docker-compose.yml` | Add profiles for dev/prod | Phase 1 |
| `apps/api/dealbrain_api/settings.py` | Add PlaywrightAdapterConfig | Phase 2A |
| `apps/api/dealbrain_api/adapters/router.py` | Add PlaywrightAdapter to registry, enhance logging | Phase 2B |
| `apps/api/dealbrain_api/main.py` | Add browser pool shutdown handler | Phase 3 |
| `pyproject.toml` | Ensure playwright in main dependencies | Phase 2A |
| `tests/adapters/test_router.py` | Add fallback chain tests | Phase 2B |

---

## Success Criteria Summary

### Part 1: Build Optimization (Phase 1)
- [ ] Development Docker image <600MB
- [ ] Development build time 2-3 minutes
- [ ] Production image unchanged (~1.71GB)
- [ ] All existing commands work without changes
- [ ] Documentation updated with new build process

### Part 2: URL Ingestion (Phases 2-4)
- [ ] PlaywrightAdapter extracts title, price, condition from 70%+ of Amazon URLs
- [ ] Overall extraction success rate improved to 85%+
- [ ] Fallback chain works correctly (tries adapters in priority order)
- [ ] Latency <10s per Playwright request
- [ ] Browser pool stable (no unbounded memory growth)
- [ ] Proper error handling and observability
- [ ] Production hardening complete (rate limiting, retry, cleanup)
- [ ] Adapter can be disabled via settings without breaking system

---

## References & Related Documentation

- **Playwright Optimization Analysis:** `/docs/architecture/playwright-optimization-analysis.md`
- **URL Ingestion Architecture:** `/docs/architecture/URL_INGESTION_ARCHITECTURE.md`
- **Existing Adapters:** `apps/api/dealbrain_api/adapters/ebay.py`, `apps/api/dealbrain_api/adapters/jsonld.py`
- **Adapter Base Class:** `apps/api/dealbrain_api/adapters/base.py`
- **Current Docker Setup:** `infra/api/Dockerfile`, `docker-compose.yml`
- **Playwright Documentation:** https://playwright.dev/python/
- **Playwright Stealth Mode:** https://github.com/easyinsf/playwright_stealth

---

## Appendix: Code Examples

### Example: Multi-Stage Dockerfile (Phase 1)

```dockerfile
FROM python:3.11-slim AS development

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Development stage: minimal dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000
CMD ["dealbrain-api"]

# ===================================

FROM python:3.11-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Production stage: all dependencies including Playwright
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libnss3 libxss1 libasound2 libatk-bridge2.0-0 \
        libgtk-3-0 libdrm2 libgbm1 libxkbcommon0 \
        libatspi2.0-0 libxcomposite1 libxdamage1 \
        libxfixes3 libxrandr2 libpango-1.0-0 libcairo2 \
        libcups2 libdbus-1-3 libexpat1 libfontconfig1 \
        libgcc1 libglib2.0-0 libnspr4 libuuid1 libx11-6 \
        libx11-xcb1 libxcb1 libxext6 libxrender1 \
        ca-certificates fonts-liberation wget \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY data ./data

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN playwright install chromium

EXPOSE 8000
CMD ["dealbrain-api"]
```

### Example: Browser Pool (Phase 2A)

```python
import logging
from typing import Optional
from playwright.async_api import Browser, async_playwright

logger = logging.getLogger(__name__)

class BrowserPool:
    """Manages reusable Chromium browser instances."""

    _instance: Optional["BrowserPool"] = None

    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.available_browsers: list[Browser] = []
        self.in_use: set[Browser] = set()
        self._playwright = None

    @classmethod
    def get_instance(cls, pool_size: int = 3) -> "BrowserPool":
        if cls._instance is None:
            cls._instance = BrowserPool(pool_size)
        return cls._instance

    async def acquire(self) -> Browser:
        """Acquire a browser from pool (create if needed)."""
        if self.available_browsers:
            browser = self.available_browsers.pop()
        else:
            # Launch new browser if under limit
            if len(self.in_use) < self.pool_size:
                browser = await self._launch_browser()
            else:
                # Wait for one to be available
                while not self.available_browsers:
                    await asyncio.sleep(0.1)
                browser = self.available_browsers.pop()

        self.in_use.add(browser)
        return browser

    async def release(self, browser: Browser) -> None:
        """Return browser to pool."""
        self.in_use.discard(browser)
        self.available_browsers.append(browser)

    async def _launch_browser(self) -> Browser:
        """Launch new Chromium instance."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        logger.info(f"Launched browser instance (total in pool: {len(self.in_use) + len(self.available_browsers)})")
        return browser

    async def close_all(self) -> None:
        """Close all browser instances."""
        for browser in self.available_browsers + list(self.in_use):
            try:
                await browser.close()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")

        if self._playwright:
            await self._playwright.stop()

        self.available_browsers = []
        self.in_use = set()
        logger.info("Closed all browser instances")
```

### Example: PlaywrightAdapter (Phase 2A)

```python
import logging
from playwright.async_api import Page
from dealbrain_api.adapters.base import BaseAdapter, AdapterError, AdapterException
from dealbrain_api.adapters.browser_pool import BrowserPool
from dealbrain_core.schemas.ingestion import NormalizedListingSchema

logger = logging.getLogger(__name__)

class PlaywrightAdapter(BaseAdapter):
    """Fallback adapter using Playwright for JavaScript-rendered content."""

    _adapter_name = "playwright"
    _adapter_domains = ["*"]  # Wildback: all domains
    _adapter_priority = 10    # Lowest priority (fallback)

    def __init__(self):
        super().__init__(
            name="playwright",
            supported_domains=["*"],
            priority=10,
            timeout_s=8,
            max_retries=2,
        )
        self.browser_pool = BrowserPool.get_instance()

    async def extract(self, url: str) -> NormalizedListingSchema:
        """Extract listing data using Playwright."""
        logger.info(f"[Playwright] Extracting from {url}")

        browser = None
        try:
            # Acquire browser from pool
            browser = await self.browser_pool.acquire()

            # Create page with anti-detection measures
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            )

            # Navigate with timeout
            try:
                await page.goto(url, wait_until="networkidle", timeout=self.timeout_s * 1000)
            except Exception as e:
                raise AdapterException(
                    AdapterError.TIMEOUT,
                    f"Failed to load page: {e}",
                    metadata={"url": url}
                )

            # Extract data
            data = await self._extract_data(page)

            # Map to schema
            normalized = await self._map_to_schema(data, url)

            await page.close()
            logger.info(f"[Playwright] Success extracting from {url}")
            return normalized

        except AdapterException:
            raise
        except Exception as e:
            raise AdapterException(
                AdapterError.PARSE_ERROR,
                str(e),
                metadata={"url": url}
            )
        finally:
            # Return browser to pool
            if browser:
                await self.browser_pool.release(browser)

    async def _extract_data(self, page: Page) -> dict:
        """Extract data from page using CSS selectors + JS."""
        title = await page.text_content("h1") or \
                await page.text_content("h2") or \
                await page.text_content(".title")

        price = await page.text_content(".price") or \
                await page.text_content("[data-price]")

        condition = await page.text_content(".condition")

        return {
            "title": title.strip() if title else None,
            "price": price.strip() if price else None,
            "condition": condition.strip() if condition else "used",
        }

    async def _map_to_schema(self, data: dict, url: str) -> NormalizedListingSchema:
        """Map extracted data to NormalizedListingSchema."""
        if not data.get("title"):
            raise AdapterException(
                AdapterError.INVALID_SCHEMA,
                "Failed to extract title",
                metadata={"url": url}
            )

        price = None
        if data.get("price"):
            try:
                price = Decimal(data["price"].replace("$", "").strip())
            except:
                pass

        return NormalizedListingSchema(
            title=data["title"],
            price=price,
            condition=data.get("condition", "used"),
            marketplace="generic",
            quality="partial" if price is None else "full",
            extraction_metadata={
                "title": "extracted",
                "price": "extracted" if price else "extraction_failed",
            },
            missing_fields=[] if price else ["price"],
        )
```

---

**Document Status:** Published
**Version:** 1.0
**Last Updated:** 2025-11-20
**Next Review:** 2025-12-04 (after Phase 1-2 completion)
