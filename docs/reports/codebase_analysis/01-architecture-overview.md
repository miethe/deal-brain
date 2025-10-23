# Architecture Overview

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Data Flow](#data-flow)
3. [Design Patterns](#design-patterns)
4. [Component Interactions](#component-interactions)
5. [Request Lifecycle](#request-lifecycle)

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         User / Browser                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Next.js Frontend (Port 3000)                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐   │
│  │  React Pages   │  │  Components    │  │  React Query           │   │
│  │  (App Router)  │  │  (Radix UI)    │  │  (Data Fetching)       │   │
│  └────────────────┘  └────────────────┘  └────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐   │
│  │  Zustand Store │  │  Hooks         │  │  TypeScript Types      │   │
│  └────────────────┘  └────────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Port 8000)                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                         API Layer                               │    │
│  │  /v1/listings │ /v1/catalog │ /v1/rules │ /v1/baseline         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                       Services Layer                            │    │
│  │  listings.py │ rules.py │ component_catalog.py │ ports.py      │    │
│  │  custom_fields.py │ rule_evaluation.py │ baseline_loader.py    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │              Shared Domain Logic (packages/core)                │    │
│  │  valuation.py │ scoring.py │ rule_evaluator.py │ enums.py      │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                      Data Layer (SQLAlchemy)                    │    │
│  │  models/core.py │ Alembic Migrations │ AsyncSession            │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                │                          │
                ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│  PostgreSQL Database     │   │  Redis Cache/Queue       │
│  (Port 5432)             │   │  (Port 6379)             │
│                          │   │                          │
│  - Listings              │   │  - Session cache         │
│  - CPUs/GPUs             │   │  - Celery tasks          │
│  - Valuation Rules       │   │  - Query results         │
│  - Custom Fields         │   │                          │
└──────────────────────────┘   └──────────────────────────┘
                                           │
                                           ▼
                              ┌──────────────────────────┐
                              │  Celery Worker           │
                              │  (Background Tasks)      │
                              │                          │
                              │  - Bulk recalculation    │
                              │  - Import processing     │
                              │  - Metric updates        │
                              └──────────────────────────┘
```

### Additional Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Observability Stack                                 │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │  Prometheus      │  │  Grafana         │  │  OTEL Collector  │     │
│  │  (Metrics)       │◄─│  (Dashboards)    │◄─│  (Tracing)       │     │
│  │  Port 9090       │  │  Port 3021       │  │                  │     │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘     │
│         ▲                                              ▲                 │
│         │                                              │                 │
│         └──────────────────────────────────────────────┘                │
│                        Metrics & Traces                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. User Request Flow

```
User Action (Frontend)
    │
    ├─► React Query Hook
    │       │
    │       └─► apiFetch() utility
    │               │
    │               └─► HTTP Request → FastAPI
    │                                      │
    │                                      ├─► Route Handler
    │                                      │       │
    │                                      │       └─► Service Layer
    │                                      │               │
    │                                      │               ├─► Domain Logic (packages/core)
    │                                      │               │
    │                                      │               └─► Database (SQLAlchemy)
    │                                      │                       │
    │                                      │                       └─► PostgreSQL
    │                                      │
    │                                      └─► Response (JSON)
    │                                              │
    │                                              ▼
    └─────────────────────────────────────► React Component Update
```

### 2. Valuation Computation Flow

```
Listing Price + Components
    │
    ├─► API: /v1/listings/{id}/valuation
    │       │
    │       └─► listings.py service
    │               │
    │               ├─► Fetch Active Rulesets (Priority Order)
    │               │       │
    │               │       └─► ValuationRuleset model
    │               │
    │               ├─► Rule Evaluation Service
    │               │       │
    │               │       ├─► Evaluate Conditions (rule_evaluator.py)
    │               │       │       │
    │               │       │       └─► Match entity fields against rule conditions
    │               │       │
    │               │       └─► Apply Actions
    │               │               │
    │               │               ├─► Deduct/Add amounts
    │               │               ├─► Multiply factors
    │               │               └─► Set overrides
    │               │
    │               ├─► Aggregate Adjustments by Rule Group
    │               │       │
    │               │       └─► Apply Rule Group Weights
    │               │
    │               └─► Compute Final Adjusted Price
    │                       │
    │                       └─► valuation.py (core)
    │
    └─► Return Breakdown + Adjusted Price
```

### 3. Import Pipeline Flow

```
Excel Workbook Upload
    │
    ├─► Frontend: /import page
    │       │
    │       └─► POST /v1/imports/upload
    │               │
    │               └─► imports.py service
    │                       │
    │                       ├─► Parse Excel (pandas + openpyxl)
    │                       │       │
    │                       │       └─► Extract sheets (CPUs, GPUs, Listings)
    │                       │
    │                       ├─► Normalize Data
    │                       │       │
    │                       │       └─► SpreadsheetSeed schema (packages/core)
    │                       │
    │                       ├─► Upsert Components
    │                       │       │
    │                       │       ├─► component_catalog.py service
    │                       │       │       │
    │                       │       │       └─► Create/Update CPUs, GPUs, RAM, Storage
    │                       │       │
    │                       │       └─► Database (Async SQLAlchemy)
    │                       │
    │                       ├─► Create Listings
    │                       │       │
    │                       │       └─► listings.py service
    │                       │               │
    │                       │               └─► Link to CPUs/GPUs
    │                       │
    │                       ├─► Apply Valuation Rules
    │                       │       │
    │                       │       └─► Compute adjusted prices
    │                       │
    │                       └─► Calculate Scores
    │                               │
    │                               └─► scoring.py (core)
    │
    └─► Return Import Summary
```

### 4. Performance Metrics Calculation

```
Listing with CPU/GPU
    │
    ├─► update_listing_metrics() service
    │       │
    │       ├─► Fetch CPU benchmark data (PassMark)
    │       │       │
    │       │       └─► CPU.cpu_mark_multi, cpu_mark_single
    │       │
    │       ├─► Calculate Price Efficiency Metrics
    │       │       │
    │       │       ├─► dollars_per_cpu_mark = price / cpu_mark_multi
    │       │       └─► dollars_per_cpu_mark_single = price / cpu_mark_single
    │       │
    │       ├─► Calculate Performance Per Watt
    │       │       │
    │       │       └─► perf_per_watt = cpu_mark_multi / tdp_w
    │       │
    │       └─► Store metrics in listing.performance_metrics_json
    │
    └─► Metrics available for ranking and filtering
```

---

## Design Patterns

### 1. Domain-Driven Design (DDD)

**Core Domain Logic Isolation:**
- Business logic lives in `packages/core/dealbrain_core/`
- Independent of infrastructure (database, web framework)
- Shared by API, CLI, and future services

**Example:**
```python
# packages/core/dealbrain_core/valuation.py
def compute_adjusted_price(
    listing_price_usd: float,
    condition: Condition,
    rules: Iterable[ValuationRuleData],
    components: Iterable[ComponentValuationInput],
) -> ValuationResult:
    # Pure domain logic - no database, no HTTP
    ...
```

### 2. Service Layer Pattern

**Orchestration Services:**
- Services in `apps/api/dealbrain_api/services/`
- Coordinate between domain logic, database, and external systems
- Handle transactions, error handling, and caching

**Example:**
```python
# apps/api/dealbrain_api/services/listings.py
async def create_listing(
    session: AsyncSession,
    payload: ListingCreate
) -> Listing:
    # 1. Validate input
    # 2. Call domain logic
    # 3. Persist to database
    # 4. Return result
    ...
```

### 3. Repository Pattern (Implicit)

**Database Abstraction:**
- Services act as repositories
- SQLAlchemy queries encapsulated in service methods
- Domain layer never touches database directly

### 4. Strategy Pattern

**Valuation Rules:**
- Different rule types (condition, action) pluggable
- Rule evaluation engine (`rule_evaluator.py`) applies strategies
- Baseline vs. custom rulesets switchable

### 5. Factory Pattern

**Component Creation:**
```python
# apps/api/dealbrain_api/services/component_catalog.py
async def get_or_create_ram_spec(...) -> RamSpec:
    # Factory for RAM specifications
    ...
```

### 6. Observer Pattern (Implicit)

**React Query:**
- Frontend components observe API data
- Auto-refetch on mutations
- Invalidation triggers re-renders

### 7. Decorator Pattern

**Pydantic Models:**
- Request/response models wrap domain logic
- Add validation, serialization, API contracts
- Domain models remain pure

---

## Component Interactions

### Backend Service Dependencies

```
┌────────────────────────────────────────────────────────────┐
│                      API Endpoints                         │
│  (listings.py, catalog.py, rules.py, baseline.py)         │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│                    Service Layer                           │
│                                                             │
│  listings.py ◄─────────┐                                   │
│     │                  │                                   │
│     ├─► rule_evaluation.py                                 │
│     ├─► component_catalog.py                               │
│     ├─► custom_fields.py                                   │
│     └─► ports.py                                           │
│                                                             │
│  rules.py ◄────────────┐                                   │
│     │                  │                                   │
│     ├─► rule_evaluation.py                                 │
│     ├─► rule_preview.py                                    │
│     └─► ruleset_packaging.py                               │
│                                                             │
│  baseline_loader.py ◄──┐                                   │
│     │                  │                                   │
│     └─► rules.py       │                                   │
│                        │                                   │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│                  Domain Logic (core)                       │
│                                                             │
│  valuation.py ◄─────────────┐                             │
│  scoring.py ◄────────────────┤                             │
│  rule_evaluator.py ◄─────────┤                             │
│  enums.py ◄──────────────────┤                             │
│  schemas/ ◄──────────────────┘                             │
│                                                             │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│                   Database Models                          │
│  (models/core.py via SQLAlchemy AsyncSession)              │
└────────────────────────────────────────────────────────────┘
```

### Frontend Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      Root Layout                            │
│  (app/layout.tsx)                                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Providers (React Query, Theme, etc.)              │    │
│  │                                                      │    │
│  │  ┌────────────────────────────────────────────┐    │    │
│  │  │  AppShell (Navigation + Content)           │    │    │
│  │  │                                              │    │    │
│  │  │  ┌────────────────────────────────────┐    │    │    │
│  │  │  │  Page Components                   │    │    │    │
│  │  │  │  (app/*/page.tsx)                  │    │    │    │
│  │  │  │                                      │    │    │    │
│  │  │  │  ┌──────────────────────────┐      │    │    │    │
│  │  │  │  │  Feature Components      │      │    │    │    │
│  │  │  │  │  (components/listings/)  │      │    │    │    │
│  │  │  │  │                          │      │    │    │    │
│  │  │  │  │  ┌────────────────┐     │      │    │    │    │
│  │  │  │  │  │  UI Components │     │      │    │    │    │
│  │  │  │  │  │  (Radix UI)    │     │      │    │    │    │
│  │  │  │  │  └────────────────┘     │      │    │    │    │
│  │  │  │  └──────────────────────────┘      │    │    │    │
│  │  │  └────────────────────────────────────┘    │    │    │
│  │  └────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Request Lifecycle

### Example: Update Listing Price

**1. User Action (Frontend)**
```typescript
// User edits price in listings table
const mutation = useMutation({
  mutationFn: (data) => apiFetch('/v1/listings/123', {
    method: 'PATCH',
    body: JSON.stringify({ price_usd: 500 })
  })
});
```

**2. API Request**
```
PATCH /v1/listings/123
Content-Type: application/json
Body: {"price_usd": 500}
```

**3. Backend Processing**
```python
# apps/api/dealbrain_api/api/listings.py
@router.patch("/v1/listings/{listing_id}")
async def update_listing_endpoint(
    listing_id: int,
    payload: ListingPartialUpdateRequest,
    session: AsyncSession = Depends(session_dependency)
):
    # 1. Call service layer
    listing = await partial_update_listing(
        session=session,
        listing_id=listing_id,
        updates=payload.model_dump(exclude_none=True)
    )

    # 2. Trigger metric recalculation
    await update_listing_metrics(session, listing)

    # 3. Apply valuation rules
    await apply_listing_metrics(session, listing)

    # 4. Commit transaction
    await session.commit()

    # 5. Return updated listing
    return ListingRead.model_validate(listing)
```

**4. Service Layer**
```python
# apps/api/dealbrain_api/services/listings.py
async def partial_update_listing(session, listing_id, updates):
    # Fetch listing
    listing = await session.get(Listing, listing_id)

    # Apply updates
    for key, value in updates.items():
        setattr(listing, key, value)

    # Mark as modified
    listing.updated_at = datetime.utcnow()

    await session.flush()
    return listing
```

**5. Domain Logic**
```python
# packages/core/dealbrain_core/valuation.py
def compute_adjusted_price(...):
    # Calculate deductions based on components and rules
    adjusted = listing_price_usd - total_deductions
    return ValuationResult(...)
```

**6. Response**
```json
{
  "id": 123,
  "title": "Mini PC",
  "price_usd": 500,
  "adjusted_price_usd": 450,
  "valuation_breakdown": { ... },
  "performance_metrics": { ... }
}
```

**7. Frontend Update**
```typescript
// React Query auto-refetches and updates UI
queryClient.invalidateQueries(['listings', 123]);
// Component re-renders with new data
```

---

## Key Architecture Decisions

### 1. Monorepo Structure
**Decision:** Single repo with apps + shared packages
**Rationale:**
- Shared domain logic (packages/core) reused by API and CLI
- Simplified dependency management
- Atomic changes across stack

### 2. Async-First Backend
**Decision:** Async SQLAlchemy, FastAPI, async services
**Rationale:**
- High concurrency without threading overhead
- Efficient I/O for database-heavy operations
- Modern Python best practices

### 3. Next.js App Router
**Decision:** Next.js 14 with App Router (not Pages Router)
**Rationale:**
- Server components for better performance
- Nested layouts for consistent UI
- Improved data fetching patterns

### 4. React Query for Data Fetching
**Decision:** TanStack Query instead of SWR or built-in fetch
**Rationale:**
- Powerful caching and invalidation
- Optimistic updates
- DevTools for debugging

### 5. Pydantic Everywhere
**Decision:** Pydantic for all data validation (API, domain, CLI)
**Rationale:**
- Type safety
- Automatic JSON serialization
- Clear API contracts

### 6. Custom Fields System
**Decision:** Dynamic field system (EntityField, EntityFieldValue)
**Rationale:**
- Extend entities without schema migrations
- User-defined fields per entity type
- Flexible data model

### 7. Rule-Based Valuation
**Decision:** Configurable rulesets with conditions + actions
**Rationale:**
- Business logic in data, not code
- Shareable baseline rulesets
- User customization without dev changes

---

**Next:** [Directory Structure →](./02-directory-structure.md)
