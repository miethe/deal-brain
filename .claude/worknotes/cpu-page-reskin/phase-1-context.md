# CPU Page Reskin - Phase 1 Context & Implementation Notes

**Project:** CPU Catalog Page Reskin
**Phase:** 1 - Backend Foundation
**Created:** 2025-11-05
**Status:** Architecture Review Complete

---

## Architectural Decisions Made

### 1. Database Schema Strategy

**Decision:** Store analytics fields directly on CPU table (denormalized approach)

**Rationale:**
- Simplifies queries - single table read for CPU + analytics
- Aligns with existing Deal Brain pattern (Listing model stores `valuation_breakdown` JSON)
- Eliminates JOIN overhead for most common queries
- Easier cache invalidation (single row update)
- Single source of truth for CPU data

**Trade-offs:**
- CPU table grows wider (12 new columns)
- Some data duplication vs. normalized analytics table
- **Accepted:** Performance and simplicity benefits outweigh normalization concerns

**Alternative Rejected:** Separate `cpu_analytics` table with 1:1 relationship
- Would require JOINs on every query
- More complex cache invalidation
- Additional model and schema management overhead

**Implementation:**
- Add 12 new columns to CPU table via Alembic migration
- Add 5 new indexes for query performance
- Use `nullable=True` for all analytics fields (data may not exist initially)
- Add `updated_at` timestamps to track freshness

---

### 2. Analytics Calculation Architecture

**Decision:** Dedicated `CPUAnalyticsService` class following existing service layer patterns

**Rationale:**
- Aligns with Deal Brain layered architecture: API Routes → Services → Domain Logic
- Follows existing patterns in `listings.py`, `component_catalog.py`, `rules.py`
- Centralizes calculation logic for reusability (Celery tasks + API endpoints)
- Enables comprehensive logging and error handling
- Facilitates unit testing

**Service Layer Design:**
```python
# Location: apps/api/dealbrain_api/services/cpu_analytics.py

class CPUAnalyticsService:
    """
    Service for calculating and persisting CPU analytics data.

    Responsibilities:
    - Calculate price targets from listing data (mean ± stddev)
    - Calculate performance value metrics ($/PassMark)
    - Update CPU table with calculated analytics
    - Batch process all CPUs for nightly recalculation
    - Handle edge cases and error scenarios
    """

    async def calculate_price_targets(
        self, session: AsyncSession, cpu_id: int
    ) -> PriceTarget:
        """Calculate price target ranges from active listings."""
        # Query all ACTIVE listings with this CPU
        # Extract adjusted_price values
        # Calculate mean, stddev, confidence
        # Exclude outliers (> 3 stddev)
        # Return PriceTarget schema

    async def calculate_performance_value(
        self, session: AsyncSession, cpu_id: int
    ) -> PerformanceValue:
        """Calculate $/PassMark metrics and percentile ranking."""
        # Lookup CPU's cpu_mark_single, cpu_mark_multi
        # Query average listing prices for this CPU
        # Calculate $/mark_single, $/mark_multi
        # Query all CPUs for percentile ranking
        # Map percentile to rating (excellent/good/fair/poor)
        # Return PerformanceValue schema

    async def update_cpu_analytics(
        self, session: AsyncSession, cpu_id: int
    ) -> None:
        """Calculate and persist all analytics for a CPU."""
        # Call calculate_price_targets()
        # Call calculate_performance_value()
        # Update CPU table with all fields
        # Set updated_at timestamps
        # Commit transaction

    async def recalculate_all_cpu_metrics(
        self, session: AsyncSession
    ) -> dict[str, int]:
        """Batch process all CPUs for nightly recalculation."""
        # Query all CPUs
        # For each CPU: call update_cpu_analytics()
        # Track success/error counts
        # Log detailed progress
        # Return summary dict
```

**Key Patterns:**
- All methods are async (follows Deal Brain async-first principle)
- All methods accept `AsyncSession` parameter (explicit dependency)
- Return Pydantic schemas for type safety
- Comprehensive error handling and logging
- No direct API dependencies (pure service layer logic)

---

### 3. API Endpoint Design

**Decision:** Extend existing `/v1/catalog` router with new CPU analytics endpoints

**Rationale:**
- Catalog router already exists at `apps/api/dealbrain_api/api/catalog.py`
- Current CPU endpoints: `GET /cpus`, `GET /cpus/{id}`, `POST /cpus`
- Logical grouping with existing catalog endpoints
- Consistent URL structure with rest of API

**New/Updated Endpoints:**

| Endpoint | Method | Purpose | Response | Performance Target |
|----------|--------|---------|----------|-------------------|
| `/v1/cpus` | GET | List all CPUs with analytics | `List[CPUWithAnalytics]` | < 500ms P95 |
| `/v1/cpus/{id}` | GET | CPU details + top listings | `CPUDetail` | < 300ms P95 |
| `/v1/cpus/statistics` | GET | Filter dropdown options | `CPUStatistics` | < 200ms (cached) |
| `/v1/cpus/recalculate-metrics` | POST | Trigger background recalc | `TaskStatus` | Immediate 202 |

**Implementation Notes:**
- **Query Optimization Critical:** Use single query with JOINs + aggregations
- **Caching Strategy:** Redis cache for `/statistics` (5 min TTL)
- **Pagination:** Not required for Phase 1 (< 500 CPUs expected)
- **Analytics Toggle:** `include_analytics` query param for `/cpus` (default: true)

**Performance Optimization Strategies:**
1. **Pre-computed Fields:** Analytics calculated nightly, stored in CPU table
2. **Eager Loading:** Use `selectinload()` for relationships
3. **Aggregation in DB:** Use SQLAlchemy aggregation functions, not Python loops
4. **Index Coverage:** Ensure all queries covered by indexes

---

### 4. Background Task Architecture

**Decision:** Use existing Celery infrastructure with scheduled beat task

**Rationale:**
- Celery already configured in `apps/api/dealbrain_api/worker.py`
- Existing pattern for scheduled tasks (see `cleanup_expired_payloads` in beat schedule)
- Redis backend already available
- Proven reliability for long-running batch operations

**Task Design:**
```python
# Location: apps/api/dealbrain_api/tasks/cpu_metrics.py

from celery import shared_task
from dealbrain_api.db import session_scope
from dealbrain_api.services.cpu_analytics import CPUAnalyticsService
from dealbrain_api.telemetry import get_logger

logger = get_logger("dealbrain.tasks.cpu_metrics")

@shared_task(name="cpu_analytics.recalculate_all_metrics")
def recalculate_all_cpu_metrics():
    """
    Nightly task to refresh all CPU analytics.

    Scheduled: 2:00 AM UTC daily
    Target Duration: < 5 minutes for 500 CPUs
    Error Handling: Continue processing on individual failures
    Alerting: Alert if > 10% failure rate
    """
    async with session_scope() as session:
        service = CPUAnalyticsService()
        result = await service.recalculate_all_cpu_metrics(session)

        logger.info(
            "CPU metrics recalculation complete",
            extra={
                "total": result['total'],
                "success": result['success'],
                "errors": result['errors'],
                "duration_seconds": result['duration']
            }
        )

        # Alert on high error rate
        if result['errors'] > result['total'] * 0.1:
            logger.error(
                "High error rate in CPU metrics recalculation",
                extra=result
            )
            # TODO: Integrate with alerting system

        return result
```

**Celery Beat Schedule Update:**
```python
# In apps/api/dealbrain_api/worker.py

celery_app.conf.beat_schedule = {
    # ... existing tasks ...

    "recalculate-cpu-metrics-nightly": {
        "task": "cpu_analytics.recalculate_all_metrics",
        "schedule": crontab(hour=2, minute=0),  # 2:00 AM UTC
        "options": {"expires": 3600},  # Expire if not run within 1 hour
    },
}
```

**Performance Targets:**
- **Batch Size:** Process 50 CPUs per batch to avoid memory issues
- **Duration:** < 5 minutes for 500 CPUs (< 600ms per CPU)
- **Success Rate:** > 90% success rate per run
- **Retries:** Individual CPU failures logged but don't halt batch

---

### 5. Pydantic Schema Design

**Decision:** Create new schemas in `packages/core/dealbrain_core/schemas/cpu.py`

**Rationale:**
- Follows Deal Brain pattern: schemas in `packages/core` for reusability
- Type safety across API boundaries
- Self-documenting API with Pydantic field descriptions
- Frontend TypeScript generation from OpenAPI spec

**New Schemas:**

```python
# Location: packages/core/dealbrain_core/schemas/cpu.py

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class PriceTarget(BaseModel):
    """CPU price target ranges derived from listing data."""
    good: float | None = Field(
        description="Average adjusted price from active listings"
    )
    great: float | None = Field(
        description="One standard deviation below average (better value)"
    )
    fair: float | None = Field(
        description="One standard deviation above average (premium)"
    )
    sample_size: int = Field(
        description="Number of active listings used in calculation"
    )
    confidence: Literal['high', 'medium', 'low', 'insufficient'] = Field(
        description="Confidence level based on sample size"
    )
    stddev: float | None = Field(
        description="Standard deviation of listing prices"
    )
    updated_at: datetime | None = Field(
        description="Last calculation timestamp"
    )

class PerformanceValue(BaseModel):
    """CPU performance value metrics ($/PassMark)."""
    dollar_per_mark_single: float | None = Field(
        description="Price per single-thread PassMark point"
    )
    dollar_per_mark_multi: float | None = Field(
        description="Price per multi-thread PassMark point"
    )
    percentile: float | None = Field(
        ge=0, le=100,
        description="Performance value percentile rank (0-100)"
    )
    rating: Literal['excellent', 'good', 'fair', 'poor'] | None = Field(
        description="Performance value rating based on percentile"
    )
    updated_at: datetime | None = Field(
        description="Last calculation timestamp"
    )

class CPUWithAnalytics(CpuRead):
    """CPU with embedded analytics data."""
    price_targets: PriceTarget
    performance_value: PerformanceValue
    listings_count: int = Field(
        description="Number of active listings with this CPU"
    )

class CPUDetail(CPUWithAnalytics):
    """Detailed CPU information for detail modal."""
    top_listings: list[ListingRead] = Field(
        description="Top 10 listings by adjusted price"
    )
    price_distribution: list[dict[str, float]] = Field(
        description="Price histogram data for charts"
    )

class CPUStatistics(BaseModel):
    """Global CPU statistics for filter dropdowns."""
    manufacturers: list[str] = Field(
        description="Unique manufacturers (Intel, AMD, Apple)"
    )
    sockets: list[str] = Field(
        description="Unique socket types (LGA1700, AM5, etc.)"
    )
    core_range: tuple[int, int] = Field(
        description="Min and max core counts"
    )
    tdp_range: tuple[int, int] = Field(
        description="Min and max TDP values in watts"
    )
    year_range: tuple[int, int] = Field(
        description="Min and max release years"
    )
    total_count: int = Field(
        description="Total number of CPUs in catalog"
    )
```

---

## Critical Path & Dependencies

### Phase 1 Critical Path

**Sequential Tasks (Must Complete in Order):**

1. **DB-001: Database Migration** (4h)
   → Blocks: DB-002, all backend tasks
   → Deliverable: Migration script, test on staging

2. **DB-002: Update CPU Model** (2h)
   → Blocks: BE-001, BE-002
   → Deliverable: Updated SQLAlchemy model with new fields

3. **BE-001: Pydantic Schemas** (3h)
   → Blocks: BE-002, BE-003, BE-004
   → Deliverable: All schemas in `schemas/cpu.py`

4. **BE-002: CPU Analytics Service** (12h) **← CRITICAL PATH BOTTLENECK**
   → Blocks: BE-003, BE-004, BE-006, BE-007
   → Deliverable: Complete service with all methods

5. **BE-003/004/005: API Endpoints** (9h combined)
   → Can be parallelized after BE-002
   → Deliverable: All endpoints operational

6. **BE-006/007: Background Tasks** (6h combined)
   → Requires BE-002
   → Can be parallelized with BE-003/004/005

**Parallel Work Opportunities:**
- Once BE-002 complete: BE-003, BE-004, BE-005, BE-006, BE-007 can run in parallel
- Testing (BE-008, BE-009) can start as soon as individual components complete

**Total Critical Path:** ~40 hours (5 days) as estimated

---

## Risk Assessment & Mitigation

### High-Priority Risks

**Risk 1: Query Performance Degradation**
- **Impact:** `/v1/cpus` endpoint exceeds 500ms P95 latency target
- **Probability:** Medium (complex analytics queries)
- **Mitigation:**
  - Pre-compute analytics and store in CPU table (denormalized)
  - Create comprehensive indexes on filter columns
  - Use database aggregation functions, not Python loops
  - Load test with 500+ CPUs before Phase 1 completion
  - **Fallback:** Implement pagination if latency still high

**Risk 2: Nightly Recalculation Duration**
- **Impact:** Task takes > 5 minutes for 500 CPUs (target: < 5 min)
- **Probability:** Medium
- **Mitigation:**
  - Batch processing (50 CPUs at a time)
  - Optimize database queries (use aggregations)
  - Parallel processing if needed (Celery task groups)
  - Monitor duration metrics from day 1
  - **Fallback:** Increase target to 10 minutes if acceptable

**Risk 3: Insufficient Listing Data**
- **Impact:** Many CPUs have < 2 listings, confidence is "insufficient"
- **Probability:** High (expected for rare/old CPUs)
- **Mitigation:**
  - Design UI to gracefully handle missing data
  - Show "No data available" state in badges/price targets
  - Document minimum data requirements in API docs
  - Consider fallback to industry pricing data (future enhancement)

**Risk 4: Outlier Price Handling**
- **Impact:** Extreme prices (typos, auctions) skew price targets
- **Probability:** Medium
- **Mitigation:**
  - Exclude listings > 3 standard deviations from mean
  - Manual review of outliers during development
  - Add admin endpoint to flag/exclude specific listings
  - Log outliers for monitoring

**Risk 5: Schema Migration on Production**
- **Impact:** Migration causes downtime or data loss
- **Probability:** Low (but high impact)
- **Mitigation:**
  - Test migration on staging with production data snapshot
  - All new columns are `nullable=True` (no data required)
  - Downgrade function tested and verified
  - Run migration during low-traffic window
  - Database backup before migration

---

## Integration Points with Existing System

### 1. Listings Service Integration

**Connection:** CPU analytics depend on Listing data

**Integration Pattern:**
```python
# CPUAnalyticsService queries Listing table
from dealbrain_api.models import Listing
from dealbrain_core.enums import ListingStatus

# Query active listings for a CPU
stmt = select(Listing.adjusted_price).where(
    Listing.cpu_id == cpu_id,
    Listing.status == ListingStatus.ACTIVE,
    Listing.adjusted_price.isnot(None)
)
```

**Key Fields:**
- `Listing.cpu_id` - Foreign key to CPU
- `Listing.adjusted_price` - Valuation-adjusted price (use this, not `price_usd`)
- `Listing.status` - Only count ACTIVE listings

**No Service Layer Changes Required:**
- ListingsService doesn't need to call CPUAnalyticsService
- Analytics are recalculated nightly (eventual consistency acceptable)
- Future: Consider invalidating CPU analytics when listings change (Phase 4 enhancement)

---

### 2. Valuation System Integration

**Connection:** Price targets use `adjusted_price` from valuation system

**Current Flow:**
```
Listing → Valuation Rules → adjusted_price field
             ↓
         CPU Analytics ← reads adjusted_price
```

**No Changes Required:**
- Valuation system is upstream dependency
- Analytics consume valuation output (adjusted_price)
- No circular dependencies

**Future Enhancement (Post-Phase 1):**
- Consider using valuation_breakdown JSON for more detailed insights
- Could show "common adjustments" in CPU detail modal

---

### 3. PassMark Data Integration

**Connection:** Performance metrics depend on PassMark scores

**Existing Data:**
- CPU table already has `cpu_mark_single`, `cpu_mark_multi`, `igpu_mark`
- Populated by `scripts/import_passmark_data.py`
- Data source: `data/passmark_cpus.csv`

**Analytics Dependency:**
```python
# Requires non-null PassMark scores
if cpu.cpu_mark_single is None:
    return None  # Can't calculate $/mark

dollar_per_mark = avg_price / cpu.cpu_mark_single
```

**Edge Case Handling:**
- CPUs without PassMark scores → performance_value fields remain NULL
- UI must handle NULL gracefully (show "No benchmark data" badge)

---

### 4. React Query Integration (Frontend)

**Backend Readiness:**
- Phase 1 delivers API endpoints, but no frontend
- Phase 2 will consume endpoints via React Query

**Expected Frontend Pattern (Phase 2):**
```typescript
// apps/web/hooks/use-cpus.ts
import { useQuery } from '@tanstack/react-query';
import { CPUWithAnalytics } from '@/types/cpu';

export function useCPUs() {
  return useQuery({
    queryKey: ['cpus', 'analytics'],
    queryFn: () => apiFetch<CPUWithAnalytics[]>('/v1/cpus'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

**Backend Optimization for React Query:**
- Fast response times (< 500ms)
- Consistent schema structure
- Predictable error responses
- Support for conditional fetching (`include_analytics` param)

---

## Technology Stack Compliance

### Backend Stack Verification

✅ **FastAPI** - Async routes, dependency injection via `Depends()`
✅ **SQLAlchemy 2.0 (Async)** - All queries use `AsyncSession`
✅ **Alembic** - Database migrations for schema changes
✅ **Pydantic v2** - Request/response validation via schemas
✅ **Celery** - Background task processing with Redis backend
✅ **PostgreSQL** - Primary database (via SQLAlchemy)
✅ **Redis** - Celery backend, future cache for statistics endpoint

### Architectural Pattern Compliance

✅ **Layered Architecture:** API Routes → Services → Domain Logic → Database
- API endpoints in `api/catalog.py`
- Service layer in `services/cpu_analytics.py`
- Domain logic in `packages/core` (schemas)
- Database models in `models/core.py`

✅ **Async-First:** All database operations use async/await
✅ **Error Handling:** Pydantic validation + proper HTTP status codes
✅ **Observability:** Structured logging via `get_logger()`
✅ **Testing Strategy:** Unit tests for service, integration tests for API

---

## Performance Optimization Strategy

### Database Query Optimization

**1. Index Strategy:**
```sql
-- Migration includes these indexes:
CREATE INDEX idx_cpu_price_targets ON cpu(price_target_good, price_target_confidence);
CREATE INDEX idx_cpu_performance_value ON cpu(dollar_per_mark_single, dollar_per_mark_multi);
CREATE INDEX idx_cpu_manufacturer ON cpu(manufacturer);
CREATE INDEX idx_cpu_socket ON cpu(socket);
CREATE INDEX idx_cpu_cores ON cpu(cores);

-- Existing indexes on Listing:
-- Ensure index on (cpu_id, status, adjusted_price) for analytics queries
```

**2. Query Patterns:**
```python
# BAD: N+1 query pattern
for cpu in cpus:
    count = await session.scalar(select(func.count()).where(Listing.cpu_id == cpu.id))

# GOOD: Single aggregation query
stmt = (
    select(Listing.cpu_id, func.count(Listing.id))
    .where(Listing.status == ListingStatus.ACTIVE)
    .group_by(Listing.cpu_id)
)
listing_counts = dict(await session.execute(stmt))
```

**3. Batch Processing:**
- Process CPUs in batches of 50 during nightly recalculation
- Use `session.flush()` periodically, not after every update
- Final `session.commit()` at end of batch

---

### Caching Strategy

**Phase 1 Caching (Simple):**
- `/v1/cpus/statistics` endpoint: Redis cache with 5-minute TTL
- Pre-computed analytics in CPU table (nightly refresh)

**Future Enhancements (Phase 4):**
- Implement Redis caching for `/v1/cpus` list endpoint
- Cache individual CPU details
- Invalidate cache on CPU/Listing updates

---

### API Response Optimization

**1. Selective Field Loading:**
```python
# Support include_analytics parameter
@router.get("/cpus")
async def list_cpus(
    include_analytics: bool = Query(default=True),
    session: AsyncSession = Depends(session_dependency)
):
    if not include_analytics:
        # Return minimal CPU data (faster)
        return [CpuRead.model_validate(cpu) for cpu in cpus]
    else:
        # Return full analytics data
        return [CPUWithAnalytics(...) for cpu in cpus]
```

**2. Response Compression:**
- FastAPI automatically compresses responses with gzip
- No additional configuration needed

---

## Testing Strategy

### Unit Tests (BE-008: 6h)

**Test Coverage Requirements:**
- **Service Methods:** All CPUAnalyticsService methods
- **Edge Cases:** Insufficient data, missing benchmarks, outliers
- **Calculation Logic:** Verify price targets, performance metrics
- **Error Handling:** Database errors, null values

**Test Scenarios:**
```python
# tests/services/test_cpu_analytics.py

async def test_calculate_price_targets_with_sufficient_data():
    """Test price target calculation with 10+ listings."""
    # Setup: Create CPU with 10 listings
    # Expected: High confidence, accurate mean/stddev

async def test_calculate_price_targets_with_outliers():
    """Test outlier exclusion (> 3 stddev)."""
    # Setup: Create CPU with 1 extreme outlier price
    # Expected: Outlier excluded, mean not skewed

async def test_calculate_price_targets_insufficient_data():
    """Test handling of < 2 listings."""
    # Setup: Create CPU with 1 listing
    # Expected: Confidence = 'insufficient', nulls for targets

async def test_calculate_performance_value_percentile():
    """Test percentile ranking across multiple CPUs."""
    # Setup: Create 10 CPUs with known $/mark values
    # Expected: Correct percentile ranking (0-100)

async def test_recalculate_all_cpu_metrics_batch():
    """Test batch processing of 100 CPUs."""
    # Setup: Create 100 CPUs
    # Expected: All processed, summary dict accurate
```

---

### Integration Tests (BE-009: 6h)

**Test Coverage Requirements:**
- **API Endpoints:** All endpoints with real database
- **Performance:** Response time benchmarks
- **Error Scenarios:** 404s, validation errors
- **Schema Validation:** Response matches Pydantic schemas

**Test Scenarios:**
```python
# tests/api/test_catalog_cpus.py

async def test_list_cpus_with_analytics(client, session):
    """Test GET /v1/cpus returns analytics data."""
    # Expected: 200 OK, List[CPUWithAnalytics]

async def test_list_cpus_without_analytics(client, session):
    """Test GET /v1/cpus?include_analytics=false."""
    # Expected: 200 OK, List[CpuRead] (minimal data)

async def test_get_cpu_detail(client, session):
    """Test GET /v1/cpus/{id} with top listings."""
    # Expected: 200 OK, CPUDetail with listings

async def test_get_cpu_statistics(client, session):
    """Test GET /v1/cpus/statistics returns filter options."""
    # Expected: 200 OK, CPUStatistics schema

async def test_recalculate_metrics_endpoint(client, session):
    """Test POST /v1/cpus/recalculate-metrics triggers task."""
    # Expected: 202 Accepted, task ID returned

async def test_list_cpus_performance_100_cpus(client, session, benchmark):
    """Benchmark /v1/cpus with 100 CPUs."""
    # Expected: < 500ms P95 latency
```

---

## Agent Delegation Strategy

### Recommended Agent Assignments

**Phase 1 is Backend-Heavy → Use Backend Specialists**

**Task Grouping for Delegation:**

**Group 1: Database Foundation (Sequential)**
```markdown
Task("data-layer-expert", "Phase 1 CPU Analytics - Database Foundation

Create Alembic migration and update CPU SQLAlchemy model:

Tasks:
- DB-001: Generate migration script for CPU analytics fields
  - Add 12 new columns (price targets, performance metrics, timestamps)
  - Create 5 indexes (manufacturer, socket, cores, price targets, performance)
  - Test migration upgrade/downgrade on staging snapshot

- DB-002: Update CPU model in apps/api/dealbrain_api/models/core.py
  - Add all new fields with correct types
  - Implement properties: has_sufficient_pricing_data, price_targets_fresh
  - Maintain existing relationships

Success Criteria:
- Migration runs without errors
- All fields nullable (no data required initially)
- Indexes created successfully
- Model validates with existing data

Time Estimate: 6 hours
")
```

**Group 2: Service Layer + Schemas (After Group 1)**
```markdown
Task("python-backend-engineer", "Phase 1 CPU Analytics - Service Layer Implementation

Implement Pydantic schemas and CPU analytics service:

Tasks:
- BE-001: Create Pydantic schemas in packages/core/dealbrain_core/schemas/cpu.py
  - PriceTarget, PerformanceValue schemas
  - CPUWithAnalytics, CPUDetail, CPUStatistics schemas
  - Field descriptions and validation

- BE-002: Implement CPUAnalyticsService in apps/api/dealbrain_api/services/cpu_analytics.py
  - calculate_price_targets() method
  - calculate_performance_value() method
  - update_cpu_analytics() method
  - recalculate_all_cpu_metrics() method
  - Comprehensive error handling and logging
  - Edge case handling (insufficient data, outliers)

Reference Implementation Plan:
/mnt/containers/deal-brain/docs/project_plans/cpu-page-reskin/IMPLEMENTATION_PLAN.md (lines 272-353)

Success Criteria:
- All schemas validate correctly
- Service methods return correct calculations
- Edge cases handled gracefully
- Comprehensive logging implemented

Time Estimate: 15 hours
Dependencies: Group 1 must complete first
")
```

**Group 3: API Endpoints (After Group 2, Can Parallelize)**
```markdown
Task("python-backend-engineer", "Phase 1 CPU Analytics - API Endpoints

Implement CPU analytics API endpoints in apps/api/dealbrain_api/api/catalog.py:

Tasks:
- BE-003: Update GET /v1/cpus endpoint
  - Return List[CPUWithAnalytics]
  - Support include_analytics query parameter
  - Optimize query (single DB query with aggregations)
  - Include listings_count for each CPU
  - Ensure < 500ms P95 latency

- BE-004: Update GET /v1/cpus/{id} endpoint
  - Return CPUDetail with analytics
  - Include top 10 listings by adjusted_price
  - Include price distribution for histogram
  - Handle 404 errors
  - Ensure < 300ms P95 latency

- BE-005: Create GET /v1/cpus/statistics endpoint
  - Return CPUStatistics schema
  - Query unique manufacturers, sockets
  - Query min/max ranges (cores, TDP, years)
  - Implement Redis caching (5 min TTL)
  - Ensure < 200ms latency

- BE-006: Create POST /v1/cpus/recalculate-metrics endpoint
  - Admin-only endpoint
  - Trigger background Celery task
  - Return 202 Accepted with task ID
  - Implement authorization check

Reference Implementation Plan:
/mnt/containers/deal-brain/docs/project_plans/cpu-page-reskin/IMPLEMENTATION_PLAN.md (lines 356-460)

Success Criteria:
- All endpoints return correct schemas
- Performance targets met
- Error handling implemented
- Query optimization verified

Time Estimate: 11 hours
Dependencies: Group 2 must complete first
")
```

**Group 4: Background Tasks (After Group 2, Parallel with Group 3)**
```markdown
Task("python-backend-engineer", "Phase 1 CPU Analytics - Background Tasks

Implement Celery task for nightly CPU metrics recalculation:

Tasks:
- BE-007: Create Celery task in apps/api/dealbrain_api/tasks/cpu_metrics.py (NEW FILE)
  - Implement recalculate_all_cpu_metrics task
  - Schedule for 2:00 AM UTC via Celery Beat
  - Process all CPUs in batches (50 at a time)
  - Complete in < 5 minutes for 500 CPUs
  - Log summary (total, success, errors)
  - Alert if > 10% failure rate

- Update apps/api/dealbrain_api/worker.py
  - Import new task module
  - Add beat_schedule entry for nightly task

Reference Implementation Plan:
/mnt/containers/deal-brain/docs/project_plans/cpu-page-reskin/IMPLEMENTATION_PLAN.md (lines 462-513)

Success Criteria:
- Task runs without errors
- Completes within time budget
- Comprehensive logging
- Error handling for individual CPU failures

Time Estimate: 5 hours
Dependencies: Group 2 must complete first
")
```

**Group 5: Testing (After Groups 3 & 4)**
```markdown
Task("python-backend-engineer", "Phase 1 CPU Analytics - Testing

Implement comprehensive test coverage:

Tasks:
- BE-008: Unit tests in tests/services/test_cpu_analytics.py
  - Test calculate_price_targets with various scenarios
  - Test calculate_performance_value calculations
  - Test edge cases (insufficient data, outliers, missing benchmarks)
  - Test batch processing efficiency
  - Achieve > 85% code coverage

- BE-009: Integration tests in tests/api/test_catalog_cpus.py
  - Test all endpoints with real database
  - Verify performance (response times < targets)
  - Test error scenarios (404, validation errors)
  - Validate response schemas
  - Test with varying data sizes (10, 100, 500 CPUs)

Success Criteria:
- All tests pass
- > 85% code coverage for new code
- Performance benchmarks met
- Edge cases covered

Time Estimate: 12 hours
Dependencies: Groups 3 & 4 must complete
")
```

---

## Next Immediate Steps

### Step 1: Confirm Architectural Decisions
- [ ] Review architectural decisions documented above
- [ ] Confirm database schema approach (denormalized)
- [ ] Approve service layer design
- [ ] Validate API endpoint design

### Step 2: Begin Phase 1 Execution
- [ ] Delegate Group 1 (Database Foundation) to data-layer-expert
- [ ] Wait for Group 1 completion (~6 hours)
- [ ] Delegate Group 2 (Service Layer) to python-backend-engineer
- [ ] Wait for Group 2 completion (~15 hours)
- [ ] Delegate Groups 3 & 4 in parallel (API + Tasks) (~16 hours)
- [ ] Delegate Group 5 (Testing) after Groups 3 & 4 (~12 hours)

### Step 3: Phase 1 Verification
- [ ] Run full test suite
- [ ] Performance benchmarks on staging
- [ ] Manual verification of analytics calculations
- [ ] Review logs for errors/warnings
- [ ] Prepare Phase 1 completion report

---

## Quick Reference

### Key Files to Create/Modify

**New Files:**
- `apps/api/alembic/versions/xxx_add_cpu_analytics_fields.py` - Migration
- `packages/core/dealbrain_core/schemas/cpu.py` - Pydantic schemas (NEW)
- `apps/api/dealbrain_api/services/cpu_analytics.py` - Analytics service (NEW)
- `apps/api/dealbrain_api/tasks/cpu_metrics.py` - Celery task (NEW)
- `tests/services/test_cpu_analytics.py` - Service tests (NEW)
- `tests/api/test_catalog_cpus.py` - API tests (NEW)

**Modified Files:**
- `apps/api/dealbrain_api/models/core.py` - Update CPU model
- `apps/api/dealbrain_api/api/catalog.py` - Add/update endpoints
- `apps/api/dealbrain_api/worker.py` - Add beat schedule entry

### Common Commands

```bash
# Create migration
poetry run alembic revision --autogenerate -m "Add CPU analytics fields"

# Apply migration
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1

# Run tests
poetry run pytest tests/services/test_cpu_analytics.py -v
poetry run pytest tests/api/test_catalog_cpus.py -v

# Run Celery worker
poetry run celery -A dealbrain_api.worker worker --loglevel=debug

# Trigger task manually
poetry run celery -A dealbrain_api.worker call cpu_analytics.recalculate_all_metrics

# Check Celery beat schedule
poetry run celery -A dealbrain_api.worker beat --loglevel=debug
```

---

**Last Updated:** 2025-11-05
**Status:** Architecture Review Complete - Ready for Implementation
**Next Review:** After Group 1 completion (Database Foundation)
