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
| ID-016 | Celery Ingestion Task | 16h | 🔄 In Progress | - | Creating async task |
| ID-017 | Single URL Import Endpoint | 14h | ⏳ Pending | - | POST /api/v1/ingest/single |
| ID-018 | Bulk Import Endpoint | 18h | ⏳ Pending | - | POST /api/v1/ingest/bulk |
| ID-019 | Bulk Status Poll Endpoint | 12h | ⏳ Pending | - | GET /api/v1/ingest/bulk/:id |
| ID-020 | ListingsService Integration | 12h | ⏳ Pending | - | Wire to existing service |
| ID-021 | Raw Payload Cleanup | 8h | ⏳ Pending | - | TTL cleanup task |

**Legend**: ⏳ Pending | 🔄 In Progress | ✅ Complete | ❌ Blocked

---

## Detailed Task Progress

### Task ID-016: Celery Ingestion Task (16h) 🔄

**Goal**: Create async Celery task for URL ingestion with retry logic

**Files**:
- `apps/api/dealbrain_api/tasks/ingestion.py` (new)

**Requirements**:
- [x] Create `@celery_app.task` decorator
- [ ] Implement `ingest_url_task(job_id, url, adapter_config)`
- [ ] Call `IngestionService.ingest_single_url()`
- [ ] Update ImportSession status (queued → running → complete/partial/failed)
- [ ] Store result: listing_id, provenance, quality, errors
- [ ] Implement retry logic (3 retries with exponential backoff)
- [ ] Add comprehensive error handling
- [ ] Write unit tests for task
- [ ] Write integration tests for task execution

**Status**: Starting implementation

**Blockers**: None

---

### Task ID-017: Single URL Import Endpoint (14h) ⏳

**Goal**: Create FastAPI endpoint for single URL ingestion

**Files**:
- `apps/api/dealbrain_api/api/ingestion.py` (new)

**Requirements**:
- [ ] Implement `POST /api/v1/ingest/single`
- [ ] Accept `IngestionRequest` schema (url, priority optional)
- [ ] Validate URL format (http/https, valid domain)
- [ ] Create ImportSession record
- [ ] Queue Celery task
- [ ] Return 202 Accepted with job_id
- [ ] Implement `GET /api/v1/ingest/{job_id}` status endpoint
- [ ] Return full job status with listing details
- [ ] Add API tests

**Status**: Pending completion of ID-016

**Blockers**: Depends on ID-016 (Celery task)

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

**Last Updated**: 2025-10-18
