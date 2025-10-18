# Phase 2 Progress Tracker

## Document Information

- **Plan Reference**: [docs/project_plans/url-ingest/implementation-plan.md](/docs/project_plans/url-ingest/implementation-plan.md)
- **Started Date**: 2025-10-18
- **Status**: In Progress
- **Phase Duration**: Weeks 2-3 (Scraping Infrastructure)
- **Total Effort**: ~115 hours

---

## Success Criteria

- [ ] All 7 infrastructure tasks completed (ID-009 through ID-015)
- [ ] eBay adapter working with real API responses (mocked in tests)
- [ ] JSON-LD adapter extracting from HTML pages
- [ ] Adapter router selecting correct adapter by domain
- [ ] Deduplication preventing duplicates
- [ ] Normalizer standardizing all data formats
- [ ] Event emission working for listing.created, price.changed
- [ ] Orchestrator service coordinating full workflow
- [ ] All tests passing with >80% coverage
- [ ] No regressions in existing functionality

---

## Development Checklist

### Task ID-009: Implement eBay Browse API Adapter (35h)

- **File**: `/apps/api/dealbrain_api/adapters/ebay.py` (new)
- **Scope**: eBay Browse API adapter implementation
- **Status**: Not Started

Tasks:
- [ ] Parse eBay item URL and extract item ID
- [ ] Implement eBay Browse API client (getItem endpoint)
- [ ] Map item specifics (CPU, RAM, storage, condition) to NormalizedListingSchema
- [ ] Extract primary image, seller name, seller rating
- [ ] Implement exponential backoff retry logic
- [ ] Respect rate limits (per eBay tier)
- [ ] Handle common errors (item not found, API key invalid, rate limited)
- [ ] Unit tests with mocked API responses
- [ ] Integration tests with real/live-mocked API

---

### Task ID-010: Implement JSON-LD / Microdata Adapter (28h)

- **File**: `/apps/api/dealbrain_api/adapters/jsonld.py` (new)
- **Scope**: Generic JSON-LD/Microdata extraction adapter
- **Status**: Not Started

Tasks:
- [ ] Use extruct library to extract JSON-LD Product schema from HTML
- [ ] Fallback to microdata (Schema.org) if JSON-LD absent
- [ ] Map offer.price, name, image, description, seller to NormalizedListingSchema
- [ ] Parse CPU/RAM/storage from description using regex patterns
- [ ] Normalize condition enum
- [ ] Handle edge cases: nested offers, price as string/number, multiple images
- [ ] Unit tests with sample HTML fixtures
- [ ] Integration tests with real retailer pages

---

### Task ID-011: Create Adapter Router / Selector (12h)

- **File**: `/apps/api/dealbrain_api/adapters/router.py` (new)
- **Scope**: Adapter selection and routing logic
- **Status**: Not Started

Tasks:
- [ ] Implement AdapterRouter class
- [ ] Select adapter by domain priority (ebay → jsonld → scraper)
- [ ] Check adapter enabled status in settings
- [ ] Raise AdapterDisabledError if adapter not enabled
- [ ] Return configured adapter instance with timeout/retries
- [ ] Unit tests for router logic
- [ ] Integration tests with multiple adapters

---

### Task ID-012: Implement Deduplication Logic (18h)

- **File**: `/apps/api/dealbrain_api/services/ingestion.py` (new, partial)
- **Scope**: Deduplication service for preventing duplicate listings
- **Status**: Not Started

Tasks:
- [ ] Create DeduplicationService class
- [ ] Generate dedup hash: sha256(normalize(title) + seller + price) for JSON-LD
- [ ] Primary dedup key: (marketplace, vendor_item_id) for API sources
- [ ] Implement find_existing_listing() to check both keys
- [ ] Return (exists_listing, is_exact_match, confidence_score)
- [ ] Unit tests for hash generation stability
- [ ] Integration tests with database

---

### Task ID-013: Implement Normalizer / Component Enricher (20h)

- **File**: `/apps/api/dealbrain_api/services/ingestion.py` (new, partial)
- **Scope**: Data normalization and component enrichment
- **Status**: Not Started

Tasks:
- [ ] Create ListingNormalizer class
- [ ] Standardize extracted data (currency to USD, condition enum, price parsing)
- [ ] Implement CPU/RAM/storage regex extraction from description
- [ ] Integrate with existing ComponentCatalogService for CPU canonicalization
- [ ] Enrich with CPU Mark, iGPU Mark from catalog
- [ ] Set quality=full|partial based on field coverage
- [ ] Unit tests for normalization logic
- [ ] Integration tests with component catalog

---

### Task ID-014: Implement Event Emission (12h)

- **File**: `/apps/api/dealbrain_api/services/ingestion.py` (new, partial)
- **Scope**: Event emission for listing lifecycle events
- **Status**: Not Started

Tasks:
- [ ] Create IngestionEventService class
- [ ] Emit listing.created event on new listing
- [ ] Emit price.changed event on price update
- [ ] Calculate price change: abs(new - old) >= threshold_abs OR percentage >= threshold_pct
- [ ] Integrate with existing event infrastructure (Celery signal or webhook queue)
- [ ] Unit tests for event emission logic
- [ ] Integration tests with event queue

---

### Task ID-015: Create Ingestion Service Orchestrator (10h)

- **File**: `/apps/api/dealbrain_api/services/ingestion.py` (new, completed)
- **Scope**: Main orchestration service coordinating full workflow
- **Status**: Not Started

Tasks:
- [ ] Implement IngestionService.ingest_single_url() orchestration method
- [ ] Orchestrate: adapter → normalize → dedupe → upsert workflow
- [ ] Implement IngestionService.upsert_from_url() integrating with ListingsService
- [ ] Handle errors gracefully throughout workflow
- [ ] Store raw payload and error details
- [ ] Unit tests for orchestration flow
- [ ] Integration tests for full workflow

---

## Work Log

### 2025-10-18

**Phase 2 Started**

- Created Phase 2 progress tracker
- Added required dependencies to pyproject.toml (extruct, url-normalize)
- Ready to begin adapter implementations

---

## Decisions Log

*(Technical decisions and architectural choices will be logged here)*

---

## Files to Create/Modify in Phase 2

### NEW Files (to create)

- [ ] `/apps/api/dealbrain_api/adapters/ebay.py` - eBay Browse API adapter
- [ ] `/apps/api/dealbrain_api/adapters/jsonld.py` - JSON-LD/Microdata adapter
- [ ] `/apps/api/dealbrain_api/adapters/router.py` - Adapter router/selector
- [ ] `/apps/api/dealbrain_api/services/ingestion.py` - Ingestion services (dedup, normalizer, events, orchestrator)
- [ ] `/tests/test_ebay_adapter.py` - eBay adapter unit tests
- [ ] `/tests/test_jsonld_adapter.py` - JSON-LD adapter unit tests
- [ ] `/tests/test_adapter_router.py` - Router unit tests
- [ ] `/tests/test_deduplication.py` - Deduplication unit tests
- [ ] `/tests/test_normalizer.py` - Normalizer unit tests
- [ ] `/tests/test_ingestion_service.py` - Ingestion service unit tests

### MODIFIED Files

- [x] `/pyproject.toml` - Added extruct, url-normalize dependencies
- [ ] `/apps/api/dealbrain_api/services/listings.py` - Integrate with ingestion workflow (if needed)

---

## Next Phase Reference

For Phase 3 (API & Integration), see: [docs/project_plans/url-ingest/implementation-plan.md#phase-3-api--integration-week-4--80-hours](/docs/project_plans/url-ingest/implementation-plan.md#phase-3-api--integration-week-4--80-hours)

Phase 3 begins with Task ID-016: Implement Celery Ingestion Task (16h)
