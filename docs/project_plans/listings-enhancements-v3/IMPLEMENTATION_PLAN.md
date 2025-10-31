# Deal Brain Listings Enhancements v3 - Implementation Plan

**Version:** 1.0
**Created:** October 31, 2025
**Updated:** October 31, 2025
**Status:** Ready for Development
**Engineering Lead:** TBD

---

## Executive Summary

This implementation plan provides a detailed technical roadmap for the four enhancement areas defined in the PRD:

1. **Data Tab Performance Optimization** - Implement virtualization and optimize rendering
2. **Adjusted Value Renaming & Tooltips** - Rename terminology and add contextual help
3. **CPU Metrics Layout** - Pair related metrics with dual values and color coding
4. **Image Management System** - Create configuration-driven image resolution

### Effort Estimate

| Phase | Backend | Frontend | Testing | Total |
|-------|---------|----------|---------|-------|
| Phase 1: Performance | 16h | 40h | 16h | 72h (9 days) |
| Phase 2: Adjusted Value | 4h | 16h | 8h | 28h (3.5 days) |
| Phase 3: CPU Metrics | 8h | 24h | 12h | 44h (5.5 days) |
| Phase 4: Image Management | 8h | 32h | 12h | 52h (6.5 days) |
| **TOTAL** | **36h** | **112h** | **48h** | **196h (24.5 days)** |

**Timeline:** 6-8 weeks (with testing, review, and deployment)

### Key Technical Decisions

1. **Virtualization:** Use `@tanstack/react-virtual` for table virtualization
2. **Backend Pagination:** Add cursor-based pagination for datasets > 500 rows
3. **Image Config:** JSON configuration file for maintainability and TypeScript integration
4. **Settings Storage:** Reuse ApplicationSettings model for thresholds
5. **Backward Compatibility:** Feature flags for gradual rollout

### Critical Dependencies

- **External:** No new major dependencies
- **Internal:** Completion of Phase 2 before Phase 3 (shared tooltip component)
- **Team:** Frontend engineer availability (112 hours needed)

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser / Client                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Listings Page    │  │ Detail Page      │  │ Image Config │ │
│  │                  │  │                  │  │ (Static JSON)│ │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │              │ │
│  │ │ Catalog Tab  │ │  │ │ Specs Tab    │ │  │ Loaded at    │ │
│  │ └──────────────┘ │  │ │ - CPU Metrics│ │  │ Build Time   │ │
│  │ ┌──────────────┐ │  │ │ - Tooltips   │ │  │              │ │
│  │ │ Data Tab     │ │  │ └──────────────┘ │  │              │ │
│  │ │ - Virtual    │ │  │ ┌──────────────┐ │  │              │ │
│  │ │   Table      │ │  │ │ Hero Section │ │  │              │ │
│  │ │ - Pagination │ │  │ │ - Image      │ │  │              │ │
│  │ └──────────────┘ │  │ │ - Tooltip    │ │  │              │ │
│  └──────────────────┘  │ └──────────────┘ │  │              │ │
│           │             └──────────────────┘  └──────────────┘ │
│           │                     │                      │        │
│           ▼                     ▼                      ▼        │
│  ┌────────────────────────────────────────────────────────────┐│
│  │               React Query Cache (5min TTL)                 ││
│  └────────────────────────────────────────────────────────────┘│
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP/REST
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                         │  │
│  │  GET /v1/listings (with pagination params)               │  │
│  │  GET /v1/listings/{id}                                   │  │
│  │  GET /v1/settings/valuation_thresholds                   │  │
│  │  GET /v1/settings/cpu_mark_thresholds (NEW)              │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│                   ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Services Layer                              │  │
│  │  - ListingsService (CRUD, metrics calculation)           │  │
│  │  - SettingsService (threshold management)                │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│                   ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy ORM                              │  │
│  │  - Listing model (existing fields)                       │  │
│  │  - ApplicationSettings model (NEW: cpu_mark_thresholds)  │  │
│  └────────────────┬─────────────────────────────────────────┘  │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
           ┌──────────────────┐
           │   PostgreSQL     │
           │   Database       │
           └──────────────────┘
```

### Data Flow: Adjusted Value Tooltip

```
User hovers over "Adjusted Value"
         │
         ▼
Tooltip component renders
         │
         ▼
Extract listing.valuation_breakdown JSON
         │
         ├─> listing_price: $500
         ├─> adjusted_price: $450
         ├─> matched_rules: [...]
         │   └─> Sort by absolute adjustment
         │       └─> Take top 3-5 rules
         ▼
Format tooltip content
  "List Price: $500.00"
  "Adjustments: -$50.00"
  "Adjusted Value: $450.00 (10% savings)"
  "Applied 3 valuation rules:"
  "• RAM deduction: -$30"
  "• Condition (Used): -$15"
  "• Missing storage: -$5"
  [View Full Breakdown →]
         │
         ▼
Render tooltip with link to modal
```

### Data Flow: CPU Mark Color Coding

```
Listing loaded from API
         │
         ▼
Extract metrics:
  - price_usd: $500
  - adjusted_price_usd: $450
  - cpu.cpu_mark_multi: 18,200
  - cpu.cpu_mark_single: 3,450
         │
         ▼
Calculate base $/CPU Mark:
  - base_multi = $500 / 18,200 = $0.0275
  - base_single = $500 / 3,450 = $0.145
         │
         ▼
Calculate adjusted $/CPU Mark:
  - adj_multi = $450 / 18,200 = $0.0247
  - adj_single = $450 / 3,450 = $0.130
         │
         ▼
Calculate improvement:
  - multi_improvement = (base - adj) / base * 100 = 10.2%
  - single_improvement = (base - adj) / base * 100 = 10.3%
         │
         ▼
Fetch cpu_mark_thresholds from settings:
  {excellent: 20%, good: 10%, fair: 5%, ...}
         │
         ▼
Apply threshold logic:
  - multi_improvement (10.2%) → "good" threshold
  - single_improvement (10.3%) → "good" threshold
         │
         ▼
Apply color styling:
  - Background: Medium green
  - Text: Dark green
  - Icon: ⬇️
         │
         ▼
Render colored metric display
```

---

## Implementation Phases

### Phase 1: Data Tab Performance Optimization

**Duration:** 2 weeks | **Effort:** 72 hours

Achieve <200ms interaction latency for 1,000 listings through virtualization, backend pagination, and rendering optimizations.

**[View Phase 1 Details →](./PHASE_1_PERFORMANCE.md)**

**Tasks:**
- PERF-001: Install and Configure React Virtual (4h)
- PERF-002: Implement Table Row Virtualization (16h)
- PERF-003: Add Backend Pagination Endpoint (8h)
- PERF-004: Optimize React Component Rendering (12h)
- PERF-005: Add Performance Monitoring (8h)
- Testing (16h)

---

### Phase 2: Adjusted Value Renaming & Tooltips

**Duration:** 3-4 days | **Effort:** 28 hours

Rename "Adjusted Price" terminology and add contextual tooltips with accessibility support.

**[View Phase 2 Details →](./PHASE_2_ADJUSTED_VALUE.md)**

**Tasks:**
- UX-001: Global Find-and-Replace for "Adjusted Price" (4h)
- UX-002: Create Valuation Tooltip Component (8h)
- UX-003: Integrate Tooltip in Detail Page (4h)
- Testing (8h)

---

### Phase 3: CPU Performance Metrics Layout

**Duration:** 5-6 days | **Effort:** 44 hours

Pair related CPU metrics with color-coded dual values based on configurable thresholds.

**[View Phase 3 Details →](./PHASE_3_CPU_METRICS.md)**

**Prerequisites:** Phase 2 (UX-002) must be completed first

**Tasks:**
- METRICS-001: Create CPU Mark Thresholds Setting (4h)
- METRICS-002: Create Performance Metric Display Component (12h)
- METRICS-003: Update Specifications Tab Layout (8h)
- Testing (12h)

---

### Phase 4: Image Management System

**Duration:** 2 weeks | **Effort:** 52 hours

Create configuration-driven image resolution system with maintainability focus.

**[View Phase 4 Details →](./PHASE_4_IMAGE_MANAGEMENT.md)**

**Tasks:**
- IMG-001: Design and Create Image Configuration File (4h)
- IMG-002: Implement Image Resolver Utility (8h)
- IMG-003: Refactor ProductImageDisplay Component (12h)
- IMG-004: Reorganize Image Directory Structure (4h)
- IMG-005: Documentation for Non-Technical Users (4h)
- Testing (12h)

---

## Database Migrations

### Migration 1: Add CPU Mark Thresholds

**File:** `apps/api/alembic/versions/xxx_add_cpu_mark_thresholds.py`

**Changes:**
- Add `cpu_mark_thresholds` setting to `application_settings` table

**Rollback:**
- Delete setting from `application_settings`

---

## API Changes

### New Endpoints

#### `GET /v1/listings/paginated`

**Description:** Cursor-based pagination for large datasets

**Query Parameters:**
- `limit` (int, default: 50, max: 500)
- `cursor` (string, optional)
- `sort_by` (string, default: "updated_at")
- `sort_order` (string, default: "desc")
- `form_factor` (string, optional)
- `manufacturer` (string, optional)
- `min_price` (float, optional)
- `max_price` (float, optional)

**Response:**
```json
{
  "items": [/* ListingRead objects */],
  "total": 1234,
  "limit": 50,
  "next_cursor": "eyJpZCI6MTIzLCJzb3J0X3ZhbHVlIjoiMjAyNS0xMC0zMSJ9",
  "has_next": true
}
```

---

#### `GET /v1/settings/cpu_mark_thresholds`

**Description:** Get CPU Mark color-coding thresholds

**Response:**
```json
{
  "excellent": 20.0,
  "good": 10.0,
  "fair": 5.0,
  "neutral": 0.0,
  "poor": -10.0,
  "premium": -20.0
}
```

---

## Frontend Component Changes

### New Components

1. **ValuationTooltip** (`apps/web/components/listings/valuation-tooltip.tsx`)
   - Displays adjusted value calculation summary
   - Shows top rules by impact
   - Links to full breakdown modal

2. **PerformanceMetricDisplay** (`apps/web/components/listings/performance-metric-display.tsx`)
   - Displays CPU performance metrics
   - Shows base and adjusted values
   - Color-coded based on improvement

### Modified Components

1. **ListingsTable** (`apps/web/components/listings/listings-table.tsx`)
   - Add row virtualization
   - Update column header to "Adjusted Value"

2. **DetailPageLayout** (`apps/web/components/listings/detail-page-layout.tsx`)
   - Rename "Adjusted Price" to "Adjusted Value"
   - Add ValuationTooltip

3. **SpecificationsTab** (`apps/web/components/listings/specifications-tab.tsx`)
   - Pair CPU metrics (Score next to $/Mark)
   - Use PerformanceMetricDisplay component

4. **ProductImageDisplay** (`apps/web/components/listings/product-image-display.tsx`)
   - Use image resolver utility
   - Remove hardcoded fallback logic

---

## Configuration Changes

### New Configuration Files

1. **`apps/web/config/product-images.json`**
   - Image mappings for manufacturers, series, form factors, CPU vendors
   - Fallback hierarchy configuration

### Environment Variables

No new environment variables required.

### Feature Flags

Add to application settings (optional):

- `ENABLE_VIRTUALIZATION` (default: true)
- `ENABLE_IMAGE_CONFIG` (default: true)
- `ENABLE_CPU_MARK_COLORING` (default: true)

---

## Testing Strategy

### Unit Test Coverage Targets

- **Backend:** 80% coverage
  - Settings service methods
  - Pagination logic
  - Cursor encoding/decoding

- **Frontend:** 75% coverage
  - Component rendering
  - Image resolver logic
  - Threshold calculations

### Integration Test Scenarios

1. **Pagination:**
   - Fetch first page
   - Fetch subsequent pages using cursor
   - Verify total count accuracy

2. **Settings:**
   - Fetch CPU mark thresholds
   - Verify default values when not set

3. **Image Resolution:**
   - Test all 7 fallback levels
   - Verify correct image returned

### E2E Test Scenarios

1. **Data Tab Performance:**
   - Load 1,000 listings
   - Sort column
   - Filter by manufacturer
   - Measure interaction latency (<200ms)

2. **Tooltips:**
   - Hover over "Adjusted Value"
   - Verify tooltip appears
   - Click "View Full Breakdown"
   - Verify modal opens

3. **CPU Metrics:**
   - Navigate to detail page
   - Verify metrics paired
   - Verify color coding applied
   - Hover over adjusted value
   - Verify tooltip appears

4. **Image Display:**
   - Verify manufacturer logo appears
   - Verify fallback to CPU vendor logo
   - Verify fallback to generic image

### Performance Test Benchmarks

| Metric | Target | Test Method |
|--------|--------|-------------|
| Data tab load (1,000 rows) | <300ms | React Profiler |
| Interaction latency (sort) | <150ms | Performance.measure |
| Scroll FPS (virtualized) | 60fps | Chrome DevTools |
| Image resolution time | <1ms | Unit test |

### Accessibility Test Checklist

- [ ] All tooltips keyboard accessible
- [ ] Screen reader announces tooltip content
- [ ] Color contrast ratios meet WCAG AA (4.5:1)
- [ ] Focus indicators visible
- [ ] Tab order logical
- [ ] ARIA labels present

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Performance benchmarks met
- [ ] Accessibility audit passed
- [ ] Database migrations tested in staging
- [ ] Rollback plan validated
- [ ] Monitoring dashboards updated
- [ ] Documentation complete

### Deployment Steps

1. **Backend Deployment:**
   ```bash
   # Run migrations
   poetry run alembic upgrade head

   # Deploy API
   make deploy-api

   # Verify health check
   curl https://api.dealbrain.com/health
   ```

2. **Frontend Deployment:**
   ```bash
   # Build with new changes
   cd apps/web
   pnpm build

   # Deploy to production
   make deploy-web

   # Verify deployment
   curl https://dealbrain.com
   ```

3. **Verify Deployment:**
   - Check /listings page loads
   - Verify "Adjusted Value" terminology
   - Test tooltip functionality
   - Verify CPU metrics layout
   - Check image display

### Feature Flag Rollout

**Phase 1: Internal Testing (Day 1-2)**
- Enable all features for internal users
- Monitor error rates and performance
- Gather feedback

**Phase 2: Beta Users (Day 3-5)**
- Enable for 10% of users
- Monitor engagement metrics
- Collect user feedback

**Phase 3: Full Rollout (Day 6-7)**
- Enable for 50% of users
- Monitor metrics
- Address any issues

**Phase 4: 100% Rollout (Day 8+)**
- Enable for all users
- Remove feature flags (code cleanup)

### Monitoring & Alerting

**Metrics to Monitor:**
- Data tab load time (P95)
- Interaction latency (P95)
- Image load failures
- Tooltip engagement rate
- Error rates

**Alerts:**
- P95 latency > 300ms → Warning
- P95 latency > 500ms → Critical
- Error rate > 1% → Warning
- Error rate > 5% → Critical
- Image load failure rate > 5% → Warning

### Rollback Procedures

**Emergency Rollback (if critical issues):**
1. Flip feature flags to disable new features
2. Redeploy previous version
3. Verify issues resolved
4. Investigate root cause

**Database Rollback:**
```bash
# Rollback migration
poetry run alembic downgrade -1

# Verify rollback
poetry run alembic current
```

**Frontend Rollback:**
```bash
# Revert to previous commit
git revert <commit-hash>

# Rebuild and deploy
pnpm build
make deploy-web
```

---

## Timeline & Resource Allocation

### Gantt Chart (Text-Based)

```
Week 1:
  Mon  ████ PERF-001, PERF-002 (Frontend)
  Tue  ████ PERF-002 (continued)
  Wed  ████ PERF-003 (Backend), PERF-002 (Frontend)
  Thu  ████ PERF-004 (Frontend)
  Fri  ████ PERF-005, Testing

Week 2:
  Mon  ████ UX-001, UX-002 (Frontend)
  Tue  ████ UX-002 (continued), UX-003
  Wed  ████ METRICS-001 (Backend), METRICS-002 (Frontend)
  Thu  ████ METRICS-002 (continued)
  Fri  ████ METRICS-003, Testing

Week 3:
  Mon  ████ IMG-001, IMG-002 (Frontend)
  Tue  ████ IMG-003 (Frontend)
  Wed  ████ IMG-003 (continued), IMG-004 (Infra)
  Thu  ████ IMG-005 (Documentation)
  Fri  ████ Integration Testing

Week 4:
  Mon  ████ Performance Testing, Bug Fixes
  Tue  ████ Accessibility Audit
  Wed  ████ Security Review
  Thu  ████ Staging Deployment
  Fri  ████ Production Deployment

Week 5-6:
  Mon-Fri  ████ Monitoring, Iteration, Documentation
```

### Resource Allocation

| Week | Backend (hours) | Frontend (hours) | QA (hours) | Total |
|------|-----------------|------------------|------------|-------|
| 1 | 8 | 32 | 8 | 48 |
| 2 | 8 | 24 | 8 | 40 |
| 3 | 4 | 28 | 12 | 44 |
| 4 | 0 | 16 | 16 | 32 |
| 5-6 | 8 | 12 | 12 | 32 |
| **Total** | **28h** | **112h** | **56h** | **196h** |

### Critical Path

```
PERF-001 → PERF-002 → PERF-004 → Testing → Deployment
             ↓
           PERF-003

UX-002 → METRICS-002 → METRICS-003 → Testing
  ↓
UX-003

IMG-001 → IMG-002 → IMG-003 → IMG-004 → Testing
```

**Critical tasks:** PERF-002, UX-002, METRICS-002, IMG-003

**Buffer:** 20% buffer (5 days) included for unforeseen issues

---

## Risk Management

### Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Virtualization breaks row selection | Medium | High | Thorough testing, feature flag, fallback mode | Frontend Lead |
| Performance degradation on mobile | Medium | High | Test on low-end devices, monitor RUM metrics | Frontend Lead |
| Image config file grows too large | Low | Medium | Set file size limits, lazy loading, code-splitting | Frontend Lead |
| Backend pagination slower than expected | Low | High | Index frequently sorted columns, optimize queries | Backend Lead |
| Tooltip engagement lower than expected | Medium | Low | A/B test designs, add onboarding tour | Product Owner |
| Users struggle with image uploads | Low | Medium | Detailed documentation, video tutorial, onboarding | Content Manager |

### Dependency Risks

**External Dependencies:**
- `@tanstack/react-virtual` library stability → **Low risk** (stable, widely used)
- Next.js Image component compatibility → **Low risk** (core Next.js feature)

**Internal Dependencies:**
- Completion of UX-002 before METRICS-002 → **Medium risk** (sequential work)
  - **Mitigation:** Start UX-002 early, allocate dedicated frontend resource

### Technical Debt Considerations

**Introduced Debt:**
- Image config file may need database migration if it grows beyond 100KB
- Virtualization adds complexity to table component

**Addressed Debt:**
- Removes hardcoded image fallback logic
- Centralizes threshold configuration
- Improves render performance

### Contingency Plans

**If virtualization performance insufficient:**
- Implement server-side pagination as primary solution
- Use virtualization only for pagination result sets
- Reduce page size to 25 rows

**If tooltip engagement low:**
- Add onboarding tour highlighting tooltips
- Experiment with different trigger mechanisms (click vs. hover)
- A/B test tooltip designs

**If image config becomes unwieldy:**
- Migrate to database-backed configuration
- Implement UI for managing images (admin panel)
- Add image upload directly in UI

---

## Quality Assurance

### Code Review Checklist

**Backend:**
- [ ] Migrations are reversible
- [ ] API endpoints have proper error handling
- [ ] Query performance tested with 1,000+ rows
- [ ] Type hints present
- [ ] Docstrings for public methods

**Frontend:**
- [ ] Components are memoized where appropriate
- [ ] Accessibility attributes present (ARIA labels)
- [ ] TypeScript types defined
- [ ] Error boundaries in place
- [ ] Performance optimizations applied

### Performance Benchmarking Plan

**Tools:**
- React Profiler for component render time
- Chrome DevTools Performance tab for interaction latency
- Lighthouse for overall page performance
- Custom instrumentation for API response time

**Benchmarks:**
1. **Baseline (before changes):**
   - Data tab load time with 500 listings
   - Interaction latency for sort/filter
   - Image load time

2. **Target (after changes):**
   - 50% reduction in load time
   - <200ms interaction latency
   - <500ms image load time

3. **Regression prevention:**
   - Automated performance tests in CI/CD
   - Fail build if performance degrades >10%

### Accessibility Audit Plan

**Manual Testing:**
- [ ] Keyboard-only navigation
- [ ] Screen reader testing (NVDA, JAWS)
- [ ] Color contrast verification
- [ ] Focus management

**Automated Testing:**
- [ ] jest-axe tests for all components
- [ ] Lighthouse accessibility score >90
- [ ] Wave browser extension audit

**Compliance:**
- WCAG 2.1 Level AA compliance required

### Security Review Checklist

**Backend:**
- [ ] Input validation on all API parameters
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting on paginated endpoints
- [ ] Authorization checks

**Frontend:**
- [ ] XSS prevention (React auto-escaping)
- [ ] CSP headers for external images
- [ ] No sensitive data in client-side config
- [ ] Image URL validation (same-origin or trusted domains)

---

## Documentation Requirements

### User-Facing Documentation

1. **Release Notes:**
   - Performance improvements
   - New tooltip feature
   - Adjusted value terminology change
   - Enhanced CPU metrics display

2. **User Guide Updates:**
   - How to use tooltips
   - Understanding CPU performance metrics
   - Color-coding explanation

3. **Image Management Guide:**
   - Adding manufacturer logos
   - Troubleshooting image issues

### Developer Documentation

1. **Architecture Documentation:**
   - Update `architecture.md` with virtualization approach
   - Document image resolution system
   - Explain threshold configuration

2. **Component Documentation:**
   - JSDoc for all new components
   - Storybook stories (optional)
   - Usage examples

3. **API Documentation:**
   - Update OpenAPI spec with new endpoints
   - Document pagination cursor format
   - Add examples

### Deployment Runbooks

1. **Migration Runbook:**
   - Pre-migration checklist
   - Migration commands
   - Rollback procedure
   - Verification steps

2. **Deployment Runbook:**
   - Pre-deployment checklist
   - Deployment commands
   - Health check procedures
   - Rollback steps

3. **Monitoring Runbook:**
   - Metrics to monitor
   - Alert thresholds
   - Incident response procedures

---

## Appendix

### Task Dependencies Graph

```
PERF-001 (Install React Virtual)
    ↓
PERF-002 (Implement Virtualization) ──┐
    ↓                                  │
PERF-004 (Optimize Rendering) ────────┼─→ Phase 1 Testing
    ↓                                  │
PERF-005 (Add Monitoring) ────────────┘

PERF-003 (Backend Pagination) → Phase 1 Testing

UX-001 (Find-Replace) ──┐
    ↓                    │
UX-002 (Tooltip Component) ──┼─→ Phase 2 Testing
    ↓                    │
UX-003 (Integrate Tooltip) ──┘

METRICS-001 (Thresholds Setting) ──┐
    ↓                               │
METRICS-002 (Metric Component) ────┼─→ Phase 3 Testing
    ↓                               │
METRICS-003 (Update Layout) ───────┘

IMG-001 (Config File) ──┐
    ↓                    │
IMG-002 (Image Resolver) ──┼─→ Phase 4 Testing
    ↓                    │
IMG-003 (Refactor Component) ──┼
    ↓                    │
IMG-004 (Reorganize Images) ───┼
    ↓                    │
IMG-005 (Documentation) ───────┘
```

### Estimated Effort Breakdown

```
Phase 1: Performance (72h)
├─ PERF-001: 4h
├─ PERF-002: 16h
├─ PERF-003: 8h
├─ PERF-004: 12h
├─ PERF-005: 8h
└─ Testing: 16h

Phase 2: Adjusted Value (28h)
├─ UX-001: 4h
├─ UX-002: 8h
├─ UX-003: 4h
└─ Testing: 8h

Phase 3: CPU Metrics (44h)
├─ METRICS-001: 4h
├─ METRICS-002: 12h
├─ METRICS-003: 8h
└─ Testing: 12h

Phase 4: Images (52h)
├─ IMG-001: 4h
├─ IMG-002: 8h
├─ IMG-003: 12h
├─ IMG-004: 4h
├─ IMG-005: 4h
└─ Testing: 12h
```

---

**End of Implementation Plan**
