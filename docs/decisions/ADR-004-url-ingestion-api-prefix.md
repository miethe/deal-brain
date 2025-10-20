# ADR-004: URL Ingestion API Prefix Standardization

**Date:** 2025-10-20
**Status:** Accepted
**Decision Maker:** Lead Architect

## Context

The URL ingestion feature (Phases 1-4) was implemented with API endpoints under the prefix `/v1/ingest`, but the frontend and documentation expect endpoints at `/api/v1/ingest`. This mismatch causes 404 errors when the frontend attempts to POST to `/api/v1/ingest/single`.

### Current State

**Backend Implementation:**
- Router prefix: `/v1/ingest` (in `apps/api/dealbrain_api/api/ingestion.py`)
- Actual endpoints: `/v1/ingest/single`, `/v1/ingest/bulk`, etc.

**Frontend Expectation:**
- Documented paths: `/api/v1/ingest/single`, `/api/v1/ingest/{job_id}`, etc.
- Client code attempts to call `/api/v1/ingest/*` endpoints

### Existing Prefix Patterns in Codebase

Analysis of existing routers shows inconsistent prefix patterns:

**Group 1: `/v1/` prefix** (most common)
- `/v1/admin` (admin.py)
- `/v1/catalog` (catalog.py)
- `/v1/dashboard` (dashboard.py)
- `/v1/imports` (imports.py)
- `/v1/ingest` (ingestion.py - **current**)

**Group 2: `/api/v1/` prefix** (critical infrastructure)
- `/api/v1/baseline` (baseline.py)
- `/api/v1/health` (health.py)

**Group 3: No version prefix**
- `/entities` (entities.py)

## Problem Statement

The URL ingestion feature is non-functional in production due to the routing mismatch. The frontend cannot successfully invoke any ingestion endpoints because:

1. Frontend calls `/api/v1/ingest/single`
2. Backend only responds to `/v1/ingest/single`
3. Result: 404 Not Found

## Decision

**Change the ingestion router prefix from `/v1/ingest` to `/api/v1/ingest`.**

This aligns the backend implementation with:
- Frontend expectations
- Project documentation
- Critical infrastructure endpoints (health, baseline)

## Rationale

### Why `/api/v1/ingest` (Chosen Solution)

**Pros:**
- Matches frontend implementation and documentation
- Aligns with critical infrastructure endpoints (health, baseline)
- No frontend changes required
- Maintains API contract as documented in project plans
- Feature is not yet in production, so no breaking changes

**Cons:**
- Creates slight inconsistency with majority pattern (`/v1/`)
- Requires backend code change

### Why NOT `/v1/ingest` (Current State)

**Pros:**
- Matches majority of API endpoints
- Simpler prefix pattern

**Cons:**
- Breaks frontend expectations and documentation
- Requires updating frontend code and documentation
- Would require changing documented API paths in project plans
- Creates friction between documented contract and implementation

### Why NOT Standardize ALL Endpoints

While there is inconsistency across the codebase (`/v1/` vs `/api/v1/`), a full standardization effort is out of scope for this fix. Reasoning:
- Would require coordinating frontend + backend changes across many modules
- Risk of breaking existing integrations
- URL ingestion needs immediate remediation

**Recommendation for Future:** Create ADR-005 to standardize all API prefixes (suggest `/api/v1/` as standard).

## Implementation

**File to Modify:** `apps/api/dealbrain_api/api/ingestion.py`

**Change:**
```python
# Before
router = APIRouter(prefix="/v1/ingest", tags=["ingestion"])

# After
router = APIRouter(prefix="/api/v1/ingest", tags=["ingestion"])
```

**Impact:**
- All 4 ingestion endpoints will be accessible at `/api/v1/ingest/*`
- No database migrations required
- No service layer changes required
- No frontend changes required

**Endpoints After Fix:**
- `POST /api/v1/ingest/single` - Single URL import
- `GET /api/v1/ingest/{job_id}` - Import status polling
- `POST /api/v1/ingest/bulk` - Bulk URL upload
- `GET /api/v1/ingest/bulk/{bulk_job_id}` - Bulk progress

## Validation

**Test Plan:**
1. Apply the prefix change
2. Restart FastAPI server
3. Verify endpoint registration in OpenAPI docs (`/docs`)
4. Test POST to `/api/v1/ingest/single` returns 202 (not 404)
5. Verify frontend can successfully call all ingestion endpoints

## Consequences

**Immediate:**
- URL ingestion feature becomes functional
- Frontend and backend align on API paths
- 404 errors resolved

**Long-term:**
- Establishes precedent for `/api/v1/` prefix for new features
- Highlights need for prefix standardization across codebase
- Sets pattern for critical user-facing API endpoints

## Related Decisions

**Future ADR:** ADR-005 should address full API prefix standardization strategy across all routers.

**Pattern to Follow:** New API endpoints should use `/api/v1/` prefix to align with infrastructure endpoints and this decision.

## References

- Project Plan: `docs/project_plans/url-ingest/context/url-ingest-context.md`
- Frontend Implementation: `apps/web/app/admin/import/page.tsx`
- Backend Implementation: `apps/api/dealbrain_api/api/ingestion.py`
- Error Log: 404 Not Found for POST `/api/v1/ingest/single`
