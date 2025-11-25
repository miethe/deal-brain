---
title: "Deal Builder - Implementation Plan"
description: "Phased implementation plan for interactive PC build configuration with real-time valuation and deal quality indicators. Covers database, backend, frontend, and testing phases."
audience: [ai-agents, developers]
tags: [implementation, planning, deal-builder, phases, subagents, backend, frontend]
created: 2025-11-12
updated: 2025-11-12
category: "product-planning"
status: draft
related:
  - /home/user/deal-brain/docs/project_plans/PRDs/features/deal-builder-v1.md
  - /home/user/deal-brain/docs/design/deal-builder-ux-specification.md
  - /home/user/deal-brain/docs/design/deal-builder-implementation-guide.md
---

# Deal Builder - Implementation Plan

## Executive Summary

**Feature**: Interactive PC build configuration tool with real-time valuation, performance metrics, and shareable builds.

**Complexity**: Large (L) - 25-30 tasks, 4-6 weeks estimated

**Approach**: Layer-by-layer backend implementation (Database → Repository → Service → API) in parallel with component-driven frontend development. Shared valuation system integration enables real-time calculations reusing existing rules and scoring logic.

**Key Milestones**:
1. **Week 1**: Database schema + Repository layer ready
2. **Week 2**: BuilderService + API endpoints functional
3. **Week 3**: Frontend components + real-time calculations
4. **Week 4**: Save/Share features fully integrated
5. **Week 5**: Mobile optimization + accessibility
6. **Week 6**: Testing, performance tuning, deployment

**Success Criteria**:
- API response time <300ms for calculations
- Component selection modal loads <500ms
- Page initial load <2s
- Save/load workflow end-to-end
- Share URLs functional and accessible
- WCAG AA accessibility compliance
- 95%+ test coverage on backend service logic

**Team Structure**:
- **Database/Migrations**: data-layer-expert (1 agent)
- **Repository/Service**: python-backend-engineer (1-2 agents)
- **API Endpoints**: backend-typescript-architect (1 agent)
- **Frontend Components**: ui-engineer-enhanced, frontend-developer (2 agents)
- **Testing**: test-automator, testing-specialists (1-2 agents)
- **Overall Coordination**: This orchestrator + phase review agents

---

## Implementation Strategy

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend (Next.js)                      │
├─────────────────────────────────────────────────────────────────┤
│ /builder - BuilderProvider → ComponentBuilder → ValuationPanel   │
│ /builder/shared/[token] - Shared build read-only view           │
│ React Query for API calls, debounced calculations               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    API Layer (FastAPI)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Backend Layered Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│ Routers (builder.py) → Services (builder_service.py)            │
│ → Repositories (builder_repository.py)                          │
│ → Database (SavedBuild ORM model + migrations)                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                  Existing Valuation System
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ packages/core: valuation.py, scoring.py, enums.py              │
│ Reuse: apply_valuation_rules(), calculate_metrics()            │
└─────────────────────────────────────────────────────────────────┘
```

### Sequencing Strategy

**Critical Path**:
1. Database schema (SavedBuild model + migration) - BLOCKING
2. Repository layer (CRUD operations, queries) - BLOCKING
3. Service layer (business logic, valuation integration) - BLOCKING
4. API endpoints (POST /calculate, POST /builds, GET /builds/*) - BLOCKING
5. Frontend context + component structure - Can start once API skeleton exists
6. Component selection + valuation calculations - Depends on API working
7. Save/Share UI + functionality - Depends on database persistence
8. Mobile + accessibility + testing - Can run in parallel with features

**Parallel Work Opportunities**:
- **Week 1-2**: Phase 1 (Database) runs completely isolated
- **Week 2 (Day 3+)**: Repository layer starts while DB migration finalizes
- **Week 2 (Day 4+)**: Service layer starts while Repository is being tested
- **Week 3**: Frontend component development starts in parallel with Phase 4 API testing
- **Week 4-5**: Save/Share and Mobile work can happen simultaneously with API refinement
- **Week 6**: Testing/QA can start on Phase 4-5 deliverables while Phase 8 is being executed

### Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Slow valuation calculations (many components) | Medium | High | Implement caching, optimize queries, add timeouts, test with 10+ components early |
| N+1 query problems in API | Medium | High | Use eager loading/joinedload from start, test with QueryCount monitoring |
| Frontend state management complexity | Medium | Medium | Start with simple reducer, test state transitions early |
| Mobile UX issues | Low | Medium | Implement floating drawer first, test on multiple devices early |
| Share token collisions | Very Low | High | Use uuid4 with database unique constraint, no custom implementation |
| Feature adoption slower than expected | Low | Medium | Easy access from listings page, in-app prompts, marketing coordination |
| Performance degradation as saved_builds table grows | Low | Medium | Implement pagination from start, test with 10k+ records |

---

## Phase Breakdown

### Phase 1: Database Layer (Days 1-2, 2-3 points)

**Goal**: SavedBuild table exists with proper schema, indexes, and soft delete support.

**Deliverables**:
- SavedBuild SQLAlchemy model in `apps/api/dealbrain_api/models/core.py`
- Alembic migration creating table with indexes
- Model relationships to CPU, GPU, RAM, Storage entities
- Soft delete support via `deleted_at` column

**Acceptance Criteria**:
- Table created and migration runs successfully
- All columns present with correct types (Decimal for prices, JSONB for snapshots)
- Indexes created: `idx_user_builds (user_id, deleted_at)`, `idx_share_token`, `idx_visibility`
- Foreign keys to CPU, GPU, etc. if available
- Soft delete queries work (filter by deleted_at is None)
- Unique constraint on share_token prevents collisions

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-1-3-backend-database.md`

---

### Phase 2: Repository Layer (Days 3-4, 3 points)

**Goal**: Data access layer for SavedBuild CRUD operations and queries.

**Deliverables**:
- BuilderRepository class with async methods
- Standard CRUD: create, read, update, delete (soft)
- Bulk queries: by_user_id, by_share_token, paginated list
- Query optimization: eager loading relationships, optimized for performance

**Acceptance Criteria**:
- All CRUD operations work correctly
- Queries return data sorted correctly (created_at desc for list)
- Pagination working (limit + offset)
- Soft delete respected in all queries (deleted_at is None filter)
- No N+1 queries (use joinedload)
- Response time <100ms for typical queries

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-1-3-backend-database.md`

---

### Phase 3: Service Layer (Days 5-6, 5 points)

**Goal**: Business logic layer orchestrating valuation, validation, and persistence.

**Deliverables**:
- BuilderService with core methods:
  - `calculate_build_valuation(components)` - Use existing valuation.py
  - `calculate_build_metrics(cpu, adjusted_price)` - Use existing scoring.py
  - `save_build(request)` - Persist with snapshot
  - `get_user_builds(user_id)` - List with pagination
  - `compare_build_to_listings(cpu_id, ram, storage)` - Find similar listings
- Input validation (component IDs exist, etc.)
- Snapshot creation (pricing, metrics, breakdown at save time)
- Share token generation (uuid4 format)

**Acceptance Criteria**:
- Calculations match existing listing valuation within 1% tolerance
- Metrics calculated correctly ($/CPU Mark formulas verified)
- Save creates snapshot that's retrievable later
- Share token is unique and URL-safe
- Validation catches invalid component IDs
- All methods have >85% test coverage
- Performance <300ms for calculate, <500ms for save

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-1-3-backend-database.md`

---

### Phase 4: API Layer (Days 7-9, 5 points)

**Goal**: FastAPI router with endpoints for frontend integration.

**Deliverables**:
- BuilderRouter in `apps/api/dealbrain_api/api/builder.py`
- Endpoints (all under `/v1/builder/`):
  - `POST /calculate` - Request validation, call service, return pricing + metrics
  - `POST /builds` - Save build with validation
  - `GET /builds` - List user's builds with pagination
  - `GET /builds/{id}` - Get single build (check access control)
  - `PATCH /builds/{id}` - Update build
  - `DELETE /builds/{id}` - Soft delete
  - `GET /builds/shared/{token}` - Get by share token (no auth required for public)
  - `GET /compare` - Compare build to listings

**Acceptance Criteria**:
- All endpoints return correct response schemas
- Request validation (required fields, valid IDs)
- Response time <300ms for /calculate, <500ms for /builds list
- Error handling: 400 for bad input, 404 for not found, 403 for access denied
- CORS headers correct
- Documentation in docstrings
- Integration tests for all happy paths

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-4-integration.md`

---

### Phase 5: Frontend Component Structure (Days 10-11, 3 points)

**Goal**: Core React components and state management.

**Deliverables**:
- BuilderProvider context (component selection state, calculations)
- ComponentBuilder layout (left panel with component cards)
- ComponentCard component (empty/selected states)
- ComponentSelectorModal (searchable component list)
- Page structure and routing

**Acceptance Criteria**:
- Context dispatch works (select/remove component)
- State persists correctly (not lost on re-render)
- Modal opens/closes properly
- Component cards show selected state
- Layout matches design (left 60%, right 40% on desktop)
- Mobile layout stacks correctly

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-5-7-frontend.md`

---

### Phase 6: Valuation Display & Real-time Calculations (Days 12-14, 5 points)

**Goal**: Live calculations, deal meter, performance metrics display.

**Deliverables**:
- ValuationPanel component (sticky on desktop, drawer on mobile)
- DealMeter component (color-coded, percentage display)
- PerformanceMetrics display ($/CPU Mark, composite score)
- ValuationBreakdown expandable section
- React Query integration with debounced API calls (300ms)
- Real-time updates when components change

**Acceptance Criteria**:
- Calculations trigger 300ms after component selection
- Pricing updates visible within 500ms
- Deal meter color matches thresholds (great/good/fair/premium)
- Performance metrics display with correct formulas
- Breakdown shows component prices + applied rules
- Loading state shown during calculation
- Error states handled (API timeout, invalid components)

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-5-7-frontend.md`

---

### Phase 7: Save/Share Features (Days 15-17, 5 points)

**Goal**: Persist builds, create shareable URLs, manage saved builds.

**Deliverables**:
- SaveBuildModal (form for name, description, visibility)
- SavedBuildsSection (gallery of user's builds)
- ShareModal (copy link, export options)
- Shared build view page (`/builder/shared/[token]`)
- Load/Edit/Delete actions on saved builds
- API mutations (POST save, PATCH update, DELETE, GET shared)

**Acceptance Criteria**:
- Save modal validates name (required)
- Build saved with snapshot of pricing/metrics
- Share token generated and URL accessible
- Shared URL shows read-only build (no editing)
- Load build repopulates builder correctly
- Delete requires confirmation
- Edit updates existing build (not create new)
- Saved builds section responsive (3 cols desktop, 1 col mobile)

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-5-7-frontend.md`

---

### Phase 8: Testing, Mobile & Deployment (Days 18-20, 5 points)

**Goal**: Comprehensive testing, mobile optimization, accessibility, production readiness.

**Deliverables**:
- Unit tests: BuilderService methods, utilities
- Integration tests: Service + Repository + Database
- Component tests: React components with different states
- E2E tests: Complete workflows (select → calculate → save → share)
- Mobile responsiveness (floating drawer, touch targets)
- Accessibility testing (WCAG AA, keyboard nav, screen reader)
- Performance optimization (memoization, code splitting)
- Documentation updates
- Deployment checklist

**Acceptance Criteria**:
- Backend test coverage >85%
- Component test coverage >80%
- E2E tests cover all major workflows
- Mobile layout passes on iOS Safari, Android Chrome
- WCAG AA accessibility validated
- Lighthouse score >95 on performance
- No console errors/warnings
- All PRD acceptance criteria met

**See**: `/home/user/deal-brain/docs/project_plans/implementation_plans/features/deal-builder-v1/phase-8-validation.md`

---

## Task Breakdown Summary

### Backend Tasks (Phases 1-4)

| Phase | Task Count | Story Points | Primary Agents |
|-------|-----------|--------------|-----------------|
| Phase 1: Database | 4 | 3 | data-layer-expert |
| Phase 2: Repository | 3 | 3 | python-backend-engineer, data-layer-expert |
| Phase 3: Service | 6 | 5 | python-backend-engineer, backend-architect |
| Phase 4: API | 8 | 5 | backend-typescript-architect, python-backend-engineer |

### Frontend Tasks (Phases 5-7)

| Phase | Task Count | Story Points | Primary Agents |
|-------|-----------|--------------|-----------------|
| Phase 5: Components | 4 | 3 | ui-engineer-enhanced, frontend-developer |
| Phase 6: Valuation | 5 | 5 | frontend-developer, react-performance-optimizer |
| Phase 7: Save/Share | 5 | 5 | ui-engineer-enhanced, frontend-developer |

### Testing/Deployment Tasks (Phase 8)

| Phase | Task Count | Story Points | Primary Agents |
|-------|-----------|--------------|-----------------|
| Phase 8: Testing | 6 | 5 | test-automator, a11y-sheriff |

**Total**: ~44 tasks, ~34 story points, 4-6 weeks

---

## Resource Requirements

### Recommended Subagent Assignments

**Data Layer Specialist**:
- Agent: data-layer-expert
- Assignment: Phase 1 (Database) + Phase 2 (Repository optimization)
- Effort: 6 story points
- Critical path blocker: Yes

**Backend Service Engineer**:
- Agent: python-backend-engineer
- Assignment: Phase 2 (Repository) + Phase 3 (Service layer)
- Effort: 8 story points
- Critical path blocker: Yes

**Backend Architect**:
- Agent: backend-architect
- Assignment: Phase 3 (Service integration with valuation system) + Phase 4 oversight
- Effort: 3 story points
- Critical path blocker: Yes

**API Engineer**:
- Agent: backend-typescript-architect
- Assignment: Phase 4 (API router, schema validation)
- Effort: 5 story points
- Critical path blocker: Yes

**Frontend Engineer (Primary)**:
- Agent: ui-engineer-enhanced
- Assignment: Phase 5 (Components) + Phase 7 (Save/Share UI)
- Effort: 8 story points
- Critical path blocker: Yes

**Frontend Developer**:
- Agent: frontend-developer
- Assignment: Phase 5-6 (Component development, real-time updates)
- Effort: 8 story points
- Critical path blocker: Yes

**Performance Specialist**:
- Agent: react-performance-optimizer
- Assignment: Phase 6 (Debouncing, memoization) + Phase 8 (optimization)
- Effort: 3 story points
- Nice to have but recommended

**Testing Specialist**:
- Agent: test-automator
- Assignment: Phase 8 (Unit, integration, E2E tests)
- Effort: 5 story points
- Critical path: Week 6

**Accessibility Specialist**:
- Agent: a11y-sheriff
- Assignment: Phase 8 (WCAG AA validation, keyboard nav)
- Effort: 2 story points
- Critical path: Week 5

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time - Calculate | <300ms | Backend performance monitoring |
| API Response Time - Get Builds | <500ms | Load test with 1000 saved builds |
| Component Modal Load | <500ms | Frontend performance monitoring |
| Page Initial Load | <2s | Lighthouse performance report |
| Build Save/Load | <1s | End-to-end timing test |
| Test Coverage (Backend) | >85% | pytest coverage report |
| Test Coverage (Frontend) | >80% | Jest/React Testing Library report |
| WCAG AA Score | 100% | WAVE accessibility validator |
| Lighthouse Score | >95 | Lighthouse audit report |
| Database Query Time | <100ms | query monitoring (no N+1) |

### Functional Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| CPU Selection Required | Yes | Component still fails if missing |
| Real-time Updates | All changes | <500ms latency verified |
| Save Workflow | End-to-end | Create → Save → Load = same data |
| Share Feature | URLs accessible | /builder/shared/[token] works |
| Mobile Responsive | <768px stacks | Manual testing on 3+ devices |
| Keyboard Navigation | All interactions | Tab through all controls |
| Accessibility Announcements | Price updates | aria-live tested with screen reader |

### Adoption Metrics (Post-Launch)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Builds Created/DAU | 0.3+ | Analytics event tracking |
| Save Rate | 40%+ | Builds saved / builds started |
| Share Rate | 25%+ | Shared URLs / saved builds |
| Feature Adoption | 30% MAU | Monthly active users using feature |
| Session Time | >5 minutes | Average page duration |
| Error Rate | <1% | API error logs |

---

## Parallel Work Tracks

### Track 1: Backend (Weeks 1-2, then refinement)
- **Leads**: data-layer-expert, python-backend-engineer, backend-architect
- **Work**: Database → Repository → Service → API
- **Blockers**: None (parallel with frontend)
- **Gating**: API must be testable by end of Week 2

### Track 2: Frontend Components (Weeks 2-3, then refinement)
- **Leads**: ui-engineer-enhanced, frontend-developer
- **Work**: Context → Layout → Component Selection → Valuation Panel
- **Blockers**: Needs API endpoints (from Track 1) to test integration
- **Gating**: Components must integrate with real API by end of Week 3

### Track 3: Save/Share & Mobile (Weeks 3-4)
- **Leads**: ui-engineer-enhanced, frontend-developer
- **Work**: SaveBuild → SavedBuilds Gallery → Share → Shared View
- **Blockers**: Depends on database persistence (Phase 1 complete)
- **Gating**: All features must be testable by end of Week 4

### Track 4: Testing & Deployment (Weeks 4-6)
- **Leads**: test-automator, a11y-sheriff
- **Work**: Unit tests → Integration tests → E2E tests → Accessibility
- **Blockers**: Can start mocking APIs in Week 2, integrate real APIs in Week 3
- **Gating**: All tests green + accessibility validated before deployment

---

## Detailed Phase Files

See separate documents for complete task breakdowns:

- **[Phase 1-3: Backend Database & Service](./deal-builder-v1/phase-1-3-backend-database.md)**
  - Database schema design
  - Migration strategy
  - Repository CRUD operations
  - Service business logic
  - Detailed task table with acceptance criteria

- **[Phase 4: API Integration](./deal-builder-v1/phase-4-integration.md)**
  - Router design and endpoints
  - Request/response schemas
  - API contracts
  - Error handling strategy
  - Detailed task table with API specifications

- **[Phase 5-7: Frontend Components & Features](./deal-builder-v1/phase-5-7-frontend.md)**
  - Component architecture
  - State management strategy
  - Real-time calculation flow
  - Save/Share workflows
  - Mobile responsiveness
  - Detailed task table with component specifications

- **[Phase 8: Testing, Mobile & Deployment](./deal-builder-v1/phase-8-validation.md)**
  - Testing strategy (unit/integration/E2E)
  - Accessibility requirements
  - Mobile optimization checklist
  - Performance tuning
  - Deployment readiness
  - Detailed task table with test specifications

---

## Critical Success Factors

1. **Reuse Existing Valuation Logic**: Don't reimplement - directly import and call `apply_valuation_rules()` from `packages/core/valuation.py`

2. **Real-time Debouncing**: API calls must be debounced at 300ms to prevent overwhelming backend during rapid selections

3. **Snapshot Consistency**: When saving build, capture pricing/metrics at that moment - future UI loads must show original saved values

4. **Mobile-First Drawer**: Floating drawer pattern for mobile must be tested early - affects Phases 5-6

5. **Share Token Security**: Use uuid4 with database unique constraint - no custom generation

6. **Eager Loading**: All repository queries must use joinedload to prevent N+1 issues - critical for performance

7. **Early E2E Testing**: Complete end-to-end workflow tests (select → calculate → save → load → share) must run by mid-Week 3

---

## Communication Plan

### Subagent Handoffs

**Phase 1 → Phase 2**:
- data-layer-expert → python-backend-engineer
- Deliverable: Tested SavedBuild model with migration
- Handoff: Model documentation, migration file

**Phase 2 → Phase 3**:
- python-backend-engineer → python-backend-engineer + backend-architect
- Deliverable: Tested BuilderRepository with all CRUD operations
- Handoff: Repository interface documentation

**Phase 3 → Phase 4**:
- python-backend-engineer + backend-architect → backend-typescript-architect
- Deliverable: Tested BuilderService with all business logic
- Handoff: Service method documentation, integration tests

**Phase 4 → Phase 5**:
- backend-typescript-architect → ui-engineer-enhanced + frontend-developer
- Deliverable: Tested API endpoints
- Handoff: API documentation, example cURL requests, response schemas

**Phase 5-6 ↔ Phase 4**:
- Parallel coordination: frontend-developer integrates with API as it's being built
- Handoff: Real-time feedback on API contracts, changes if needed

**Phase 7 ↔ Phase 3**:
- Coordinates with database: Schema validated for snapshot storage
- Handoff: Snapshot field definitions, JSONB structure

**Phase 8 ↔ All Phases**:
- test-automator: Creates tests for all phases as they complete
- a11y-sheriff: Reviews components and provides accessibility feedback

---

## Assumptions & Constraints

### Assumptions
- User authentication handled by existing system (not required for MVP)
- Component pricing data already exists in database
- PassMark benchmark data already imported
- Existing valuation.py and scoring.py functions are stable
- Next.js and FastAPI infrastructure ready
- React Query already in use for API calls

### Constraints
- Timeline: 6 weeks maximum
- Team: 7-9 subagents (some shared)
- Database: No major schema changes to existing tables (SavedBuild is new)
- API: Must follow existing `/v1/` versioning convention
- Frontend: Must use existing shadcn/ui components

### Out of Scope (Phase 2+)
- Component compatibility validation
- Price history tracking
- Build templates
- AI recommendations
- Community gallery
- Multi-user collaboration

---

## Deployment & Rollout

### Staging Validation (End of Week 5)
- [ ] All Phase 1-7 features deployed to staging
- [ ] Integration tests passing on staging
- [ ] Performance benchmarks validated
- [ ] Accessibility audit passed
- [ ] Manual testing on desktop + mobile completed
- [ ] API contract testing passed

### Production Rollout (Week 6)
- [ ] Feature flag enabled for 10% of users
- [ ] Monitor error rates, performance metrics
- [ ] Gradual rollout: 10% → 50% → 100%
- [ ] Analytics tracking operational
- [ ] Support team trained

### Post-Launch Monitoring (Week 7+)
- [ ] Track adoption metrics daily
- [ ] Monitor API performance (p95, p99 latency)
- [ ] Collect user feedback
- [ ] Plan Phase 2 features based on adoption

---

## Document Maintenance

**Last Updated**: 2025-11-12
**Status**: Draft - Ready for Stakeholder Review
**Next Step**: Approval to begin Phase 1

For detailed task breakdowns, implementation code, and acceptance criteria, see phase-specific documents linked above.
