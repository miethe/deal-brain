---
title: "URL Import Enhancement: Partial Data Extraction & Manual Field Population"
description: "Enable partial data extraction from URLs with manual field population. Accept imports with title only (price optional), store in database with provenance tracking, and provide real-time modal UI for completing missing fields."
audience: [ai-agents, developers, pm]
tags:
  - import
  - ingestion
  - partial-data
  - manual-population
  - real-time-updates
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: accepted
related:
  - /docs/project_plans/import-partial-data-manual-population/implementation-plan.md
  - /docs/project_plans/import-partial-data-manual-population/phase-1-backend-schema-database.md
  - /docs/project_plans/import-partial-data-manual-population/phase-2-backend-api-services.md
  - /docs/project_plans/import-partial-data-manual-population/phase-3-frontend-manual-population.md
  - /docs/project_plans/import-partial-data-manual-population/phase-4-frontend-realtime-updates.md
  - /docs/project_plans/import-partial-data-manual-population/phase-5-integration-testing.md
  - /docs/project_plans/requests/completed/listings-enhancements-v3.md
---

# URL Import Enhancement: Partial Data Extraction & Manual Field Population

## Problem Statement

Current import pipeline uses all-or-nothing validation: if price extraction fails, entire import fails and extracted data (title, images, specs) is lost. This results in ~30% success rate for Amazon/similar sources.

**Technical constraints:**
- `NormalizedListingSchema` has `price: Decimal | None` but validation rejects null prices
- `BaseAdapter._validate_response()` requires both title AND price
- Database `listings.price_usd` is NOT NULL, blocking partial data storage
- No UI mechanism to capture missing fields post-import
- No real-time feedback without page refresh

**Result**: 60-70% of Amazon imports fail; users manually re-enter listings (5-10 min vs. 30 sec URL import).

---

## Solution Overview

Enable partial imports with minimum viable data (title only, price optional). Store partial listings in database with quality tracking and extraction provenance. Provide real-time modal UI for immediately completing missing fields. Deploy immediately when Phase 5 integration testing passes.

**Key capabilities:**
- Accept imports with title only
- Store partial listings with `quality="partial"` flag
- Track extraction provenance (which fields extracted vs. manual)
- Real-time modal UI for field completion
- Live progress updates without page refresh

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Import Success Rate | ~30% | 80%+ |
| Partial Import Rate | 0% | 15-25% |
| Manual Completion Rate | N/A | 70%+ |
| Time to Import | 5-10 min | 30-60 sec |
| Amazon Success Rate | ~20% | 70%+ |
| Data Quality Score | ~85% | 90%+ |

---

## User Stories

### Story 1: Partial Import with Manual Completion

User imports from Amazon with price extraction failure. Import succeeds with title + specs. Modal auto-opens with extracted fields (read-only) and price field (editable). User enters price, clicks save. Listing appears in grid immediately with quality indicator.

**Flow**:
```
URL → Adapter extraction (Title: "Dell OptiPlex 7090", Images: [3], CPU: i5-10500, Price: null)
  → Import succeeds with quality="partial", listing_id=123 created
  → Modal opens: "Complete 1 missing field"
  → User enters price $299.99
  → PATCH /api/v1/listings/123/complete
  → Modal closes, listing appears in grid
```

### Story 2: Real-Time Import Status

User uploads 5 URLs via bulk import. Sees progress indicator "Processing 2 of 5..." without refresh. Each URL completion triggers grid update and toast notification with action button for partial imports.

**Flow**:
```
Bulk Upload (5 URLs) → POST /api/v1/ingest/bulk → bulk_job_id=abc-123
  → Frontend polls GET /api/v1/ingest/bulk/abc-123/status every 2 seconds
  → Import 1 completes (full) → Grid updates, toast shows result
  → Import 2 completes (partial) → Toast with [Complete] button
  → User clicks [Complete] → PartialImportModal opens with extracted data
  → Imports 3-5 complete in parallel
```

### Story 3: Abandoned Partial Import Recovery

User closes modal after partial import without completing. Listing remains in database. User can return to dashboard and click "Complete" to reopen modal with original extracted data. No data loss.

---

## Technical Requirements

### Phase 1: Backend - Partial Extraction Support

Reference implementation: `/docs/project_plans/import-partial-data-manual-population/phase-1-backend-schema-database.md`

**Duration**: 2-3 days

**Critical changes:**
1. Update `NormalizedListingSchema` validator to accept null price, require title only
2. Add `quality` field ("full" vs. "partial") and `extraction_metadata` dict for provenance tracking
3. Update adapter validation to not require price; log warning if missing
4. Database migration: Make `listings.price_usd` nullable
5. Add `quality`, `extraction_metadata`, `missing_fields` columns to Listing model
6. ListingsService: Create listings without price, defer metrics calculation until price provided
7. New PATCH endpoint: `/api/v1/listings/{listing_id}/complete` for completing partial imports

**Key decision**: Nullable price in database is irreversible once partial imports exist. Deploy to staging first for validation.

### Phase 2: Backend - Real-Time Status Updates

Reference implementation: `/docs/project_plans/import-partial-data-manual-population/phase-2-backend-api-services.md`

**Duration**: 1-2 days

**Changes:**
1. New endpoint: `GET /api/v1/ingest/bulk/{bulk_job_id}/status` with pagination
2. Add `bulk_job_id`, `quality`, `listing_id`, `completed_at` fields to ImportSession model
3. Service method to aggregate status: total, queued, running, complete, partial, failed counts
4. Return per-URL status for UI display (title, marketplace, status, quality)

### Phase 3: Frontend - Manual Population Modal

Reference implementation: `/docs/project_plans/import-partial-data-manual-population/phase-3-frontend-manual-population.md`

**Duration**: 2-3 days

**Components:**
1. PartialImportModal: Dialog with extracted fields (read-only) and missing fields form (editable)
2. usePartialImportCompletion hook: Form state, validation, mutation to PATCH endpoint
3. Integration with import flow: Auto-open modal when quality="partial" in response
4. Accessibility: ARIA labels, keyboard navigation, screen reader support

**Features:**
- Auto-open when partial import completes
- Real-time validation (price must be positive number)
- Form data preserved if user closes modal (retry-friendly)
- Success toast on completion

### Phase 4: Frontend - Real-Time UI Updates

Reference implementation: `/docs/project_plans/import-partial-data-manual-population/phase-4-frontend-realtime-updates.md`

**Duration**: 2-3 days

**Components:**
1. useImportStatus hook: Poll status endpoint every 2 seconds, stop when all complete
2. BulkImportProgress indicator: Progress bar with counts (complete, partial, failed)
3. ImportToasts: Per-URL toast notifications with action buttons
4. ImportResultsGrid: Subscribe to import-complete events, update listings without refresh

**Features:**
- 2-second poll interval for real-time status
- Separate toasts for full (success), partial (warning), failed (error) imports
- Toast actions: "View" (full), "Complete" (partial), "Retry" (failed)
- Auto-dismiss after 5 seconds
- Progress indicator updates as each URL completes

### Phase 5: Integration Testing

Reference implementation: `/docs/project_plans/import-partial-data-manual-population/phase-5-integration-testing.md`

**Duration**: 1-2 days

**Test coverage:**
- Schema validation (null price allowed, title required)
- Listing creation without price (database constraints)
- Partial import completion flow (PATCH endpoint)
- Bulk job status polling (pagination, accuracy)
- Modal auto-open on partial import response
- Real-time grid updates without refresh
- Error handling (network failures, validation errors)
- Edge cases: no title extracted, invalid price format, abandoned modals

See phase-5 doc for detailed test scenarios and code examples.

---

## Edge Cases & Error Handling

**No Title Extracted**: Validation fails. Import fails with error. No partial listing created. User sees message: "Could not extract listing information."

**Invalid Price Format**: Parsing fails, `price=None`, `extraction_metadata["price"]="parse_failed"`. Import succeeds as partial. User completes via modal.

**User Abandons Modal**: Listing remains in database with `quality="partial"`, `price_usd=NULL`. Data persists. User can complete later by reopening modal.

**Duplicate Detection**: Deduplication runs on `dedup_hash`. If duplicate found, still creates import (user may want multiple versions). Shows warning in UI (future enhancement).

**Network Error During Completion**: Mutation fails, React Query retries (3 attempts). Error toast shown. Form data preserved in modal. User can retry.

---

## Data Model Changes

**New Listing fields:**
- `quality: str` ("full" | "partial") - completeness indicator
- `extraction_metadata: dict[str, str]` - provenance tracking {field_name: "extracted"|"manual"|"failed"}
- `missing_fields: list[str]` - fields expected but missing, guides UI

**New ImportSession fields:**
- `bulk_job_id: str` - links related imports in bulk operation
- `quality: str` - mirrors listing quality
- `listing_id: int` - references created listing
- `completed_at: datetime` - when import completed

---

## API Contracts

**PATCH /api/v1/listings/{listing_id}/complete**

Request:
```json
{
  "price": 299.99,
  "condition": "refurb"  // optional
}
```

Response: Updated ListingSchema with recalculated metrics.

**GET /api/v1/ingest/bulk/{bulk_job_id}/status?offset=0&limit=20**

Response:
```json
{
  "bulk_job_id": "abc-123",
  "total_urls": 5,
  "queued": 0,
  "running": 1,
  "completed": 4,
  "success": 3,
  "partial": 1,
  "failed": 0,
  "per_row_status": [
    {
      "url": "https://amazon.com/...",
      "title": "Dell OptiPlex 7090",
      "marketplace": "amazon",
      "status": "complete",
      "quality": "full",
      "listing_id": 123,
      "created_at": "2025-11-08T15:30:00Z"
    }
  ]
}
```

---

## Deployment

Deploy immediately when Phase 5 (Integration & Testing) passes. No feature flags, no phased rollout. Full functionality enabled by default.

**Pre-deployment validation:**
- All tests passing
- Migration tested in staging
- Metrics calculation verified on partial→full transitions
- UI accessibility verified (WCAG AA)

---

## Future Enhancements

1. **Incomplete Imports Dashboard**: Show "Incomplete Imports" section with count badge, filtering, bulk completion
2. **Field-Specific Warnings**: Show data quality warnings in grid (missing price, low-confidence CPU match)
3. **Smart Field Suggestions**: Auto-populate missing fields based on title parsing, marketplace catalog lookup
4. **Partial Import Analytics**: Track completion rates by marketplace, field type, user segment
5. **Manual Listing Template**: Pre-fill form with common defaults for manual-only workflows
6. **Batch Completion**: Complete multiple partial imports in single operation
