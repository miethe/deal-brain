# Phase 3: API & Integration - Progress Tracker

**Phase**: Phase 3 - API & Integration
**Status**: In Progress
**Started**: 2025-10-18
**Estimated Effort**: ~80 hours
**Target Completion**: ~2025-10-25

---

## Task Status Overview

| ID | Task | Estimated | Status | Actual | Notes |
|----|------|-----------|--------|--------|-------|
| ID-016 | Celery Ingestion Task | 16h | ✅ Complete | ~12h | 8 tests passing, commit 830b91e |
| ID-017 | Single URL Import Endpoint | 14h | ✅ Complete | ~10h | 14 tests passing, commit c22b69a |
| ID-018 | Bulk Import Endpoint | 18h | ⏳ Pending | - | POST /api/v1/ingest/bulk |
| ID-019 | Bulk Status Poll Endpoint | 12h | ⏳ Pending | - | GET /api/v1/ingest/bulk/:id |
| ID-020 | ListingsService Integration | 12h | ⏳ Pending | - | Wire to existing service |
| ID-021 | Raw Payload Cleanup | 8h | ⏳ Pending | - | TTL cleanup task |

**Legend**: ⏳ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked

---

## Detailed Task Progress

### Task ID-016: Celery Ingestion Task (16h) ✅

**Goal**: Create async Celery task for URL ingestion with retry logic

**Files**:
- `apps/api/dealbrain_api/tasks/ingestion.py` (NEW)
- `tests/test_ingestion_task.py` (NEW)

**Requirements**:
- [x] Create `@celery_app.task` decorator
- [x] Implement `ingest_url_task(job_id, url, adapter_config)`
- [x] Call `IngestionService.ingest_single_url()`
- [x] Update ImportSession status (queued → running → complete/partial/failed)
- [x] Store result: listing_id, provenance, quality, errors
- [x] Implement retry logic (3 retries with exponential backoff)
- [x] Add comprehensive error handling
- [x] Write unit tests for task (8 tests)
- [x] Write integration tests for task execution

**Status**: ✅ COMPLETE (commit 830b91e)

**Actual Effort**: ~12h (faster than estimate)

**Test Coverage**: 8 tests passing - success, transient retry, permanent failure, session updates

**Blockers**: None

---

### Task ID-017: Single URL Import Endpoint (14h) ✅

**Goal**: Create FastAPI endpoint for single URL ingestion

**Files**:
- `apps/api/dealbrain_api/api/ingestion.py` (NEW)
- `apps/api/dealbrain_api/api/__init__.py` (MODIFIED - router registration)
- `tests/test_ingestion_api.py` (NEW)

**Requirements**:
- [x] Implement `POST /api/v1/ingest/single`
- [x] Accept `IngestionRequest` schema (url, priority optional)
- [x] Validate URL format (http/https, valid domain)
- [x] Create ImportSession record with source_type='url_single'
- [x] Queue Celery task via `ingest_url_task.delay()`
- [x] Return 202 Accepted with job_id
- [x] Implement `GET /api/v1/ingest/{job_id}` status endpoint
- [x] Return full job status with listing details (listing_id, provenance, quality, errors)
- [x] Add comprehensive API tests (14 tests)

**Status**: ✅ COMPLETE (commit c22b69a)

**Actual Effort**: ~10h (faster than estimate)

**Test Coverage**: 14 tests passing covering:
- POST success with valid URL
- POST validation (invalid URL, missing URL, invalid priority)
- POST default priority handling
- ImportSession creation verification
- GET status for all job states (queued, running, complete, partial, failed)
- GET not found (404) and invalid UUID (422) handling
- Integration test (create -> retrieve workflow)

**Technical Implementation**:
- Async FastAPI endpoints with `session_dependency()` injection
- Proper HTTP status codes (202, 200, 404, 422, 500)
- Comprehensive error handling and logging
- Type hints throughout
- Follows Deal Brain patterns (async SQLAlchemy, Pydantic schemas)
- Black/ruff formatted

**Blockers**: None (was dependent on ID-016, now complete)

---

### Task ID-018: Bulk Import Endpoint (18h) ⏳

**Goal**: Create FastAPI endpoint for bulk URL ingestion

**Files**:
- `apps/api/dealbrain_api/api/ingestion.py` (continued)

**Requirements**:
- [ ] Implement `POST /api/v1/ingest/bulk`
- [ ] Accept `multipart/form-data` with CSV/JSON file
- [ ] Parse CSV (header: url) or JSON `[{url: ...}]`
- [ ] Validate: <1000 URLs per request
- [ ] Sanitize URLs
- [ ] Create parent ImportSession with `source_type=url_bulk`
- [ ] Create child ImportSession for each URL
- [ ] Queue Celery tasks with priority chain
- [ ] Return 202 with bulk_job_id and total_urls
- [ ] Add API tests for CSV and JSON upload

**Status**: Pending completion of ID-017

**Blockers**: Depends on ID-017 (single URL endpoint)

---

### Task ID-019: Bulk Status Poll Endpoint (12h) ⏳

**Goal**: Create endpoint to poll bulk import progress

**Files**:
- `apps/api/dealbrain_api/api/ingestion.py` (continued)

**Requirements**:
- [ ] Implement `GET /api/v1/ingest/bulk/{bulk_job_id}`
- [ ] Return parent job status
- [ ] Include child job statuses (per-URL)
- [ ] Show progress metrics (total, complete, success, partial, failed)
- [ ] Support pagination: `?offset=0&limit=100`
- [ ] Return per-row status: `[{url, status, listing_id, error}]`
- [ ] Add API tests for status polling

**Status**: Pending completion of ID-018

**Blockers**: Depends on ID-018 (bulk import endpoint)

---

### Task ID-020: ListingsService Integration (12h) ⏳

**Goal**: Wire IngestionService to existing ListingsService

**Files**:
- `apps/api/dealbrain_api/services/listings.py` (modify)

**Requirements**:
- [ ] Add `upsert_from_url(normalized_schema, dedupe_result)` method
- [ ] If dedupe match: update price, images, last_seen_at, last_modified_at
- [ ] Emit `price.changed` if threshold met
- [ ] If new: create Listing with provenance, vendor_item_id, marketplace
- [ ] Apply valuation rules (existing logic)
- [ ] Calculate metrics (existing logic)
- [ ] Ensure backward compatibility with Excel import flow
- [ ] Add unit tests for upsert logic

**Status**: Pending completion of ID-016

**Blockers**: None (can run in parallel with endpoints)

---

### Task ID-021: Raw Payload Cleanup (8h) ⏳

**Goal**: Implement TTL cleanup for raw payloads

**Files**:
- `apps/api/dealbrain_api/services/ingestion.py` (modify)
- `apps/api/dealbrain_api/tasks/ingestion.py` (modify)

**Requirements**:
- [ ] Create `RawPayloadService` class
- [ ] Implement `store_payload()` with 512KB limit
- [ ] Implement truncation logic for large payloads
- [ ] Create Celery periodic task for cleanup
- [ ] Delete payloads older than 30 days (configurable)
- [ ] Log cleanup operations
- [ ] Monitor storage usage
- [ ] Add tests for cleanup logic

**Status**: Pending completion of ID-020

**Blockers**: None (can run in parallel)

---

## Success Criteria (Phase 3)

- [ ] All 6 tasks (ID-016 through ID-021) completed
- [ ] Celery task implemented with retry logic
- [ ] Single URL endpoint working (POST + GET status)
- [ ] Bulk import endpoint working (POST + GET status)
- [ ] ListingsService integration complete
- [ ] Raw payload cleanup task implemented
- [ ] All tests passing (new + existing 242 tests)
- [ ] Test coverage >80% on new code
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] Database migrations applied (if any)
- [ ] Context document updated with learnings

---

## Test Coverage Goals

| Component | Target | Actual | Status |
|-----------|--------|--------|--------|
| Celery Task | 80% | - | ⏳ |
| API Endpoints | 90% | - | ⏳ |
| Service Integration | 85% | - | ⏳ |
| Cleanup Task | 80% | - | ⏳ |

---

## Blockers & Risks

**Current Blockers**: None

**Identified Risks**:
1. Celery configuration complexity - **Mitigation**: Use existing Celery setup patterns from valuation.py
2. Bulk import performance - **Mitigation**: Queue tasks with priority, implement batching
3. Raw payload storage growth - **Mitigation**: Implement TTL cleanup early, monitor storage

---

## Notes & Learnings

**Phase 3 Decisions**:
- Use existing Celery app configuration from `apps/api/dealbrain_api/tasks/__init__.py`
- Follow valuation task patterns for consistency
- Use 202 Accepted for async endpoints (REST best practice)
- Implement polling endpoints for job status (not webhooks in Phase 3)

**Next Steps**:
1. Start with ID-016 (Celery task) - foundation for all endpoints
2. Then ID-017 (single URL endpoint) - simplest API endpoint
3. Then ID-018 + ID-019 (bulk endpoints) - build on single URL pattern
4. ID-020 + ID-021 can run in parallel once foundation is complete

---

---

## Phase 3 Progress Summary

**Completed Tasks**: 2/6 (33%)
**Hours Spent**: ~22h / 80h estimated (28%)
**Ahead of Schedule**: Yes (tasks completed faster than estimates)

**Recent Completions**:
- 2025-10-19: Task ID-017 complete (c22b69a) - Single URL Import Endpoint
- 2025-10-19: Task ID-016 complete (830b91e) - Celery Ingestion Task

**Next Up**:
- Task ID-018: Bulk Import Endpoint (18h estimated)

---

**Last Updated**: 2025-10-19
