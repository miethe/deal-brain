# Phase 4: Frontend & Testing - Progress Tracker

**Phase**: Phase 4 - Frontend & Testing
**Status**: In Progress 🔄
**Started**: 2025-10-19
**Completed**: TBD
**Estimated Effort**: ~110 hours
**Actual Effort**: TBD
**Efficiency**: TBD

---

## Task Status Overview

| ID | Task | Estimated | Status | Actual | Notes |
|----|------|-----------|--------|--------|-------|
| ID-022 | Frontend Import Component | 20h | ⏳ Pending | - | Single URL import UI with validation |
| ID-023 | Bulk Import UI Component | 18h | ⏳ Pending | - | CSV/JSON upload with progress tracking |
| ID-024 | Provenance Badge | 8h | ⏳ Pending | - | Visual indicators for URL-sourced listings |
| ID-025 | Admin Adapter Settings UI | 16h | ⏳ Pending | - | Configure adapter priority and overrides |
| ID-026 | Unit Tests - Adapters & Normalization | 20h | ⏳ Pending | - | Coverage >80% for core logic |
| ID-027 | Integration Tests - Job Lifecycle | 18h | ⏳ Pending | - | End-to-end workflow testing |
| ID-028 | E2E Tests - Happy Paths | 10h | ⏳ Pending | - | Critical user journey testing |

**Legend**: ⏳ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked

---

## Detailed Task Progress

### Task ID-022: Frontend Import Component (20h) ⏳

**Goal**: Create React component for single URL import with validation and status tracking

**Files**:
- `apps/web/components/ingestion/UrlImportForm.tsx` (NEW)
- `apps/web/components/ingestion/ImportStatusCard.tsx` (NEW)
- `apps/web/hooks/useUrlImport.ts` (NEW)
- `apps/web/app/(dashboard)/ingestion/page.tsx` (NEW)

**Requirements**:
- [ ] Create `UrlImportForm` component with URL input field
- [ ] Implement URL validation (format, required)
- [ ] Add priority selector (low, normal, high)
- [ ] Call `POST /api/v1/ingest/single` on submit
- [ ] Show loading state during submission
- [ ] Display success/error messages
- [ ] Create `ImportStatusCard` component for job status
- [ ] Poll `GET /api/v1/ingest/{job_id}` for status updates
- [ ] Display job states: queued, running, complete, partial, failed
- [ ] Show listing link when complete
- [ ] Display error messages when failed
- [ ] Implement `useUrlImport` React Query hook
- [ ] Add accessibility features (ARIA labels, keyboard navigation)
- [ ] Follow shadcn/ui design patterns
- [ ] Add comprehensive component tests

**Status**: ⏳ PENDING

**Actual Effort**: -

**Test Coverage**: Target 70% frontend coverage

**Dependencies**: Phase 3 API endpoints (ID-017 complete)

**Blockers**: None

---

### Task ID-023: Bulk Import UI Component (18h) ⏳

**Goal**: Create React component for bulk CSV/JSON upload with progress tracking

**Files**:
- `apps/web/components/ingestion/BulkImportForm.tsx` (NEW)
- `apps/web/components/ingestion/BulkImportProgress.tsx` (NEW)
- `apps/web/hooks/useBulkImport.ts` (NEW)
- `apps/web/app/(dashboard)/ingestion/bulk/page.tsx` (NEW)

**Requirements**:
- [ ] Create `BulkImportForm` component with file upload
- [ ] Support CSV and JSON file types
- [ ] Validate file size (<1000 URLs)
- [ ] Preview uploaded URLs before submission
- [ ] Call `POST /api/v1/ingest/bulk` with multipart/form-data
- [ ] Show upload progress indicator
- [ ] Create `BulkImportProgress` component
- [ ] Poll `GET /api/v1/ingest/bulk/{bulk_job_id}` for status
- [ ] Display progress metrics (total, complete, success, partial, failed)
- [ ] Show per-URL status in paginated table
- [ ] Implement pagination controls (offset, limit)
- [ ] Display listing links for successful imports
- [ ] Show error details for failed imports
- [ ] Add cancel/abort functionality (if supported)
- [ ] Implement `useBulkImport` React Query hook
- [ ] Add WCAG 2.1 AA compliant accessibility
- [ ] Add comprehensive component tests

**Status**: ⏳ PENDING

**Actual Effort**: -

**Test Coverage**: Target 70% frontend coverage

**Dependencies**: Phase 3 API endpoints (ID-018, ID-019 complete)

**Blockers**: None

---

### Task ID-024: Provenance Badge (8h) ⏳

**Goal**: Visual indicators showing URL-sourced listings with metadata

**Files**:
- `apps/web/components/listings/ProvenanceBadge.tsx` (NEW)
- `apps/web/components/listings/ListingCard.tsx` (MODIFIED)
- `apps/web/app/(dashboard)/listings/page.tsx` (MODIFIED)

**Requirements**:
- [ ] Create `ProvenanceBadge` component
- [ ] Display marketplace name (eBay, Mercari, etc.)
- [ ] Show source type icon (URL vs Excel)
- [ ] Include tooltip with metadata (vendor_item_id, last_seen_at)
- [ ] Add badge to listing cards
- [ ] Add badge to listing detail view
- [ ] Implement color coding by marketplace
- [ ] Ensure accessibility (screen reader support)
- [ ] Follow shadcn/ui badge patterns
- [ ] Add component tests

**Status**: ⏳ PENDING

**Actual Effort**: -

**Test Coverage**: Target 70% frontend coverage

**Dependencies**: Listing model includes provenance JSON field

**Blockers**: None

---

### Task ID-025: Admin Adapter Settings UI (16h) ⏳

**Goal**: Admin interface for configuring adapter priority and field overrides

**Files**:
- `apps/web/components/admin/AdapterSettingsForm.tsx` (NEW)
- `apps/web/components/admin/FieldMappingEditor.tsx` (NEW)
- `apps/web/hooks/useAdapterSettings.ts` (NEW)
- `apps/web/app/(dashboard)/admin/adapters/page.tsx` (NEW)

**Requirements**:
- [ ] Create `AdapterSettingsForm` component
- [ ] Display adapter priority order (drag-and-drop reorder)
- [ ] Enable/disable adapters per marketplace
- [ ] Create `FieldMappingEditor` component
- [ ] Configure field overrides per adapter
- [ ] Map adapter-specific field names to normalized schema
- [ ] Add validation rules editor
- [ ] Save settings to database (ApplicationSettings or new table)
- [ ] Implement `useAdapterSettings` React Query hook
- [ ] Add reset to defaults functionality
- [ ] Show preview of adapter behavior
- [ ] Add admin permission check
- [ ] Ensure WCAG 2.1 AA compliance
- [ ] Add comprehensive component tests

**Status**: ⏳ PENDING

**Actual Effort**: -

**Test Coverage**: Target 70% frontend coverage

**Dependencies**: Adapter system (Phase 1 complete)

**Blockers**: Need to define database schema for adapter settings

---

### Task ID-026: Unit Tests - Adapters & Normalization (20h) ⏳

**Goal**: Comprehensive unit tests for adapter and normalization logic

**Files**:
- `tests/test_ebay_adapter.py` (NEW)
- `tests/test_mercari_adapter.py` (NEW)
- `tests/test_facebook_adapter.py` (NEW)
- `tests/test_generic_adapter.py` (NEW)
- `tests/test_normalization_orchestrator.py` (NEW)

**Requirements**:
- [ ] Test eBay adapter HTML parsing edge cases
- [ ] Test Mercari adapter API response handling
- [ ] Test Facebook adapter structure extraction
- [ ] Test GenericAdapter fallback behavior
- [ ] Test normalizer orchestrator adapter selection
- [ ] Test field mapping and transformation logic
- [ ] Test validation error handling
- [ ] Test quality score calculation
- [ ] Test price extraction from various formats
- [ ] Test image URL extraction and validation
- [ ] Test condition string normalization
- [ ] Test malformed HTML handling
- [ ] Test missing field handling
- [ ] Test character encoding issues
- [ ] Mock HTTP responses for adapter tests
- [ ] Achieve >80% code coverage on adapters
- [ ] Document test scenarios and edge cases

**Status**: ⏳ PENDING

**Actual Effort**: -

**Test Coverage**: Target >80% backend coverage

**Dependencies**: Adapter implementations (Phase 1 complete)

**Blockers**: None

---

### Task ID-027: Integration Tests - Job Lifecycle (18h) ⏳

**Goal**: End-to-end integration tests for complete ingestion workflows

**Files**:
- `tests/integration/test_ingestion_lifecycle.py` (NEW)
- `tests/integration/test_bulk_import_lifecycle.py` (NEW)
- `tests/integration/test_deduplication_flow.py` (NEW)

**Requirements**:
- [ ] Test single URL import: submit → queue → fetch → parse → normalize → dedupe → upsert
- [ ] Test bulk import: upload → queue tasks → parallel execution → aggregation
- [ ] Test deduplication: existing listing found → price update → event emission
- [ ] Test new listing creation: no match → create with provenance
- [ ] Test error recovery: transient failure → retry → success
- [ ] Test permanent failure: bad URL → marked failed → no retry
- [ ] Test raw payload storage and cleanup
- [ ] Test ImportSession state transitions
- [ ] Test listing metrics recalculation on price update
- [ ] Test valuation rules applied to URL-sourced listings
- [ ] Use real database (not mocks) for integration tests
- [ ] Use Celery test worker (eager mode or real worker)
- [ ] Test concurrent job execution
- [ ] Test rate limiting (if implemented)
- [ ] Document integration test setup
- [ ] Achieve >80% coverage on integration paths

**Status**: ⏳ PENDING

**Actual Effort**: -

**Test Coverage**: Target >80% on integration workflows

**Dependencies**: All backend components (Phases 1-3 complete)

**Blockers**: None

---

### Task ID-028: E2E Tests - Happy Paths (10h) ⏳

**Goal**: End-to-end Playwright tests for critical user journeys

**Files**:
- `apps/web/e2e/single-url-import.spec.ts` (NEW)
- `apps/web/e2e/bulk-import.spec.ts` (NEW)
- `apps/web/e2e/provenance-display.spec.ts` (NEW)

**Requirements**:
- [ ] Test single URL import happy path:
  - [ ] Navigate to import page
  - [ ] Enter valid URL
  - [ ] Submit form
  - [ ] Verify success message
  - [ ] Poll status until complete
  - [ ] Verify listing link appears
  - [ ] Click through to listing detail
- [ ] Test bulk import happy path:
  - [ ] Navigate to bulk import page
  - [ ] Upload CSV file
  - [ ] Preview URLs
  - [ ] Submit bulk import
  - [ ] Verify progress tracking
  - [ ] Wait for completion
  - [ ] Verify success metrics
- [ ] Test provenance badge display:
  - [ ] Navigate to listings page
  - [ ] Verify URL-sourced listings show badges
  - [ ] Hover over badge for tooltip
  - [ ] Verify marketplace name and metadata
- [ ] Test error scenarios:
  - [ ] Invalid URL submission
  - [ ] File upload validation
- [ ] Test accessibility:
  - [ ] Keyboard navigation through forms
  - [ ] Screen reader compatibility
- [ ] Document E2E test setup and CI integration

**Status**: ⏳ PENDING

**Actual Effort**: -

**Test Coverage**: Critical user journeys covered

**Dependencies**: Frontend components (ID-022, ID-023, ID-024 complete)

**Blockers**: None

---

## Success Criteria (Phase 4)

- [ ] All 7 tasks (ID-022 through ID-028) completed
- [ ] Frontend components working and accessible
- [ ] Single URL import UI functional (submit, status, errors)
- [ ] Bulk import UI functional (upload, progress, results)
- [ ] Provenance badges displayed on listings
- [ ] Admin adapter settings UI functional
- [ ] All backend tests passing (unit + integration)
- [ ] All frontend tests passing (component + E2E)
- [ ] Test coverage >80% backend, >70% frontend
- [ ] WCAG 2.1 AA compliance verified
- [ ] Type checking passes (TypeScript + mypy)
- [ ] Linting passes (eslint + ruff)
- [ ] Documentation complete (component docs, API usage)
- [ ] Progress tracker updated
- [ ] Context document updated with learnings
- [ ] All commits pushed to branch

---

## Test Coverage Summary

| Component | Target | Actual | Tests | Status |
|-----------|--------|--------|-------|--------|
| Frontend Import Components | 70% | - | TBD | ⏳ |
| Backend Adapters | 80% | - | TBD | ⏳ |
| Backend Normalization | 80% | - | TBD | ⏳ |
| Integration Workflows | 80% | - | TBD | ⏳ |
| E2E Critical Paths | 100% | - | TBD | ⏳ |

**Total Phase 4 Tests**: TBD
**Overall Test Suite**: 67 passing (current baseline)

---

## Blockers & Risks

**Current Blockers**: None

**Identified Risks**:
1. **Frontend Testing Setup**: Playwright/Jest configuration may need updates
   - **Mitigation**: Start with component tests first, add E2E later
2. **Adapter Test Complexity**: Mocking HTTP responses for various marketplaces
   - **Mitigation**: Use fixtures with real HTML samples, document patterns
3. **Integration Test Performance**: Full workflow tests may be slow
   - **Mitigation**: Use database transactions, cleanup between tests
4. **WCAG Compliance**: Ensuring all components meet AA standards
   - **Mitigation**: Use automated tools (axe, lighthouse), manual testing

---

## Phase 4 Learnings

**Implementation Decisions**: TBD

**Technical Learnings**: TBD

**Performance Optimizations**: TBD

---

## Next Steps

**Immediate Priority**: Task ID-022 (Frontend Import Component)

**Recommended Approach**:
1. Start with ID-022 (single URL import UI) - foundational component
2. Add ID-024 (provenance badge) - small, high-value feature
3. Build ID-023 (bulk import UI) - builds on ID-022 patterns
4. Add ID-026 (backend unit tests) - parallel with frontend work
5. Add ID-027 (integration tests) - requires backend components
6. Build ID-025 (admin adapter settings) - lower priority, admin-only
7. Finish with ID-028 (E2E tests) - requires all components complete

---

## Current Branch & Commit

**Branch**: valuation-rules-enhance
**Last Commit**: 8d4ccd6 (Phase 3 complete)
**Started Phase 4**: 2025-10-19

---

**Last Updated**: 2025-10-19
