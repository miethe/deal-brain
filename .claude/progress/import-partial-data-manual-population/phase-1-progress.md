# Phase 1 Progress: Backend Schema & Database Changes

**Phase**: 1 of 6
**Duration Estimate**: 2-3 days
**Status**: Not Started
**Owner**: `python-backend-engineer` + `data-layer-expert`

---

## Phase 1 Overview

Enable partial data extraction by making price optional in both Pydantic schemas and database schema, establishing quality tracking, and updating adapter validation logic.

---

## Tasks

### Task 1.1: Update NormalizedListingSchema
**Status**: ⏳ Not Started
**Owner**: `python-backend-engineer`
**File**: `packages/core/dealbrain_core/schemas/ingestion.py`

**Requirements**:
- [x] Schema already has `price: Decimal | None` ✅
- [ ] Update `validate_minimum_data()` to only require `title`
- [ ] Add `quality: str` field (pattern: "full" | "partial")
- [ ] Add `extraction_metadata: dict[str, str]` field
- [ ] Add `missing_fields: list[str]` field
- [ ] Write unit tests for validation logic

**Acceptance Criteria**:
- Schema validates with `price=None` without raising error
- `validate_minimum_data()` passes with only title present
- `quality` defaults to "full", accepts "partial"
- Unit tests cover all validation scenarios

---

### Task 1.2: Database Migration
**Status**: ⏳ Not Started
**Owner**: `data-layer-expert`
**File**: `apps/api/alembic/versions/0022_partial_import_support.py`

**Requirements**:
- [ ] Make `listings.price_usd` nullable
- [ ] Add `listings.quality` column (String(20), default='full')
- [ ] Add `listings.extraction_metadata` column (JSON, default={})
- [ ] Add `listings.missing_fields` column (JSON, default=[])
- [ ] Test migration in dev environment
- [ ] Test migration in staging environment
- [ ] Verify rollback strategy

**Acceptance Criteria**:
- Migration applies cleanly in dev and staging
- Existing listings get `quality='full'` by default
- NULL price allowed but existing data preserved
- Downgrade migration documented (requires cleanup)

**Notes**:
- ⚠️ This migration is **irreversible** if partial imports exist
- Backup database before applying in production
- Document cleanup script for downgrade scenario

---

### Task 1.3: Update BaseAdapter Validation
**Status**: ⏳ Not Started
**Owner**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/adapters/base.py`

**Requirements**:
- [ ] Update `_validate_response()` to only require title
- [ ] Remove price requirement from validation
- [ ] Log warning when price is missing
- [ ] Track extracted fields in metadata
- [ ] Update error messages to distinguish partial vs. failed
- [ ] Update all adapter subclasses (eBay, JSON-LD, Amazon)

**Acceptance Criteria**:
- Adapter succeeds with `title` present, `price=None`
- Warning logged: "No price extracted - import will be partial"
- Extracted fields tracked in response metadata
- Adapters no longer fail on missing price

---

### Task 1.4: Update ListingsService
**Status**: ⏳ Not Started
**Owner**: `python-backend-engineer`
**File**: `apps/api/dealbrain_api/services/listings.py`

**Requirements**:
- [ ] Modify `create_from_ingestion()` to accept `price=None`
- [ ] Skip metrics calculation when price is NULL
- [ ] Store quality ("full" vs "partial") based on price presence
- [ ] Store extraction_metadata and missing_fields
- [ ] Update type hints to reflect optional price
- [ ] Write integration tests

**Acceptance Criteria**:
- Service creates listing with `price_usd=None`
- `adjusted_price_usd` remains NULL when price is NULL
- `valuation_breakdown` is NULL for partial imports
- Quality field correctly set to "partial"

---

## Progress Summary

| Task | Status | Owner | Blocker |
|------|--------|-------|---------|
| 1.1: Update Schema | ⏳ Not Started | python-backend-engineer | None |
| 1.2: Database Migration | ⏳ Not Started | data-layer-expert | None |
| 1.3: Update Adapters | ⏳ Not Started | python-backend-engineer | Needs Task 1.1 |
| 1.4: Update Service | ⏳ Not Started | python-backend-engineer | Needs Task 1.1, 1.2 |

---

## Blockers

None currently.

---

## Next Steps

1. **python-backend-engineer**: Start Task 1.1 (schema updates)
2. **data-layer-expert**: Start Task 1.2 (migration) in parallel
3. Once 1.1 complete: Begin Task 1.3 (adapter updates)
4. Once 1.1 and 1.2 complete: Begin Task 1.4 (service updates)

---

## Notes

- Task 1.1 and 1.2 can run in parallel (no dependencies)
- Task 1.3 depends on Task 1.1 completion
- Task 1.4 depends on both 1.1 and 1.2 completion
- All Phase 1 tasks must complete before Phase 2 can begin

---

**Last Updated**: 2025-11-08
**Phase Target Completion**: TBD
