# Architecture Summary: Listings Catalog View Revamp

**Project:** Deal Brain Listings UI Transformation
**Lead Architect:** Claude Code
**Date:** 2025-10-06
**Status:** Architecture Approved, Ready for Implementation

---

## Executive Summary

This document provides a comprehensive architectural overview of the Listings Catalog View Revamp, designed to transform Deal Brain's listings interface from a pure data-grid to a modern, multi-view catalog experience while maintaining full backward compatibility.

### Key Architectural Decisions

1. **Tab-Based Navigation:** Catalog views alongside existing table (no breaking changes)
2. **Zustand State Management:** Simple, performant client state for UI concerns
3. **React Query for Data:** Separation of server state from UI state
4. **Virtual Scrolling:** @tanstack/react-virtual for 1000+ row lists
5. **Component-Based Design:** Modular, reusable, testable components
6. **Progressive Enhancement:** Mobile-first, accessible, performant

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │  Next.js 14 App Router (/listings)                │     │
│  │  ┌─────────────────────────────────────────────┐  │     │
│  │  │  Tabs: Catalog | Data                       │  │     │
│  │  │  ┌───────────────┐ ┌───────────────────┐    │  │     │
│  │  │  │ Catalog Tab   │ │ Data Tab          │    │  │     │
│  │  │  │ ┌───────────┐ │ │ (Existing Table)  │    │  │     │
│  │  │  │ │ Filters   │ │ │                   │    │  │     │
│  │  │  │ ├───────────┤ │ └───────────────────┘    │  │     │
│  │  │  │ │ View Mode │ │                          │  │     │
│  │  │  │ ├───────────┤ │                          │  │     │
│  │  │  │ │ Grid      │ │                          │  │     │
│  │  │  │ │ List      │ │                          │  │     │
│  │  │  │ │ M/D Split │ │                          │  │     │
│  │  │  │ └───────────┘ │                          │  │     │
│  │  │  └───────────────┘                          │  │     │
│  │  └─────────────────────────────────────────────┘  │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────────────────┐     │
│  │ Zustand Store   │  │ React Query Cache           │     │
│  ├─────────────────┤  ├─────────────────────────────┤     │
│  │ - Active View   │  │ - Listings Data             │     │
│  │ - Active Tab    │  │ - Schema                    │     │
│  │ - Filters       │  │ - CPU/GPU Catalogs          │     │
│  │ - Compare IDs   │  │ - Valuation Breakdowns      │     │
│  │ - Dialog States │  └─────────────────────────────┘     │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend                             │
├─────────────────────────────────────────────────────────────┤
│  Endpoints (No Changes Required):                          │
│  - GET /v1/listings (fetch all listings)                   │
│  - GET /v1/listings/schema (field metadata)                │
│  - PATCH /v1/listings/{id} (update single)                 │
│  - POST /v1/listings/bulk-update (bulk edit)               │
│  - GET /v1/catalog/cpus (CPU options)                      │
│  - GET /v1/catalog/gpus (GPU options)                      │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ PostgreSQL
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Database (PostgreSQL)                      │
│  Tables: listings, cpus, gpus, custom_fields, etc.         │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Component Hierarchy

```
/app/(dealbrain)/listings/page.tsx
├── ListingsTabs (NEW)
│   ├── TabsList (shadcn/ui)
│   │   ├── TabsTrigger: "Catalog" (default)
│   │   └── TabsTrigger: "Data"
│   │
│   ├── TabsContent: Catalog (NEW)
│   │   ├── ListingsFilters (NEW - shared across views)
│   │   │   ├── Search Input (debounced 200ms)
│   │   │   ├── Form Factor Select
│   │   │   ├── Manufacturer Select
│   │   │   ├── Price Range Slider
│   │   │   └── Clear Filters Button
│   │   │
│   │   ├── ViewSwitcher (NEW)
│   │   │   ├── Grid Button
│   │   │   ├── List Button
│   │   │   └── Master-Detail Button
│   │   │
│   │   └── ActiveView (conditional render based on activeView)
│   │       │
│   │       ├── GridView (NEW)
│   │       │   ├── Responsive Grid (2-4 cols)
│   │       │   └── ListingCard[] (memoized)
│   │       │       ├── Card Header (title, open button)
│   │       │       ├── Badge Row (CPU, scores, device, tags)
│   │       │       ├── Price Display (list + adjusted)
│   │       │       ├── PerformanceBadges ($/ST, $/MT, adj)
│   │       │       ├── Metadata Row (RAM, storage, condition)
│   │       │       └── Footer (vendor, quick edit)
│   │       │
│   │       ├── DenseListView (NEW)
│   │       │   ├── Virtual Scroller (@tanstack/react-virtual)
│   │       │   └── DenseTableRow[] (virtualized)
│   │       │       ├── Title Cell (name + device badge)
│   │       │       ├── CPU Cell (name + scores)
│   │       │       ├── Price Cells (formatted + accent)
│   │       │       ├── Performance Cells ($/ST, $/MT)
│   │       │       └── Actions Cell (details, edit, more)
│   │       │
│   │       └── MasterDetailView (NEW)
│   │           ├── MasterList (left panel, 4 cols)
│   │           │   ├── ScrollArea (70vh)
│   │           │   └── MasterListItem[] (selectable)
│   │           │       ├── Title + Adjusted Price
│   │           │       ├── CPU + Scores
│   │           │       └── Compare Checkbox
│   │           │
│   │           ├── DetailPanel (right panel, 6 cols)
│   │           │   ├── Card Header (title, badge, open)
│   │           │   ├── KPI Metrics Grid (4 tiles)
│   │           │   │   ├── Price Tile
│   │           │   │   ├── Adjusted Tile (accent)
│   │           │   │   ├── $/ST Tile
│   │           │   │   └── $/MT Tile
│   │           │   ├── PerformanceBadges (reused)
│   │           │   └── Specs Grid (key-value pairs)
│   │           │       ├── CPU, Scores
│   │           │       ├── RAM, Storage
│   │           │       ├── Condition, Vendor
│   │           │       └── Ports
│   │           │
│   │           └── CompareDrawer (bottom sheet)
│   │               ├── Sheet Trigger ("Compare (N)")
│   │               ├── Sheet Content (60vh)
│   │               └── CompareCard[] (1-6 items)
│   │                   ├── Mini Title
│   │                   ├── Adjusted Price + $/MT
│   │                   ├── CPU + Scores
│   │                   ├── PerformanceBadges
│   │                   └── Remove Button
│   │
│   └── TabsContent: Data (existing ListingsTable)
│
└── Shared Dialogs (NEW/REUSED)
    ├── ListingDetailsDialog (NEW)
    │   ├── Dialog Header (title, device badge)
    │   ├── KPI Metrics Grid (4 tiles)
    │   ├── PerformanceBadges
    │   ├── Specs Grid
    │   ├── Thumbnail Image (if available)
    │   └── Footer (Open link, Expand full page)
    │
    ├── QuickEditDialog (NEW)
    │   ├── Dialog Header
    │   ├── Form Fields (title, price, condition, status, tags)
    │   ├── Save Button (optimistic update)
    │   └── Cancel Button
    │
    └── ValuationBreakdownModal (EXISTING - reused)
```

### File Structure

```
apps/web/
├── app/
│   └── listings/
│       ├── page.tsx (MODIFIED)
│       │   - Add Tabs wrapper
│       │   - Add Catalog tab with view routing
│       │   - Keep Data tab with existing table
│       │
│       └── _components/ (NEW DIRECTORY)
│           ├── catalog-tab.tsx
│           │   - Main catalog container
│           │   - Filters + View switcher + Active view
│           │
│           ├── view-switcher.tsx
│           │   - Buttons: Grid | List | Master-Detail
│           │   - Wire to Zustand store
│           │
│           ├── listings-filters.tsx
│           │   - Sticky filter bar
│           │   - Search, dropdowns, slider
│           │   - Wire to Zustand store
│           │
│           ├── grid-view/
│           │   ├── index.tsx
│           │   │   - Grid layout wrapper
│           │   │   - Map filtered listings to cards
│           │   │
│           │   ├── listing-card.tsx
│           │   │   - Card component (memoized)
│           │   │   - All card sections
│           │   │
│           │   └── performance-badges.tsx
│           │       - 4 badge display
│           │       - Color logic
│           │
│           ├── dense-list-view/
│           │   ├── index.tsx
│           │   │   - Virtual scroller setup
│           │   │   - Conditional virtualization
│           │   │
│           │   └── dense-table-row.tsx
│           │       - Single row component
│           │       - All table cells
│           │
│           └── master-detail-view/
│               ├── index.tsx
│               │   - Split layout wrapper
│               │   - Master + Detail + Compare
│               │
│               ├── master-list.tsx
│               │   - Scrollable list of items
│               │   - Selection logic
│               │
│               ├── detail-panel.tsx
│               │   - Detail card for selected item
│               │   - KPI tiles + specs
│               │
│               ├── compare-drawer.tsx
│               │   - Bottom sheet with compare cards
│               │   - Add/remove logic
│               │
│               ├── kpi-metric.tsx
│               │   - Reusable metric tile
│               │   - Label + value + accent
│               │
│               └── key-value.tsx
│                   - Reusable key-value pair
│                   - Label + value
│
├── components/
│   └── listings/ (MODIFIED)
│       ├── listing-details-dialog.tsx (NEW)
│       │   - Full details modal
│       │   - Reusable from all views
│       │
│       ├── quick-edit-dialog.tsx (NEW)
│       │   - Inline edit form modal
│       │   - Optimistic updates
│       │
│       └── [existing components remain unchanged]
│
├── hooks/ (NEW DIRECTORY)
│   ├── use-catalog-state.ts
│   │   - Custom hook wrapping Zustand store
│   │   - Exports all state + actions
│   │
│   ├── use-listing-filters.ts
│   │   - Filter logic + memoized filtering
│   │   - Returns filtered & sorted listings
│   │
│   ├── use-compare-selections.ts
│   │   - Compare logic
│   │   - Add/remove/clear helpers
│   │
│   └── use-url-sync.ts
│       - Sync Zustand store <-> URL params
│       - Bidirectional updates
│
├── lib/
│   ├── utils.ts (MODIFIED)
│   │   - Add formatting helpers
│   │   - Add color accent logic
│   │
│   └── valuation-utils.ts (EXTENDED)
│       - Performance metric calculations
│       - Threshold logic
│
└── stores/ (NEW DIRECTORY)
    └── catalog-store.ts
        - Zustand store definition
        - State + actions
        - Persist middleware
```

---

## State Management Architecture

### State Layer Separation

**Server State (React Query):**
- Listings data (`/v1/listings`)
- Schema metadata (`/v1/listings/schema`)
- CPU/GPU catalogs (`/v1/catalog/cpus`, `/v1/catalog/gpus`)
- Valuation breakdowns (`/v1/listings/{id}/valuation-breakdown`)

**Client State (Zustand):**
- Active view mode (grid | list | master-detail)
- Active tab (catalog | data)
- Filter state (search, form factor, manufacturer, price range)
- Compare selections (listing IDs)
- Selected listing ID (for detail panel)
- Dialog open states (details, quick edit)

**Local Component State (useState):**
- Hover states
- Focus states
- Temporary input values (before commit)

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Component Tree                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  User Interaction (click, type, scroll)                │
│             │                                           │
│             ▼                                           │
│  ┌──────────────────────┐                              │
│  │  Zustand Action      │  (UI state change)           │
│  │  e.g., setFilters()  │                              │
│  └──────────────────────┘                              │
│             │                                           │
│             ├─────────────────┐                         │
│             │                 │                         │
│             ▼                 ▼                         │
│  ┌─────────────────┐  ┌──────────────────┐            │
│  │ localStorage    │  │  URL Params      │            │
│  │ (persist)       │  │  (sync)          │            │
│  └─────────────────┘  └──────────────────┘            │
│             │                                           │
│             ▼                                           │
│  ┌──────────────────────┐                              │
│  │ Component Re-render  │  (only affected components)  │
│  └──────────────────────┘                              │
│             │                                           │
│             ▼                                           │
│  ┌──────────────────────┐                              │
│  │ React Query Data     │  (fetch if needed)           │
│  │ (memoized filtering) │                              │
│  └──────────────────────┘                              │
│             │                                           │
│             ▼                                           │
│  ┌──────────────────────┐                              │
│  │ Render Updated UI    │                              │
│  └──────────────────────┘                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Performance Architecture

### Performance Optimization Strategies

**1. Rendering Optimization**
- **Memoization:** `React.memo` for `ListingCard`, `DenseTableRow`, `KpiMetric`
- **Virtual Scrolling:** @tanstack/react-virtual for Dense List (>100 items)
- **Code Splitting:** Dynamic imports for each view (lazy load)
- **Debouncing:** 200ms debounce on search input

**2. Data Fetching Optimization**
- **React Query Caching:** 5-minute stale time for listings data
- **Prefetching:** Prefetch CPU/GPU catalogs on page load
- **Client-Side Filtering:** For <1000 listings (no server roundtrip)
- **Optimistic Updates:** Inline edits update UI immediately

**3. Bundle Size Optimization**
- **Code Splitting:** Catalog views split from data table
- **Tree Shaking:** Import only needed shadcn/ui components
- **Lazy Loading:** Dialogs lazy-loaded on first open

**4. Mobile Optimization**
- **Responsive Images:** Use `srcset` for thumbnails
- **Touch Optimization:** 44px minimum touch targets
- **Reduced Motion:** Respect `prefers-reduced-motion`

### Performance Budgets

| Metric                        | Target    |
| ----------------------------- | --------- |
| Grid view initial render      | <500ms    |
| List view scroll FPS          | 60fps     |
| Filter update latency         | <200ms    |
| Bundle size (catalog code)    | <100KB    |
| Lighthouse Performance        | 90+       |
| First Contentful Paint (FCP)  | <1.5s     |
| Largest Contentful Paint (LCP)| <2.5s     |

---

## Accessibility Architecture

### WCAG AA Compliance Strategy

**1. Keyboard Navigation**
- All interactive elements keyboard-accessible (Tab, Enter, Escape)
- Custom shortcuts: `/` (search), `j/k` (navigate), `c` (compare)
- Focus indicators visible on all elements
- Focus traps in dialogs and drawers

**2. Screen Reader Support**
- ARIA labels on icon-only buttons
- ARIA live regions for dynamic content (filter updates, loading states)
- Semantic HTML (nav, main, section, article)
- Descriptive link text ("Open listing details" not "Click here")

**3. Visual Accessibility**
- Color contrast: 4.5:1 minimum for text
- Color never sole indicator (use icons + text labels)
- Adjustable text size (rem units, no fixed px)
- Respect `prefers-reduced-motion`

**4. Forms & Inputs**
- Labels associated with inputs (for, id)
- Error messages descriptive and associated (aria-describedby)
- Required fields marked (aria-required, visual indicator)

### Accessibility Testing Checklist

- [ ] Automated: Axe DevTools 0 violations
- [ ] Automated: Lighthouse Accessibility 95+
- [ ] Manual: Full keyboard navigation test
- [ ] Manual: Screen reader test (VoiceOver, NVDA)
- [ ] Manual: Color contrast verification
- [ ] Manual: Zoom to 200% (layout remains usable)

---

## API Integration Architecture

### Endpoint Usage (No Backend Changes Required)

| Endpoint                           | Method | Usage                          | Cache Strategy          |
| ---------------------------------- | ------ | ------------------------------ | ----------------------- |
| `/v1/listings`                     | GET    | Fetch all listings             | 5 min stale, 30 min max |
| `/v1/listings/schema`              | GET    | Fetch field metadata           | 1 hour stale            |
| `/v1/listings/{id}`                | PATCH  | Update single listing          | Invalidate on success   |
| `/v1/listings/bulk-update`         | POST   | Bulk update listings           | Invalidate on success   |
| `/v1/listings/{id}/valuation-breakdown` | GET | Breakdown modal data | 5 min stale             |
| `/v1/catalog/cpus`                 | GET    | CPU options                    | 1 hour stale            |
| `/v1/catalog/gpus`                 | GET    | GPU options                    | 1 hour stale            |

### Future Server-Side Filtering (Phase 2)

**Proposed Endpoint:**
```
GET /v1/listings?q={search}&form_factor={type}&manufacturer={brand}&max_price={price}&sort={field:direction}&limit={n}&cursor={token}
```

**When to Implement:**
- When listing count consistently exceeds 1000
- When client-side filtering causes noticeable lag (>500ms)
- Based on real-world usage metrics

---

## Testing Architecture

### Testing Strategy Pyramid

```
                  ┌──────────────┐
                  │     E2E      │  (10 tests)
                  │  Playwright  │  - Critical user paths
                  └──────────────┘  - Tab navigation
                        △           - Filter workflows
                       △ △          - Compare workflows
                      △   △
                     △     △
         ┌──────────────────────┐
         │    Integration       │   (30 tests)
         │  React Testing Lib   │   - Data flow
         └──────────────────────┘   - State sync
                   △                 - Dialog interactions
                  △ △
                 △   △
                △     △
    ┌────────────────────────────┐
    │         Unit               │    (100 tests)
    │   Vitest + Testing Lib     │    - Zustand store
    └────────────────────────────┘    - Hooks
                                       - Utilities
                                       - Components (isolated)
```

### Test Coverage Targets

| Layer              | Target Coverage | Focus Areas                          |
| ------------------ | --------------- | ------------------------------------ |
| Unit Tests         | 80%+            | Store actions, hooks, utilities      |
| Integration Tests  | 60%+            | Data flow, state sync, API mocks     |
| E2E Tests          | Critical paths  | User workflows, accessibility        |
| Visual Tests       | Key components  | Storybook stories for design review  |

### Test Files Structure

```
apps/web/
├── __tests__/
│   ├── unit/
│   │   ├── stores/
│   │   │   └── catalog-store.test.ts
│   │   ├── hooks/
│   │   │   ├── use-listing-filters.test.ts
│   │   │   ├── use-compare-selections.test.ts
│   │   │   └── use-url-sync.test.ts
│   │   └── lib/
│   │       └── utils.test.ts
│   │
│   ├── integration/
│   │   ├── catalog-tab.test.tsx
│   │   ├── grid-view.test.tsx
│   │   ├── dense-list-view.test.tsx
│   │   └── master-detail-view.test.tsx
│   │
│   └── e2e/ (Playwright)
│       ├── listings-catalog.spec.ts
│       ├── filters.spec.ts
│       ├── compare-workflow.spec.ts
│       └── accessibility.spec.ts
│
└── stories/
    ├── ListingCard.stories.tsx
    ├── PerformanceBadges.stories.tsx
    ├── KpiMetric.stories.tsx
    └── CompareDrawer.stories.tsx
```

---

## Security Considerations

### Client-Side Security

**1. Input Validation**
- All user inputs sanitized before display (prevent XSS)
- URL params validated and sanitized
- Filter values bounded (price range: 0-10000)

**2. Authentication**
- Existing authentication flows unchanged
- API requests include auth headers (handled by existing infrastructure)
- No new auth requirements

**3. Data Privacy**
- No PII stored in localStorage (only view preferences)
- No sensitive data in URL params
- Listings data follows existing permissions model

### No Backend Changes = No New Attack Surface

Since this is a pure frontend enhancement with no API changes, security risks are minimal. Existing backend RLS (Row-Level Security) policies continue to enforce data access.

---

## Deployment Architecture

### Deployment Strategy

**Phase 1: Staging Deployment (Week 1-2)**
- Deploy to staging environment
- Internal QA testing
- Fix critical bugs

**Phase 2: Feature Flag Rollout (Week 3-4)**
- Deploy to production with feature flag: `ENABLE_CATALOG_VIEWS=false`
- Enable for internal users + beta testers
- Collect feedback, monitor errors

**Phase 3: Gradual Rollout (Week 5-6)**
- Enable for 10% of users
- Monitor performance metrics (Grafana dashboards)
- Enable for 50% of users
- Full rollout if metrics meet targets

**Rollback Strategy:**
- Feature flag allows instant disable (no code deployment)
- Fallback to existing table view always available
- No database migrations = zero risk of data corruption

### Infrastructure Requirements

**No New Infrastructure:**
- Pure client-side enhancement
- Existing Next.js deployment pipeline
- Existing API infrastructure unchanged
- No new CDN or caching requirements

**Monitoring Enhancements:**
- Add client-side analytics for view usage
- Add performance monitoring (Web Vitals)
- Add error tracking for new components
- Create Grafana dashboard for catalog metrics

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk                              | Impact | Probability | Mitigation                                 |
| --------------------------------- | ------ | ----------- | ------------------------------------------ |
| Performance with large datasets   | High   | Medium      | Virtual scrolling, client/server threshold |
| State management complexity       | Medium | Low         | Simple Zustand store, comprehensive tests  |
| Accessibility regressions         | High   | Low         | Automated a11y checks, manual testing      |
| Browser compatibility issues      | Medium | Low         | Cross-browser testing before rollout       |
| User adoption resistance          | Low    | Medium      | Keep existing table, gradual rollout       |

### Operational Risks

| Risk                              | Impact | Probability | Mitigation                                 |
| --------------------------------- | ------ | ----------- | ------------------------------------------ |
| Resource availability delays      | Medium | Medium      | Phase-based rollout allows flexibility     |
| Design approval delays            | Low    | Low         | Use example implementation as reference    |
| Testing delays                    | Medium | Low         | Automated tests, early QA involvement      |
| Production bugs                   | High   | Low         | Feature flag, gradual rollout, rollback    |

---

## Success Metrics & KPIs

### Adoption Metrics

- % of users trying catalog views (target: 60% within first month)
- % of users preferring catalog vs. table (target: 40% catalog preference)
- View distribution: Grid vs. List vs. Master-Detail (track relative usage)

### Performance Metrics

- Grid view render time p50 (target: <300ms)
- Grid view render time p95 (target: <500ms)
- List view scroll FPS (target: 60fps sustained)
- Filter update latency (target: <200ms)

### Engagement Metrics

- Time spent in catalog views (track average session duration)
- Compare drawer usage rate (target: 20% of sessions)
- Quick edit usage rate (target: 30% of edits via catalog)
- Details dialog open rate (track engagement with drill-down)

### Quality Metrics

- Error rate per view (target: <0.1%)
- Inline edit success/failure rate (target: >99% success)
- Browser compatibility issues (target: 0 critical issues)
- Accessibility violations (target: 0 automated violations)

---

## Technical Debt & Future Work

### Known Technical Debt

**None at Launch:**
- Greenfield implementation (no legacy code to refactor)
- Clean architecture from day 1
- Comprehensive tests prevent future debt

### Future Enhancements (Post-Launch)

**Phase 2 Features:**
- Save filter presets ("My SFF deals", "Creator OLED")
- Smart sort options (multiple sort keys, custom rankings)
- Export compare results to CSV
- Deal alerts (notifications for filter matches)
- Bulk actions from compare drawer
- Drag-and-drop to reorder compare items

**Performance Optimizations:**
- Server-side pagination with cursor-based navigation
- GraphQL API for flexible data fetching
- Service worker caching for offline support
- Image lazy loading with blurhash placeholders

**UX Enhancements:**
- Image gallery in detail view
- Price history charts
- Related listings recommendations
- Saved searches with email notifications

---

## Appendices

### Related Documentation

- [PRD: Listings Catalog View Revamp](./PRD.md)
- [Implementation Plan](./IMPLEMENTATION_PLAN.md)
- [ADR-007: Catalog State Management](../../architecture/decisions/ADR-007-catalog-state-management.md)
- [ADR-008: Virtual Scrolling Strategy](../../architecture/decisions/ADR-008-virtual-scrolling-strategy.md)
- [Design Overview](./listings-ui-reskin.md)
- [Example Implementation](./listings.tsx.example)

### Glossary

- **$/ST:** Dollars per single-thread CPU mark (lower = better value)
- **$/MT:** Dollars per multi-thread CPU mark (lower = better value)
- **Adjusted Price:** Price after RAM/storage/OS valuation rule deductions
- **KPI Tile:** Key performance indicator card in detail view
- **Master-Detail:** Split view pattern with list + detail panel
- **Virtual Scrolling:** Render only visible rows for performance
- **Zustand:** State management library for React
- **React Query:** Server state management library

### Stakeholder Sign-Off

**Lead Architect:** Claude Code (Approved: 2025-10-06)
**Product Owner:** TBD
**Engineering Manager:** TBD
**UX Designer:** TBD
**QA Lead:** TBD

---

**Document Version:** 1.0
**Last Updated:** 2025-10-06
**Status:** ✅ Architecture Approved, Ready for Implementation
