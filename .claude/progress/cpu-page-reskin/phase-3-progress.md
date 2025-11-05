# CPU Page Reskin - Phase 3 Progress Tracker

**Project:** CPU Catalog Page Reskin
**Phase:** 3 - Performance Metrics & Analytics
**Duration:** Week 2-3
**Status:** Not Started
**Created:** 2025-11-05

---

## Phase Overview

Integration of performance metrics and analytics components. Includes PerformanceBadge, PriceTargets display, interactive CPU detail modal, and integration with Listings page for cross-feature consistency.

**Time Estimate:** 40 hours (5 days)
**Dependencies:** Phase 1 analytics data must be available, Phase 2 page structure must be complete

---

## Success Criteria

### Core Requirements (Must Complete)

- [ ] Performance badges display correct ratings
- [ ] Price targets show confidence levels accurately
- [ ] Detail modal loads in < 300ms
- [ ] All tooltips provide helpful context
- [ ] Charts render without performance issues
- [ ] Listings integration doesn't break existing functionality

### Quality Metrics

- [ ] No performance regressions in Listings page
- [ ] Components properly memoized
- [ ] Chart rendering optimized
- [ ] Accessibility maintained for new components
- [ ] Test coverage > 80% for new code

---

## Development Tasks

### Performance Badge Component

- [ ] **FE-101: Create PerformanceBadge Component** (8h)
  - Display color-coded rating badges (Excellent/Good/Fair/Poor)
  - Show percentile ranking
  - Display $/mark metrics
  - Tooltip with detailed metrics
  - Proper sizing and styling
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-102: Rating Algorithm Implementation** (4h)
  - Implement rating logic based on percentile
  - Define thresholds (excellent > 75%, good > 50%, fair > 25%)
  - Color mapping (green/yellow/orange/red)
  - Consistent with Listings page coloring
  - Status: Not Started
  - Assignee: TBD

### Price Targets Component

- [ ] **FE-103: Create PriceTargets Component** (6h)
  - Display three price tiers (Great/Good/Fair)
  - Show confidence level (High/Medium/Low/Insufficient)
  - Include sample size indicator
  - Conditional rendering (show "Insufficient data" when needed)
  - Tooltip explaining calculation
  - Status: Not Started
  - Assignee: TBD

### CPU Detail Modal

- [ ] **FE-104: Create CPUDetailModal Component** (12h)
  - Modal layout with header and tabs
  - **Overview tab:** Specs, manufacturer, socket, cores, TDP
  - **Performance tab:** Rating badge, percentile, $/mark metrics
  - **Pricing tab:** Price targets, sample size, confidence
  - **Market tab:** Top listings table, price distribution
  - Close button, keyboard support (Escape)
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-105: Price Distribution Chart** (6h)
  - Implement histogram of listing prices for CPU
  - Show mean and std dev lines
  - Interactive tooltip on hover
  - Responsive sizing
  - Use Recharts or similar library
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-106: Top Listings Table in Modal** (4h)
  - Display top 10 listings by adjusted price
  - Columns: Name, Price, Value Score, Link to listing
  - Sortable by price/value
  - Click to navigate to listing detail
  - Status: Not Started
  - Assignee: TBD

### Integration with Listings Page

- [ ] **FE-107: Add CPU Columns to Listings Table** (6h)
  - Add "CPU Performance" column showing badge
  - Add "CPU Price Target" column showing price range
  - Click badge to open CPU detail modal
  - Maintain existing table functionality
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-108: Update Listings Detail Page** (4h)
  - Add CPU performance card in specifications section
  - Link to CPU catalog page
  - Show relevant CPU metrics
  - Status: Not Started
  - Assignee: TBD

### Data & Hooks

- [ ] **FE-109: Create useCPUDetail Hook** (4h)
  - Fetch detailed CPU data from GET /v1/cpus/{id}
  - Cache results with React Query
  - Handle loading and error states
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-110: Create usePerformanceRating Hook** (3h)
  - Calculate rating from percentile
  - Return color and label
  - Handle null/undefined data
  - Status: Not Started
  - Assignee: TBD

### Accessibility & UX

- [ ] **FE-111: Modal Accessibility** (3h)
  - Focus management (trap inside modal)
  - Keyboard navigation (Tab, Shift+Tab, Escape)
  - ARIA labels for tabs and buttons
  - Screen reader announcements
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-112: Tooltip Accessibility** (2h)
  - Tooltip content readable by screen readers
  - Keyboard accessible tooltips
  - Proper contrast ratios
  - Status: Not Started
  - Assignee: TBD

### Performance Optimization

- [ ] **FE-113: Memoize Components** (3h)
  - Wrap expensive components with React.memo
  - Optimize re-render triggers
  - Use useMemo for calculations
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-114: Chart Performance Optimization** (3h)
  - Lazy load charts
  - Debounce resize handlers
  - Optimize data transformation
  - Status: Not Started
  - Assignee: TBD

### Testing

- [ ] **FE-115: Component Tests** (8h)
  - Test PerformanceBadge with various ratings
  - Test PriceTargets with confidence levels
  - Test CPU detail modal interaction
  - Test chart rendering
  - Test accessibility features
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-116: Integration Tests** (6h)
  - Test modal opening from badge click
  - Test Listings page integration
  - Test cross-page navigation
  - Test data consistency
  - Status: Not Started
  - Assignee: TBD

- [ ] **FE-117: Performance Tests** (4h)
  - Measure modal load time
  - Measure chart render time
  - Verify no regressions in Listings page
  - Status: Not Started
  - Assignee: TBD

---

## Work Log

### Session 1
- Date: TBD
- Tasks Completed: None
- Hours: 0h
- Notes: Awaiting Phase 2 completion

---

## Decisions Log

### Component Library

- **Decision:** Use Recharts for price distribution visualization
  - Rationale: Lightweight, responsive, integrates well with React
  - Alternatives Considered: Chart.js, D3.js
  - Date: TBD
  - Status: Pending

### Modal Management

- **Decision:** Use React context for modal state instead of URL
  - Rationale: Simpler modal triggering from multiple locations
  - Alternatives Considered: URL-based modal state
  - Date: TBD
  - Status: Pending

---

## Files Changed

### New Files
- `apps/web/components/cpus/PerformanceBadge.tsx` - Performance rating badge
- `apps/web/components/cpus/PriceTargets.tsx` - Price targets display
- `apps/web/components/cpus/CPUDetailModal.tsx` - CPU detail modal
- `apps/web/components/cpus/PriceDistributionChart.tsx` - Price histogram
- `apps/web/components/cpus/TopListingsTable.tsx` - Listings in modal
- `apps/web/hooks/useCPUDetail.ts` - CPU detail hook
- `apps/web/hooks/usePerformanceRating.ts` - Performance rating hook
- `__tests__/cpus/PerformanceBadge.test.tsx` - Badge tests
- `__tests__/cpus/CPUDetailModal.test.tsx` - Modal tests
- `__tests__/cpus/PriceDistributionChart.test.tsx` - Chart tests

### Modified Files
- `apps/web/components/listings/ListingsTable.tsx` - Add CPU columns
- `apps/web/app/listings/[id]/page.tsx` - Add CPU info section
- `apps/web/package.json` - Add recharts dependency

---

## Blockers & Issues

None currently.

---

## Next Steps

1. **Wait for Phase 2 Completion**
   - Verify page structure and state management

2. **Begin FE-101: PerformanceBadge Component**
   - Define rating thresholds
   - Create component with basic styling
   - Add tooltip

3. **Parallel Work**
   - Start FE-109: useCPUDetail hook
   - Start FE-110: usePerformanceRating hook

---

## Quick Links

- **Implementation Plan:** `/mnt/containers/deal-brain/docs/project_plans/cpu-page-reskin/IMPLEMENTATION_PLAN.md`
- **PRD:** `/mnt/containers/deal-brain/docs/project_plans/cpu-page-reskin/PRD.md`
- **Phase 2 Progress:** `.claude/progress/cpu-page-reskin/phase-2-progress.md`
- **Phase Context:** `.claude/worknotes/cpu-page-reskin/phase-3-context.md`

---

**Last Updated:** 2025-11-05
**Next Review:** Upon Phase 2 completion
