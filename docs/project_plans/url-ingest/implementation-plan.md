# URL Ingestion Implementation Plan

## Overview

This plan enables Deal Brain to import PC listings from URLs (eBay, Amazon, retailers) via official APIs and structured data extraction. The system extends the existing ImportSession pattern with URL-specific adapters, normalizes extracted data, deduplicates listings, and enriches components using existing catalogs. Single URLs complete in <10s via async job tracking; bulk imports of 100 URLs complete in <5 min with per-row status tracking. Timeline: 4-6 weeks. Total effort: ~290-340 hours across a team of 2-3 engineers.

---

## Phase 1: Foundation (Week 1) – ~55 hours

**Task ID-001: Extend Listing Model with URL Ingestion Fields** (6h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- Add `vendor_item_id` (str, nullable), `marketplace` (enum: ebay|amazon|other), `provenance` (ebay_api|jsonld|scraper), `last_seen_at` (datetime) columns to Listing model.
- Create unique constraint on `(vendor_item_id, marketplace)` for deduplication.

**Task ID-002: Create Alembic Migration for Listing Schema** (4h)
- File: `/mnt/containers/deal-brain/apps/api/alembic/versions/*_add_url_ingestion_fields.py`
- Generate migration to add new columns and constraint; set sensible defaults for existing rows.
- Include rollback logic.

**Task ID-003: Extend ImportSession for URL Jobs** (6h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- Add `source_type` (enum: excel|url_single|url_bulk), `url` (str, nullable), `adapter_config` (JSON) to ImportSession.
- Update existing imports to set `source_type='excel'`.

**Task ID-004: Create Ingestion Schemas (Pydantic)** (8h)
- File: `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/ingestion.py` (new)
- Define `NormalizedListingSchema` (title, price, currency, condition, images, seller, marketplace, vendor_item_id, cpu_model, ram_gb, storage_gb).
- Define `IngestionRequest`, `IngestionResponse` (job_id, status, listing_id, provenance, quality).
- Define `BulkIngestionRequest`, `BulkIngestionResponse` (bulk_job_id, total_urls, per_row_statuses).

**Task ID-005: Create Base Adapter Interface** (7h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/base.py` (new)
- Define abstract `BaseAdapter` class with `extract()` method → `NormalizedListingSchema`.
- Include rate-limit tracking, retry configuration, error enum (TIMEOUT, INVALID_SCHEMA, ADAPTER_DISABLED, etc.).
- Add adapter metadata (name, supported_domains, priority).

**Task ID-006: Create Ingestion Settings Configuration** (6h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/settings.py`
- Add `IngestionSettings` class with per-adapter config (enabled, timeout_s, retries, API keys).
- Set defaults: eBay enabled (timeout=6s, retries=2), JSON-LD enabled (timeout=8s, retries=1), Amazon disabled (P1).
- Add price_change_threshold_pct, raw_payload_ttl_days.

**Task ID-007: Create Raw Payload Storage Model** (8h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- Create `RawPayload` table (id, listing_id FK, adapter, source_type json|html, payload JSONB|text, created_at, ttl_days).
- Add migration to create table with index on (listing_id, adapter).

**Task ID-008: Create Ingestion Metrics Model** (10h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`
- Create `IngestionMetric` table (adapter, success_count, failure_count, p50_latency_ms, p95_latency_ms, field_completeness_pct, measured_at).
- Add Alembic migration; define aggregation queries for telemetry dashboard.

---

## Phase 2: Scraping Infrastructure (Weeks 2-3) – ~115 hours

**Task ID-009: Implement eBay Browse API Adapter** (35h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/ebay.py` (new)
- Parse eBay item URL, extract item ID; call Browse API (getItem endpoint).
- Map item specifics (CPU, RAM, storage, condition) to `NormalizedListingSchema`.
- Extract primary image, seller name, seller rating.
- Implement exponential backoff retry; respect rate limits (per eBay tier).
- Handle common errors (item not found, API key invalid, rate limited).

**Task ID-010: Implement JSON-LD / Microdata Adapter** (28h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/jsonld.py` (new)
- Use `extruct` library to extract JSON-LD Product schema from HTML.
- Fallback to microdata (Schema.org) if JSON-LD absent.
- Map offer.price, name, image, description, seller to schema.
- Parse CPU/RAM/storage from description regex patterns; normalize condition.
- Handle edge cases: nested offers, price as string/number, multiple images.

**Task ID-011: Create Adapter Router / Selector** (12h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/router.py` (new)
- Implement `AdapterRouter` class that selects adapter by domain priority (ebay → jsonld → scraper).
- Check adapter enabled status in settings; raise `AdapterDisabledError` if not.
- Return selected adapter instance with configured timeouts/retries.

**Task ID-012: Implement Deduplication Logic** (18h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py` (new, partial)
- Create `DeduplicationService` that generates dedup hash: `sha256(normalize(title) + seller + price)` for JSON-LD sources.
- Primary dedup key: `(marketplace, vendor_item_id)` for API sources (eBay, Amazon).
- Implement `find_existing_listing()` to check both keys.
- Return (exists_listing, is_exact_match, confidence_score).

**Task ID-013: Implement Normalizer / Component Enricher** (20h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py` (new, partial)
- Create `ListingNormalizer` that standardizes extracted data (currency to USD, condition enum, price parsing).
- Implement CPU/RAM/storage regex extraction from description.
- Call existing `ComponentCatalogService` to canonicalize CPU (e.g., "Intel Core i7-12700K" → CPU record).
- Enrich with CPU Mark, iGPU Mark from catalog; set `quality=full|partial` based on field coverage.

**Task ID-014: Implement Event Emission** (12h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py` (new, partial)
- Create `IngestionEventService` to emit events: `listing.created`, `price.changed`.
- `price.changed` emitted if `abs(new_price - old_price) >= threshold_abs OR (new_price - old_price) / old_price * 100 >= threshold_pct`.
- Use existing event infrastructure (Celery signal or webhook queue).

**Task ID-015: Create Ingestion Service Orchestrator** (10h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py` (new, completed)
- Implement `IngestionService.ingest_single_url()` → orchestrates adapter → normalize → dedupe → upsert.
- Implement `IngestionService.upsert_from_url()` integrating with `ListingsService` (create or update logic).
- Handle errors gracefully; store raw payload and error details.

---

## Phase 3: API & Integration (Week 4) – ~80 hours

**Task ID-016: Implement Celery Ingestion Task** (16h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/ingest.py` (new)
- Create `@celery_app.task` `ingest_url_task(job_id, url, adapter_config)` that calls `IngestionService.ingest_single_url()`.
- Update ImportSession status (queued → running → complete/partial/failed).
- Store result: listing_id, provenance, quality, errors.
- Implement retry logic (3 retries with exponential backoff) for transient errors.

**Task ID-017: Create Single URL Import Endpoint** (14h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/ingestion.py` (new)
- Implement `POST /api/v1/ingest/single` accepting `{url, priority: optional}`.
- Validate URL format (http/https, valid domain).
- Create ImportSession record; queue Celery task.
- Return 202 Async response: `{job_id, status: queued}` or 200 Fast-path if configured.
- Implement GET polling endpoint `/api/v1/ingest/{job_id}` returning full job status.

**Task ID-018: Create Bulk Import Endpoint** (18h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/ingestion.py` (continued)
- Implement `POST /api/v1/ingest/bulk` accepting `multipart/form-data` with CSV/JSON file.
- Parse CSV (header: url) or JSON `[{url: ...}]` into `import_session_items` rows.
- Validate: <1000 URLs per request, sanitize URLs.
- Create ImportSession with `source_type=url_bulk`; queue one Celery task per URL with priority chain.
- Return 202: `{bulk_job_id, total_urls}`.

**Task ID-019: Create Bulk Status Poll Endpoint** (12h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/ingestion.py` (continued)
- Implement `GET /api/v1/ingest/bulk/{bulk_job_id}` returning per-row statuses.
- Response: `{job_id, status, total_urls, complete, success, partial, failed, per_row_status: [{url, status, listing_id, error}]}`.
- Support query params: `?offset=0&limit=100` for pagination.

**Task ID-020: Integrate with ListingsService Upsert** (12h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/listings.py`
- Add `upsert_from_url(normalized_schema, dedupe_result)` method.
- If dedupe match found: update price, images, last_seen_at, last_modified_at; emit `price.changed` if threshold met.
- If new: create Listing with provenance, vendor_item_id, marketplace, raw_payload.
- Ensure backward compatibility with Excel import flow.

**Task ID-021: Implement Raw Payload Storage / Cleanup** (8h)
- File: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py`
- Create `RawPayloadService` to store adapter response (limit 512KB, truncate if larger).
- Implement TTL cleanup task: delete payloads older than 30 days (async Celery task, run nightly).

---

## Phase 4: Frontend & Testing (Weeks 5-6) – ~90 hours

**Task ID-022: Create Frontend Import Component** (20h)
- File: `/mnt/containers/deal-brain/apps/web/components/ingestion/single-url-form.tsx` (new)
- Form with URL input, priority dropdown; submit calls `POST /api/v1/ingest/single`.
- Display job status polling (useQuery with refetch interval).
- Show loading state, error messages, success result (listing ID, provenance badge).

**Task ID-023: Create Bulk Import UI Component** (18h)
- File: `/mnt/containers/deal-brain/apps/web/components/ingestion/bulk-import-dialog.tsx` (new)
- Modal with file upload (CSV/JSON or paste URLs textarea).
- Display job progress: total/complete/success/failed with progress bar.
- Per-row status table with expand details (error message).
- Download results as CSV option.

**Task ID-024: Add Provenance Badge to Listing Detail** (8h)
- File: `/mnt/containers/deal-brain/apps/web/components/listings/listing-detail.tsx`
- Display provenance badge (ebay_api / jsonld / scraper) near title.
- Add quality indicator (full / partial) with tooltip explaining missing fields.
- Show last_seen_at timestamp.

**Task ID-025: Create Admin Adapter Settings UI** (16h)
- File: `/mnt/containers/deal-brain/apps/web/components/admin/adapter-settings.tsx` (new)
- Toggle per-adapter enable/disable (eBay, JSON-LD, Amazon).
- Edit timeout_s, retries per adapter.
- Show per-adapter success rate, P50/P95 latency, field completeness (from IngestionMetric).

**Task ID-026: Unit Tests – Adapters & Normalization** (20h)
- File: `/mnt/containers/deal-brain/tests/test_ebay_adapter.py`, `test_jsonld_adapter.py`, `test_normalizer.py` (new)
- Mock eBay API responses (success, rate limit, item not found).
- Mock HTML with JSON-LD schema; test microdata fallback.
- Test dedup hash stability (whitespace, case sensitivity).
- Test CPU/RAM/storage regex extraction; edge cases (no CPU, RAM as string).
- Test price change threshold detection (≥$1 OR ≥2%).

**Task ID-027: Integration Tests – Job Lifecycle** (18h)
- File: `/mnt/containers/deal-brain/tests/test_ingestion_integration.py` (new)
- Test single URL flow: endpoint → Celery task → adapter → dedupe → upsert → check DB.
- Test bulk import: file upload → parse → queue 10 jobs → poll completion.
- Test re-import same URL: verify no duplicate, fields updated, last_seen_at refreshed.
- Test price change event emission (mock event queue).
- Test adapter disabled error handling.

**Task ID-028: E2E Tests – Happy Paths** (10h)
- File: `/mnt/containers/deal-brain/tests/test_ingestion_e2e.py` (new)
- Real or live-mocked eBay Browse API: import single eBay URL → verify <10s latency, all fields present.
- Bulk import 50 URLs → verify <3 min completion, 100% success rate, no duplicates.

---

## Technical Decisions

**TD-001: Adapter Priority Chain (API > JSON-LD > Scraper)**
Rationale: Official APIs (eBay Browse) return high-quality, consistent data. JSON-LD extraction works across 80% of retailers without API keys. Scraping (P1) reserved as fallback. Reduces infrastructure cost and improves reliability.

**TD-002: Deduplication Strategy (Marketplace + Vendor ID Primary)**
Rationale: eBay item IDs, ASINs are globally unique and immutable. For JSON-LD sources without IDs, hash (title + seller + price) provides ~95% accuracy. Hybrid approach balances accuracy with coverage.

**TD-003: Async Job Tracking (Celery + ImportSession)**
Rationale: Reuses existing ImportSession infrastructure (already used for Excel import). Celery workers scale independently. Clients poll job status; API returns 202 Async immediately, matching REST best practices for long-running tasks.

**TD-004: Raw Payload Storage (JSONB + TTL Cleanup)**
Rationale: Enables debugging (compare extracted vs. raw). JSONB indexing in Postgres allows querying. TTL cleanup (30 days) balances retention with storage costs. Truncate at 512KB prevents unbounded growth.

**TD-005: Feature Flags (IngestionSettings + Per-Adapter Toggle)**
Rationale: Decouples deployment from enablement. Admin can disable Amazon adapter (P1) without redeploying. Supports gradual rollout: start eBay+JSON-LD, add Amazon later.

**TD-006: Enrichment via Existing ComponentCatalogService**
Rationale: Avoids duplicate CPU/GPU canonicalization logic. Reuses CPU Mark, iGPU Mark lookups. Minimal scope creep; integrates seamlessly with existing valuation pipeline.

---

## Testing Strategy

**Unit Tests (40 hours allocated, tasks 026-027-028 partial)**
- Adapter domain routing (correct adapter selected per domain).
- eBay adapter: item specifics mapping, image extraction, error handling.
- JSON-LD parser: nested offers, missing fields, microdata fallback.
- Normalizer: currency conversion, condition enum mapping, CPU/RAM regex.
- Dedup hash: whitespace/case stability, collision resistance.

**Integration Tests (28 hours, task 027)**
- Single URL full flow: endpoint → Celery → adapter → dedupe → upsert (mock adapter, real DB).
- Bulk import: 10-URL CSV → per-row job tracking → status polling.
- Re-import scenario: same URL twice → verify update, no duplicate, event emission.
- Error scenarios: adapter timeout, disabled adapter, invalid JSON-LD, malformed price.

**E2E Tests (10 hours, task 028)**
- Live or mocked eBay Browse API: real(ish) item import <10s p50.
- Bulk 50 URLs, verify <3 min, 100% success, no duplicates in DB.

---

## Rollout Plan

**Phase 0 (Internal Testing, Days 1-5)**
- Feature flag `ingestion.enabled = False` in production. Deploy code behind flag.
- Internal smoke test: single eBay URL, bulk 10 CSV URLs, re-import dedup test.
- Monitor: adapter latency, error rate, payload sizes.

**Phase 1 (Opt-In Beta, Days 6-14)**
- Enable flag for 10% of users (by user_id % 10 == 0).
- Monitor: success rate, P95 latency, errors. Refine adapter config if needed.

**Phase 2 (Gradual Rollout, Days 15-21)**
- Increase to 50% of users. Disable Amazon adapter (P1).
- Monitor: no DB bloat, event emission working, no duplicate issues.

**Phase 3 (Full Availability, Days 22+)**
- Enable flag for 100% of users. Document feature in help docs.
- Keep monitoring: maintain SLA (99.5% API availability, <3% error rate excl. bad URLs).

---

## Success Metrics

- Single eBay URL import: <10s p50, <20s p95.
- Single JSON-LD import: <8s p50, <15s p95.
- Bulk 100 URLs: <5 min (120 URLs/min throughput at 4 workers).
- Dedup accuracy: 0 unexpected duplicates in production (audited weekly).
- Event emission: 100% of price changes ≥$1 or ≥2% emitted.
- Adapter availability: ≥99.5% (excluding valid API downtime).
- Raw payload retention: <5GB cumulative (30-day TTL).
- Error rate: <3% (excluding malformed URLs, disabled adapters).

---

## Dependencies & Library Additions

**New Python Libraries (to add to pyproject.toml)**
- `extruct >= 0.16` – JSON-LD, microdata extraction
- `url-normalize >= 1.4` – URL normalization for dedup
- `httpx-retry >= 0.3` – HTTP retry middleware (optional; can use httpx built-in retry)

**Existing Libraries Used**
- `httpx` (already in deps) – HTTP client for adapters
- `sqlalchemy >= 2.0` (already in deps) – ORM, JSONB support
- `pydantic >= 2.0` (already in deps) – Schemas
- `celery` (already in deps) – Async task queue

---

## Estimated Effort Breakdown

| Phase | Tasks | Hours | FTE Weeks |
|-------|-------|-------|-----------|
| P1: Foundation | 001-008 | 55 | 1.4 |
| P2: Infrastructure | 009-015 | 115 | 2.9 |
| P3: API | 016-021 | 80 | 2.0 |
| P4: Frontend | 022-028 | 90 | 2.3 |
| **Total** | 28 | **340** | **8.6 FTE weeks** |

**With 2-3 engineers, 4-6 week calendar timeline (accounting for reviews, dependencies, buffer).**
