# URL Ingestion Fixes - October 22, 2025

## Status: ✅ PHASE 2 & 3 COMPLETE

## Summary

**Phase 2**: Implemented backend progress tracking for URL ingestion. The progress bar now reflects real backend status with updates at 5 milestones during the import process.

**Phase 3**: Fixed incomplete field population in URL ingestion by updating persistence layer and adding brand/model parsing. All 12 fields from adapters are now properly persisted to the database.

---

## Quick Start - Apply Migration

```bash
# From project root
poetry run alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade 0bfccac265c8 -> 0022, Add progress_pct to ImportSession
```

---

## What Was Fixed

### ✅ Progress Bar Issue (Phase 2)

**Before**: Progress bar was cosmetic, never completed, not tied to backend status

**After**: Progress bar now reflects real backend progress with 5 milestones:
- 10% - Job started
- 30% - Extraction started
- 60% - Normalization complete
- 80% - Persistence starting
- 100% - Import complete

**Implementation**:
- Added `progress_pct` field to `import_session` table
- Celery task updates progress at each milestone
- API returns `progress_pct` in response
- 3 new tests verify progress tracking

**Files Changed**:
1. Migration: `apps/api/alembic/versions/0022_add_progress_pct_to_import_session.py`
2. Model: `apps/api/dealbrain_api/models/core.py` (line 528)
3. Task: `apps/api/dealbrain_api/tasks/ingestion.py`
4. Schema: `packages/core/dealbrain_core/schemas/ingestion.py` (line 178)
5. API: `apps/api/dealbrain_api/api/ingestion.py` (line 544)
6. Tests: `tests/test_ingestion_task.py` (lines 841-1028)

**Test Results**: All 51 tests passing (17 task + 34 API)

---

## Manual Testing

```bash
# Start services
make up

# Import a URL
curl -X POST http://localhost:8000/api/v1/ingest/single \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.ebay.com/itm/266977653378"}'

# Poll status (watch progress_pct increase)
curl http://localhost:8000/api/v1/ingest/{job_id}

# Expected progression:
# 0% -> 10% -> 30% -> 60% -> 80% -> 100%
```

---

## ✅ Phase 3: Field Population Enhancement (COMPLETE)

Fixed incomplete field population in URL ingestion by updating the persistence layer and adding brand/model parsing logic.

### Problem

Previously only 7 of 12 fields were persisted:
- ✅ title, price, condition, seller, marketplace, vendor_item_id, dedup_hash
- ❌ images, cpu_model, ram_gb, storage_gb, description, manufacturer, model_number

### Solution

**1. Schema Updates** (`packages/core/dealbrain_core/schemas/ingestion.py`):
- Added `manufacturer` field (brand/manufacturer name)
- Added `model_number` field (product model number)

**2. Brand/Model Parsing** (`apps/api/dealbrain_api/services/ingestion.py`):
- New `_parse_brand_and_model()` method extracts brand/model from titles
- Supports common patterns: "Dell OptiPlex 7090", "Venus NAB9 by MINISFORUM"
- Handles 10+ common brands (Dell, HP, Lenovo, ASUS, Intel, AMD, etc.)
- Auto-strips trailing "Mini PC", "Desktop", "Computer", etc.

**3. CPU Lookup** (`apps/api/dealbrain_api/services/ingestion.py`):
- New `_find_cpu_by_model()` method with fuzzy matching
- Supports exact match (case-insensitive)
- Supports partial match (e.g., "i9-12900H" matches "Intel Core i9-12900H")
- Returns `None` if no match found

**4. Updated Persistence**:
- `_create_listing()` now persists ALL 12 fields
- `_update_listing()` updates all fields without data loss
- CPU lookup converts cpu_model to cpu_id foreign key
- Images stored in `attributes_json["images"]`
- Description stored in `notes` field
- RAM/storage stored in `ram_gb` and `primary_storage_gb`

### Field Mapping

| Adapter Field | Database Column | Notes |
|---------------|----------------|-------|
| `title` | `title` | Required |
| `price` | `price_usd` | Required, converted to USD |
| `condition` | `condition` | Required, normalized to enum |
| `marketplace` | `marketplace` | Required |
| `vendor_item_id` | `vendor_item_id` | Optional, for deduplication |
| `seller` | `seller` | Optional |
| `dedup_hash` | `dedup_hash` | Auto-generated |
| `cpu_model` | `cpu_id` | Lookup via `_find_cpu_by_model()` |
| `ram_gb` | `ram_gb` | Default to 0 if not provided |
| `storage_gb` | `primary_storage_gb` | Default to 0 if not provided |
| `description` | `notes` | Optional |
| `images` | `attributes_json["images"]` | Stored as JSON array |
| `manufacturer` | `manufacturer` | Parsed from title if not provided |
| `model_number` | `model_number` | Parsed from title if not provided |

### Tests

**New Test File**: `tests/test_ingestion_service.py` (16 tests)
- Field persistence tests (4 tests)
- CPU lookup tests (7 tests)
- Brand/model parsing tests (5 tests)

**Results**:
- ✅ 16/16 new tests passing
- ✅ 24/24 existing tests passing (no regressions)

**Files Changed**:
1. Schema: `packages/core/dealbrain_core/schemas/ingestion.py`
2. Service: `apps/api/dealbrain_api/services/ingestion.py`
3. Tests: `tests/test_ingestion_service.py` (NEW)

---

## Documentation

- **Phase 2 Implementation**: `docs/project_plans/url-ingest/progress/phase2-implementation-summary.md`
- **Phase 1 Investigation**: `docs/project_plans/url-ingest/progress/phase1-investigation-findings.md`

---

## Next Steps

### Phase 4: Frontend Integration (Recommended)

Update import UI to consume real progress data:
1. Modify polling logic in `/apps/web/app/dashboard/import/page.tsx`
2. Replace fake progress with backend `progress_pct` values
3. Test with real URLs

### Phase 5: Future Enhancements

**Expand Brand Patterns**:
- Add more manufacturer patterns as needed
- Support international brands

**Improve CPU Matching**:
- Add fuzzy string matching (Levenshtein distance)
- Support CPU aliases (e.g., "i7 12th gen" → "i7-12700")

**Field Validation**:
- Add min/max constraints for RAM/storage
- Validate image URLs are accessible

**Performance Metrics**:
- Track field population rates in IngestionMetric table
- Add telemetry for brand/model parsing success rate