# ADR-002: Backend Entity Detail Endpoints

**Date:** 2025-10-26
**Status:** Accepted
**Context:** Phase 3, TASK-012 - Verify Backend Entity Endpoints
**Decision Maker:** Lead Architect

---

## Context

The frontend needs entity detail pages for CPU, GPU, RAM Spec, and Storage Profile entities. Currently, clicking entity links results in 404 errors because catalog detail pages don't exist. Before building frontend catalog pages, we must ensure backend API endpoints exist to serve entity data.

## Decision

Create RESTful entity detail endpoints following Deal Brain's layered architecture, async SQLAlchemy patterns, and Pydantic schema validation.

### Endpoint Design

**Required Endpoints:**
```
GET /v1/cpus/{id}              → CPURead schema
GET /v1/gpus/{id}              → GPURead schema
GET /v1/ram-specs/{id}         → RAMSpecRead schema
GET /v1/storage-profiles/{id}  → StorageProfileRead schema
```

**Optional "Used In" Endpoints:**
```
GET /v1/cpus/{id}/listings              → List[ListingRead]
GET /v1/gpus/{id}/listings              → List[ListingRead]
GET /v1/ram-specs/{id}/listings         → List[ListingRead]
GET /v1/storage-profiles/{id}/listings  → List[ListingRead]
```

**Rationale:**
- Follows Deal Brain's existing `/v1/` API versioning pattern
- RESTful resource naming (plural nouns: `/cpus/`, not `/cpu/`)
- Relationship endpoints enable "Used in" sections on entity detail pages
- Consistent with existing `/v1/listings/{id}` pattern

**Alternative Considered:** Generic `/v1/entities/{type}/{id}` endpoint
**Rejected Because:**
- Less type-safe (dynamic type parameter)
- Harder to document (single endpoint with variable response schemas)
- Non-standard REST pattern
- Complicates OpenAPI schema generation

### Backend Architecture

**File Structure:**
```
apps/api/dealbrain_api/api/
├── cpus.py              # CPU router (APIRouter)
├── gpus.py              # GPU router (APIRouter)
├── ram_specs.py         # RAM spec router (APIRouter)
├── storage_profiles.py  # Storage profile router (APIRouter)
```

**Optional Service Layer:**
```
apps/api/dealbrain_api/services/
├── catalog.py  # Shared entity catalog operations (if needed)
```

**Implementation Pattern:**
```python
# apps/api/dealbrain_api/api/cpus.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import session_dependency
from ..models import CPU, Listing
from dealbrain_core.schemas import CPURead, ListingRead

router = APIRouter(prefix="/v1/cpus", tags=["cpus"])

@router.get("/{cpu_id}", response_model=CPURead)
async def get_cpu(
    cpu_id: int,
    session: AsyncSession = Depends(session_dependency)
):
    """Get CPU details by ID."""
    cpu = await session.get(CPU, cpu_id)
    if not cpu:
        raise HTTPException(status_code=404, detail="CPU not found")
    return CPURead.model_validate(cpu)

@router.get("/{cpu_id}/listings", response_model=list[ListingRead])
async def get_cpu_listings(
    cpu_id: int,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(session_dependency)
):
    """Get all listings using this CPU."""
    # Verify CPU exists
    cpu = await session.get(CPU, cpu_id)
    if not cpu:
        raise HTTPException(status_code=404, detail="CPU not found")

    # Query listings
    query = (
        select(Listing)
        .where(Listing.cpu_id == cpu_id)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    listings = result.scalars().all()

    return [ListingRead.model_validate(listing) for listing in listings]
```

**Rationale:**
- Follows Deal Brain's layered architecture: API Routes → Domain Logic → Database
- Async SQLAlchemy with `session_dependency` for performance
- Proper 404 handling for missing entities
- Pydantic schema validation for type safety
- Pagination support for "Used in" endpoints (prevents large payloads)

### Schema Design

**Schema Location:**
```python
# packages/core/dealbrain_core/schemas/cpu.py
from pydantic import BaseModel

class CPURead(BaseModel):
    id: int
    model: str
    manufacturer: str
    cores: int
    threads: int
    base_clock_ghz: float
    boost_clock_ghz: float | None
    tdp_watts: int | None
    cpu_mark: int | None
    single_thread_rating: int | None
    igpu_mark: int | None
    generation: str | None

    model_config = {"from_attributes": True}
```

**Rationale:**
- Schemas live in `packages/core` for reuse across API and CLI
- Follow existing Deal Brain schema patterns
- Pydantic v2 for validation and serialization
- Proper typing with optional fields (`| None`)
- `from_attributes=True` enables SQLAlchemy model validation

**Schema Reuse:**
If schemas already exist in `dealbrain_core.schemas`, reuse them. If not, create them following this pattern.

### Performance Requirements

**Target:** < 200ms response time for entity detail endpoints

**Optimizations:**
1. Ensure primary key indexes on entity tables (likely already exist)
2. For "Used in" endpoints, verify composite indexes on `listing.cpu_id`, `listing.gpu_id`, etc.
3. Use pagination (`limit`, `offset`) for "Used in" endpoints to prevent large payloads
4. Return only necessary fields (don't over-fetch)

**Index Verification:**
```sql
-- Verify indexes exist (run in DB if needed)
SHOW INDEX FROM cpus WHERE Key_name = 'PRIMARY';
SHOW INDEX FROM listings WHERE Column_name = 'cpu_id';
```

**Pagination Pattern:**
```python
@router.get("/{cpu_id}/listings")
async def get_cpu_listings(
    cpu_id: int,
    limit: int = 50,  # Default 50 results
    offset: int = 0,  # Pagination offset
    session: AsyncSession = Depends(session_dependency)
):
    query = select(Listing).where(Listing.cpu_id == cpu_id).limit(limit).offset(offset)
    result = await session.execute(query)
    listings = result.scalars().all()
    return [ListingRead.model_validate(l) for l in listings]
```

**Rationale:**
- < 200ms ensures snappy UI interactions
- Pagination prevents overwhelming frontend with hundreds of listings
- Indexes ensure fast foreign key lookups

### Router Registration

**Ensure routers are registered in main FastAPI app:**

```python
# apps/api/dealbrain_api/main.py (or similar app initialization file)
from .api import cpus, gpus, ram_specs, storage_profiles

app.include_router(cpus.router)
app.include_router(gpus.router)
app.include_router(ram_specs.router)
app.include_router(storage_profiles.router)
```

**Rationale:**
- FastAPI requires explicit router registration
- Routers won't be accessible without `include_router` calls

## Consequences

### Positive

- Frontend can build entity catalog pages without 404 errors
- Consistent RESTful API design
- Proper async SQLAlchemy usage ensures performance
- Pagination prevents large payload issues
- OpenAPI documentation auto-generated by FastAPI
- Type-safe schemas prevent runtime errors

### Negative

- Requires backend work before frontend entity pages can be built
- "Used in" endpoints add complexity (optional, can defer to Phase 4)
- Must ensure all routers are registered in main app

### Neutral

- May discover missing indexes during performance testing
- Schemas may need adjustments based on frontend needs

## Implementation Tasks

**Delegation to `python-backend-engineer`:**

1. **Verify Existing Endpoints:**
   - Check if `/v1/cpus/{id}`, `/v1/gpus/{id}`, etc. already exist
   - Use Bash to grep for existing routers: `grep -r "cpus.router" apps/api/`

2. **Create Missing Endpoints:**
   - Create router files following pattern above
   - Implement GET `/{id}` endpoint for each entity type
   - Implement GET `/{id}/listings` endpoints (optional, lower priority)

3. **Register Routers:**
   - Add `include_router` calls to main FastAPI app
   - Verify in FastAPI interactive docs (`/docs`) that endpoints appear

4. **Testing:**
   - Manually test endpoints return 200 status
   - Test 404 handling for non-existent IDs
   - Verify response schemas match TypeScript types
   - Benchmark response time (should be < 200ms)

## Acceptance Criteria

- [ ] All required entity endpoints return 200 status for valid IDs
- [ ] Endpoints return proper 404 status for invalid IDs
- [ ] Response schemas match TypeScript frontend types
- [ ] Performance is acceptable (< 200ms per request)
- [ ] Routers are registered in main FastAPI app
- [ ] Endpoints appear in FastAPI interactive docs (`/docs`)
- [ ] No TypeScript or Python linting errors

## Related Documents

- **PRD:** `docs/project_plans/listings-facelift-enhancement/enhance-v2/prd-listings-facelift-v2.md` (FR-7)
- **Implementation Plan:** `docs/project_plans/listings-facelift-enhancement/enhance-v2/implementation-plan-v2-ph3-4.md` (TASK-012)
- **FastAPI Docs:** https://fastapi.tiangolo.com/tutorial/bigger-applications/
- **SQLAlchemy Async Docs:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

## Review Notes

- Approved by: Lead Architect
- Delegated to: `python-backend-engineer` subagent for implementation
- Priority: High (blocks TASK-013-016 frontend entity pages)
- Estimated Duration: 2-3 hours
