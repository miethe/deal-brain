# Phase 3 Task Delegation Plan
**Created:** 2025-11-06
**Lead Architect:** Orchestration Plan
**Phase:** CPU Page Reskin - Phase 3 (Performance Metrics & Analytics)

---

## Executive Summary

Phase 3 has **REDUCED SCOPE** due to architectural discovery:
- ✅ FE-007 (PerformanceBadge) - **ALREADY COMPLETE** in Phase 2
- 🔨 FE-008 (PriceTargets) - Extract existing inline code to reusable component
- 🔨 FE-009 (Detail Modal) - Enhance existing detail-panel.tsx with charts
- ⚠️ Listings Integration - **OUT OF SCOPE** for Phase 3 (separate feature)

**Total Estimated Effort:** 8-10 hours (reduced from 18 hours)

---

## Architectural Decisions Summary

| Decision | Outcome | Impact |
|----------|---------|--------|
| AD-001: Component Reuse | Reuse existing PerformanceBadge | FE-007 eliminated |
| AD-002: Price Targets Extraction | Create PriceTargets component | New component (4h) |
| AD-003: Chart Library | Use Recharts (already installed) | No new dependencies |
| AD-004: Detail Modal | Enhance existing detail-panel.tsx | No new modal (8h) |
| AD-005: Listings Integration | Defer to separate task | Avoid scope creep |

---

## Task Breakdown with Agent Assignments

### ✅ Task 1: Validate PerformanceBadge Component (FE-007)
**Status:** COMPLETE - No work needed
**Agent:** N/A
**Estimated Effort:** 0 hours

**Rationale:**
- Component exists at `apps/web/app/cpus/_components/grid-view/performance-badge.tsx`
- Already implements all FE-007 requirements:
  - ✅ Color-coded variants (excellent, good, fair, poor)
  - ✅ Tooltips with explanations
  - ✅ Accessible (ARIA labels, keyboard support)
  - ✅ Handles null/missing data gracefully
  - ✅ Integrated in Grid View and Master-Detail View

**Action:** Mark FE-007 as complete in progress tracker.

---

### 🔨 Task 2: Create PriceTargets Component (FE-008)
**Priority:** P0
**Agent:** `ui-engineer`
**Estimated Effort:** 4 hours
**Dependencies:** None

**Description:**
Extract duplicated price target display logic into a dedicated, reusable component.

**Current State:**
- Price targets shown inline in `cpu-card.tsx` (lines 142-180)
- Price targets shown as KPI metrics in `detail-panel.tsx` (lines 90-109)
- Duplication between two components

**Requirements:**
1. Create `apps/web/app/cpus/_components/price-targets.tsx`
2. Accept `CPURecord` as prop (or extract relevant fields)
3. Display Great/Good/Fair prices with color coding:
   - Great: Green (`emerald-*` classes)
   - Good: Blue (`blue-*` classes)
   - Fair: Amber (`amber-*` classes)
4. Show confidence badge (high/medium/low/insufficient)
5. Display sample size ("Based on N listings")
6. Handle insufficient data case (< 2 listings)
7. Optional: Last updated timestamp (from `price_target_updated_at`)
8. Maintain accessibility (ARIA labels, semantic HTML)

**Component API:**
```typescript
interface PriceTargetsProps {
  cpu: CPURecord;
  variant?: 'compact' | 'detailed'; // compact for cards, detailed for panels
}

export function PriceTargets({ cpu, variant = 'compact' }: PriceTargetsProps)
```

**Acceptance Criteria:**
- [ ] Component created and typed correctly
- [ ] Shows all three price points (Great, Good, Fair) when available
- [ ] Confidence badge color matches confidence level
- [ ] Sample size displayed below price grid
- [ ] Handles null/missing data gracefully (shows message or hides section)
- [ ] Accessible (semantic HTML, ARIA labels if needed)
- [ ] Responsive (works on mobile and desktop)
- [ ] Memoized with React.memo for performance

**Files to Modify:**
- Create: `apps/web/app/cpus/_components/price-targets.tsx`
- Refactor: `apps/web/app/cpus/_components/grid-view/cpu-card.tsx` (replace inline with component)
- Refactor: `apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx` (replace KPI metrics with component)

**Delegation Command:**
```markdown
Task("ui-engineer", "Create PriceTargets component for CPU price targets display:

Requirements:
- Extract price target display logic from cpu-card.tsx and detail-panel.tsx
- Create apps/web/app/cpus/_components/price-targets.tsx
- Accept CPURecord as prop
- Display Great/Good/Fair prices with color coding (emerald, blue, amber)
- Show confidence badge (high/medium/low/insufficient)
- Display sample size ('Based on N listings')
- Handle insufficient data case (< 2 listings)
- Support two variants: 'compact' (for cards) and 'detailed' (for panels)
- Maintain accessibility (WCAG 2.1 AA)
- Memoize with React.memo
- Refactor cpu-card.tsx and detail-panel.tsx to use new component

Reference existing implementation:
- apps/web/app/cpus/_components/grid-view/cpu-card.tsx (lines 142-180)
- apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx (lines 90-109)

Types available in: apps/web/types/cpus.ts (CPURecord interface)
")
```

---

### 🔨 Task 3: Enhance Detail Panel with Analytics Sections (FE-009)
**Priority:** P1
**Agent:** `ui-engineer` (charts) + `frontend-developer` (data fetching)
**Estimated Effort:** 6-8 hours
**Dependencies:** Task 2 (PriceTargets component), Recharts library

**Description:**
Enhance existing detail panel with interactive analytics sections and charts.

**Current State:**
- Detail panel exists at `apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx`
- Shows basic KPI metrics and specifications
- Does NOT show charts or market data visualizations
- Currently fetches data from store (not detail endpoint)

**Requirements:**

**3A: Data Fetching Enhancement (frontend-developer)**
- Modify detail-panel.tsx to fetch from `/v1/cpus/{id}` endpoint
- Use React Query for detail data (not just store data)
- Response type: `CPUDetail` (includes `associated_listings` and `market_data`)
- Cache detail queries with `staleTime: 2 * 60 * 1000` (2 minutes)
- Show loading skeleton while fetching

**3B: Analytics Sections (ui-engineer)**
Add five analytics sections to detail panel:

1. **Performance Overview Section** (ENHANCE EXISTING)
   - Already shows PassMark badges
   - Add horizontal bar chart comparing ST/MT/iGPU scores to catalog average
   - Use Recharts BarChart component
   - Show percentile rank badge

2. **Performance Value Section** (NEW)
   - Use new PriceTargets component (from Task 2)
   - Show $/ST Mark and $/MT Mark metrics
   - Display value rating badge (excellent/good/fair/poor)
   - Show percentile rank with tooltip explanation

3. **Specifications Section** (EXISTING - NO CHANGES)
   - Keep current grid layout
   - Already shows cores, threads, TDP, socket, release year, iGPU

4. **Market Data Section** (NEW)
   - Show listings count
   - Price distribution histogram (Recharts AreaChart or BarChart)
   - X-axis: Price buckets, Y-axis: Count
   - Highlight CPU's price targets on chart (vertical lines)

5. **Associated Listings Section** (NEW)
   - Show top 10 associated listings (from `CPUDetail.associated_listings`)
   - Table with: Title, Base Price, Adjusted Price, Condition, Marketplace
   - "View All Listings" button navigates to `/dashboard/listings?cpu_id={id}`
   - Optional: Link to listing detail page

**Component Structure:**
```typescript
// Fetch detail data
const { data: cpuDetail, isLoading } = useQuery({
  queryKey: ["cpu", cpuId, "detail"],
  queryFn: () => apiFetch<CPUDetail>(`/v1/cpus/${cpuId}`),
  enabled: !!cpuId,
  staleTime: 2 * 60 * 1000,
});

// Sections (in order)
<PerformanceOverviewSection cpu={cpuDetail} /> // with chart
<PerformanceValueSection cpu={cpuDetail} /> // use PriceTargets component
<SpecificationsSection cpu={cpuDetail} /> // existing
<MarketDataSection cpu={cpuDetail} /> // with histogram
<AssociatedListingsSection listings={cpuDetail.associated_listings} />
```

**Charts to Implement:**
1. **PassMark Comparison Bar Chart** (Recharts BarChart)
   - Data: [{ metric: 'ST', value: cpu.cpu_mark_single, avg: catalogAverage }]
   - Grouped bars (CPU value vs Catalog average)
   - Color code by performance rating

2. **Price Distribution Histogram** (Recharts BarChart or AreaChart)
   - Data: `cpuDetail.market_data.price_distribution` (array of prices)
   - Create buckets (10-15 buckets across price range)
   - Show count per bucket
   - Overlay price targets as vertical reference lines

**Acceptance Criteria:**
- [ ] Detail panel fetches from `/v1/cpus/{id}` endpoint
- [ ] Loading skeleton shows while fetching
- [ ] All five sections render correctly
- [ ] PassMark comparison chart displays correctly
- [ ] Price distribution histogram displays correctly
- [ ] Associated listings table shows top 10 listings
- [ ] "View All Listings" button navigates correctly
- [ ] Charts are accessible (ARIA labels, keyboard nav)
- [ ] Charts are responsive (resize with container)
- [ ] Error states handled gracefully

**Files to Modify:**
- `apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx` (main enhancement)
- Create: `apps/web/app/cpus/_components/master-detail-view/passmark-chart.tsx` (optional: extract chart)
- Create: `apps/web/app/cpus/_components/master-detail-view/price-distribution-chart.tsx` (optional: extract chart)

**Delegation Commands:**

**Step 1: Data Fetching (frontend-developer)**
```markdown
Task("frontend-developer", "Enhance CPU detail panel data fetching:

Requirements:
- Modify apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx
- Add React Query hook to fetch /v1/cpus/{id} endpoint
- Use CPUDetail type from apps/web/types/cpus.ts
- Cache with staleTime: 2 minutes
- Show loading skeleton while fetching
- Handle error states

API Response Type: CPUDetail (includes associated_listings and market_data)

Reference:
- Existing detail-panel.tsx for component structure
- apps/web/types/cpus.ts for CPUDetail interface
")
```

**Step 2: Analytics Sections + Charts (ui-engineer)**
```markdown
Task("ui-engineer", "Add analytics sections and charts to CPU detail panel:

Requirements:
1. Performance Overview Section:
   - Add PassMark comparison bar chart (Recharts BarChart)
   - Compare CPU scores to catalog average
   - Color code by performance rating

2. Performance Value Section:
   - Use PriceTargets component (from Task 2)
   - Show $/ST Mark and $/MT Mark
   - Display value rating badge
   - Show percentile rank

3. Market Data Section (NEW):
   - Show listings count
   - Price distribution histogram (Recharts BarChart)
   - Overlay price targets as reference lines
   - X-axis: Price buckets, Y-axis: Count

4. Associated Listings Section (NEW):
   - Table showing top 10 associated listings
   - Columns: Title, Base Price, Adjusted Price, Condition, Marketplace
   - 'View All Listings' button → /dashboard/listings?cpu_id={id}

Charts:
- Use Recharts library (already installed)
- Maintain accessibility (ARIA labels, tooltips)
- Responsive design (resize with container)
- Handle null/missing data gracefully

Data Sources:
- cpuDetail.market_data.price_distribution (array of prices for histogram)
- cpuDetail.associated_listings (top 10 listings)
- cpuDetail.price_targets (for reference lines)

Reference:
- apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx (existing structure)
- apps/web/app/cpus/_components/price-targets.tsx (PriceTargets component from Task 2)
- Recharts documentation for chart examples
")
```

---

### 📝 Task 4: Update Documentation (documentation-writer)
**Priority:** P2
**Agent:** `documentation-writer`
**Estimated Effort:** 1 hour
**Dependencies:** Tasks 2 and 3 complete

**Description:**
Document new components and enhanced features for future developers.

**Requirements:**
1. Add JSDoc comments to PriceTargets component
2. Add JSDoc comments to chart components (if extracted)
3. Update Phase 3 progress tracker with completion status
4. Document chart data structure and props

**Delegation Command:**
```markdown
Task("documentation-writer", "Document Phase 3 components:

Requirements:
- Add comprehensive JSDoc comments to PriceTargets component
- Document chart components (PassMark comparison, price distribution)
- Include prop types, usage examples, accessibility notes
- Update Phase 3 progress tracker (.claude/progress/cpu-page-reskin/phase-3-progress.md)

Files:
- apps/web/app/cpus/_components/price-targets.tsx
- apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx
- .claude/progress/cpu-page-reskin/phase-3-progress.md
")
```

---

## Implementation Order (Dependencies Considered)

**Sequential Order:**

1. ✅ **Validate PerformanceBadge** (0h)
   - No work needed, mark FE-007 as complete

2. 🔨 **Create PriceTargets Component** (4h - ui-engineer)
   - Standalone component, no dependencies
   - Required by Task 3

3. 🔨 **Enhance Detail Panel - Data Fetching** (2h - frontend-developer)
   - Fetch CPUDetail from API endpoint
   - Required by Task 3B (charts need data)

4. 🔨 **Enhance Detail Panel - Analytics Sections** (6h - ui-engineer)
   - Depends on: Task 2 (PriceTargets) + Task 3A (data fetching)
   - Add charts and analytics sections

5. 📝 **Update Documentation** (1h - documentation-writer)
   - Depends on: Tasks 2 and 3 complete
   - Document components and charts

**Total Timeline:** 13 hours (sequential), ~10 hours (with parallelization)

---

## Identified Risks & Mitigation

### Risk 1: Listings Page Integration Scope Creep
**Risk Level:** HIGH
**Description:** PRD mentions "Integrate performance metrics into Listings page/table"
**Mitigation:**
- Explicitly mark as OUT OF SCOPE for Phase 3
- Listings page is separate feature with different routing/store
- Create separate task/ticket for Listings integration
- Focus Phase 3 on CPU catalog page only

### Risk 2: Chart Performance with Large Datasets
**Risk Level:** MEDIUM
**Description:** Price distribution histogram may lag with 500+ data points
**Mitigation:**
- Bucket prices into 10-15 bins (not 1:1 data points)
- Use Recharts built-in optimization
- Debounce resize events
- Monitor performance with React DevTools Profiler

### Risk 3: API Endpoint Availability
**Risk Level:** LOW
**Description:** `/v1/cpus/{id}` endpoint may not return all required fields
**Mitigation:**
- Verify endpoint response matches `CPUDetail` type before implementation
- Test with sample CPU IDs from backend
- Handle missing fields gracefully (show placeholders)

### Risk 4: Component Refactoring Breaking Changes
**Risk Level:** MEDIUM
**Description:** Refactoring CPUCard and DetailPanel to use PriceTargets may break existing functionality
**Mitigation:**
- Test Grid View and Master-Detail View after refactoring
- Ensure visual consistency (same styling before/after)
- Use React.memo to prevent unnecessary re-renders
- Incremental refactoring: refactor one component at a time

---

## Success Criteria (from Progress Tracker)

- [ ] Performance badges display correct ratings (✅ Already complete - Phase 2)
- [ ] Price targets show confidence levels accurately (🔨 Task 2)
- [ ] Detail modal loads in < 300ms (🔨 Task 3 - detail panel enhancement)
- [ ] All tooltips provide helpful context (✅ Already complete - Phase 2)
- [ ] Charts render without performance issues (🔨 Task 3)
- [ ] Listings integration doesn't break existing functionality (⚠️ OUT OF SCOPE - deferred)

**Adjusted Success Criteria for Phase 3:**
- [x] PerformanceBadge component displays correct ratings (already complete)
- [ ] PriceTargets component shows confidence levels accurately
- [ ] Detail panel fetches data in < 300ms
- [ ] Charts render without lag (< 16ms per frame)
- [ ] All charts are accessible (WCAG 2.1 AA)
- [ ] Tooltips provide helpful context for metrics

---

## Key Patterns to Enforce (For Subagents)

### 1. Component Composition
- Reuse existing UI components (Badge, Tooltip, Card, Button)
- Follow shadcn/ui patterns for consistency
- Use Radix UI primitives for accessibility

### 2. Type Safety
- All components use TypeScript interfaces from `types/cpus.ts`
- No `any` types allowed
- Explicit prop types for all components

### 3. Accessibility (WCAG 2.1 AA)
- ARIA labels for charts and interactive elements
- Keyboard navigation support (Tab, Enter, Escape)
- Screen reader compatibility (test with VoiceOver/NVDA)
- Sufficient color contrast for all text

### 4. Performance
- Memoize components with React.memo
- Debounce expensive operations (chart resizing)
- Use React Query caching (staleTime, cacheTime)
- Virtualize long lists if needed (> 100 items)

### 5. Error Handling
- Gracefully handle null/missing data (show "-" or placeholder)
- Show loading skeletons during data fetching
- Display error messages for failed API calls
- Fallback UI for charts that fail to render

### 6. Code Organization
- Keep components small and focused (< 300 lines)
- Extract charts to separate files if > 100 lines
- Co-locate component files with related view (grid-view/, master-detail-view/)
- Use barrel exports (index.ts) for cleaner imports

---

## Out of Scope (Explicitly)

**NOT included in Phase 3:**
1. ❌ Listings page integration (separate feature, different scope)
2. ❌ New modal component (enhance existing detail panel instead)
3. ❌ Backend API changes (Phase 1 complete, no backend work needed)
4. ❌ Dense List View enhancements (Phase 2 complete)
5. ❌ Data Table view (Phase 2 complete)
6. ❌ URL synchronization (Phase 2 complete)
7. ❌ Export to CSV functionality (future enhancement)
8. ❌ Edit CPU functionality (admin feature, separate task)

---

## Next Steps (After Delegation)

1. **Execute Task 2:** Delegate PriceTargets component creation to ui-engineer
2. **Execute Task 3A:** Delegate data fetching enhancement to frontend-developer
3. **Execute Task 3B:** Delegate analytics sections to ui-engineer (after 3A completes)
4. **Execute Task 4:** Delegate documentation to documentation-writer
5. **Review:** Conduct architecture review of completed components
6. **Test:** Manual testing of all analytics features
7. **Update Progress:** Mark Phase 3 as complete in progress tracker

---

## Appendix: File References

**Components to Create:**
- `apps/web/app/cpus/_components/price-targets.tsx` (NEW)

**Components to Enhance:**
- `apps/web/app/cpus/_components/master-detail-view/detail-panel.tsx` (ENHANCE)
- `apps/web/app/cpus/_components/grid-view/cpu-card.tsx` (REFACTOR - use PriceTargets)

**Components Already Complete (No Changes):**
- `apps/web/app/cpus/_components/grid-view/performance-badge.tsx` (✅ Complete)
- `apps/web/app/cpus/_components/grid-view/cpu-card.tsx` (✅ Complete - except price targets refactor)
- `apps/web/app/cpus/_components/list-view/*` (✅ Complete)
- `apps/web/stores/cpu-catalog-store.ts` (✅ Complete)

**Types:**
- `apps/web/types/cpus.ts` (CPURecord, CPUDetail, PriceTarget, PerformanceValue)

**API Endpoints:**
- `GET /v1/cpus` - List CPUs with analytics (already used in Phase 2)
- `GET /v1/cpus/{id}` - Get CPU detail with market data (NEW usage in Phase 3)

---

**End of Delegation Plan**
