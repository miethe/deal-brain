# CPU Page Reskin Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** feat/listings-enhancements-v3
**Last Commit:** 8859fe5
**Current Phase:** Phase 3 - Performance Metrics & Analytics
**Current Task:** Planning Complete - Ready for Implementation
**Last Updated:** 2025-11-06

---

## Phase 3 Architectural Decisions (2025-11-06)

### Key Findings from Codebase Analysis

1. **PerformanceBadge Already Exists**
   - Location: `apps/web/app/cpus/_components/grid-view/performance-badge.tsx`
   - Purpose: Displays PassMark scores (ST, MT, iGPU) with color-coded variants
   - Already integrated in Grid View and Master-Detail View
   - **Decision:** REUSE existing component, NO new component needed for FE-007

2. **Price Targets Already Displayed**
   - CPU Card (grid-view/cpu-card.tsx) shows inline price targets
   - Detail Panel (master-detail-view/detail-panel.tsx) shows KPI metrics
   - **Decision:** Extract to dedicated PriceTargets component for FE-008 (reusability + maintainability)

3. **Chart Library Already Available**
   - `recharts@2.12.0` already in package.json
   - Industry standard, accessible, TypeScript-friendly
   - **Decision:** Use Recharts for all Phase 3 visualizations

4. **Phase 2 Complete**
   - All view modes implemented (Grid, List, Master-Detail)
   - Store, routing, filtering, sorting all working
   - Types already defined in `apps/web/types/cpus.ts`
   - **Decision:** Build on existing patterns, avoid refactoring

### Architectural Decisions

**AD-001: Component Reuse Strategy**
- **Decision:** Reuse existing PerformanceBadge component instead of creating new one
- **Rationale:** Already implements exact requirements (color coding, tooltips, variants)
- **Impact:** Reduces FE-007 scope to documentation/validation only

**AD-002: Price Targets Component Extraction**
- **Decision:** Create dedicated PriceTargets component for reusability
- **Rationale:** Currently duplicated in CPUCard and DetailPanel; extract for DRY
- **Location:** `apps/web/app/cpus/_components/price-targets.tsx`
- **API:** Accept `CPURecord` and display Great/Good/Fair with confidence badge

**AD-003: Chart Library Selection**
- **Decision:** Use Recharts for all visualizations
- **Rationale:** Already installed, accessible, composable, TypeScript support
- **Charts Needed:** Price distribution histogram, PassMark comparison bars

**AD-004: CPU Detail Modal Enhancement Strategy**
- **Decision:** Enhance existing detail panel patterns, NOT create new modal
- **Rationale:** Master-Detail View already provides comprehensive detail panel
- **Implementation:** Add analytics sections to existing detail-panel.tsx

**AD-005: Listings Page Integration**
- **Decision:** Add performance columns to existing Listings table (NOT in Phase 3 scope)
- **Rationale:** Listings page is separate feature; handle in separate task
- **Risk:** Scope creep if attempted in Phase 3

### Key Patterns to Enforce

1. **Component Composition:** Reuse existing components (Badge, Tooltip, Card, etc.)
2. **Type Safety:** All components use TypeScript interfaces from `types/cpus.ts`
3. **Accessibility:** Maintain WCAG 2.1 AA compliance (ARIA labels, keyboard nav)
4. **Performance:** Memoize components using React.memo for grid/list views
5. **Error Handling:** Gracefully handle null/missing data (show "No data" or "-")

---

## Key Decisions (Historical)

- **Architecture:** Following existing Listings page patterns (React Query + Zustand)
- **Patterns:**
  - shadcn/ui for all UI components
  - Radix UI primitives for accessibility
  - Client-side filtering and sorting
  - Server-side data fetching with React Query
- **Trade-offs:**
  - Client-side filtering chosen for Phase 2 (simpler, faster to implement)
  - Analytics data pre-computed in backend (Phase 1) for fast frontend display

---

## Important Learnings

- **Phase 1 Backend:** All analytics endpoints and calculations are complete
  - `/v1/cpus` returns CPUs with embedded price_targets and performance_value
  - Data pre-computed and cached in CPU table columns
- **Phase 2 Frontend:** Core page structure complete
  - Store, routing, view modes, filters all implemented
  - FE-001 through FE-011 complete per git history
- **Phase 3 Focus:** Display components for analytics data
  - PerformanceBadge shows $/PassMark rating with color coding
  - PriceTargets shows Great/Good/Fair prices with confidence
  - Both components already referenced in Phase 2 code but not yet implemented

---

## Quick Reference

### Environment Setup
```bash
# Backend API
export PYTHONPATH="$PWD/apps/api"
poetry install

# Frontend Web
pnpm install
pnpm --filter "./apps/web" dev

# Database
make migrate

# Full stack
make up
```

### Key Files
- Schema: packages/core/dealbrain_core/schemas/cpu.py
- Service: apps/api/dealbrain_api/services/cpu_analytics.py
- Model: apps/api/dealbrain_api/models/core.py
- API: apps/api/dealbrain_api/api/catalog.py
- Store: apps/web/stores/cpu-catalog-store.ts
- Main Page: apps/web/app/cpus/page.tsx
- Types: apps/web/types/cpus.ts

---

## Phase 3 Scope (From Plan)

**Objectives:**
- Integrate performance value badges and price target displays
- Implement CPU detail modal with comprehensive analytics
- Add performance metrics to Listings page/table
- Build interactive charts and visualizations

**Success Metric:** All analytics data from Phase 1 backend visible and interactive in frontend

---

## Architecture Patterns

### Component Structure
```
apps/web/app/cpus/_components/
├── performance-badge.tsx      # NEW - Phase 3
├── price-targets.tsx          # NEW - Phase 3
├── cpu-detail-modal.tsx       # ENHANCE - Phase 3
├── cpu-card.tsx               # COMPLETE - Phase 2
├── cpu-filters.tsx            # COMPLETE - Phase 2
├── grid-view/                 # COMPLETE - Phase 2
├── list-view/                 # COMPLETE - Phase 2
└── master-detail-view/        # COMPLETE - Phase 2
```

### Data Flow
1. React Query fetches `/v1/cpus` with analytics embedded
2. Components display pre-computed price_targets and performance_value
3. Detail modal fetches `/v1/cpus/{id}` for comprehensive data
4. No client-side calculations needed - all metrics from backend

### Type Definitions (from PRD)
```typescript
interface PriceTarget {
  good: number | null;
  great: number | null;
  fair: number | null;
  sample_size: number;
  confidence: 'high' | 'medium' | 'low' | 'insufficient';
  stddev: number | null;
  updated_at: string | null;
}

interface PerformanceValue {
  dollar_per_mark_single: number | null;
  dollar_per_mark_multi: number | null;
  percentile: number | null;
  rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
  updated_at: string | null;
}
```
