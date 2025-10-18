# Phase 1 Working Context

**Document Type**: Token-efficient context for AI work sessions
**Purpose**: Enable quick context re-entry across multiple work turns
**Last Updated**: 2025-10-17
**Branch**: valuation-rules-enhance

---

## Current State

**Phase**: Phase 1 - Foundation (Starting)
**Status**: Just started, no work completed yet
**Total Scope**: 8 foundational tasks, ~55 hours over 1.4 weeks
**Success Metric**: All 8 tasks completed, migrations applied, schemas validated with tests

**Key Milestone**: Database schema extended with URL ingestion support, foundational interfaces created, settings configured.

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

## Important Learnings & Gotchas

*(Template for lessons discovered during implementation)*

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

## Files to Create/Modify in Phase 1

### NEW Files (to create)
1. **`packages/core/dealbrain_core/schemas/ingestion.py`**
   - NormalizedListingSchema
   - IngestionRequest/Response
   - BulkIngestionRequest/Response
   - Enums: Marketplace, Provenance, QualityLevel

2. **`apps/api/dealbrain_api/adapters/base.py`**
   - BaseAdapter abstract class
   - Error enums
   - Rate limit tracking

3. **Database Migrations** (auto-generated via alembic)
   - `apps/api/alembic/versions/*_add_url_ingestion_fields.py`
   - `apps/api/alembic/versions/*_create_raw_payload_model.py`
   - `apps/api/alembic/versions/*_create_ingestion_metrics_model.py`

### MODIFIED Files
1. **`apps/api/dealbrain_api/models/core.py`**
   - Extend Listing with 4 new columns + unique constraint
   - Extend ImportSession with 3 new columns
   - Add RawPayload model
   - Add IngestionMetric model

2. **`apps/api/dealbrain_api/settings.py`**
   - Add IngestionSettings class
   - Extend main Settings to include ingestion config

---

## Phase Scope Summary

Phase 1 establishes the **foundation for URL ingestion** by:

1. **Database Schema**: Extend Listing with marketplace-specific fields (vendor_item_id, marketplace, provenance, last_seen_at)
2. **Job Tracking**: Extend ImportSession to support URL imports (single & bulk)
3. **Schemas**: Define Pydantic contracts for request/response, normalized listing format
4. **Base Adapter**: Create abstract interface for all extraction adapters
5. **Configuration**: Add IngestionSettings with per-adapter toggles, timeouts, retries
6. **Debug Storage**: RawPayload table for storing raw adapter responses
7. **Telemetry**: IngestionMetric table for monitoring adapter health & latency
8. **Migrations**: Create & test all Alembic migrations

**No adapters implemented yet** (that's Phase 2). Phase 1 is purely foundational: schema, interfaces, config.

**Estimated Effort**: 55 hours over 1.4 weeks
**Target Completion**: ~2025-10-24 (end of week 1)

---

## Success Criteria

All of the following must be true for Phase 1 to be complete:

- [ ] All 8 foundation tasks completed (ID-001 through ID-008)
- [ ] Database schema extended: Listing has vendor_item_id, marketplace, provenance, last_seen_at
- [ ] ImportSession extended: has source_type, url, adapter_config
- [ ] RawPayload table created with index on (listing_id, adapter)
- [ ] IngestionMetric table created with telemetry columns
- [ ] Alembic migrations created, tested (upgrade + downgrade)
- [ ] Pydantic schemas defined (NormalizedListing, Ingestion Request/Response, Bulk variants)
- [ ] BaseAdapter abstract class defined with extract() method signature
- [ ] IngestionSettings configuration class added with per-adapter defaults
- [ ] All existing tests still pass
- [ ] New tests added for schema validation (pytest)
- [ ] No breaking changes to existing Excel import flow

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

## Phase 2 Preview

After Phase 1 completes, Phase 2 adds the actual extraction logic:
- eBay Browse API Adapter (35h)
- JSON-LD / Microdata Adapter (28h)
- Adapter Router (12h)
- Deduplication Service (18h)
- Normalizer / Enricher (20h)
- Event Emission (12h)
- Orchestration Service (10h)

**Phase 2 Dependencies**: All Phase 1 foundation must be complete, tested, and working.

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

## Next Steps (When Ready to Start Work)

1. **Start Task ID-001**: Read current Listing model structure, identify where to add columns
2. **Then Task ID-002**: Generate and test Alembic migration
3. **Parallel**: Create new files (schemas, base adapter)
4. **Then**: Extend ImportSession and create remaining models
5. **Final**: Add IngestionSettings configuration
6. **Validate**: Run tests, verify no breaking changes

Estimated time per task:
- ID-001: 1-2 sessions (6h)
- ID-002: 1 session (4h)
- ID-003: 1 session (6h)
- ID-004: 2 sessions (8h)
- ID-005: 1-2 sessions (7h)
- ID-006: 1 session (6h)
- ID-007: 1-2 sessions (8h)
- ID-008: 2 sessions (10h)

Total: ~8-10 focused work sessions to complete Phase 1 foundation.
