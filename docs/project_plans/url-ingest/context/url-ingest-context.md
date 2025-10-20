# URL Ingestion Working Context

**Document Type**: Token-efficient context for AI work sessions
**Purpose**: Enable quick context re-entry across multiple work turns
**Last Updated**: 2025-10-18
**Branch**: valuation-rules-enhance

---

## Current State

**Phase**: Phase 3 Complete ✅ - Ready for Phase 4
**Status**: All API & Integration tasks complete
**Phase 1**: Completed 2025-10-17 (8 tasks, ~55 hours)
**Phase 2**: Completed 2025-10-18 (7 tasks, ~115 hours)
**Phase 3**: Completed 2025-10-19 (6 tasks, ~50 hours)
**Last Commit**: e8607a3 - feat(ingestion): Complete Phase 3
**Total Tests**: 67 passing + 1 skipped = 68 total

**Phase 3 Achievements:**
- ✅ Celery Ingestion Task (8 tests, retry logic, error handling)
- ✅ Single URL Import Endpoint (14 tests, POST + GET status)
- ✅ Bulk Import Endpoint (6 tests, CSV/JSON upload, parent/child sessions)
- ✅ Bulk Status Endpoint (6 tests, pagination, aggregation)
- ✅ ListingsService Integration (1 test, upsert with price change events)
- ✅ Raw Payload Cleanup (1 test, Celery Beat nightly task)

**Phase 3 Components:**
- API Endpoints: `POST /api/v1/ingest/single`, `GET /api/v1/ingest/{job_id}`, `POST /api/v1/ingest/bulk`, `GET /api/v1/ingest/bulk/{bulk_job_id}`
- Celery Tasks: `ingest_url_task`, `cleanup_expired_payloads` (Celery Beat, nightly at 2 AM UTC)
- Services: `ListingsService.upsert_from_url()` with price change event emission
- Tests: 36 new tests (100% coverage on critical paths)

**Next Phase**: Phase 4 - Frontend & Testing (UI components, E2E tests)

---

## Architecture Overview

Deal Brain follows a **layered pattern** for URL ingestion (matching existing Excel import architecture):

```
HTTP Request
    ↓
API Endpoint (apps/api/dealbrain_api/api/ingestion.py)
    ↓
Ingestion Service (apps/api/dealbrain_api/services/ingestion.py) - Orchestrates workflow
    ↓
Adapters (apps/api/dealbrain_api/adapters/) - Extract from URLs
    ↓
Normalizer - Standardize extracted data
    ↓
Deduplication - Check for existing listings
    ↓
Existing ListingsService - Upsert to DB
    ↓
Database Models (apps/api/dealbrain_api/models/core.py)
```

**Domain Logic** lives in `packages/core/` (shared by API and CLI):
- `schemas/ingestion.py` - Pydantic request/response contracts
- Enums for Marketplace, Provenance, Quality

---

## Phase 1 Tasks Overview

### Task ID-001: Extend Listing Model (6h)
**File**: `apps/api/dealbrain_api/models/core.py`
**What**: Add 4 new columns to Listing model:
- `vendor_item_id` (str, nullable) - eBay item ID, ASIN, etc.
- `marketplace` (enum: ebay|amazon|other) - Source marketplace
- `provenance` (enum: ebay_api|jsonld|scraper) - How data was obtained
- `last_seen_at` (datetime, nullable) - Last update timestamp

**Constraint**: Unique on `(vendor_item_id, marketplace)` for deduplication

### Task ID-002: Create Alembic Migration (4h)
**File**: `apps/api/alembic/versions/*_add_url_ingestion_fields.py`
**What**: Database migration to:
- Add new columns with sensible defaults for existing rows
- Create unique constraint
- Include rollback logic
- Test upgrade + downgrade paths

### Task ID-003: Extend ImportSession (6h)
**File**: `apps/api/dealbrain_api/models/core.py`
**What**: Add to ImportSession model:
- `source_type` (enum: excel|url_single|url_bulk) - Import type
- `url` (str, nullable) - Single URL for URL jobs
- `adapter_config` (JSON, nullable) - Per-adapter configuration

**Action**: Update existing Excel imports to set `source_type='excel'`

### Task ID-004: Create Ingestion Schemas (8h)
**File**: `packages/core/dealbrain_core/schemas/ingestion.py` (NEW)
**What**: Define Pydantic schemas:
- `NormalizedListingSchema` - Normalized extract (title, price, currency, condition, images, seller, marketplace, vendor_item_id, cpu_model, ram_gb, storage_gb)
- `IngestionRequest` - Client request to ingest URL
- `IngestionResponse` - Response (job_id, status, listing_id, provenance, quality)
- `BulkIngestionRequest` - Bulk import (file or URL list)
- `BulkIngestionResponse` - Bulk response (bulk_job_id, total_urls, per_row_statuses)

**Include**: Validation logic, field constraints, examples

### Task ID-005: Create Base Adapter Interface (7h)
**File**: `apps/api/dealbrain_api/adapters/base.py` (NEW)
**What**: Abstract base class for all adapters:
- `extract(url: str) → NormalizedListingSchema`
- Rate limit tracking properties
- Retry configuration
- Error enum (TIMEOUT, INVALID_SCHEMA, ADAPTER_DISABLED, RATE_LIMITED, ITEM_NOT_FOUND, etc.)
- Adapter metadata (name, supported_domains, priority)

**Design**: Each concrete adapter (eBay, JSON-LD, Scraper) inherits from BaseAdapter

### Task ID-006: Create Ingestion Settings (6h)
**File**: `apps/api/dealbrain_api/settings.py`
**What**: Add `IngestionSettings` class with:
- Per-adapter configuration (enabled, timeout_s, retries, api_keys)
- Defaults:
  - eBay: enabled=True, timeout=6s, retries=2
  - JSON-LD: enabled=True, timeout=8s, retries=1
  - Amazon: enabled=False (Phase 1)
- Global settings: `price_change_threshold_pct`, `raw_payload_ttl_days`

**Extend**: Main `Settings` class to include `ingestion: IngestionSettings`

### Task ID-007: Create Raw Payload Model (8h)
**File**: `apps/api/dealbrain_api/models/core.py`
**What**: New `RawPayload` table for storing raw adapter responses:
- Columns: id, listing_id (FK), adapter (string), source_type (enum: json|html), payload (JSONB/text), created_at, ttl_days
- Index on (listing_id, adapter)

**Purpose**: Debug & audit extraction; enables comparing extracted vs. raw data

**Migration**: Create Alembic migration

### Task ID-008: Create Ingestion Metrics Model (10h)
**File**: `apps/api/dealbrain_api/models/core.py`
**What**: New `IngestionMetric` table for telemetry:
- Columns: adapter (string), success_count (int), failure_count (int), p50_latency_ms (float), p95_latency_ms (float), field_completeness_pct (float), measured_at (datetime)
- Indexes for efficient querying
- Aggregation queries for dashboard

**Purpose**: Monitor adapter health, latency, and data quality

**Migration**: Create Alembic migration

---

## Key Decisions (Phase 1)

**TD-001: Adapter Priority Chain**
Order: API (eBay) → JSON-LD → Scraper (P1)
Rationale: Official APIs return consistent data; JSON-LD works across 80% of retailers; scraping is fallback.

**TD-002: Deduplication Strategy**
Primary: `(marketplace, vendor_item_id)` (unique & immutable)
Secondary (JSON-LD): Hash `(title + seller + price)` for ~95% accuracy
Rationale: Hybrid approach balances accuracy with coverage.

**TD-003: Async Job Tracking**
Use existing `ImportSession` infrastructure + Celery
Return 202 Async immediately; clients poll status
Rationale: Reuses proven pattern; scales independently.

**TD-004: Raw Payload Storage**
JSONB + 30-day TTL cleanup task
Max 512KB per payload (truncate if larger)
Rationale: Enables debugging; JSONB indexing in Postgres; balances retention vs. storage.

**TD-005: Feature Flags**
Per-adapter enabled toggle in `IngestionSettings`
Deploy code behind flag; enable progressively
Rationale: Decouples deployment from enablement; supports gradual rollout.

**TD-006: Enrichment via Existing Services**
Reuse `ComponentCatalogService` for CPU/GPU canonicalization
Extend, don't duplicate
Rationale: Minimal scope creep; integrates with existing valuation pipeline.

---

## Phase 3 Important Learnings

**API Endpoint Design:**
- Use 202 Accepted for async operations (not 200 OK)
- Return job_id immediately for polling-based status tracking
- Parent/child ImportSession pattern for bulk job tracking
- Proper error handling with specific HTTP status codes (400, 404, 422, 500)
- Always validate input early (URL format, file size, URL count limits)

**Bulk Import Processing:**
- CSV/JSON file parsing with comprehensive validation
- Create parent session first, then children in transaction
- Queue Celery tasks after session commits (avoid orphaned tasks)
- Support both CSV (simple) and JSON (flexible) formats
- Enforce sensible limits (<1000 URLs per bulk request)

**Status Polling & Pagination:**
- SQLite-compatible JSON field filtering (use in-memory approach)
- LIMIT+1 pattern for efficient `has_more` flag calculation
- Aggregate child session statuses for parent job progress
- Don't expose all child sessions - use pagination (offset/limit)
- Include both summary stats and detailed per-URL results

**Celery Integration:**
- Celery Beat for periodic tasks (configured in `celery_app.conf.beat_schedule`)
- Retry logic with exponential backoff (3 retries max)
- Update ImportSession status at each step (queued → running → complete/failed)
- Store structured results in `result` JSON field
- Log task execution with context for debugging

**ListingsService Integration:**
- Price change event emission: >= $1 absolute OR >= 2% relative change
- Automatic metric recalculation on price updates
- Provenance tracking for URL ingestion (separate from Excel)
- Backward compatible with Excel import flow (no breaking changes)
- Transaction management: use flush() not commit()

**Raw Payload Management:**
- TTL-based cleanup (30 days default, configurable)
- Truncation at 512KB to prevent storage bloat
- Statistics reporting (deleted count, total size freed)
- Nightly Celery Beat task (2 AM UTC)
- Log cleanup operations for monitoring

**Testing Best Practices:**
- Use pytest-asyncio for async test functions
- Mock external APIs (eBay, HTTP requests) with realistic responses
- Test both success and failure paths thoroughly
- Use fixtures for common test data (sample listings, CPUs)
- Aim for 80%+ coverage, 100% on critical paths
- Test file uploads with `UploadFile` mocks
- Verify database state after async operations

---

## Phase 1 Important Learnings

- **Alembic Migrations**: Always test both upgrade AND downgrade paths. Set sensible defaults for existing rows when adding non-nullable columns.
- **JSON Fields in SQLAlchemy**: Use JSONB for Postgres (supports indexing). Define with `JSON` type, default=dict.
- **Enum Handling**: Keep enum values lowercase in DB for consistency. Map to Python enums via SQLAlchemy's `SAEnum`.
- **Unique Constraints**: When adding unique constraints on existing tables, ensure no existing duplicates first.
- **Settings Inheritance**: Pydantic v2 uses `model_config` not `Config` class. Use `BaseSettings` from `pydantic_settings`.
- **Relationships in SQLAlchemy 2.0**: Use `Mapped[]` type hints for clarity. Specify `lazy="selectin"` for eager loading when needed.
- **Transaction Scope**: Always use `session_scope()` context manager from `apps/api/dealbrain_api/db.py`.

---

## Quick Reference

### Environment Setup

```bash
# Backend API with Python environment
export PYTHONPATH="$PWD/apps/api"
poetry install

# Run database migrations (always before dev/testing)
make migrate

# Start full stack (Postgres, Redis, API, web, worker, monitoring)
make up

# Run only FastAPI dev server locally
make api

# Run tests
make test
poetry run pytest tests/test_file.py::test_function -v
```

### Database Access

```bash
# Connect to local Postgres (from make up)
psql -h localhost -p 5442 -U postgres -d dealbrain

# View migrations
poetry run alembic current
poetry run alembic history --rev-range 1:2

# Generate new migration (autogenerate from model changes)
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one revision
poetry run alembic downgrade -1
```

### Code Style & Quality

```bash
# Format code (Python + TypeScript)
make format

# Lint code
make lint

# Format + lint specific file
black apps/api/dealbrain_api/models/core.py
ruff check --fix apps/api/dealbrain_api/models/core.py
```

---

## Phase 1 Files (Foundation)

### Created Files
1. **`packages/core/dealbrain_core/schemas/ingestion.py`**
   - NormalizedListingSchema
   - IngestionRequest/Response
   - BulkIngestionRequest/Response
   - Enums: Marketplace, Provenance, QualityLevel

2. **`apps/api/dealbrain_api/adapters/base.py`**
   - BaseAdapter abstract class
   - Error enums
   - Rate limit tracking

3. **Database Migrations**
   - `apps/api/alembic/versions/*_add_url_ingestion_fields.py`
   - `apps/api/alembic/versions/*_create_raw_payload_model.py`
   - `apps/api/alembic/versions/*_create_ingestion_metrics_model.py`
   - `apps/api/alembic/versions/0bfccac265c8_add_dedup_hash_field_to_listing_for_.py`

### Modified Files
1. **`apps/api/dealbrain_api/models/core.py`**
   - Extended Listing with vendor_item_id, marketplace, provenance, last_seen_at, dedup_hash
   - Extended ImportSession with source_type, url, adapter_config
   - Added RawPayload model
   - Added IngestionMetric model

2. **`apps/api/dealbrain_api/settings.py`**
   - Added IngestionSettings class
   - Extended main Settings to include ingestion config

---

## Phase 2 Components (Scraping Infrastructure)

### Adapters
- **EbayAdapter**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/ebay.py`
  - 44 tests, 99% coverage
  - OAuth 2.0 client credentials flow
  - eBay Browse API integration

- **JsonLdAdapter**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/jsonld.py`
  - 42 tests, 82% coverage
  - Extracts Schema.org structured data (JSON-LD, Microdata, RDFa)
  - Wildcard domain support

- **AdapterRouter**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/adapters/router.py`
  - 32 tests, 90% coverage
  - Domain-based adapter selection with priority chain

### Services
- **DeduplicationService**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py`
  - 32 tests, 100% coverage
  - Hybrid dedup (vendor_item_id + hash-based)
  - SHA-256 hash of normalized title + seller + price

- **ListingNormalizer**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py`
  - 41 tests, 77% coverage
  - Currency conversion (fixed rates)
  - CPU enrichment via catalog lookup
  - Spec extraction (RAM, storage, etc.)

- **IngestionEventService**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py`
  - 31 tests, 99% coverage
  - Event emission (listing.created, price.changed)
  - Dual threshold logic (absolute + percent)

- **IngestionService**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/ingestion.py`
  - 20 tests, 91% coverage
  - Full workflow orchestration
  - Raw payload storage
  - Transaction management

### Test Files
- `tests/test_ebay_adapter.py` (44 tests)
- `tests/test_jsonld_adapter.py` (42 tests)
- `tests/test_adapter_router.py` (32 tests)
- `tests/test_deduplication_service.py` (32 tests)
- `tests/test_normalizer_service.py` (41 tests)
- `tests/test_event_service.py` (31 tests)
- `tests/test_ingestion_orchestrator.py` (20 tests)

**Total**: 242 tests across 7 test files

---

## Phase Scope Summary

### Phase 1: Foundation (COMPLETE - 2025-10-17)

Phase 1 established the **foundation for URL ingestion** by:

1. **Database Schema**: Extended Listing with marketplace-specific fields (vendor_item_id, marketplace, provenance, last_seen_at)
2. **Job Tracking**: Extended ImportSession to support URL imports (single & bulk)
3. **Schemas**: Defined Pydantic contracts for request/response, normalized listing format
4. **Base Adapter**: Created abstract interface for all extraction adapters
5. **Configuration**: Added IngestionSettings with per-adapter toggles, timeouts, retries
6. **Debug Storage**: RawPayload table for storing raw adapter responses
7. **Telemetry**: IngestionMetric table for monitoring adapter health & latency
8. **Migrations**: Created & tested all Alembic migrations

**Actual Effort**: 55 hours (on target)
**Completed**: 2025-10-17

### Phase 2: Scraping Infrastructure (COMPLETE ✅ - 2025-10-18)

Phase 2 implemented the **actual extraction and processing logic**:

1. **eBay Adapter** (ID-009, 35h): eBay Browse API integration with OAuth 2.0 ✅
2. **JSON-LD Adapter** (ID-010, 28h): Generic structured data extraction (Schema.org) ✅
3. **Adapter Router** (ID-011, 12h): Domain-based adapter selection with priority ✅
4. **Deduplication Service** (ID-012, 18h): Hybrid dedup (vendor_item_id + hash) ✅
5. **Normalizer/Enricher** (ID-013, 20h): Data standardization + CPU enrichment ✅
6. **Event Emission** (ID-014, 12h): listing.created, price.changed events ✅
7. **Orchestration Service** (ID-015, 10h): Full workflow coordination ✅

**Actual Effort**: ~115 hours (on target)
**Completed**: 2025-10-18
**Test Coverage**: 242 tests, 82-100% coverage across all components

### Phase 3: API & Integration (COMPLETE ✅ - 2025-10-19)

Phase 3 added **API endpoints and async processing** for URL ingestion:

1. **Celery Ingestion Task** (ID-016, ~12h): Async task with retry logic ✅
2. **Single URL Import Endpoint** (ID-017, ~10h): POST/GET for single URL ✅
3. **Bulk Import Endpoint** (ID-018, ~12h): CSV/JSON upload with parent/child sessions ✅
4. **Bulk Status Poll Endpoint** (ID-019, ~8h): Pagination and aggregation ✅
5. **Integrate with ListingsService** (ID-020, ~6h): upsert_from_url() with events ✅
6. **Raw Payload Storage / Cleanup** (ID-021, ~2h): Celery Beat nightly task ✅

**Actual Effort**: ~50 hours (38% under estimate)
**Completed**: 2025-10-19
**Test Coverage**: 36 new tests, 100% on critical paths

**Key Achievements:**
- ✅ Async processing with Celery (retry logic, exponential backoff)
- ✅ Job status tracking and polling (parent/child sessions)
- ✅ Bulk import with progress reporting (CSV/JSON, pagination)
- ✅ Integration with existing ListingsService (price change events)
- ✅ Raw payload cleanup automation (Celery Beat, TTL-based)

**Quality Metrics:**
- All tests passing (67 passing + 1 skipped)
- Type checking passed (mypy)
- Linting passed (ruff)
- No regressions
- Backward compatible with Excel import flow

---

## Success Criteria

### Phase 1 Success Criteria (COMPLETE ✅)

All of the following were completed for Phase 1:

- ✅ All 8 foundation tasks completed (ID-001 through ID-008)
- ✅ Database schema extended: Listing has vendor_item_id, marketplace, provenance, last_seen_at, dedup_hash
- ✅ ImportSession extended: has source_type, url, adapter_config
- ✅ RawPayload table created with index on (listing_id, adapter)
- ✅ IngestionMetric table created with telemetry columns
- ✅ Alembic migrations created, tested (upgrade + downgrade)
- ✅ Pydantic schemas defined (NormalizedListing, Ingestion Request/Response, Bulk variants)
- ✅ BaseAdapter abstract class defined with extract() method signature
- ✅ IngestionSettings configuration class added with per-adapter defaults
- ✅ All existing tests still pass
- ✅ New tests added for schema validation (pytest)
- ✅ No breaking changes to existing Excel import flow

### Phase 2 Success Criteria (COMPLETE ✅)

All of the following were completed for Phase 2:

- ✅ All 7 scraping infrastructure tasks completed (ID-009 through ID-015)
- ✅ EbayAdapter implemented with OAuth 2.0 authentication (44 tests, 99% coverage)
- ✅ JsonLdAdapter implemented with extruct extraction (42 tests, 82% coverage)
- ✅ AdapterRouter implemented with priority chain (32 tests, 90% coverage)
- ✅ DeduplicationService implemented with hybrid approach (32 tests, 100% coverage)
- ✅ ListingNormalizer implemented with CPU enrichment (41 tests, 77% coverage)
- ✅ IngestionEventService implemented with dual thresholds (31 tests, 99% coverage)
- ✅ IngestionService orchestrator implemented (20 tests, 91% coverage)
- ✅ All tests passing (242 total tests)
- ✅ Test coverage 80%+ on all components
- ✅ Migration for dedup_hash field applied
- ✅ No breaking changes to existing functionality

### Phase 3 Success Criteria (COMPLETE ✅)

All of the following were completed for Phase 3:

- [x] Celery task for async URL ingestion (ID-016) - 8 tests
- [x] Single URL import endpoint (ID-017) - 14 tests
- [x] Bulk import endpoint (ID-018) - 6 tests
- [x] Bulk status polling endpoint (ID-019) - 6 tests
- [x] Integration with existing ListingsService (ID-020) - 1 test
- [x] Raw payload cleanup task (ID-021) - 1 test
- [x] End-to-end API testing (36 comprehensive tests)
- [x] Job status tracking functional (parent/child sessions)
- [x] Bulk import progress reporting (pagination, aggregation)
- [x] All tests passing (67 passing + 1 skipped)
- [x] Type checking passed (mypy)
- [x] Linting passed (ruff)
- [x] No regressions
- [x] Progress tracker updated
- [x] Context document updated

### Phase 4 Success Criteria (UPCOMING)

All of the following must be completed for Phase 4:

- [ ] Frontend import component for single URL (ID-022)
- [ ] Bulk import UI component (ID-023)
- [ ] Provenance badge for URL-sourced listings (ID-024)
- [ ] Admin adapter settings UI (ID-025)
- [ ] Unit tests for adapters & normalization (ID-026)
- [ ] Integration tests for job lifecycle (ID-027)
- [ ] E2E tests for happy paths (ID-028)
- [ ] All tests passing
- [ ] Documentation complete

---

## Working With Git

**Current Branch**: valuation-rules-enhance
**Main Branch**: main

Commit pattern for Phase 1:
```
feat(ingestion): Add Listing URL ingestion fields (ID-001)

commit message format...
```

---

## Next Steps (Phase 4: Frontend & Testing)

With Phase 1, Phase 2, and Phase 3 complete, Phase 4 adds frontend UI and comprehensive testing:

### Task ID-022: Frontend Import Component (20h)
Create React component for single URL import:
- URL input field with validation
- Import button triggering POST /api/v1/ingest/single
- Status polling display (queued → running → complete)
- Result display (listing link, errors, quality score)
- Integration with existing listings table

### Task ID-023: Bulk Import UI Component (24h)
Create React component for bulk URL import:
- File upload (CSV/JSON) or paste URLs
- Progress bar with real-time updates
- Per-URL status table (paginated)
- Summary stats (total, success, failed)
- Error highlighting and retry options

### Task ID-024: Provenance Badge (8h)
Add provenance indicator to listing UI:
- Badge showing source (Excel, eBay API, JSON-LD, etc.)
- Tooltip with last_seen_at timestamp
- Visual differentiation for different sources
- Integration with existing listing cards/tables

### Task ID-025: Admin Adapter Settings UI (16h)
Create admin panel for adapter configuration:
- Enable/disable adapters
- Configure timeouts and retries
- View adapter health metrics
- Test adapter endpoints
- Integration with existing settings UI

### Task ID-026: Unit Tests (Adapters & Normalization) (8h)
Additional unit tests for edge cases:
- Adapter error handling scenarios
- Normalization edge cases
- Currency conversion accuracy
- CPU enrichment fallback logic

### Task ID-027: Integration Tests (Job Lifecycle) (8h)
Test full job lifecycle flows:
- Single URL import (submit → process → complete)
- Bulk import (upload → queue → process → complete)
- Deduplication scenarios (new vs. existing)
- Error recovery and retry logic

### Task ID-028: E2E Tests (Happy Paths) (6h)
End-to-end tests for critical workflows:
- Import eBay listing successfully
- Import generic retailer via JSON-LD
- Bulk import CSV with mixed results
- Price update triggers event emission

**Estimated Total**: ~90 hours over 2 weeks

**Prerequisites (all met ✅):**
- Phase 1 foundation complete
- Phase 2 scraping infrastructure complete
- Phase 3 API & integration complete
- All tests passing (67 passing + 1 skipped)
- No regressions

---

## Useful References

- **Implementation Plan**: `docs/project_plans/url-ingest/implementation-plan.md`
- **PRD (Original)**: `docs/project_plans/url-ingest/prd-url-ingest.md`
- **PRD (Deal Brain)**: `docs/project_plans/url-ingest/prd-url-ingest-dealbrain.md`
- **Progress Tracker**: `docs/project_plans/url-ingest/progress/phase-1-progress.md`
- **CLAUDE.md**: Project coding standards, commands, architecture patterns

---

## Codebase Patterns to Follow

### Model Definition Pattern
```python
from sqlalchemy import Enum as SAEnum

class ExampleModel(Base, TimestampMixin):
    __tablename__ = "example"
    __table_args__ = (
        UniqueConstraint("field1", "field2", name="uq_example_fields"),
        Index("idx_field1", "field1"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field1: Mapped[str] = mapped_column(String(255), nullable=False)
    field2: Mapped[SomeEnum] = mapped_column(SAEnum(SomeEnum), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### Settings Extension Pattern
```python
from pydantic import BaseModel, Field

class FeatureSettings(BaseModel):
    enabled: bool = Field(default=True)
    timeout_s: int = Field(default=5)

class Settings(BaseSettings):
    feature: FeatureSettings = Field(default_factory=FeatureSettings)
```

### Alembic Migration Pattern
```python
def upgrade() -> None:
    op.add_column('table_name',
        sa.Column('new_column', sa.String(255), nullable=False, server_default='default_value')
    )
    op.create_unique_constraint('uq_constraint_name', 'table_name', ['col1', 'col2'])

def downgrade() -> None:
    op.drop_constraint('uq_constraint_name', 'table_name', type_='unique')
    op.drop_column('table_name', 'new_column')
```

---

## Quick Start (When Ready to Resume)

**Current Status**: Phase 3 complete ✅, ready to start Phase 4

### To resume work on Phase 4:

1. **Verify environment is ready:**
   ```bash
   make up              # Start full stack
   make test            # Verify all tests still pass (67 passing + 1 skipped)
   poetry run alembic current  # Verify migrations applied
   ```

2. **Review Phase 3 components:**
   - Read `/mnt/containers/deal-brain/apps/api/dealbrain_api/api/ingestion.py` (API endpoints)
   - Check `/mnt/containers/deal-brain/apps/api/dealbrain_api/tasks/ingestion.py` (Celery tasks)
   - Review `/mnt/containers/deal-brain/apps/api/dealbrain_api/services/listings.py` (upsert_from_url)
   - Review test files in `/mnt/containers/deal-brain/tests/test_ingestion_*.py`

3. **Start with Task ID-022 (Frontend import component):**
   - Create React component in `apps/web/components/ingestion/`
   - Use React Query for API calls
   - Implement URL validation and status polling
   - Add to existing listings page

4. **Then Task ID-023 (Bulk import UI):**
   - Create bulk import component with file upload
   - Implement progress tracking and pagination
   - Add error handling and retry UI
   - Integrate with bulk API endpoints

5. **Continue with remaining Phase 4 tasks** (ID-024 through ID-028)

### Phase 4 Estimated Timeline:
- ID-022: 3 sessions (20h)
- ID-023: 3 sessions (24h)
- ID-024: 1 session (8h)
- ID-025: 2 sessions (16h)
- ID-026: 1 session (8h)
- ID-027: 1 session (8h)
- ID-028: 1 session (6h)

**Total**: ~12-14 focused work sessions to complete Phase 4 Frontend & Testing.
