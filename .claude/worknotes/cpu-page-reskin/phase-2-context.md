# CPU Page Reskin - Phase 2 Context & Implementation Notes

**Project:** CPU Catalog Page Reskin
**Phase:** 2 - Frontend Core
**Created:** 2025-11-05

---

## Current State

Phase 2 begins after Phase 1 completes. This phase builds the core frontend experience with:

1. CPU Catalog page structure with dual-tab interface
2. Three view modes: Grid, List, Master-Detail
3. Zustand store for state management
4. Client-side filtering with URL synchronization
5. React Query integration for API data fetching

**Key Dependency:** Phase 1 API endpoints must be functional before starting

**Deliverables Upon Completion:**
- `/cpus` page with fully functional dual-tab interface
- Three view modes with working interactions
- Zustand store managing filter state
- URL-synchronized filter state
- React Query hooks for data fetching
- Full component test suite

---

## Key Decisions

### State Management Approach

**Decision:** Use Zustand for CPU catalog state management
- **Rationale:**
  - Lightweight (~2KB), better performance than Context API
  - Less boilerplate than Redux
  - Easy to debug and test
  - Good integration with persistence (localStorage)
- **Alternative Considered:** Context API (rejected for re-render overhead), Redux (rejected for complexity)

**Store Structure:**
```typescript
interface CPUCatalogState {
  // Filters
  filters: {
    manufacturers: string[];
    sockets: string[];
    coresRange: [number, number];
    tdpRange: [number, number];
    yearRange: [number, number];
    searchQuery: string;
  };

  // UI State
  selectedCpuId: number | null;
  viewMode: 'grid' | 'list' | 'master-detail';
  sortBy: 'name' | 'cores' | 'price' | 'performance';
  sortOrder: 'asc' | 'desc';
  currentPage: number;

  // Actions
  setFilters: (filters: Partial<Filters>) => void;
  clearFilters: () => void;
  setViewMode: (mode: ViewMode) => void;
  setSelectedCpuId: (id: number | null) => void;
  // ... other actions
}
```

### View Modes Architecture

**Decision:** Separate components for each view mode
- **Rationale:**
  - Clear separation of concerns
  - Easier to test and maintain
  - Different layout requirements
  - Potential for lazy loading

**Component Structure:**
- `CPUCatalogPage.tsx` - Page wrapper, tab switcher
- `GridView.tsx` - Card-based grid layout
- `ListView.tsx` - Table-based list with virtualization
- `MasterDetailView.tsx` - Two-panel responsive layout

**Shared Components:**
- `CPUCard.tsx` - Reusable card for grid view
- `CPUListItem.tsx` - Reusable row for list view
- `CPUFilterPanel.tsx` - Filter controls (shared across views)

### URL Synchronization Strategy

**Decision:** Keep filter state synchronized with URL query parameters
- **Rationale:**
  - Allow shareable links to filtered views
  - Support browser back/forward navigation
  - Bookmarkable states
  - SEO benefits
- **Implementation:** Use `next/router` to sync store ↔ URL

**URL Pattern:**
```
/cpus?view=grid&sort=name&manufacturers=Intel,AMD&cores=8-16
/cpus?view=list&sort=price-desc&sockets=LGA1700
/cpus?view=master-detail&selected=5
```

**Sync Strategy:**
- On mount: Hydrate store from URL params
- On store change: Update URL (debounced)
- On URL change: Update store (e.g., browser back button)
- Validate URL params (ignore invalid values)

### Data Fetching Approach

**Decision:** Use React Query for API data fetching
- **Rationale:**
  - Built-in caching
  - Automatic stale-while-revalidate
  - Easy refetching
  - Great DevTools
- **Hook Pattern:**
  ```typescript
  const { data: cpus, isLoading, error } = useListCpus({
    include_analytics: true
  });

  const { data: stats } = useCpuStatistics(); // For filter options
  ```

**Caching Strategy:**
- CPU list: Cache for 5 minutes (likely to change less frequently)
- Statistics: Cache for 1 hour (never changes during session)
- Individual CPU: Cache indefinitely (reference data)

---

## Important Learnings

### From Listings Page Pattern

The Listings page in Deal Brain has a similar structure:

1. **Similar Features:**
   - Multiple view modes (needed to review implementation)
   - Filter panel on left
   - URL synchronization
   - Virtual scrolling for large datasets
   - React Query for data fetching

2. **Reusable Patterns:**
   - Filter state management pattern
   - URL sync hooks
   - Virtual list components
   - Table column configuration

3. **Files to Reference:**
   - `apps/web/components/listings/ListingsPage.tsx`
   - `apps/web/stores/listings-store.ts` (if using Zustand)
   - `apps/web/hooks/useListings.ts`

**Note:** Review how Listings page implements view modes and filters - we'll follow similar patterns for consistency.

### React Virtual for Virtualization

List view with 500+ CPUs needs virtualization to stay performant:

1. **Install:** Already available in dependencies
2. **Implementation:**
   - Wrap list items with `FixedSizeList` or `VariableSizeList`
   - Render visible items only
   - Smooth scroll with proper height calculation
   - Maintain selection state during scroll

3. **Key Considerations:**
   - Row height must be consistent or pre-calculated
   - Selection highlighting must work with virtualization
   - Keyboard navigation (arrow keys) needs special handling

### Responsive Design Breakpoints

Target breakpoints (Tailwind):
- Mobile: < 640px (single column, stacked filters)
- Tablet: 640px - 1024px (2 columns, sidebar filters)
- Desktop: > 1024px (full layout, floating filters)

Master-Detail view is challenging on mobile - consider collapsible side panel or bottom sheet.

---

## Quick Reference

### Files Involved

**Pages:**
- `apps/web/app/cpus/page.tsx` - Route page
- `apps/web/app/cpus/layout.tsx` - Page layout (if needed)

**Components:**
- `apps/web/components/cpus/CPUCatalogPage.tsx` - Main page component
- `apps/web/components/cpus/GridView.tsx` - Grid view
- `apps/web/components/cpus/ListView.tsx` - List view
- `apps/web/components/cpus/MasterDetailView.tsx` - Master-detail view
- `apps/web/components/cpus/CPUCard.tsx` - Card component
- `apps/web/components/cpus/CPUFilterPanel.tsx` - Filters
- `apps/web/components/cpus/CPUListItem.tsx` - List item

**State & Hooks:**
- `apps/web/stores/cpu-catalog-store.ts` - Zustand store
- `apps/web/hooks/useCpuCatalog.ts` - Custom hooks
- `apps/web/lib/cpu-api.ts` - API client functions

**Tests:**
- `__tests__/cpus/CPUCatalog.test.tsx` - Integration tests
- `__tests__/stores/cpuCatalogStore.test.ts` - Store tests
- `__tests__/cpus/GridView.test.tsx` - Grid view tests
- `__tests__/cpus/ListView.test.tsx` - List view tests

### Common Commands

```bash
# Development server
make web
# or
cd apps/web && pnpm dev

# Run frontend tests
cd apps/web && pnpm test

# Lint frontend code
cd apps/web && pnpm lint

# Build for production
cd apps/web && pnpm build

# Type check
cd apps/web && pnpm tsc --noEmit

# Format code
cd apps/web && pnpm format
```

### Development Patterns

```typescript
// Using the Zustand store
import { useCpuCatalogStore } from '@/stores/cpu-catalog-store';

export function CPUFilterPanel() {
  const filters = useCpuCatalogStore((s) => s.filters);
  const setFilters = useCpuCatalogStore((s) => s.setFilters);

  return (
    // Filter controls
  );
}

// Using React Query
import { useListCpus } from '@/hooks/useListCpus';

export function CPUGrid() {
  const { data: cpus, isLoading, error } = useListCpus({
    include_analytics: true
  });

  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="grid grid-cols-3 gap-4">
      {cpus?.map(cpu => <CPUCard key={cpu.id} cpu={cpu} />)}
    </div>
  );
}

// URL synchronization helper
export function useUrlSync() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const updateUrl = useCallback((params: Record<string, any>) => {
    const query = new URLSearchParams(searchParams);
    Object.entries(params).forEach(([key, value]) => {
      if (value) query.set(key, value);
      else query.delete(key);
    });
    router.push(`/cpus?${query.toString()}`);
  }, [router, searchParams]);

  return updateUrl;
}
```

### Performance Optimization Checklist

- [ ] Memoize expensive components with `React.memo()`
- [ ] Use `useMemo()` for filter derivations
- [ ] Debounce search input (200ms typical)
- [ ] Lazy load images in grid view
- [ ] Use virtual scrolling for lists > 100 items
- [ ] Limit re-renders with proper selector usage in Zustand
- [ ] Cache React Query results appropriately

---

## Phase Scope Summary

**Frontend Core Phase encompasses:**

1. Page Structure & Layout (6 hours)
   - Create `/cpus` page
   - Dual-tab interface
   - Layout with Tailwind

2. View Modes (24 hours)
   - Grid view component
   - List view component
   - Master-detail view component
   - Responsive design

3. State Management (6 hours)
   - Zustand store
   - Filter actions
   - View mode management
   - LocalStorage persistence

4. Filtering & Sync (12 hours)
   - Filter controls
   - URL synchronization
   - Browser navigation

5. Data Fetching (4 hours)
   - React Query setup
   - API hooks
   - Caching strategy

6. Testing & Polish (8 hours)
   - Component unit tests
   - Integration tests
   - Accessibility
   - Responsive testing

**Total: 40 hours (5 days)**

**Critical Path:** Page Structure → View Modes → Store → Filtering → API Integration → Testing

---

## Next Session Preparation

Before starting Phase 2:

1. **Review Phase 1 Deliverables**
   - Verify all API endpoints working
   - Test endpoints with curl/Postman
   - Check response schemas

2. **Review Listings Page**
   - Study `apps/web/components/listings/ListingsPage.tsx`
   - Understand view modes implementation
   - Review filter panel pattern

3. **Setup Frontend Environment**
   - Run `make web` to start dev server
   - Verify API connectivity
   - Test API endpoints from browser

4. **Start with FE-001: Page Structure**
   - Create `/cpus/page.tsx`
   - Create CPUCatalogPage component
   - Implement tab switching

---

**Last Updated:** 2025-11-05
**Status:** Planning Complete, Ready for Phase 1 Completion
