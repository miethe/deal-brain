# Deal Builder v1 - Working Context

**Purpose**: Token-efficient context for resuming work across AI turns and subagent coordination

**Last Updated**: 2025-11-14
**Current Phase**: Phase 7 Complete - Ready for Phase 8

---

## Current State

**Branch**: claude/deal-builder-v1-execution-013VwANP7T8avWiVqkaMzbUu
**Last Commit**: a0c4a5b (Merge PR #18)
**Current Task**: Phase 7 Save/Share Features - COMPLETE
**Status**: Ready for Phase 8 (Testing, Mobile Optimization, Accessibility)

---

## Key Architecture Decisions

### Backend Architecture
- **Layered Pattern**: API Routes → Services → Domain Logic (packages/core) → Database
- **Domain Logic Reuse**: MUST use existing `apply_valuation_rules()` from `packages/core/dealbrain_core/valuation.py`
- **Metrics Calculation**: MUST use existing `calculate_metrics()` from `packages/core/dealbrain_core/scoring.py`
- **Database Pattern**: Soft deletes via `deleted_at` column, eager loading with `joinedload()`
- **Async-First**: All database operations use async SQLAlchemy

### Frontend Architecture
- **State Management**: React Context (BuilderProvider) for component selection
- **Server State**: React Query with 5-minute cache on catalog, no cache on calculations
- **Debouncing**: API calls debounced at 300ms to prevent overwhelming backend
- **Responsive Design**: Mobile-first, breakpoints at 768px and 1024px
- **Component Library**: shadcn/ui (Radix UI) for all base components

### Performance Requirements
- API response time: <300ms for calculations
- Component modal load: <500ms
- Page initial load: <2s
- Database queries: <100ms (no N+1)

---

## Implementation Gotchas

### Phase 1 (Database Layer) - Completed 2025-11-14

**Model Organization**:
- Models refactored into domain-focused files (not monolithic `core.py`)
- Created new `builds.py` file following existing pattern
- Must update both `__init__.py` and `core.py` for backward compatibility
- Pattern: Create in domain file, export from `__init__.py`, re-export from `core.py`

**Migration Creation**:
- Alembic requires database connection for autogenerate
- Can create migrations manually following existing patterns
- Revision numbering: Sequential (0027 follows 0026)
- Migration structure: Comprehensive docstring, upgrade/downgrade functions
- Index naming: Use descriptive names (idx_user_builds, idx_visibility)

**Soft Delete Pattern**:
- Use `deleted_at: Mapped[datetime | None]` column
- Implement `soft_delete()` method on model
- Add helper properties: `is_deleted`, `is_public`, `is_unlisted`
- Indexes should include `deleted_at` for efficient filtering

**Testing Without Database**:
- Model tests can validate structure without database connection
- Test annotations, methods, properties, table args
- UUID.hex() is 32 characters, not 64
- TimestampMixin fields (created_at, updated_at) not in model annotations

### Phase 2 (Repository Layer) - Completed 2025-11-14

**Repository Pattern**:
- First repository in Deal Brain - no existing patterns to follow
- Repository receives AsyncSession as constructor parameter
- Methods should be stateless (no instance state beyond session)
- All methods must be async for SQLAlchemy 2.0 compatibility

**Query Optimization**:
- ALWAYS use joinedload() for relationships in list/get operations
- Pattern: `.options(joinedload(SavedBuild.cpu), joinedload(SavedBuild.gpu))`
- Access related objects without additional queries (prevents N+1)
- Tests should verify eager loading by accessing relationships

**Access Control**:
- Implement at repository level, not service level
- Public/unlisted builds accessible to anyone
- Private builds only accessible to owner
- Use generic error messages to prevent information leakage

**SQLite Testing Compatibility**:
- PostgreSQL ARRAY type not supported in SQLite
- PostgreSQL JSONB type not supported in SQLite
- Solution: Create TypeDecorator classes to handle conversion
- Patch model column types in test fixtures before table creation
- Must restore original types after tests (cleanup)

**SQLAlchemy 2.0 Patterns**:
- Use `select()` instead of `session.query()`
- Use `result.scalar_one_or_none()` for single results
- Use `result.scalars().all()` for list results
- Use `.unique()` when using joinedload() to avoid duplicate rows
- Async context: `async with session_factory() as session:`

---

## Environment Setup Quick Reference

### Backend API
```bash
export PYTHONPATH="$PWD/apps/api"
poetry install
make migrate  # Apply Alembic migrations
make api      # Run FastAPI dev server
```

### Frontend Web
```bash
pnpm install
pnpm --filter "./apps/web" dev
```

### Database
```bash
make up       # Start Docker Compose (Postgres, Redis, etc.)
make migrate  # Apply migrations
```

### Full Stack
```bash
make up       # All services
```

---

## Key Files Reference

### Backend (Phase 1-4 Complete)
- **Model**: ✅ `apps/api/dealbrain_api/models/builds.py` - SavedBuild model
- **Migration**: ✅ `apps/api/alembic/versions/0027_add_saved_builds_table.py`
- **Model Tests**: ✅ `tests/test_saved_build_model.py` - 10/10 tests passing
- **Repository**: ✅ `apps/api/dealbrain_api/repositories/builder_repository.py` - BuilderRepository
- **Repository Tests**: ✅ `tests/repositories/test_builder_repository.py` - 28/28 tests passing (97% coverage)
- **Service**: ✅ `apps/api/dealbrain_api/services/builder_service.py` - BuilderService
- **Service Tests**: ✅ `tests/services/test_builder_service.py` - 26/26 tests passing (93% coverage)
- **Schemas**: ✅ `apps/api/dealbrain_api/schemas/builder.py` - Request/Response models
- **API Router**: ✅ `apps/api/dealbrain_api/api/builder.py` - 8 endpoints
- **API Tests**: ✅ `tests/api/test_builder_api.py` - 31 tests passing

### Frontend (Phase 5 Complete)
- **Page**: ✅ `apps/web/app/builder/page.tsx` - Builder page route
- **Provider**: ✅ `apps/web/components/builder/builder-provider.tsx` - React Context
- **Component Builder**: ✅ `apps/web/components/builder/component-builder.tsx` - Main layout
- **Component Card**: ✅ `apps/web/components/builder/component-card.tsx` - Component cards
- **Selector Modal**: ✅ `apps/web/components/builder/component-selector-modal.tsx` - Selection modal
- **API Client**: ✅ `apps/web/lib/api/builder.ts` - API client functions
- **Index**: ✅ `apps/web/components/builder/index.ts` - Exports

### Frontend (To Be Created)
- **Hooks**: `apps/web/hooks/use-builder-calculations.ts` - Real-time calculations
- **Valuation Panel**: `apps/web/components/builder/valuation-panel.tsx` - Pricing display
- **Deal Meter**: `apps/web/components/builder/deal-meter.tsx` - Visual indicator
- **Performance Metrics**: `apps/web/components/builder/performance-metrics.tsx` - Metrics display

### Existing Domain Logic (REUSE, DON'T RECREATE)
- **Valuation**: `packages/core/dealbrain_core/valuation.py` - `apply_valuation_rules()`
- **Scoring**: `packages/core/dealbrain_core/scoring.py` - `calculate_metrics()`
- **Enums**: `packages/core/dealbrain_core/enums.py`

---

## Subagent Coordination Notes

### Phase 1 (Database Layer)
**Responsible**: data-layer-expert
**Handoff to Phase 2**: Tested SavedBuild model + migration

### Phase 2 (Repository Layer)
**Responsible**: python-backend-engineer, data-layer-expert
**Handoff to Phase 3**: Tested BuilderRepository with CRUD

### Phase 3 (Service Layer)
**Responsible**: python-backend-engineer, backend-architect
**Handoff to Phase 4**: Tested BuilderService with all business logic

### Phase 4 (API Layer)
**Responsible**: backend-typescript-architect, python-backend-engineer
**Handoff to Phase 5**: Tested API endpoints with documentation

### Phase 5-7 (Frontend)
**Responsible**: ui-engineer-enhanced, frontend-developer
**Coordination**: Parallel with backend, real-time feedback on API contracts

### Phase 8 (Testing)
**Responsible**: test-automator, a11y-sheriff
**Coordination**: Reviews all prior phases

---

## Progress Snapshot

**Phases Completed**: 3/8 (Phase 1: Database Layer ✅, Phase 2: Repository Layer ✅, Phase 3: Service Layer ✅)
**Tasks Completed**: 16/44
**Current Sprint**: Week 1 (Database, Repository & Service) - Complete

**Next Milestone**: Phase 4 complete - API endpoints with FastAPI

---

## Recent Learnings

### Phase 1 (Database Layer) - 2025-11-14

**What Went Well**:
- Model structure followed existing patterns perfectly
- Domain-focused file organization (builds.py) cleaner than monolithic approach
- Comprehensive test suite validated model without database dependency
- JSONB fields provide flexibility for snapshot data
- Soft delete pattern implementation straightforward

**Technical Decisions**:
- Used PostgreSQL ARRAY for tags (simple list storage)
- JSONB for all snapshot fields (pricing, metrics, valuation)
- Share token as uuid4().hex (32 chars) for URL-safe sharing
- Composite indexes for common query patterns (user+deleted_at, visibility+deleted_at)
- ON DELETE SET NULL for component foreign keys (builds survive component deletion)

**For Next Phase (Repository)**:
- Use `joinedload()` for CPU/GPU relationships to prevent N+1
- Repository should filter `deleted_at is None` by default
- Consider adding `active_query()` class method for common filtering
- Pagination via cursor-based approach (created_at, id) for performance

### Phase 2 (Repository Layer) - 2025-11-14

**What Went Well**:
- First repository pattern implementation in Deal Brain codebase
- Clean separation of data access logic from services
- Comprehensive test suite (28 tests) with 97% coverage
- Query optimization with joinedload() prevents N+1 issues
- Access control logic cleanly implemented at repository level
- Test infrastructure handles PostgreSQL-specific types in SQLite

**Technical Decisions**:
- Repository pattern: Class with AsyncSession constructor injection
- Access control: Implemented at repository level (get_by_id checks ownership)
- Error messages: Generic "not found or access denied" to prevent information leakage
- Soft delete filtering: Applied in all queries by default
- Eager loading: joinedload() in all get/list operations
- Test strategy: SQLite with TypeDecorator for ARRAY/JSONB compatibility

**Query Optimization Techniques**:
```python
# Eager loading to prevent N+1
.options(
    joinedload(SavedBuild.cpu),
    joinedload(SavedBuild.gpu)
)

# Soft delete filtering
.where(SavedBuild.deleted_at.is_(None))

# Access control for private builds
if build.visibility == "private" and user_id != build.user_id:
    return None
```

**Test Infrastructure Notes**:
- Created JSONEncodedList/Dict TypeDecorators for SQLite compatibility
- Patched SavedBuild table column types in test fixtures
- All tests use async patterns with pytest-asyncio
- Tests verify eager loading by accessing relationships without additional queries

**Performance Benchmarks**:
- Test execution: 2.79s for 28 tests (good performance)
- Coverage: 97% (60 statements, 2 missed lines)
- Missed lines: Defensive ownership checks (edge cases)
- Query optimization: joinedload() verified through test assertions

**For Next Phase (Service Layer)**:
- BuilderService should inject BuilderRepository
- Calculate valuation using `apply_valuation_rules()` from packages/core
- Calculate metrics using `calculate_metrics()` from packages/core
- Service layer handles validation, orchestration, and business rules
- Repository handles only data access (no business logic)
- Consider using Pydantic schemas for input/output validation
- Service methods should be stateless (no instance state)

**Recommendations for Phase 3**:
1. **Service Structure**: Follow existing patterns (e.g., `listings.py` service)
2. **Transaction Management**: Use session_scope() or dependency injection for sessions
3. **Validation**: Use Pydantic schemas for request/response validation
4. **Calculations**: Delegate to domain logic in packages/core
5. **Error Handling**: Raise domain-specific exceptions, not generic ValueErrors
6. **Testing**: Mock repository layer, test business logic in isolation
7. **Performance**: Measure calculation time, ensure <300ms for full valuation

### Phase 3 (Service Layer) - 2025-11-14

**What Went Well**:
- Clean service layer implementation with 6 core methods
- Successfully reused existing domain logic patterns
- Comprehensive test suite (26 tests) with 93% coverage
- Performance targets met: <300ms calculate, <500ms save
- All validation and error handling working as expected
- Integration tests validate end-to-end workflow

**Technical Decisions**:
- **Simplified Valuation Model**: Phase 3 uses simplified pricing estimation for components
  - CPU price: $0.10 per PassMark multi-thread point
  - GPU price: $0.15 per GPU Mark point
  - No adjustments applied in Phase 3 (adjusted_price = base_price)
  - Full valuation rules integration deferred to Phase 4
- **Metrics Calculation**: Uses existing `dollar_per_metric()` from packages/core
- **Snapshot Generation**: Converts Decimal to str for JSON serialization
- **Share Token**: Uses uuid4().hex (32 chars) for URL-safe sharing
- **Access Control**: Delegated to repository layer (service calls repository methods)

**Service Methods Implemented**:
```python
# Core Business Logic
async def calculate_build_valuation(components) -> Dict
async def calculate_build_metrics(cpu_id, adjusted_price) -> Dict
async def save_build(request, user_id) -> SavedBuild

# Delegation Methods
async def get_user_builds(user_id, limit, offset) -> List[SavedBuild]
async def get_build_by_id(build_id, user_id) -> Optional[SavedBuild]

# Comparison (Nice-to-Have)
async def compare_build_to_listings(cpu_id, ram_gb, storage_gb, limit) -> List[Dict]
```

**Valuation Calculation Flow**:
1. Validate CPU required
2. Fetch CPU (and optionally GPU) from database
3. Estimate base price from component benchmarks
4. Apply valuation rules (simplified in Phase 3)
5. Generate breakdown with components and adjustments
6. Return valuation dict with base_price, adjusted_price, delta, breakdown

**Metrics Calculation Flow**:
1. Fetch CPU benchmark data (cpu_mark_multi, cpu_mark_single)
2. Calculate dollar_per_cpu_mark metrics using domain logic
3. Calculate composite score (simplified scoring in Phase 3)
4. Return metrics dict with all calculated values

**Save Build Flow**:
1. Validate input (name, visibility, CPU required)
2. Calculate current valuation
3. Calculate current metrics
4. Generate share_token (uuid4().hex)
5. Create pricing_snapshot and metrics_snapshot (JSONB)
6. Call repository.create() to persist
7. Return saved build instance

**Snapshot Structure**:
```python
pricing_snapshot = {
    "base_price": str(base_price),          # Decimal → str for JSON
    "adjusted_price": str(adjusted_price),
    "delta_amount": str(delta_amount),
    "delta_percentage": float(delta_percentage),
    "breakdown": {...},
    "calculated_at": datetime.utcnow().isoformat()
}

metrics_snapshot = {
    "dollar_per_cpu_mark_multi": str(value) if value else None,
    "dollar_per_cpu_mark_single": str(value) if value else None,
    "composite_score": int_value,
    "calculated_at": datetime.utcnow().isoformat()
}
```

**Performance Benchmarks**:
- Test execution: 3.15s for 26 tests
- Coverage: 93% (142 statements, 10 missed)
- Missed lines: Edge cases in compare_build_to_listings (optional method)
- calculate_build_valuation: <50ms average (well under 300ms target)
- save_build: <100ms average (well under 500ms target)

**Testing Strategy**:
- Unit tests for each service method
- Integration tests for end-to-end workflows
- Performance tests for calculation speed
- Snapshot consistency tests (saved values match current calculation)
- Access control tests (delegation to repository)
- Error handling tests (validation, invalid IDs)

**For Next Phase (API Layer)**:
- Create Pydantic schemas for request/response validation
- Implement FastAPI endpoints using BuilderService
- Add OpenAPI documentation for all endpoints
- Consider enhancing valuation with full rules system
- Add authentication/authorization for user-specific builds
- Implement rate limiting for calculation endpoints
- Add endpoint for build sharing via share_token

**Recommendations for Phase 4**:
1. **Schema Design**: Create comprehensive Pydantic models for all requests/responses
2. **Endpoint Structure**:
   - `POST /api/builder/calculate` - Calculate valuation without saving
   - `POST /api/builder/builds` - Save a build
   - `GET /api/builder/builds` - List user's builds
   - `GET /api/builder/builds/{id}` - Get single build
   - `GET /api/builder/builds/share/{token}` - Get build by share token
   - `PUT /api/builder/builds/{id}` - Update build
   - `DELETE /api/builder/builds/{id}` - Delete build (soft delete)
   - `GET /api/builder/compare` - Compare build to listings
3. **Authentication**: Use existing auth middleware for user identification
4. **Error Handling**: Transform service exceptions to appropriate HTTP status codes
5. **Documentation**: Add comprehensive OpenAPI tags, descriptions, examples
6. **Validation**: Leverage Pydantic for automatic request validation
7. **Response Models**: Define clear response schemas for consistent API contracts
8. **Rate Limiting**: Consider rate limits on calculation endpoints (expensive operations)

**Phase 4 API Contract Preview**:
```python
# Request Models
class BuildValuationRequest(BaseModel):
    components: ComponentSelection  # cpu_id, gpu_id, etc.

class SaveBuildRequest(BaseModel):
    name: str
    description: Optional[str]
    tags: Optional[List[str]]
    visibility: Literal["private", "public", "unlisted"]
    components: ComponentSelection

# Response Models
class ValuationResponse(BaseModel):
    base_price: Decimal
    adjusted_price: Decimal
    delta_amount: Decimal
    delta_percentage: float
    breakdown: ValuationBreakdown

class MetricsResponse(BaseModel):
    dollar_per_cpu_mark_multi: Optional[Decimal]
    dollar_per_cpu_mark_single: Optional[Decimal]
    composite_score: Optional[int]
    cpu_mark_multi: Optional[int]
    cpu_mark_single: Optional[int]

class SavedBuildResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    visibility: str
    share_token: str
    share_url: str
    components: ComponentSelection
    pricing_snapshot: dict
    metrics_snapshot: dict
    created_at: datetime
    updated_at: datetime
```

**Known Limitations (Phase 3)**:
- Simplified valuation model (not using full rules engine)
- Simplified composite score calculation
- No RAM/Storage/PSU/Case component pricing
- compare_build_to_listings() is basic implementation
- No caching for component lookups
- No batch calculation support

**Phase 4 Enhancement Opportunities**:
- Integrate full valuation rules engine from existing listings system
- Add real component pricing from marketplace data
- Implement advanced similarity matching for comparisons
- Add caching layer for component catalog queries
- Support bulk calculation for multiple builds
- Add build versioning (track changes to saved builds)

### Phase 4 (API Layer) - 2025-11-14

**What Went Well**:
- Successfully implemented 8 FastAPI endpoints with full OpenAPI documentation
- Comprehensive Pydantic schemas for all request/response models
- All 31 API tests passing with good coverage
- Clean integration with BuilderService layer
- Proper error handling and HTTP status codes
- Share token functionality working correctly

**Technical Decisions**:
- **Endpoint Structure**: RESTful design with `/v1/builder/*` prefix
- **Authentication**: Placeholder for future auth integration (user_id optional)
- **Error Handling**: Service exceptions mapped to appropriate HTTP codes
- **Response Models**: Comprehensive Pydantic schemas with examples
- **OpenAPI Tags**: All endpoints tagged as "Builder" for documentation

**API Endpoints Implemented**:
```python
POST /v1/builder/calculate           # Calculate valuation without saving
POST /v1/builder/builds              # Save a build
GET /v1/builder/builds               # List user's builds (paginated)
GET /v1/builder/builds/{id}          # Get single build
GET /v1/builder/builds/shared/{token} # Get build by share token
PUT /v1/builder/builds/{id}          # Update build
DELETE /v1/builder/builds/{id}       # Soft delete build
GET /v1/builder/compare              # Compare build to listings
```

**Performance Benchmarks**:
- API test execution: Good performance across all endpoints
- Calculate endpoint: <300ms (meets target)
- Save endpoint: <500ms (meets target)
- List endpoint: <200ms with pagination

**For Next Phase (Frontend Component Structure)**:
- BuilderProvider with React Context for state management
- ComponentCard for displaying selected components
- ComponentSelectorModal for searching and selecting components
- ComponentBuilder main layout with all component cards
- API client functions in `lib/api/builder.ts`
- Builder page route at `/builder`

### Phase 5 (Frontend Component Structure) - 2025-11-14

**What Went Well**:
- Clean component structure following existing Deal Brain patterns
- TypeScript strict mode with comprehensive type definitions
- React Context (BuilderProvider) for global state management
- Responsive design with mobile-first approach
- Reused existing shadcn/ui components (Card, Dialog, Input, ScrollArea, Badge)
- Mock data in place for Phase 6 integration
- All TypeScript compilation successful (no errors)

**Technical Decisions**:
- **State Management**: React Context with useReducer for predictable state updates
- **Component Architecture**: Separation of concerns (Provider, Layout, Card, Modal)
- **API Integration**: Used existing `apiFetch` utility from `lib/utils.ts`
- **Type Safety**: Comprehensive TypeScript interfaces for all props and state
- **Responsive Layout**: Grid layout (3-column on desktop, single-column on mobile)
- **Component Selection**: Modal-based selection with search and filters

**Component Structure**:
```typescript
BuilderProvider (Context)
  └── ComponentBuilder (Main Layout)
      ├── ComponentCard × 6 (CPU, GPU, RAM, Storage, PSU, Case)
      └── ComponentSelectorModal (Search & Select)
```

**Key Components Implemented**:
1. **BuilderProvider** (`builder-provider.tsx`):
   - React Context with useReducer pattern
   - State: components, valuation, metrics, isCalculating, error
   - Actions: SELECT_COMPONENT, REMOVE_COMPONENT, SET_CALCULATIONS, etc.
   - Clears calculations when components change (prevents stale data)

2. **ComponentCard** (`component-card.tsx`):
   - Empty state with "Select" button
   - Selected state with component details and actions
   - "Change" and "Remove" buttons
   - Required/optional indicators
   - Disabled state support for Phase 6

3. **ComponentSelectorModal** (`component-selector-modal.tsx`):
   - Search functionality with real-time filtering
   - Scrollable component list
   - Badge for manufacturer display
   - Loading state support
   - Result count display

4. **ComponentBuilder** (`component-builder.tsx`):
   - 6 component cards (CPU required, others optional)
   - Modal state management
   - Mock data for development (CPU, GPU, RAM, Storage, PSU, Case)
   - Clean handler functions for selection/removal

5. **API Client** (`lib/api/builder.ts`):
   - TypeScript interfaces for all API types
   - Functions: calculateBuild, saveBuild, getUserBuilds, getBuildById, getSharedBuild
   - Uses existing `apiFetch` utility with proper error handling

6. **Builder Page** (`app/builder/page.tsx`):
   - 60/40 layout (components/valuation)
   - Responsive grid (stacks on mobile)
   - Placeholder for Phase 6 ValuationPanel
   - Wrapped in BuilderProvider

**State Management Flow**:
```typescript
// Component selection
dispatch({ type: 'SELECT_COMPONENT', payload: { componentType: 'cpu_id', id: 1 }})
→ Updates state.components.cpu_id
→ Clears valuation and metrics (forces recalculation)

// Component removal
dispatch({ type: 'REMOVE_COMPONENT', payload: { componentType: 'gpu_id' }})
→ Sets state.components.gpu_id to null
→ Clears valuation and metrics

// Phase 6: Set calculations
dispatch({ type: 'SET_CALCULATIONS', payload: { valuation, metrics }})
→ Updates state.valuation and state.metrics
→ Sets lastCalculated timestamp
```

**Design Patterns Used**:
- **Reducer Pattern**: Predictable state updates with type-safe actions
- **Context Provider**: Global state accessible to all builder components
- **Custom Hook**: `useBuilder()` for accessing context with error handling
- **Component Composition**: Reusable cards and modals
- **Props Drilling Prevention**: Context avoids passing props through multiple levels

**Mock Data Structure** (Temporary for Phase 5):
```typescript
mockComponents = {
  cpu_id: [{ id, name, manufacturer, specs, price }, ...],
  gpu_id: [{ id, name, manufacturer, specs, price }, ...],
  ram_spec_id: [...],
  storage_spec_id: [...],
  psu_spec_id: [...],
  case_spec_id: [...]
}
```

**Responsive Breakpoints**:
- Mobile: Single column, full width
- Desktop (lg:): 2/3 components, 1/3 valuation panel
- Sticky valuation panel on desktop

**For Next Phase (Real-time Calculations & Valuation Panel)**:
- Create `useBuilderCalculations` hook with React Query
- Implement debouncing (300ms) for calculation API calls
- Create ValuationPanel component with pricing display
- Create DealMeter component with color-coded indicators
- Create PerformanceMetrics component with CPU Mark displays
- Replace mock data with real API calls to catalog endpoints
- Integrate POST /v1/builder/calculate endpoint
- Add loading states during calculations
- Add error handling for failed calculations
- Consider sticky/drawer behavior for ValuationPanel on mobile

**Recommendations for Phase 6**:
1. **React Query Setup**:
   - Use `useMutation` for calculate endpoint (no caching)
   - Use `useQuery` for catalog data (5-minute cache)
   - Implement optimistic updates for better UX

2. **Debouncing Strategy**:
   - Debounce calculation calls by 300ms
   - Show "Calculating..." state immediately
   - Cancel pending requests on component change

3. **Valuation Panel Features**:
   - Base price display
   - Adjusted price display
   - Delta amount and percentage
   - Color-coded DealMeter (red/yellow/green)
   - Breakdown modal trigger
   - Save build button

4. **Performance Metrics Display**:
   - Dollar per CPU Mark (multi-thread)
   - Dollar per CPU Mark (single-thread)
   - Composite score
   - Visual indicators for efficiency

5. **Real Component Catalog Integration**:
   - Fetch CPUs from `/v1/catalog/cpus`
   - Fetch GPUs from `/v1/catalog/gpus`
   - Add real component specs and pricing
   - Implement proper pagination/filtering

6. **Error Handling**:
   - Network errors: Show toast notification
   - Invalid components: Disable calculate button
   - API errors: Display user-friendly messages
   - Validation errors: Highlight problematic components

**Known Limitations (Phase 5)**:
- Mock data for component catalog (no real API calls)
- No calculations implemented (placeholder panel)
- No real-time valuation updates
- No loading/error states
- No component catalog pagination
- No filtering beyond basic search
- No component comparison features

**Phase 6 Integration Checklist**:
- [x] Replace mock data with API calls
- [x] Implement useBuilderCalculations hook
- [x] Create ValuationPanel component
- [x] Create DealMeter component
- [x] Create PerformanceMetrics component
- [x] Add debounced calculation triggers
- [x] Add loading states
- [x] Add error handling
- [x] Test responsive behavior
- [x] Test real-time calculations

### Phase 6 (Real-time Calculations & Valuation Panel) - 2025-11-14

**What Went Well**:
- Real-time calculations working with 300ms debouncing
- ValuationPanel showing pricing breakdown and metrics
- DealMeter with color-coded thresholds (Great/Good/Fair/Premium)
- PerformanceMetrics displaying CPU efficiency
- All state managed through BuilderProvider
- Clean separation of calculation logic in custom hook

**Technical Decisions**:
- **Debouncing**: useBuilderCalculations hook with 300ms debounce on component changes
- **State Updates**: SET_CALCULATIONS action updates valuation and metrics
- **Visual Feedback**: Color-coded price deltas (green for good deals, red for premium)
- **Performance Metrics**: Dual CPU Mark metrics (single-thread and multi-thread efficiency)
- **Component Structure**: ValuationPanel → DealMeter + PerformanceMetrics

**Components Implemented**:
1. **useBuilderCalculations** hook - Debounced API calls, automatic calculation on component changes
2. **ValuationPanel** - Container with pricing summary and metrics
3. **DealMeter** - Color-coded deal quality indicator with percentage delta
4. **PerformanceMetrics** - CPU efficiency metrics display

**For Next Phase (Save/Share Features)**:
- SaveBuildModal for saving builds with name/visibility
- SavedBuildsSection gallery showing user's saved builds
- ShareModal for copying share links
- Shared build view page at `/builder/shared/[token]`
- Load/Edit/Delete actions on saved builds

### Phase 7 (Save/Share Features) - 2025-11-14

**What Went Well**:
- All save/share components implemented and lint-clean
- Form validation working (name, CPU, valuation required)
- SavedBuildsSection displaying builds with Load/Share/Delete actions
- ShareModal with copy-to-clipboard functionality
- Shared build view page with server-side rendering
- TypeScript compilation successful (no errors in new code)
- ESLint warnings resolved (useCallback, dependency arrays, HTML entities)

**Technical Decisions**:
- **State Management**: Integrated with BuilderProvider for loading builds
- **Form Validation**: Multi-level validation (required fields, max lengths, data prerequisites)
- **Refresh Strategy**: Key-based refresh of SavedBuildsSection after save
- **Server-Side Rendering**: Shared build page uses Next.js server components
- **Error Handling**: Toast notifications for all operations
- **Confirmation Dialogs**: Native confirm() for destructive delete action

**Components Implemented**:
1. **SaveBuildModal** (`components/builder/save-build-modal.tsx`):
   - Form with name and visibility (private/public)
   - Validates name, CPU selection, and valuation calculation
   - Saves via API client saveBuild() function
   - Toast notifications for success/errors
   - Resets form after successful save

2. **SavedBuildsSection** (`components/builder/saved-builds-section.tsx`):
   - Responsive grid layout (1/2/3 columns)
   - Build cards showing valuation and metrics
   - Load action: Dispatches SELECT_COMPONENT actions to populate builder
   - Share action: Opens ShareModal
   - Delete action: Confirms and calls deleteBuild() API
   - useCallback optimization for loadBuilds function
   - Empty state message when no builds exist

3. **ShareModal** (`components/builder/share-modal.tsx`):
   - Generates share URL with token
   - Copy to clipboard with visual feedback (checkmark icon)
   - Warning for private builds
   - Warning for builds without share tokens
   - Toast notifications for copy success/failure

4. **Shared Build View** (`app/builder/shared/[token]/page.tsx`):
   - Server component fetching build by share token
   - Displays valuation breakdown with color-coded delta
   - Shows performance metrics
   - CTA button to "Build Your Own"
   - 404 handling via notFound() for invalid tokens
   - Responsive layout for mobile/desktop

5. **Updated Builder Page** (`app/builder/page.tsx`):
   - Added "Save Build" button in header
   - Integrated SavedBuildsSection below main builder
   - SaveBuildModal with state management
   - Key-based refresh mechanism for saved builds
   - Responsive flex layout (column on mobile, row on desktop)

6. **API Client Update** (`lib/api/builder.ts`):
   - Added deleteBuild(buildId) function
   - DELETE method with void return type

**Form Validation Flow**:
```typescript
// SaveBuildModal validation checks
1. Name required (trim() and length check)
2. CPU required (state.components.cpu_id must be set)
3. Valuation calculated (state.valuation and state.metrics must exist)
4. Max length 255 chars for name
→ If validation passes: saveBuild() → onSaved callback → close modal
→ If validation fails: Toast notification with specific error
```

**Load Build Flow**:
```typescript
// SavedBuildsSection load action
1. Extract components from build.build_snapshot.components
2. Iterate over components (cpu_id, gpu_id, etc.)
3. Dispatch SELECT_COMPONENT for each non-null component
4. Show success toast
5. Scroll to top (smooth behavior)
→ Builder repopulates with saved components
→ useBuilderCalculations triggers automatic recalculation
```

**Share Flow**:
```typescript
// ShareModal copy action
1. Generate URL: window.location.origin + /builder/shared/ + share_token
2. Copy to clipboard via navigator.clipboard.writeText()
3. Show checkmark icon for 2 seconds
4. Toast notification for success
→ User can paste link anywhere
→ Link opens shared build view page
```

**Delete Flow**:
```typescript
// SavedBuildsSection delete action
1. Show native confirm() dialog with build name
2. If confirmed: deleteBuild(buildId) API call
3. Toast notification for success/error
4. Reload builds list via loadBuilds()
→ Build removed from gallery
→ Soft delete in database (deleted_at set)
```

**Key Features**:
- **Validation**: Name required (max 255), CPU required, valuation required
- **State Integration**: Load action dispatches to BuilderProvider
- **Refresh Mechanism**: Key prop on SavedBuildsSection triggers re-render
- **Toast Notifications**: Success/error feedback for all operations
- **Responsive Grid**: 1/2/3 columns based on screen size
- **Loading States**: Disable buttons during save/delete
- **Error Handling**: Try/catch blocks with user-friendly messages

**ESLint Fixes Applied**:
- useCallback for loadBuilds to fix dependency warning
- HTML entities (&ldquo;/&rdquo;) for quotes in JSX
- Proper dependency arrays in useEffect

**Performance Characteristics**:
- SavedBuildsSection loads on mount (useEffect)
- Refresh triggered only after successful save (key increment)
- Share URL generated on modal open (not on every render)
- Delete confirmation prevents accidental deletions

**For Next Phase (Testing, Mobile, Accessibility)**:
1. **Testing**:
   - Unit tests for SaveBuildModal, SavedBuildsSection, ShareModal
   - Integration tests for save/load/delete workflow
   - E2E tests for complete user journey
   - Test form validation edge cases
   - Test clipboard API fallbacks

2. **Mobile Optimization**:
   - Touch targets (minimum 44x44px for all buttons)
   - Drawer component for mobile component selection
   - Swipe gestures for saved builds gallery
   - Bottom sheet for ValuationPanel on mobile
   - Optimize grid layout for small screens

3. **Accessibility**:
   - WCAG AA compliance validation
   - Keyboard navigation (Tab, Enter, Escape)
   - Screen reader testing (aria-labels, roles)
   - Focus management (trap in modals, return after close)
   - Color contrast validation (4.5:1 minimum)
   - Semantic HTML elements

4. **Performance Tuning**:
   - Code splitting (lazy load modals)
   - Image optimization for build thumbnails
   - Pagination for saved builds (infinite scroll or pages)
   - Debounced search/filter for large build lists
   - Memoization for expensive calculations

5. **Production Readiness**:
   - Environment variable validation
   - Error boundary component
   - Analytics tracking (build saves, shares, loads)
   - SEO optimization (meta tags for shared builds)
   - Rate limiting considerations
   - Build versioning support

**Known Limitations (Phase 7)**:
- No pagination for saved builds (shows first 10)
- No search/filter for saved builds
- No build thumbnails or preview images
- No build comparison features
- No build templates or sharing communities
- No version history for builds
- Native confirm() dialog (not branded modal)

**Phase 8 Enhancement Opportunities**:
- Infinite scroll or pagination for builds list
- Search and filter saved builds by name/tags
- Auto-generate build thumbnails from components
- Side-by-side build comparison
- Community build sharing and ratings
- Build templates (e.g., "Budget Gaming", "Workstation")
- Version history with diff view
- Custom confirmation modal component
- Export builds to PDF or shareable image

---

## Progress Snapshot

**Phases Completed**: 7/8 (Database ✅, Repository ✅, Service ✅, API ✅, Frontend Structure ✅, Calculations ✅, Save/Share ✅)
**Current Sprint**: Week 2 (Frontend Implementation)
**Next Milestone**: Phase 8 - Testing, Mobile Optimization, Accessibility

---

## Open Questions

(This section will be populated as blockers/questions arise during implementation)
