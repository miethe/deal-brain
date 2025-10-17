# Deal Brain – Universal URL ingestion (P0–P1)

## Summary

Enable Deal Brain to ingest listings directly from retailer/marketplace URLs. The system prefers first-party APIs when available, falls back to structured page data (JSON-LD/microdata), and finally to site-specific scraping as a last resort. Output is a normalized `Listing` record plus raw source payloads, with dedupe, enrichment (e.g., CPU canonicalization), and eventing for price/watch workflows.

---

## Goals

| ID | Goal                                                                                                                                 |
| -- | ------------------------------------------------------------------------------------------------------------------------------------ |
| G1 | Paste a URL and import a listing with accurate price, title, images, condition, and key specs (CPU, RAM, storage, GPU, form factor). |
| G2 | Bulk import from a list of URLs (CSV/JSON) with resilient, observable job processing.                                                |
| G3 | Prefer official APIs (eBay first) and structured data extraction; use headless scraping only if required.                            |
| G4 | Normalize disparate sources into a single schema and deduplicate identical listings.                                                 |
| G5 | Provide clear UX feedback: success, partial data, or failure causes; show provenance.                                                |
| G6 | Emit telemetry and events for price changes and watchlists.                                                                          |

## Non-goals

* Full price history for all sites (P2+; limited to what the source/API provides in P0–P1).
* Seller-side actions (offers, messaging).
* Search/browse within external marketplaces (except where needed for API lookups).

---

## Scope and phases

| Phase       | Scope                                                                                                                                                                                                                                                       |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P0          | **eBay adapter (Browse API)**, **Generic schema adapter** (JSON-LD/microdata via extruct-equivalent), ingestion jobs, normalization, dedupe, minimal enrichment (CPU/GPU canonical name), “Add by URL” UI, bulk URL file import, base telemetry and events. |
| P1          | **Amazon adapter (PA-API)** behind feature flag; settings UI for credentials/eligibility; adapter priority & per-domain toggles; basic robots/rate-limit guardrails; headless **site adapter** skeleton for future scrapers.                                |
| P2 (future) | Best Buy/Walmart/Newegg adapters; price history providers; browser extension; advanced anti-bot playbooks; content-based dedupe; richer spec extraction models.                                                                                             |

---

## Assumptions and open questions

**Assumptions**

* Backend: FastAPI (Python 3.11+), Celery/RQ/Arq for async jobs, Postgres as primary DB.
* We can store raw payloads (API JSON and/or extracted HTML fragments) for debugging within a reasonable retention window (e.g., 30 days).
* Minimal enrichment tables for CPU/GPU exist or will be created in this feature.

**Open question (non-blocking)**

* What is the initial per-domain concurrency/rate cap policy (defaults proposed below)? If not provided, use defaults in NFRs.

---

## User stories

| ID  | As a…   | I want…                                     | So that…                                     | Acceptance hints                                                                |
| --- | ------- | ------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------- |
| US1 | buyer   | to paste a product URL and import a listing | I can evaluate it in my Deal Brain workspace | One-click import, <10s median complete if API path, clear status if queued/slow |
| US2 | buyer   | to bulk import a CSV/JSON of URLs           | I can seed my backlog quickly                | File upload → job tracker → per-row results with errors                         |
| US3 | analyst | to see where each field came from           | I can trust/verify data                      | Field-level provenance (adapter, extraction mode)                               |
| US4 | buyer   | deduplication of the same listing           | my workspace isn’t cluttered                 | Idempotent upsert by stable keys                                                |
| US5 | admin   | to disable/enable adapters per domain       | I can respect ToS/ops constraints            | Domain settings toggle + rate limits                                            |
| US6 | buyer   | to receive events on price changes          | I can act on deals                           | Event emitted on material change                                                |

---

## UX requirements

### Add by URL (single)

* Input: URL text field with “Import” button.
* Inline status: `Queued → Fetching → Normalizing → Enriched → Complete | Partial | Failed`.
* Show a summary card after completion: Title, image, price, condition, seller, key specs, and a **Provenance** chip (“eBay API” / “JSON-LD” / “Scraper”).
* On partial: highlight missing fields and provide “Open source payload” (modal) for debugging.

### Bulk import (file)

* Upload CSV (`url` column) or JSON (`[{ "url": …}]`) or paste multi-line URLs.
* Job monitor with per-row result: success/partial/fail + reason.
* Export results as CSV with appended columns.

---

## Architecture and flows

```mermaid
flowchart TD
  U[User] -->|POST /ingest?url=| API[Ingestion API]
  API --> Q[Job Queue]
  Q --> W[Ingestion Worker]
  W --> R[Router picks adapter]
  R -->|API available| A1[eBay Adapter]
  R -->|JSON-LD/microdata| A2[Generic Schema Adapter]
  R -->|Last resort| A3[Site-Specific Scraper]
  A1 --> N[Normalizer]
  A2 --> N
  A3 --> N
  N --> D[(DB: listings, sources, raw_payloads)]
  N --> E[Enricher: CPU/GPU map]
  E --> D
  N --> EV[Event Bus: listing.created/updated, price.changed]
  D --> API
  EV --> SUB[Subscribers (watchlists, notifications)]
```

---

## API contracts

### Public ingestion

**POST** `/api/ingest`
Imports a single URL.

* Query/body:

  ```json
  { "url": "https://example.com/product/123", "priority": "normal", "force": false }
  ```
* Response 202 (async):

  ```json
  { "job_id": "ing_01J8...", "status": "queued" }
  ```
* Response 200 (sync best-effort, only when adapter path is fast and configured as sync):

  ```json
  { "listing_id": "lst_01J8...", "status": "complete", "provenance": "ebay_api", "quality": "full" }
  ```

**GET** `/api/ingest/{job_id}`

* Response:

  ```json
  {
    "job_id": "ing_01J8...",
    "status": "complete|partial|failed|running|queued",
    "errors": [{"code":"ADAPTER_TIMEOUT","message":"..."}],
    "result": { "listing_id": "lst_01J8...", "quality": "partial", "provenance":"jsonld" }
  }
  ```

**POST** `/api/ingest/bulk`

* Multipart with `file` (CSV/JSON) or `urls` text.
* Response 202:

  ```json
  { "bulk_job_id":"bkg_01J8...", "total": 127 }
  ```

**GET** `/api/ingest/bulk/{bulk_job_id}`

* Returns array of row results with the same schema as single job plus per-row error reason.

### Internal adapter SDK (Python)

```python
class AdapterContext(TypedDict):
    url: str
    domain: str
    user_agent: str
    request_id: str
    timeout_s: int

class AdapterResult(TypedDict):
    source: Literal["api","jsonld","microdata","scraper"]
    raw: dict | str  # JSON or HTML snippet
    listing: "NormalizedListing"  # may be partial
    vendor_keys: dict  # e.g., {"ebay_item_id":"..."}
    quality: Literal["full","partial"]

class BaseAdapter(Protocol):
    def supports(self, url: str) -> bool: ...
    async def fetch(self, ctx: AdapterContext) -> AdapterResult: ...
```

Adapter registry priority: `api > jsonld/microdata > scraper`.

### Normalized listing schema (JSON Schema excerpt)

```json
{
  "$id": "https://dealbrain/schema/normalized-listing.json",
  "type": "object",
  "required": ["source_url","title","marketplace","provenance"],
  "properties": {
    "source_url": {"type":"string","format":"uri"},
    "marketplace": {"type":"string","enum":["ebay","amazon","other"]},
    "title": {"type":"string"},
    "description": {"type":"string"},
    "images": {"type":"array","items":{"type":"string","format":"uri"}},
    "price": {"type":"number"},
    "currency": {"type":"string","minLength":3,"maxLength":3},
    "shipping_cost": {"type":["number","null"]},
    "availability": {"type":"string","enum":["in_stock","out_of_stock","unknown"]},
    "condition": {"type":"string"},
    "seller": {
      "type":"object",
      "properties":{"name":{"type":"string"},"rating":{"type":["number","null"]},"location":{"type":["string","null"]}}
    },
    "specs": {
      "type":"object",
      "properties": {
        "cpu":{"type":["string","null"]},
        "ram_gb":{"type":["number","null"]},
        "storage":{"type":["string","null"]},
        "gpu":{"type":["string","null"]},
        "form_factor":{"type":["string","null"]},
        "misc":{"type":"object","additionalProperties":true}
      }
    },
    "variant":{"type":["string","null"]},
    "taxes":{"type":["number","null"]},
    "returns":{"type":["string","null"]},
    "location":{"type":["string","null"]},
    "listing_id_source":{"type":["string","null"]},   // e.g., eBay item id
    "provenance":{"type":"string"},                   // "ebay_api" | "jsonld" | "scraper"
    "last_seen_at":{"type":"string","format":"date-time"}
  }
}
```

### Events

* `listing.created` → `{ listing_id, marketplace, price, currency, provenance }`
* `listing.updated` → `{ listing_id, changed_fields:[...], provenance }`
* `price.changed` → `{ listing_id, previous:{price,currency}, current:{price,currency}, delta }`

---

## Data model

New/updated tables (Postgres):

| Table              | Purpose                     | Key fields                                                                                                                                                                     |                                                                                      |
| ------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| `ingest_jobs`      | track single and bulk tasks | `id (pk)`, `type (single                                                                                                                                                       | bulk)`, `status`, `requested_by`, `started_at`, `completed_at`, `error_code`, `meta` |
| `ingest_job_items` | per-URL results for bulk    | `id`, `bulk_job_id (fk)`, `url`, `status`, `listing_id`, `error_code`, `attempts`, `provenance`, `quality`                                                                     |                                                                                      |
| `listings`         | normalized listing          | `id`, `source_url`, `marketplace`, `title`, `price`, `currency`, `condition`, `seller_name`, `specs jsonb`, `listing_id_source`, `provenance`, `hash_identity`, `last_seen_at` |                                                                                      |
| `raw_payloads`     | debugging payloads          | `id`, `listing_id (fk)`, `adapter`, `source_type`, `payload jsonb/text`, `created_at`, TTL policy                                                                              |                                                                                      |
| `enrichment_cpu`   | cpu canonical               | `id`, `raw_name`, `canonical_name`, `family`, `tdp_w`, `cores`, `threads`, `passmark_id`                                                                                       |                                                                                      |

**Deduplication key**

* Primary: `(marketplace, listing_id_source)` when available.
* Fallback: `hash_identity = sha256(normalize(title) + seller_name + price)`.

Indexes on `listing_id_source`, `hash_identity`, `marketplace`, `last_seen_at`.

---

## Adapter specifics

### eBay adapter (P0)

* Input: Item URL → extract item id or call Browse API `getItemByLegacyId` fallback by URL parsing.
* Data: title, price (value/currency), condition, seller, shipping, item specifics (aspects), images.
* Mapping: aspects → `specs.misc` + targeted extraction for CPU/RAM/Storage heuristics.

### Generic schema adapter (P0)

* Parse page for JSON-LD `schema.org/Product` and/or microdata/RDFa.
* Use `offers.price`, `offers.priceCurrency`, `brand`, `sku`, `image`, `name`, `description`.
* Map to normalized schema; mark missing fields as null.

### Amazon adapter (P1)

* PA-API `GetItems` with ASIN extracted from URL.
* Respect credentials/eligibility gating; feature flag `ingestion.amazon.enabled`.

### Site-specific scraper skeleton (P1)

* Playwright-based with robots.txt check, per-domain rate limiter, CSS selectors registry.

---

## Normalization and enrichment rules

* **Currency**: from source; default USD if absent and domain in known USD list; else mark unknown and set `quality: partial`.
* **Condition**: map known source strings to canonical set: `new | refurbished | used_like_new | used_good | used_fair | for_parts`.
* **Specs parsing**:

  * CPU: regex over title/description/aspects; feed through `enrichment_cpu` to map to canonical.
  * RAM: capture “(\d+)\s?GB” near “RAM/Memory”.
  * Storage: prefer explicit NVMe/SATA + capacity; keep raw as fallback.
* **Provenance**: carry exact adapter source; expose to UX.

---

## Telemetry and observability

| Metric                                      | Type      | Notes                                               |
| ------------------------------------------- | --------- | --------------------------------------------------- |
| `ingest.jobs.count{status}`                 | counter   | queued, running, complete, failed                   |
| `ingest.adapter.latency_ms{adapter,source}` | histogram | API/jsonld/scraper                                  |
| `ingest.adapter.success_rate{adapter}`      | gauge     | rolling window                                      |
| `ingest.field.completeness{field}`          | gauge     | % listings with non-null                            |
| `price.changed.count`                       | counter   | emitted per delta                                   |
| `errors{code,adapter,domain}`               | counter   | timeouts, parse_fail, robots_disallow, rate_limited |

Structured logs with `request_id`, `job_id`, `adapter`, `domain`, `status`.

---

## Security, compliance, and rate limits

* **Robots respect** for scraper paths; store robots verdict per domain daily (cache TTL 24h).
* **Per-domain caps** (defaults): API adapters as per vendor quota; JSON-LD: 6 req/min; scrapers: 2 pages/min, 1 concurrent/tab.
* **User agent**: product string with contact URL/email.
* **Config toggles**: enable/disable adapter per domain; set concurrency and backoff per adapter.
* **PII**: do not store buyer/sensitive info; only seller public names/ratings.

---

## Performance targets (NFRs)

| Area                                 | Target                                                      |
| ------------------------------------ | ----------------------------------------------------------- |
| Median single-URL ingest via API     | ≤ 5s                                                        |
| Median single-URL ingest via JSON-LD | ≤ 8s                                                        |
| Bulk throughput                      | ≥ 120 URLs/min (API/JSON-LD mixed, 4 workers)               |
| Availability                         | 99.5% for ingestion API                                     |
| Max payload size stored              | 512 KB per raw payload (truncate beyond)                    |
| Error budget                         | < 3% failed due to adapter/runtime (excluding invalid URLs) |

---

## Acceptance criteria

| ID  | Criteria                                                                                                                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC1 | Given a valid eBay item URL, system imports listing with title, price, currency, condition, at least one image, and seller name; `provenance=ebay_api`. |
| AC2 | Given a retailer page with valid JSON-LD Product, system imports listing with title, price, and currency; `provenance=jsonld`.                          |
| AC3 | Dedupe: importing the same URL twice results in a single `listing` row updated (no duplicates); `last_seen_at` refreshed.                               |
| AC4 | Bulk file with 100 URLs completes with per-row statuses; overall job reported as complete with counts.                                                  |
| AC5 | Setting `amazon.enabled=false` prevents the adapter from running; attempts return `failed` with `ADAPTER_DISABLED`.                                     |
| AC6 | On price change (≥ $1 or ≥ 2% delta), `price.changed` event is emitted with previous/current values.                                                    |
| AC7 | Field-level provenance is exposed in API response and UI card.                                                                                          |
| AC8 | Robots disallow for a domain prevents scraper execution and records `ROBOTS_DISALLOW` error without retries.                                            |
| AC9 | Telemetry dashboards show adapter success rate and latency histograms over last 24h.                                                                    |

---

## Test plan

### Unit tests

* Adapter supports/route selection by domain and precedence order.
* eBay mapping: aspects → specs; missing fields → null.
* JSON-LD parser tolerates arrays, nested offers, price as string/number.
* Normalizer: currency mapping, condition normalization, CPU/RAM regexes.
* Dedupe hash stability with noisy titles (case/whitespace).

### Integration tests

* Golden fixtures: eBay API JSON; retailer HTML with JSON-LD; malformed JSON-LD; robots.txt disallow.
* Bulk job with mixed outcomes: success/partial/fail.
* Events pipeline: `price.changed` emitted only on material deltas.

### E2E (happy paths)

* Paste URL → success card within target SLA.
* Bulk 500 URLs → completes under 10 minutes with throughput target.

---

## Risks and mitigations

| Risk                                 | Impact                   | Mitigation                                                                       |
| ------------------------------------ | ------------------------ | -------------------------------------------------------------------------------- |
| API credential gating/quotas         | Ingestion delays         | Cache, backoff, queue, fall back to JSON-LD when allowed                         |
| Structured data missing or incorrect | Partial/incorrect fields | Mark `quality=partial`, surface provenance, allow manual edit                    |
| Anti-bot defenses                    | Failures/blocks          | Prefer APIs/JSON-LD; low scraper concurrency; respect robots; per-domain toggles |
| Dedupe false positives               | Lost variants            | Include variant and seller in identity hash; surface merges in audit log         |
| Enrichment mis-mapping (CPU/GPU)     | Wrong specs              | Maintain curated canonical tables + tests; show raw in `misc`                    |

---

## Rollout plan

1. **P0** ship behind feature flag `ingestion.enabled`. Enable eBay + Generic JSON-LD.
2. Instrument telemetry dashboards; validate on 200 known URLs.
3. Enable bulk import; soak for a week.
4. **P1** add Amazon adapter gated by credentials; add per-domain toggles and rate settings in admin UI.

---

## Developer tasks (stories)

| ID         | Title                | Desc                                                      | Est |
| ---------- | -------------------- | --------------------------------------------------------- | --- |
| ST-ING-001 | Adapter SDK          | Base classes, registry, priority rules, retries, timeouts | 3d  |
| ST-ING-002 | eBay adapter         | Browse API integration, mapping, tests, fixtures          | 4d  |
| ST-ING-003 | JSON-LD adapter      | Parser, Product mapping, microdata fallback               | 3d  |
| ST-ING-004 | Normalizer & schema  | JSON Schema, mapper, condition/currency/specs rules       | 2d  |
| ST-ING-005 | Dedupe & upsert      | Identity keys, hash, idempotent writes                    | 2d  |
| ST-ING-006 | Ingest jobs          | Queue, job model, status API, retries/backoff             | 3d  |
| ST-ING-007 | Raw payload store    | Table, size guard, retention TTL                          | 1d  |
| ST-ING-008 | Enrichment (CPU/GPU) | Minimal canonical tables + mapping                        | 2d  |
| ST-ING-009 | Events bus           | listing.* and price.changed events                        | 2d  |
| ST-ING-010 | Add by URL UI        | Form, status, result card with provenance                 | 3d  |
| ST-ING-011 | Bulk import UI/API   | File upload, job monitor, CSV export                      | 3d  |
| ST-ING-012 | Telemetry            | Metrics, traces, dashboards                               | 2d  |
| ST-ING-013 | Admin toggles        | Per-domain enable/disable + rate caps                     | 2d  |
| ST-ING-014 | Amazon adapter (P1)  | PA-API integration, settings UI, tests                    | 5d  |

---

## Configuration defaults

```yaml
ingestion:
  enabled: true
  adapters:
    ebay:
      enabled: true
      timeout_s: 6
      retries: 2
    jsonld:
      enabled: true
      timeout_s: 8
      retries: 1
    amazon:
      enabled: false   # P1
      timeout_s: 6
      retries: 2
  scraper:
    enabled: false     # P1 scaffold
    robots_respect: true
    per_domain_rps: 0.03     # ~2/min
    max_concurrency: 1
  events:
    price_change_threshold_pct: 2
    price_change_threshold_abs: 1.0
  raw_payloads:
    ttl_days: 30
    max_bytes: 524288
```

---

## Monitoring dashboard checklist

* Tiles: success rate by adapter, P50/P95 latency, errors by domain, field completeness, event counts.
* Logs: top 10 error codes, top failing domains, sample payload links.

---

## Operational runbook

* **Rotate credentials**: admin settings → secret store; adapters reload on change.
* **Throttle a domain**: set per-domain RPS/concurrency or disable adapter.
* **Investigate bad data**: open listing → “Provenance” → raw payload; file an adapter mapping fix PR.
* **Bulk failures**: download results CSV, filter on error codes, re-queue subset.

---
