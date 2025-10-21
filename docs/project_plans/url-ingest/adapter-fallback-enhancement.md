# Adapter Fallback Enhancement Plan

**Status**: Enhancement Required
**Priority**: High
**Effort**: 14-16 hours (Phase 1+2)
**Created**: 2025-10-21

---

## Executive Summary

The URL ingestion system lacks automatic fallback between adapters. When the eBay adapter fails due to missing API credentials, the system does not attempt the JSON-LD adapter as a fallback, even though it could successfully extract data from eBay pages. This results in failed imports that could succeed with the existing infrastructure.

**Impact**: Users cannot ingest eBay URLs without an API key, blocking a key use case.

**Solution**: Implement a try-catch fallback loop in `AdapterRouter.extract()` to automatically try adapters in priority order until one succeeds.

---

## Problem Statement

### Current Behavior

When a user attempts to import an eBay URL without `EBAY_API_KEY` configured:

```
1. AdapterRouter selects EbayAdapter (priority 1)
2. EbayAdapter.__init__() checks for API key
3. If missing, raises ValueError immediately
4. Entire ingestion fails with error
5. JSON-LD adapter is never tried (even though it supports eBay)
```

### Expected Behavior (Per PRD)

```
1. Try EbayAdapter → fails (no API key)
2. Fall back to JsonLdAdapter → extracts JSON-LD from HTML
3. Fall back to ScraperAdapter → parses HTML with CSS selectors
4. Return result from first successful adapter
```

### Gap Analysis

| Component | PRD Requirement | Current Status | Gap |
|-----------|-----------------|----------------|-----|
| API→JSON-LD fallback | Automatic | ❌ Not implemented | **CRITICAL** |
| API→Scraper fallback | Automatic | ❌ No scraper exists | **CRITICAL** |
| eBay w/o API key | Works via JSON-LD | ❌ Fails immediately | **CRITICAL** |
| Error handling | Graceful degradation | ❌ All-or-nothing | **CRITICAL** |

---

## Root Cause Analysis

### Issue 1: No Fallback Loop in Router

**File**: `apps/api/dealbrain_api/adapters/router.py` (lines 157-174)

```python
async def extract(self, url: str) -> NormalizedListingSchema:
    """Convenience method: select adapter and extract in one call."""
    adapter = self.select_adapter(url)  # Selects ONE adapter
    return await adapter.extract(url)    # If this fails, entire op fails
    # ⚠️ NO TRY-CATCH to attempt next adapter
```

**Problem**: Only tries the highest-priority adapter. If it fails, no fallback occurs.

### Issue 2: EbayAdapter Fails at Initialization

**File**: `apps/api/dealbrain_api/adapters/ebay.py` (lines 104-107)

```python
def __init__(self) -> None:
    """Initialize eBay adapter."""
    self.api_key = settings.ingestion.ebay.api_key

    if not self.api_key:
        raise ValueError(
            "eBay Browse API key not configured in settings.ingestion.ebay.api_key"
        )  # ⚠️ Raises during initialization, before extract()
```

**Problem**: Fails during `__init__()`, not during `extract()`. Router can't catch and retry.

### Issue 3: No Scraper Adapter

**File**: `apps/api/dealbrain_api/adapters/router.py` (lines 16-20)

```python
AVAILABLE_ADAPTERS: list[type[BaseAdapter]] = [
    EbayAdapter,
    JsonLdAdapter,
    # GenericScraperAdapter,  # ← Not implemented
]
```

**Problem**: No HTML scraper as ultimate fallback per PRD requirement.

---

## Proposed Solution

### Phase 1: Implement Fallback Loop ⭐

**Goal**: Try adapters in priority order until one succeeds.

**Changes to** `apps/api/dealbrain_api/adapters/router.py`:

```python
async def extract(self, url: str) -> NormalizedListingSchema:
    """Extract data using fallback chain."""
    domain = self._extract_domain(url)
    matching = self._find_matching_adapters(url, domain)
    matching.sort(key=lambda a: self._get_adapter_priority(a))

    last_error = None
    attempted_adapters = []

    for adapter_class in matching:
        adapter_name = adapter_class.__name__

        try:
            # Try to initialize adapter
            adapter = adapter_class()
            attempted_adapters.append(adapter_name)

            logger.info(f"Trying adapter {adapter_name} for {url}")

            # Try to extract
            result = await adapter.extract(url)

            logger.info(f"✓ Success with {adapter_name}")
            return result

        except AdapterError as e:
            # Adapter-specific error (timeout, parse error, etc.)
            last_error = e
            logger.warning(f"✗ {adapter_name} failed: {e.message}")

            # Don't retry if item not found or disabled
            if e.error_code in {AdapterError.ITEM_NOT_FOUND, AdapterError.ADAPTER_DISABLED}:
                raise

            # Try next adapter
            continue

        except ValueError as e:
            # Initialization error (missing API key, etc.)
            last_error = AdapterError(
                error_code=AdapterError.CONFIGURATION_ERROR,
                message=str(e),
                adapter_name=adapter_name,
            )
            logger.warning(f"✗ {adapter_name} initialization failed: {e}")
            continue

    # All adapters failed
    raise AdapterError(
        error_code=AdapterError.ALL_ADAPTERS_FAILED,
        message=f"All {len(attempted_adapters)} adapters failed for {url}",
        adapter_name="router",
        details={"attempted": attempted_adapters, "last_error": str(last_error)},
    )
```

**Benefits**:
- ✅ Automatically tries next adapter if primary fails
- ✅ Logs each attempt for debugging
- ✅ Catches both initialization and extraction errors
- ✅ Fast-fails for non-retryable errors (404, disabled)

---

### Phase 2: Fix eBay Adapter Initialization ⭐

**Goal**: Allow EbayAdapter to initialize even without API key, fail gracefully during extract().

**Changes to** `apps/api/dealbrain_api/adapters/ebay.py`:

```python
def __init__(self) -> None:
    """Initialize eBay adapter."""
    settings = get_settings()
    self.api_key = settings.ingestion.ebay.api_key or None
    self.timeout_s = settings.ingestion.ebay.timeout_s
    # ⚠️ Don't raise here - allow initialization to succeed

async def extract(self, url: str) -> NormalizedListingSchema:
    """Extract listing data from eBay URL."""
    # Check API key at extraction time
    if not self.api_key:
        raise AdapterError(
            error_code=AdapterError.CONFIGURATION_ERROR,
            message="eBay Browse API key not configured",
            adapter_name=self.name,
        )

    # ... rest of extraction logic
```

**Benefits**:
- ✅ Router can catch AdapterError and try next adapter
- ✅ Initialization succeeds (allows router to construct adapter)
- ✅ Fails at correct point (extract time) with proper error type

---

### Phase 3: Implement Scraper Adapter (Future)

**File**: `apps/api/dealbrain_api/adapters/scraper.py` (NEW)

**Goal**: HTML scraper as ultimate fallback for sites without APIs or JSON-LD.

```python
class GenericScraperAdapter(BaseAdapter):
    """Fallback adapter using BeautifulSoup for HTML parsing."""

    _adapter_name = "scraper"
    _adapter_domains = ["*"]  # Wildcard
    _adapter_priority = 10     # Lowest priority

    async def extract(self, url: str) -> NormalizedListingSchema:
        """Extract data using CSS selectors."""
        html = await self._fetch_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        # Common patterns for e-commerce sites
        title = soup.select_one('h1.product-title, h1[itemprop="name"]')
        price = soup.select_one('.price, [itemprop="price"]')
        # ... etc
```

**Effort**: 20-25 hours (includes CSS selector patterns for common sites)

---

## Implementation Checklist

### Phase 1: Fallback Loop (8-10 hours)

- [ ] Update `AdapterRouter.extract()` with try-catch loop
- [ ] Add logging for each adapter attempt
- [ ] Add new error code `ALL_ADAPTERS_FAILED` to `AdapterError`
- [ ] Update `select_adapter()` to return list instead of single adapter
- [ ] Add fallback metrics tracking (attempts, successes)
- [ ] Unit tests for fallback behavior (5 test scenarios)
- [ ] Integration test: eBay URL → EbayAdapter fails → JsonLdAdapter succeeds

### Phase 2: eBay Adapter Fix (4-6 hours)

- [ ] Move API key validation from `__init__()` to `extract()`
- [ ] Replace `ValueError` with `AdapterError(CONFIGURATION_ERROR)`
- [ ] Update eBay adapter tests to handle missing API key
- [ ] Add test: EbayAdapter with no API key → raises AdapterError
- [ ] Add test: Router falls back when eBay adapter raises config error

### Phase 3: Scraper Adapter (Future, 20-25 hours)

- [ ] Create `apps/api/dealbrain_api/adapters/scraper.py`
- [ ] Implement BeautifulSoup-based extraction
- [ ] Define CSS selector patterns for common sites
- [ ] Add scraper to `AVAILABLE_ADAPTERS` registry
- [ ] Comprehensive scraper tests with mocked HTML

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_adapter_router.py`

```python
async def test_fallback_when_primary_adapter_fails():
    """Test router tries JSON-LD when eBay adapter fails."""
    # Mock eBay adapter to fail
    # Expect JSON-LD adapter to be tried next
    pass

async def test_fallback_logs_each_attempt():
    """Test that each adapter attempt is logged."""
    # Capture logs
    # Verify "Trying adapter EbayAdapter" and "Trying adapter JsonLdAdapter" appear
    pass

async def test_fast_fail_for_404():
    """Test that 404 errors don't trigger fallback."""
    # Mock adapter to return ITEM_NOT_FOUND
    # Expect no fallback attempt
    pass
```

### Integration Tests

**File**: `tests/test_ingestion_fallback.py` (NEW)

```python
async def test_ebay_url_without_api_key_uses_jsonld():
    """End-to-end test: eBay URL without API key succeeds via JSON-LD."""
    # Unset EBAY_API_KEY
    # Ingest eBay URL
    # Expect success with provenance="jsonld"
    pass
```

---

## Success Criteria

1. ✅ eBay URL ingestion works without API key (via JSON-LD fallback)
2. ✅ All adapter attempts are logged with outcome
3. ✅ Existing tests still pass (no regressions)
4. ✅ New tests added for fallback scenarios (minimum 7 tests)
5. ✅ Fallback attempts tracked in `IngestionMetric` table
6. ✅ Documentation updated (adapter README, context doc)

---

## Rollout Plan

### Step 1: Feature Flag

Add to `IngestionSettings`:

```python
fallback_enabled: bool = True  # Master switch for fallback behavior
fallback_log_level: str = "INFO"  # DEBUG for verbose logging
```

### Step 2: Gradual Rollout

1. Deploy with `fallback_enabled=False` (existing behavior)
2. Enable for internal testing
3. Monitor fallback rates and quality metrics
4. Enable for all users if metrics look good

### Step 3: Monitoring

Track in `IngestionMetric`:
- `fallback_attempts` (how often fallback was triggered)
- `fallback_successes` (how often fallback succeeded)
- `primary_adapter_failures` (why primary adapter failed)

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSON-LD data quality lower than API | Medium | Track quality metrics, show provenance badge in UI |
| Performance degradation (trying multiple adapters) | Low | Fail fast for non-retryable errors, add timeout |
| Increased complexity in error handling | Low | Comprehensive tests, clear logging |
| Breaking changes to existing behavior | High | Feature flag, gradual rollout, extensive testing |

---

## Timeline Estimate

| Phase | Tasks | Effort |
|-------|-------|--------|
| Phase 1 | Fallback loop + tests | 8-10 hours |
| Phase 2 | eBay adapter fix + tests | 4-6 hours |
| **Total (Phase 1+2)** | **Ready for production** | **12-16 hours** |
| Phase 3 (Future) | Scraper adapter | 20-25 hours |

---

## Related Documents

- **PRD**: `/docs/project_plans/url-ingest/prd-url-ingest-dealbrain.md`
- **Context**: `/docs/project_plans/url-ingest/context/url-ingest-context.md`
- **Analysis**: Codebase exploration completed 2025-10-21
- **Adapter README**: `/apps/api/dealbrain_api/adapters/README.md`

---

## Approval & Sign-Off

- [ ] **Technical Review**: Lead Architect
- [ ] **Implementation**: Backend Engineer
- [ ] **Testing**: QA Engineer
- [ ] **Deployment**: DevOps

---

## Next Steps

1. Create implementation branch: `feat/adapter-fallback-chain`
2. Implement Phase 1 (fallback loop)
3. Implement Phase 2 (eBay adapter fix)
4. Run full test suite
5. Update documentation
6. Create PR for review
7. Deploy with feature flag
8. Monitor metrics
9. Enable for all users
