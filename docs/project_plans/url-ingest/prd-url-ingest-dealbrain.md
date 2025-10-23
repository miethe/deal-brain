# URL Ingestion for Deal Brain – PRD

## Executive Summary

Enable Deal Brain to import PC listings directly from URLs (eBay, Amazon, retailers). The system adapts the existing ImportSession pattern to handle single/bulk URL imports, leveraging API-first adapters (eBay Browse API, JSON-LD), with optional site-specific scraping. Normalized listings are deduplicated and merged into the existing Listing schema; enrichment (CPU/GPU canonicalization) reuses existing catalogs.

---

## Goals

- **G1**: Single-click URL import (<10s median for API adapters).
- **G2**: Bulk import from CSV/JSON files with resilient job tracking.
- **G3**: Prefer official APIs (eBay Browse API first), fall back to JSON-LD/microdata, then scraping.
- **G4**: Deduplicate identical listings; update `last_seen_at` on re-import.
- **G5**: Show provenance (adapter source) and data quality in UI.
- **G6**: Emit `listing.created` and `price.changed` events for external subscribers (watchlists, notifications).

## Non-Goals

- Full price history (P2+; capture current/baseline only).
- Search/browse within external marketplaces.
- Seller-side interactions (offers, messaging).

---

## User Stories

| ID  | Story |
|-----|-------|
| US1 | Buyer pastes a product URL, clicks "Import" → listing appears in dashboard with auto-enriched specs. |
| US2 | Buyer uploads CSV (`url` column) or JSON → job tracker shows per-row status (success/partial/fail). |
| US3 | Analyst views listing detail → "Provenance" badge shows "eBay Browse API" / "JSON-LD" / source URL. |
| US4 | Importing same URL twice updates existing listing, no duplicate created. |
| US5 | Admin toggles eBay/Amazon adapters on/off; sets per-domain rate limits in settings. |
| US6 | Price drops $5+ → `price.changed` event emitted; subscribers notified. |

---

## Architecture Overview

### Adapter Pattern

Reuse existing ImportSession infrastructure; extend with URL-specific adapters:

```
POST /api/v1/ingest/url  (or extend /api/v1/imports)
  ↓
IngestionService (orchestrates adapters)
  ├─ AdapterRouter (selects by domain: api > jsonld > scraper)
  ├─ eBayAdapter (Browse API)
  ├─ GenericAdapter (JSON-LD/microdata extractor)
  └─ ScraperAdapter (skeleton; P1+)
  ↓
NormalizedListingSchema (Pydantic)
  ↓
ListingService.upsert_from_url()
  ├─ Deduplicate by (marketplace, vendor_item_id)
  ├─ Enrich CPU/GPU via existing catalogs
  ├─ Store raw_payload for debugging
  └─ Emit events
  ↓
Listing (updated/created in DB)
```

### Job Management

Extend ImportSession for URL jobs (parallel to Excel import):

- **New fields on ImportSession**: `source_type` (excel | url), `url` (nullable), `adapter_config` (JSON).
- **Bulk tracking**: store rows in `import_session_items` (already exists).
- **Worker**: Celery task picks jobs, invokes adapter, updates row status.

### Deduplication

Primary key: `(marketplace, vendor_item_id)` (e.g., eBay item ID).
Fallback: `sha256(normalize(title) + seller_name + price)` for sources without IDs.
Upsert logic: if exists, update `price`, `images`, `last_seen_at`, emit `price.changed` if delta ≥ $1 or 2%.

---

## API Contracts

### POST /api/v1/ingest/single

Single URL import (async).

**Request:**
```json
{
  "url": "https://www.ebay.com/itm/123456789",
  "priority": "normal"  // optional: normal | high
}
```

**Response 202 (Async):**
```json
{
  "job_id": "ing_01J8...",
  "status": "queued"
}
```

**Response 200 (Fast-path, if configured):**
```json
{
  "listing_id": "lst_01J8...",
  "status": "complete",
  "provenance": "ebay_api",
  "quality": "full"  // full | partial
}
```

### POST /api/v1/ingest/bulk

Bulk import from file or text.

**Request:** `multipart/form-data`
```
file: <CSV or JSON>  // CSV: header "url"; JSON: [{"url": "..."}]
```

**Response 202:**
```json
{
  "bulk_job_id": "bkg_01J8...",
  "total_urls": 127
}
```

### GET /api/v1/ingest/{job_id}

Poll job status.

**Response:**
```json
{
  "job_id": "ing_01J8...",
  "status": "complete | partial | failed | running | queued",
  "listing_id": "lst_01J8...",
  "provenance": "ebay_api",
  "quality": "full | partial",
  "errors": [{"code": "TIMEOUT", "message": "..."}]
}
```

### GET /api/v1/ingest/bulk/{bulk_job_id}

Poll bulk job; returns array of per-row statuses.

---

## Data Model Changes

### New Tables/Columns

| Change | Purpose |
|--------|---------|
| `ImportSession.source_type` | Enum: `excel | url_single | url_bulk` |
| `ImportSession.url` | Nullable; set for single URL imports |
| `ImportSession.adapter_config` | JSON; adapter priorities, timeouts, rate limits |
| `Listing.vendor_item_id` | Marketplace-specific ID (eBay item ID, ASIN, etc.) |
| `Listing.last_seen_at` | Timestamp; updated on re-import |
| `raw_payload` table (new) | `id, listing_id, adapter, source_type (json | html), payload (jsonb | text), created_at, ttl_days` |
| `ingestion_metrics` (new) | Track adapter latency, success rate, field completeness (for telemetry). |

### Schema Changes to Listing

```python
# Add to Listing model
vendor_item_id: Mapped[str | None] = mapped_column(String(255))  # eBay ID, ASIN, etc.
marketplace: Mapped[str] = mapped_column(String(64), default="other")  # ebay | amazon | other
provenance: Mapped[str | None] = mapped_column(String(64))  # ebay_api | jsonld | scraper
last_seen_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

# Unique constraint
__table_args__ = (
    UniqueConstraint("vendor_item_id", "marketplace", name="uq_listing_vendor_id"),
)
```

---

## Acceptance Criteria

1. **AC1**: Single eBay URL import completes with title, price, condition, image, seller, provenance=ebay_api.
2. **AC2**: JSON-LD adapter extracts from any retailer page with Product schema.
3. **AC3**: Re-importing same URL updates existing listing (no duplicate); `last_seen_at` refreshed, `last_modified_at` set.
4. **AC4**: Bulk import of 100 URLs via CSV completes with per-row statuses in <5 min.
5. **AC5**: Price change ≥ $1 or ≥2% emits `price.changed` event with previous/current values.
6. **AC6**: Missing required fields (e.g., no currency) set `quality=partial`; UI indicates incomplete.
7. **AC7**: Deduplication by `(marketplace, vendor_item_id)` prevents duplicates across re-imports.
8. **AC8**: Admin can disable adapter (e.g., `amazon.enabled=false`); requests return `ADAPTER_DISABLED` error.
9. **AC9**: Telemetry dashboard shows per-adapter success rate, P50/P95 latency, field completeness.
10. **AC10**: Raw payloads stored; retained for 30 days; truncated at 512KB; accessible for debugging.

---

## Dependencies

### Python (Poetry)

```toml
# Existing; already in use
httpx = "^0.24"  # HTTP client (already installed)
sqlalchemy = "^2.0"  # ORM (already installed)
pydantic = "^2.0"  # Schemas (already installed)

# New additions
extruct = "^0.16"  # JSON-LD / microdata extraction
url-normalize = "^1.4"  # URL normalization for dedup hashing
httpx-retry = "^0.3"  # Retry logic for HTTP
```

### Celery Tasks (existing infrastructure)

Use existing Celery worker; add new task:
```python
@app.task
def ingest_url_task(job_id: str, url: str, adapter_config: dict) -> dict:
    """Async ingestion worker task."""
    pass
```

---

## Implementation Phases

| Phase | Scope |
|-------|-------|
| **P0** | eBay Browse API adapter, JSON-LD adapter, dedupe, single/bulk import, events, telemetry. Feature flag `ingestion.enabled`. |
| **P1** | Amazon PA-API adapter (gated by credentials), per-domain rate limits, admin settings UI, site-specific scraper skeleton. |
| **P2** | Best Buy/Walmart/Newegg adapters, price history, browser extension, anti-bot refinements. |

---

## Key Files to Create/Modify

### New Files
- `apps/api/dealbrain_api/adapters/base.py` – Base adapter interface.
- `apps/api/dealbrain_api/adapters/ebay.py` – eBay Browse API adapter.
- `apps/api/dealbrain_api/adapters/jsonld.py` – JSON-LD extractor.
- `apps/api/dealbrain_api/services/ingestion.py` – Orchestration, dedupe, enrichment.
- `apps/api/dealbrain_api/api/ingestion.py` – Public endpoints.
- `apps/api/dealbrain_api/tasks/ingest.py` – Celery task.
- `packages/core/dealbrain_core/schemas/ingestion.py` – Shared schemas.
- `apps/api/alembic/versions/*_add_url_ingestion.py` – Migration.

### Modify
- `apps/api/dealbrain_api/models/core.py` – Add `vendor_item_id`, `marketplace`, `provenance`, `last_seen_at` to Listing; update ImportSession for source_type.
- `apps/api/dealbrain_api/services/listings.py` – Add `upsert_from_url()` method.
- `apps/api/dealbrain_api/settings.py` – Config for adapters, rate limits, feature flags.
- `tests/` – Adapter unit tests, integration tests (fixtures with real API responses or mocks).

---

## Configuration & Feature Flags

```python
# apps/api/dealbrain_api/settings.py
class IngestionSettings(BaseSettings):
    enabled: bool = True
    adapters: dict = {
        "ebay": {
            "enabled": True,
            "timeout_s": 6,
            "retries": 2,
            "browse_api_key": "..."  # from env
        },
        "jsonld": {
            "enabled": True,
            "timeout_s": 8,
            "retries": 1
        },
        "amazon": {
            "enabled": False,  # P1; gated
            "timeout_s": 6,
            "pa_api_key": "...",
            "pa_api_partner_tag": "..."
        }
    }
    price_change_threshold_pct: float = 2.0
    price_change_threshold_abs: float = 1.0
    raw_payload_ttl_days: int = 30
    raw_payload_max_bytes: int = 524288
```

---

## Testing Strategy

### Unit Tests
- Adapter selection by domain and priority.
- eBay mapping: item specifics → specs, image extraction.
- JSON-LD parser: nested offers, price as string/number, missing fields.
- Dedup hash stability (whitespace, case).
- Normalizer: currency, condition, CPU/RAM regex.

### Integration Tests
- Mock eBay Browse API response → listing creation.
- Mock HTML with JSON-LD → extraction and normalization.
- Bulk job with 10 URLs: success/partial/fail mixed.
- Price change event emission threshold check.
- Dedupe: re-import same URL → no duplicate, fields updated.

### E2E (Happy Paths)
- Single eBay URL → complete in <10s, correct data.
- Bulk 50 URLs → completes in <3 min, 100% success.

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Single URL (API) | ≤ 5s p50 |
| Single URL (JSON-LD) | ≤ 8s p50 |
| Bulk throughput | ≥ 120 URLs/min (4 workers) |
| API availability | 99.5% |
| Raw payload size | ≤ 512 KB (truncated) |
| Error rate | < 3% (excl. invalid URLs) |

---

## Security & Compliance

- **User-Agent**: Product string with contact; respect robots.txt (P1).
- **Rate limits**: Per domain; configurable in settings.
- **Credentials**: Store in environment/secret manager; never in logs.
- **PII**: Never store buyer info; seller name/rating only.
- **Data retention**: Raw payloads expire after 30 days.

---
