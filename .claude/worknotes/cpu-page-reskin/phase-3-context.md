# CPU Page Reskin - Phase 3 Context & Implementation Notes

**Project:** CPU Catalog Page Reskin
**Phase:** 3 - Performance Metrics & Analytics
**Created:** 2025-11-05

---

## Current State

Phase 3 begins after Phases 1-2 are complete. This phase integrates performance metrics and analytics components:

1. PerformanceBadge component for visual ratings
2. PriceTargets component for price ranges
3. CPUDetailModal for comprehensive analytics
4. Integration with Listings page
5. Charts and visualizations

**Key Dependencies:**
- Phase 1: Analytics data must be available in API
- Phase 2: Page structure and state management complete

**Deliverables Upon Completion:**
- PerformanceBadge component with ratings
- PriceTargets display component
- CPUDetailModal with tabs and analytics
- Price distribution chart visualization
- Listings page integration
- Full component test suite
- Accessibility and performance optimizations

---

## Key Decisions

### Performance Rating Display

**Decision:** Color-coded badge component with percentile ranking
- **Rationale:**
  - Visual, easy to understand at a glance
  - Consistent with Listings page valuation coloring
  - Accessible with proper contrast and labels
- **Rating Thresholds:**
  - Excellent: > 75th percentile (Green)
  - Good: > 50th percentile (Blue)
  - Fair: > 25th percentile (Yellow)
  - Poor: <= 25th percentile (Red)

**Component Structure:**
```typescript
interface PerformanceBadgeProps {
  rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
  percentile: number | null;
  showPercentile?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showTooltip?: boolean;
}

// Colors mapping
const colorMap = {
  excellent: 'bg-green-100 text-green-800 border-green-300',
  good: 'bg-blue-100 text-blue-800 border-blue-300',
  fair: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  poor: 'bg-red-100 text-red-800 border-red-300',
};
```

### Price Targets Display

**Decision:** Three-tier pricing with confidence indicators
- **Rationale:**
  - Shows market reality (range, not single price)
  - Confidence indicates data quality
  - Helps users understand value
- **Display Logic:**
  - Show "Great", "Good", "Fair" prices
  - Include sample size (e.g., "Based on 15 listings")
  - Confidence badge (High/Medium/Low/Insufficient)
  - Show standard deviation for spread visualization

### CPU Detail Modal Architecture

**Decision:** Tabbed modal with comprehensive information
- **Rationale:**
  - Organize lots of information
  - Avoid overwhelming UI
  - Similar to existing modals in app
  - Supports keyboard navigation

**Tab Structure:**
1. **Overview Tab**
   - CPU name, manufacturer, model
   - Socket, cores, threads, TDP, release year
   - Product image if available

2. **Performance Tab**
   - Performance badge (rating + percentile)
   - PassMark scores (single/multi-thread)
   - $/Mark metrics (single + multi)
   - Comparison to average

3. **Pricing Tab**
   - Price targets (Great/Good/Fair)
   - Sample size and confidence
   - Standard deviation visualization
   - Last updated timestamp

4. **Market Tab**
   - Top 10 listings for this CPU
   - Price distribution histogram
   - Average, median, min, max prices
   - Link to full listings

**Component Structure:**
```typescript
interface CPUDetailModalProps {
  cpuId: number;
  isOpen: boolean;
  onClose: () => void;
}

// Internal structure
<Modal>
  <TabGroup>
    <Tab label="Overview">...</Tab>
    <Tab label="Performance">...</Tab>
    <Tab label="Pricing">...</Tab>
    <Tab label="Market">...</Tab>
  </TabGroup>
</Modal>
```

### Chart Library Selection

**Decision:** Use Recharts for visualizations
- **Rationale:**
  - Lightweight, good performance
  - Responsive by default
  - Easy integration with React
  - Good for histogram/distribution charts
- **Alternatives Considered:**
  - Chart.js (more heavyweight)
  - D3.js (too low-level)
  - Victory (similar, but Recharts is more popular)

**Key Charts:**
1. **Price Distribution Histogram**
   - X-axis: Price range buckets
   - Y-axis: Number of listings
   - Show mean/median lines
   - Interactive tooltips

### Listings Page Integration

**Decision:** Add CPU columns to Listings table
- **Rationale:**
  - Consistent with existing UI patterns
  - Users can see CPU performance when browsing listings
  - Clicking badge opens CPU detail modal
  - Minimal changes to existing table
- **New Columns:**
  - "CPU Performance" - Shows badge with rating
  - "CPU Price Target" - Shows Great/Good/Fair prices
  - Optional: "$/Mark" metric column

**Implementation Pattern:**
```typescript
// In ListingsTable.tsx
const columns = [
  // ... existing columns ...
  {
    id: 'cpu-performance',
    header: 'CPU Performance',
    cell: (listing) => (
      <PerformanceBadge
        cpuId={listing.cpu_id}
        onClick={() => openCPUDetailModal(listing.cpu_id)}
      />
    ),
  },
  {
    id: 'cpu-price-target',
    header: 'CPU Price Target',
    cell: (listing) => (
      <PriceTargets
        cpuId={listing.cpu_id}
        onClick={() => openCPUDetailModal(listing.cpu_id)}
      />
    ),
  },
];
```

---

## Important Learnings

### From Valuation Component Pattern

Deal Brain's valuation system has similar color-coding:

1. **Existing Color Patterns:**
   - Great Deal: Green
   - Good Deal: Blue
   - Fair Deal: Yellow
   - Premium: Red

2. **Consistency Requirement:** Use similar colors for performance badges

3. **Files to Reference:**
   - `apps/web/components/listings/ValuationBadge.tsx`
   - `apps/web/components/listings/PriceDisplay.tsx`
   - `apps/web/lib/valuation-utils.ts`

### Modal Pattern in Codebase

Review existing modals for consistency:

1. **Modal Libraries Used:**
   - Probably shadcn/ui or Headless UI
   - Check `apps/web/components/ui/modal.tsx`

2. **Modal Features to Match:**
   - Close button and Escape key handling
   - Focus management
   - Animation/transitions
   - Backdrop click behavior

3. **Files to Reference:**
   - `apps/web/components/listings/ListingDetailModal.tsx` (if exists)
   - `apps/web/components/ui/modal.tsx`
   - Review how modals are triggered and managed in store

### React Query Data Fetching

Get CPU detail data using React Query:

1. **New Query Hook Needed:**
   ```typescript
   export function useCPUDetail(cpuId: number | null) {
     return useQuery({
       queryKey: ['cpu', cpuId],
       queryFn: () => getCPUDetail(cpuId),
       enabled: cpuId !== null,
     });
   }
   ```

2. **Cache Strategy:**
   - Cache individual CPU details indefinitely (reference data)
   - Share cache with list view for seamless transitions

---

## Quick Reference

### Files Involved

**Components:**
- `apps/web/components/cpus/PerformanceBadge.tsx` - Rating badge
- `apps/web/components/cpus/PriceTargets.tsx` - Price tier display
- `apps/web/components/cpus/CPUDetailModal.tsx` - Main modal
- `apps/web/components/cpus/CPUDetailTabs.tsx` - Tab container
- `apps/web/components/cpus/CPUOverviewTab.tsx` - Overview content
- `apps/web/components/cpus/CPUPerformanceTab.tsx` - Performance content
- `apps/web/components/cpus/CPUPricingTab.tsx` - Pricing content
- `apps/web/components/cpus/CPUMarketTab.tsx` - Market content
- `apps/web/components/cpus/PriceDistributionChart.tsx` - Chart
- `apps/web/components/cpus/TopListingsTable.tsx` - Listings table

**Hooks & Utilities:**
- `apps/web/hooks/useCPUDetail.ts` - Fetch CPU detail
- `apps/web/hooks/usePerformanceRating.ts` - Rating calculation
- `apps/web/lib/performance-utils.ts` - Performance calculations

**Listings Integration:**
- `apps/web/components/listings/ListingsTable.tsx` - Add columns
- `apps/web/app/listings/[id]/page.tsx` - Add CPU info section

**Tests:**
- `__tests__/cpus/PerformanceBadge.test.tsx` - Badge tests
- `__tests__/cpus/CPUDetailModal.test.tsx` - Modal tests
- `__tests__/cpus/PriceDistributionChart.test.tsx` - Chart tests
- `__tests__/cpus/integration-listings.test.tsx` - Integration tests

### Dependencies to Add

```json
{
  "recharts": "^2.10.0"  // If not already present
}
```

### Common Commands

```bash
# Run specific component tests
cd apps/web && pnpm test PerformanceBadge

# Test charts specifically
cd apps/web && pnpm test PriceDistributionChart

# Type check
cd apps/web && pnpm tsc --noEmit

# Lint before commit
cd apps/web && pnpm lint

# Format code
cd apps/web && pnpm format
```

### Component Development Pattern

```typescript
// Performance Badge Example
import { Badge } from '@/components/ui/badge';
import { Tooltip } from '@/components/ui/tooltip';

export interface PerformanceBadgeProps {
  rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
  percentile: number | null;
  size?: 'sm' | 'md' | 'lg';
}

export function PerformanceBadge({
  rating,
  percentile,
  size = 'md'
}: PerformanceBadgeProps) {
  if (!rating || percentile === null) {
    return <span className="text-gray-400">No data</span>;
  }

  const colorMap = {
    excellent: 'bg-green-100 text-green-800',
    good: 'bg-blue-100 text-blue-800',
    fair: 'bg-yellow-100 text-yellow-800',
    poor: 'bg-red-100 text-red-800',
  };

  const label = `${rating.charAt(0).toUpperCase() + rating.slice(1)} (${percentile.toFixed(0)}%)`;

  return (
    <Tooltip content={`Performance rating based on $/Mark comparison`}>
      <Badge variant="outline" className={colorMap[rating]}>
        {label}
      </Badge>
    </Tooltip>
  );
}

// Modal Trigger Pattern
import { useCallback, useState } from 'react';

export function CPUBadgeButton({ cpuId: number }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: cpu, isLoading } = useCPUDetail(cpuId);

  const handleOpenModal = useCallback(() => {
    setIsModalOpen(true);
  }, []);

  return (
    <>
      <button onClick={handleOpenModal}>
        <PerformanceBadge
          rating={cpu?.performance_value?.rating}
          percentile={cpu?.performance_value?.percentile}
        />
      </button>

      {isModalOpen && (
        <CPUDetailModal
          cpuId={cpuId}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
}
```

### Accessibility Checklist

- [ ] Badge has `role="img"` or similar
- [ ] Color not the only indicator (use labels)
- [ ] Modal has proper focus management
- [ ] Keyboard navigation (Tab, Shift+Tab, Escape)
- [ ] ARIA labels for interactive elements
- [ ] Screen reader support for charts
- [ ] Sufficient color contrast (WCAG AA)

---

## Phase Scope Summary

**Performance Metrics & Analytics Phase encompasses:**

1. Badge Component (12 hours)
   - PerformanceBadge with ratings
   - Rating algorithm
   - Styling and variants
   - Tooltip support

2. Price Display (10 hours)
   - PriceTargets component
   - Confidence indicators
   - Formatting and styling

3. Detail Modal (18 hours)
   - Modal structure
   - Four tabs with content
   - Charts and visualizations
   - Data loading and error states

4. Listings Integration (10 hours)
   - CPU columns in table
   - Modal triggering
   - Detail page updates

5. Testing & Polish (10 hours)
   - Component tests
   - Integration tests
   - Accessibility audit
   - Performance optimization

**Total: 40+ hours (5 days)**

**Critical Path:** Badge → Modal Structure → Tabs → Charts → Listings Integration → Testing

---

## Next Session Preparation

Before starting Phase 3:

1. **Verify Phase 1 & 2 Complete**
   - API endpoints functional
   - Page structure complete
   - State management working

2. **Review Existing Component Patterns**
   - Study ValuationBadge implementation
   - Review Modal usage in codebase
   - Check chart implementations

3. **Design System Review**
   - Color palette for ratings
   - Typography for modal
   - Spacing and sizing scales

4. **Start with FE-101: PerformanceBadge**
   - Create component
   - Define rating thresholds
   - Add basic styling

---

**Last Updated:** 2025-11-05
**Status:** Planning Complete, Ready for Phase 2 Completion
