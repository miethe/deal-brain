# Implementation Plan: Listings Catalog View Revamp

**Status:** Ready for Execution
**Version:** 1.0
**Last Updated:** 2025-10-06
**Lead Architect:** Claude Code

---

## Overview

This document provides the technical implementation roadmap for the Listings Catalog View Revamp, breaking down the work into discrete tasks with clear dependencies, technical specifications, and quality gates.

---

## Architecture Design

### Component Architecture

```
apps/web/app/listings/page.tsx (MODIFIED)
├── State Management: Zustand store
├── Data Layer: React Query hooks
└── Component Tree:
    ├── ListingsTabs (NEW)
    │   ├── TabsList (shadcn/ui)
    │   └── TabsContent[]
    │       ├── CatalogTab (NEW)
    │       │   ├── ListingsFilters (NEW - shared)
    │       │   ├── ViewSwitcher (NEW)
    │       │   └── ActiveView (conditional render)
    │       │       ├── GridView (NEW)
    │       │       ├── DenseListView (NEW)
    │       │       └── MasterDetailView (NEW)
    │       └── DataTab (existing ListingsTable)
    └── Dialogs (NEW)
        ├── ListingDetailsDialog
        ├── QuickEditDialog
        └── ValuationBreakdownModal (existing)
```

### File Structure

```
apps/web/
├── app/
│   └── listings/
│       ├── page.tsx (MODIFIED - add tabs)
│       └── _components/ (NEW)
│           ├── catalog-tab.tsx
│           ├── view-switcher.tsx
│           ├── listings-filters.tsx
│           ├── grid-view/
│           │   ├── index.tsx
│           │   ├── listing-card.tsx
│           │   └── performance-badges.tsx
│           ├── dense-list-view/
│           │   ├── index.tsx
│           │   └── dense-table.tsx
│           └── master-detail-view/
│               ├── index.tsx
│               ├── master-list.tsx
│               ├── detail-panel.tsx
│               ├── compare-drawer.tsx
│               ├── kpi-metric.tsx
│               └── key-value.tsx
├── components/
│   └── listings/ (MODIFIED - add new dialogs)
│       ├── listing-details-dialog.tsx (NEW)
│       └── quick-edit-dialog.tsx (NEW)
├── hooks/ (NEW)
│   ├── use-catalog-state.ts
│   ├── use-listing-filters.ts
│   └── use-compare-selections.ts
├── lib/ (MODIFIED)
│   ├── utils.ts (add formatting helpers)
│   └── valuation-utils.ts (extend if needed)
└── stores/ (NEW)
    └── catalog-store.ts
```

---

## State Management Design

### Zustand Store Schema

```typescript
// apps/web/stores/catalog-store.ts

interface CatalogState {
  // View mode
  activeView: 'grid' | 'list' | 'master-detail';
  setActiveView: (view: CatalogState['activeView']) => void;

  // Active tab
  activeTab: 'catalog' | 'data';
  setActiveTab: (tab: CatalogState['activeTab']) => void;

  // Filters
  filters: {
    searchQuery: string;
    formFactor: string; // 'all' | 'Mini-PC' | 'Laptop' | etc.
    manufacturer: string; // 'all' | manufacturer name
    priceRange: number; // max price in USD
  };
  setFilters: (filters: Partial<CatalogState['filters']>) => void;
  clearFilters: () => void;

  // Compare selections (for Master-Detail view)
  compareSelections: number[]; // listing IDs
  toggleCompare: (id: number) => void;
  clearCompare: () => void;

  // Selected listing for detail panel
  selectedListingId: number | null;
  setSelectedListing: (id: number | null) => void;

  // Dialog states
  detailsDialogOpen: boolean;
  detailsDialogListingId: number | null;
  openDetailsDialog: (id: number) => void;
  closeDetailsDialog: () => void;

  quickEditDialogOpen: boolean;
  quickEditDialogListingId: number | null;
  openQuickEditDialog: (id: number) => void;
  closeQuickEditDialog: () => void;
}
```

### URL State Synchronization

```typescript
// Sync state to URL params
?view=grid&tab=catalog&q=intel&formFactor=Mini-PC&manufacturer=ASUS&maxPrice=800

// Parse on mount, update on state change
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  // Hydrate store from URL
}, []);

useEffect(() => {
  // Update URL when store changes
  const params = new URLSearchParams();
  params.set('view', activeView);
  params.set('tab', activeTab);
  // ... update other params
  router.replace(`?${params.toString()}`, { scroll: false });
}, [activeView, activeTab, filters]);
```

---

## Data Flow & API Integration

### React Query Hooks

```typescript
// Reuse existing hooks, add new ones as needed

// Existing (from ListingsTable)
const { data: schema } = useQuery({
  queryKey: ['listings', 'schema'],
  queryFn: () => apiFetch('/v1/listings/schema')
});

const { data: listings } = useQuery({
  queryKey: ['listings', 'records'],
  queryFn: () => apiFetch('/v1/listings'),
  enabled: !!schema
});

// NEW: Filtered listings computed client-side
const filteredListings = useMemo(() => {
  if (!listings) return [];
  return listings.filter(listing => {
    // Apply filters.searchQuery
    if (filters.searchQuery) {
      const term = filters.searchQuery.toLowerCase();
      if (!listing.title?.toLowerCase().includes(term) &&
          !listing.cpu?.name?.toLowerCase().includes(term)) {
        return false;
      }
    }
    // Apply filters.formFactor
    if (filters.formFactor !== 'all' && listing.form_factor !== filters.formFactor) {
      return false;
    }
    // Apply filters.manufacturer
    if (filters.manufacturer !== 'all' && listing.manufacturer !== filters.manufacturer) {
      return false;
    }
    // Apply filters.priceRange
    if (listing.price_usd > filters.priceRange) {
      return false;
    }
    return true;
  });
}, [listings, filters]);

// NEW: Sorted listings (default: adj $/MT ascending)
const sortedListings = useMemo(() => {
  return [...filteredListings].sort((a, b) => {
    const aMetric = a.dollar_per_cpu_mark_multi_adjusted ?? Infinity;
    const bMetric = b.dollar_per_cpu_mark_multi_adjusted ?? Infinity;
    return aMetric - bMetric;
  });
}, [filteredListings]);
```

### Performance Optimization Strategy

**For <1000 listings:** Client-side filtering (current approach)
**For 1000+ listings:** Implement server-side filtering

```typescript
// Future server-side filtering (Phase 2 enhancement)
const { data: listings } = useQuery({
  queryKey: ['listings', 'records', filters],
  queryFn: () => apiFetch('/v1/listings', {
    params: {
      q: filters.searchQuery,
      form_factor: filters.formFactor,
      manufacturer: filters.manufacturer,
      max_price: filters.priceRange,
      sort: 'dollar_per_cpu_mark_multi_adjusted:asc'
    }
  }),
  enabled: !!schema && listingCount > 1000
});
```

---

## Phase-by-Phase Implementation

### Phase 1: Foundation & Tab Navigation (Days 1-2)

#### Tasks

**1.1: Zustand Store Setup**
- [ ] Create `apps/web/stores/catalog-store.ts`
- [ ] Implement `CatalogState` interface with all fields
- [ ] Add persist middleware for localStorage sync
- [ ] Create custom hooks: `useCatalogStore()`, `useFilters()`, `useCompare()`
- [ ] Write unit tests for store actions

**1.2: URL State Synchronization**
- [ ] Create `useUrlSync()` hook
- [ ] Parse URL params on mount → hydrate store
- [ ] Update URL on store changes (debounced)
- [ ] Handle browser back/forward navigation
- [ ] Test: URL updates reflect in store, vice versa

**1.3: Tab Scaffold**
- [ ] Modify `apps/web/app/listings/page.tsx`
- [ ] Add `Tabs` wrapper with `TabsList` and `TabsContent`
- [ ] Tabs: "Catalog" (default), "Data"
- [ ] Data tab renders existing `<ListingsTable />`
- [ ] Catalog tab renders placeholder "Coming soon"
- [ ] Wire `activeTab` to Zustand store
- [ ] Test: Tab switching preserves data, no refetch

**1.4: Shared Filters Component**
- [ ] Create `apps/web/app/listings/_components/listings-filters.tsx`
- [ ] Sticky filter bar layout (Tailwind `sticky top-0`)
- [ ] Text search input with debounce (200ms)
- [ ] Form Factor dropdown (`Select` component)
- [ ] Manufacturer dropdown (`Select` component)
- [ ] Price range slider (`Slider` component)
- [ ] Clear filters button
- [ ] Wire to Zustand store filters
- [ ] Test: Filters update store, URL updates

**Quality Gates:**
- [ ] URL params correctly sync with store state
- [ ] Tab navigation works without data refetch
- [ ] Filters update in real-time with debounce
- [ ] localStorage persists view preference
- [ ] No console errors or warnings

---

### Phase 2: Grid View Implementation (Days 3-5)

#### Tasks

**2.1: Grid Layout & Card Component**
- [ ] Create `apps/web/app/listings/_components/grid-view/index.tsx`
- [ ] Responsive grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
- [ ] Create `listing-card.tsx` component
- [ ] Card structure:
  - Header: Title (truncated), Open button (ArrowUpRight icon)
  - Badges row: CPU name, CPU scores (ST/MT), Device type, Tags (max 2)
  - Price section: Price USD (large), Adjusted USD (with color accent)
  - Performance badges component (see below)
  - Metadata row: RAM, Storage, Condition (small text)
  - Footer: Vendor badge, Quick Edit button (hover visible)
- [ ] Memoize card with `React.memo`
- [ ] Test: Renders 200 cards <500ms

**2.2: Performance Badges Component**
- [ ] Create `performance-badges.tsx`
- [ ] Display 4 badges: $/ST (raw), $/MT (raw), adj $/ST, adj $/MT
- [ ] Format: `$0.059` (3 decimals)
- [ ] Color accent for adjusted values: emerald if adjusted < raw, neutral otherwise
- [ ] Use `Badge` component with `variant="secondary"` for raw, custom class for adjusted
- [ ] Tooltip on hover with explanation
- [ ] Test: Color logic correct, tooltips show

**2.3: Color Accent Logic**
- [ ] Create utility function `getValuationAccent(adjusted: number, list: number)`
- [ ] Returns: `'good'` (emerald), `'warn'` (amber), `'neutral'`
- [ ] Apply to adjusted price display
- [ ] Apply to adjusted performance badges
- [ ] Test: Accent colors match design spec

**2.4: Quick Edit Dialog**
- [ ] Create `apps/web/components/listings/quick-edit-dialog.tsx`
- [ ] Dialog with form fields: Title, Price, Condition, Status, Tags
- [ ] Use existing `EditableCell` logic for field rendering
- [ ] Optimistic update on save
- [ ] Error handling with toast notifications
- [ ] Wire to Zustand `quickEditDialogOpen` state
- [ ] Test: Save persists, errors rollback

**2.5: Details Dialog Integration**
- [ ] Create `apps/web/components/listings/listing-details-dialog.tsx`
- [ ] Dialog content:
  - Header: Title, Device type badge, Open link button
  - KPI metrics grid (4 tiles): Price, Adjusted, $/ST, $/MT
  - Performance badges component (reuse from 2.2)
  - Specs grid: CPU, Scores, RAM, Storage, Condition, Vendor, Ports
  - Footer: "Expand full page" button → navigate to `/listings/{id}`
- [ ] Wire to Zustand `detailsDialogOpen` state
- [ ] Test: Opens from card click, navigates to full page

**2.6: Grid View Integration**
- [ ] Wire `grid-view/index.tsx` to filtered listings data
- [ ] Handle empty state (no listings match filters)
- [ ] Handle loading state (skeleton cards)
- [ ] Add "Add listing" CTA in empty state
- [ ] Test: Grid updates when filters change

**Quality Gates:**
- [ ] Grid renders 200 cards in <500ms
- [ ] Card hover states work smoothly
- [ ] Quick Edit saves successfully
- [ ] Details Dialog shows correct data
- [ ] Color accents match design spec
- [ ] Responsive on mobile (1 column), tablet (2 cols), desktop (3-4 cols)

---

### Phase 3: Dense List View Implementation (Days 6-8)

#### Tasks

**3.1: Dense Table Component**
- [ ] Create `apps/web/app/listings/_components/dense-list-view/index.tsx`
- [ ] Create `dense-table.tsx` using shadcn/ui `Table` component
- [ ] Columns: Title, CPU, Price, Adjusted, $/ST, $/MT, Actions
- [ ] Title cell: Bold title, small device type badge, RAM/storage below
- [ ] CPU cell: Name (main), Scores below (small text)
- [ ] Price cells: Format currency, adjusted with color accent
- [ ] Performance cells: 3 decimal format
- [ ] Actions cell: Details button, Quick Edit icon, More icon (hover visible)
- [ ] Test: Table renders with correct data

**3.2: Hover Action Clusters**
- [ ] Row hover state with `group` class
- [ ] Actions cell: `opacity-70 group-hover:opacity-100` transition
- [ ] Details button opens dialog
- [ ] Quick Edit icon opens dialog
- [ ] More icon opens dropdown menu (future: archive, duplicate, etc.)
- [ ] Test: Hover interactions smooth

**3.3: Keyboard Navigation**
- [ ] Create `useKeyboardNav()` hook
- [ ] Arrow keys: Navigate rows (update focus)
- [ ] Enter: Open details dialog for focused row
- [ ] Tab: Cycle through action buttons
- [ ] Escape: Clear focus
- [ ] Test: Full keyboard navigation works

**3.4: Bulk Selection Integration**
- [ ] Add checkbox column (first column)
- [ ] Header checkbox: Select all visible rows
- [ ] Row checkbox: Select individual row
- [ ] Shift+Click: Range selection
- [ ] Wire to existing `rowSelection` state (reuse from ListingsTable)
- [ ] Show bulk edit panel when selections active (reuse existing component)
- [ ] Test: Bulk edit applies to selected rows

**3.5: Virtual Scrolling (Performance)**
- [ ] Install `@tanstack/react-virtual`
- [ ] Implement virtual scrolling for >100 rows
- [ ] Configure overscan: 5 items
- [ ] Test: Smooth 60fps scroll with 1000+ rows

**Quality Gates:**
- [ ] Table scrolls smoothly with 1000+ rows
- [ ] Keyboard navigation fully functional
- [ ] Bulk selection works with shift+click
- [ ] Hover states performant
- [ ] Consistent styling with existing data-grid

---

### Phase 4: Master/Detail View Implementation (Days 9-12)

#### Tasks

**4.1: Split Layout Structure**
- [ ] Create `apps/web/app/listings/_components/master-detail-view/index.tsx`
- [ ] Layout: `grid grid-cols-1 lg:grid-cols-10 gap-4`
- [ ] Left panel: `lg:col-span-4`
- [ ] Right panel: `lg:col-span-6`
- [ ] Responsive: Stack vertically on mobile, split on desktop
- [ ] Test: Layout adapts to viewport

**4.2: Master List Component**
- [ ] Create `master-list.tsx`
- [ ] Scrollable area with `ScrollArea` component (height: 70vh)
- [ ] Each item:
  - Button element (full width, left-aligned)
  - Title (bold), Adjusted price (right-aligned)
  - CPU name + scores (small text below)
  - Compare checkbox at bottom
  - Hover state, selected state (border-primary bg-muted)
- [ ] Click item: Update `selectedListingId` in store
- [ ] Click checkbox: Toggle `compareSelections` in store
- [ ] Test: Selection updates detail panel

**4.3: Detail Panel Component**
- [ ] Create `detail-panel.tsx`
- [ ] Card layout with header (title, device type badge, Open button)
- [ ] KPI metrics grid: 4 tiles (Price, Adjusted, $/ST, $/MT)
- [ ] Create `kpi-metric.tsx` component:
  - Label (small muted text)
  - Value (medium bold text)
  - Optional accent border/background (good/warn)
- [ ] Performance badges (reuse from Grid view)
- [ ] Specs grid: Create `key-value.tsx` component
  - Key (small muted text)
  - Value (medium bold text)
- [ ] Specs: CPU, Scores, RAM, Storage, Condition, Vendor, Ports
- [ ] Test: Updates when selection changes

**4.4: Compare Drawer Component**
- [ ] Create `compare-drawer.tsx`
- [ ] Use shadcn/ui `Sheet` component (side="bottom")
- [ ] Trigger button: "Compare (N)" badge with compare count
- [ ] Sheet height: 60vh
- [ ] Grid layout: 1-3 cols responsive
- [ ] Each card (mini version):
  - Title, Adjusted price, $/MT
  - CPU name, Scores
  - Performance badges
  - Remove button (X icon)
- [ ] Max 6 items (show scroll if more)
- [ ] Clear all button in header
- [ ] Test: Add/remove from compare updates drawer

**4.5: Keyboard Shortcuts**
- [ ] j/k keys: Navigate master list (focus + scroll)
- [ ] c key: Toggle compare on focused item
- [ ] Enter: Open details dialog
- [ ] Escape: Close drawer
- [ ] Test: All shortcuts work

**Quality Gates:**
- [ ] Split layout responsive
- [ ] Detail panel updates instantly on selection
- [ ] Compare drawer holds up to 6 items
- [ ] Keyboard shortcuts functional
- [ ] Smooth scrolling in master list

---

### Phase 5: Integration & Polish (Days 13-15)

#### Tasks

**5.1: View State Persistence**
- [ ] Extend Zustand persist middleware
- [ ] Persist: `activeView`, `activeTab`, `filters`
- [ ] Don't persist: `selectedListingId`, `compareSelections`, dialog states
- [ ] Test: Refresh page preserves view/filters

**5.2: Error Boundaries**
- [ ] Create `ErrorBoundary` component for each view
- [ ] Fallback UI with retry button
- [ ] Log errors to console (future: error tracking service)
- [ ] Test: Component errors don't crash app

**5.3: Loading Skeletons**
- [ ] Create skeleton components:
  - `ListingCardSkeleton` (for grid view)
  - `DenseTableSkeleton` (for list view)
  - `MasterDetailSkeleton` (for split view)
- [ ] Show during initial load
- [ ] Use Tailwind `animate-pulse`
- [ ] Test: Skeletons match layout

**5.4: Empty States**
- [ ] Create `EmptyState` component
- [ ] Variations:
  - No listings at all: "Get started by adding your first listing"
  - No results from filters: "No listings match your filters. Try adjusting."
- [ ] Include relevant CTA button
- [ ] Icon + heading + description layout
- [ ] Test: Shows correct message for each scenario

**5.5: Mobile Responsive Testing**
- [ ] Test on 375px viewport (iPhone SE)
- [ ] Test on 768px viewport (iPad)
- [ ] Test on 1024px+ (Desktop)
- [ ] Adjustments:
  - Grid: 1 col mobile, 2 cols tablet, 3-4 cols desktop
  - List: Horizontal scroll on mobile (or simplified columns)
  - Master-Detail: Stack vertically on mobile, split on tablet+
- [ ] Test: All interactions work on touch

**5.6: Accessibility Audit**
- [ ] Run Axe DevTools on each view
- [ ] Fix all violations
- [ ] Manual keyboard testing checklist:
  - [ ] Tab through all interactive elements
  - [ ] Focus indicators visible
  - [ ] Dialogs trap focus
  - [ ] Escape closes dialogs
  - [ ] Enter activates buttons
- [ ] Screen reader testing (VoiceOver/NVDA):
  - [ ] ARIA labels present
  - [ ] Dynamic content announced
  - [ ] Color not sole indicator
- [ ] Test: Lighthouse Accessibility score 95+

**Quality Gates:**
- [ ] State persists correctly across sessions
- [ ] Error boundaries catch failures gracefully
- [ ] Loading states smooth and accurate
- [ ] Empty states helpful
- [ ] Mobile layout fully functional
- [ ] Zero accessibility violations

---

### Phase 6: Testing & Documentation (Days 16-18)

#### Tasks

**6.1: Unit Tests**
- [ ] Test Zustand store actions (`catalog-store.test.ts`)
- [ ] Test filter logic (`use-listing-filters.test.ts`)
- [ ] Test compare logic (`use-compare-selections.test.ts`)
- [ ] Test utility functions (formatting, color accents)
- [ ] Coverage: 80%+ for new code
- [ ] Tool: Vitest
- [ ] Test: `pnpm test`

**6.2: Integration Tests**
- [ ] Test data flow: API fetch → filter → render
- [ ] Test state synchronization: Store → URL → LocalStorage
- [ ] Test dialog interactions: Open → Edit → Save
- [ ] Tool: React Testing Library
- [ ] Test: `pnpm test:integration`

**6.3: E2E Tests (Playwright)**
- [ ] Test: Tab navigation preserves state
- [ ] Test: Filter listings in each view
- [ ] Test: Inline edit saves successfully
- [ ] Test: Compare drawer workflow (add, remove, clear)
- [ ] Test: Keyboard navigation in Master-Detail
- [ ] Test: Details dialog → Expand full page
- [ ] Tool: Playwright
- [ ] Test: `pnpm test:e2e`

**6.4: Performance Benchmarks**
- [ ] Measure: Grid view initial render (target: <500ms for 200 items)
- [ ] Measure: List view scroll FPS (target: 60fps)
- [ ] Measure: Filter debounce responsiveness (target: <200ms)
- [ ] Measure: Bundle size (target: <100KB gzipped for catalog code)
- [ ] Tool: Chrome DevTools Performance tab
- [ ] Document results in `PERFORMANCE.md`

**6.5: Component Stories (Storybook)**
- [ ] Story: `ListingCard` with variants (good/warn/neutral accents)
- [ ] Story: `PerformanceBadges` with sample data
- [ ] Story: `KpiMetric` with accents
- [ ] Story: `ListingsFilters` interactive
- [ ] Story: `CompareDrawer` with 1, 3, 6 items
- [ ] Tool: Storybook
- [ ] Test: `pnpm storybook`

**6.6: User Documentation**
- [ ] Create `docs/user-guide/catalog-views.md`
- [ ] Sections:
  - Overview of three views
  - When to use each view
  - Filter and search tips
  - Keyboard shortcuts reference
  - Comparison workflow
- [ ] Include screenshots
- [ ] Link from in-app help icon

**Quality Gates:**
- [ ] 80%+ test coverage for new code
- [ ] All E2E tests passing
- [ ] Performance budgets met
- [ ] Storybook stories complete
- [ ] User documentation reviewed

---

## Quality Assurance Checklist

### Functional Testing
- [ ] All three views render correctly
- [ ] Filters work consistently across views
- [ ] Tab navigation preserves state
- [ ] Inline editing saves successfully
- [ ] Details dialog shows correct data
- [ ] Quick edit dialog saves/cancels
- [ ] Compare drawer adds/removes items
- [ ] Keyboard shortcuts functional
- [ ] External links open in new tab
- [ ] Bulk edit applies to selections

### Performance Testing
- [ ] Grid view: 200 items render <500ms
- [ ] List view: Scroll 60fps with 1000+ items
- [ ] Filter updates: <200ms debounce
- [ ] No memory leaks on view switching
- [ ] Bundle size <100KB gzipped

### Accessibility Testing
- [ ] Keyboard navigation: Full coverage
- [ ] Screen reader: Announces dynamic content
- [ ] Focus indicators: Visible on all elements
- [ ] Color contrast: 4.5:1 minimum
- [ ] ARIA labels: Present on icon buttons
- [ ] Axe DevTools: 0 violations
- [ ] Lighthouse: Accessibility 95+

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Responsive Testing
- [ ] Mobile (375px): All features functional
- [ ] Tablet (768px): Layout adapts
- [ ] Desktop (1024px+): Full features
- [ ] Touch gestures work on mobile

---

## Deployment Strategy

### Rollout Plan

**Week 1-2: Internal Testing**
- Deploy to staging environment
- Internal QA testing
- Fix critical bugs

**Week 3: Beta Release**
- Feature flag: `ENABLE_CATALOG_VIEWS` (default: false)
- Enable for internal users + beta testers
- Collect feedback via in-app survey
- Monitor analytics (view usage, errors)

**Week 4: Gradual Rollout**
- Enable for 10% of users
- Monitor performance metrics
- Enable for 50% of users
- Full rollout if no issues

**Rollback Plan:**
- Feature flag allows instant disable
- Database: No migrations required (read-only views)
- Fallback: Existing table view always available

---

## Success Metrics & Monitoring

### Key Metrics to Track

**Adoption Metrics:**
- % of users trying catalog views
- % of users preferring catalog vs. table
- View distribution: Grid vs. List vs. Master-Detail

**Performance Metrics:**
- Grid view render time (p50, p95)
- List view scroll FPS
- Filter update latency
- Bundle load time

**Engagement Metrics:**
- Time spent in catalog views
- Number of compare drawer uses
- Quick edit usage rate
- Details dialog open rate

**Quality Metrics:**
- Error rate per view
- Inline edit success/failure rate
- Browser compatibility issues

### Monitoring Setup
- [ ] Add analytics tracking for view switches
- [ ] Add performance monitoring (Web Vitals)
- [ ] Set up error tracking (Sentry/equivalent)
- [ ] Create Grafana dashboard for key metrics

---

## Risk Mitigation

### Technical Risks

**Risk: Performance degradation with large datasets**
- Mitigation: Virtual scrolling, client/server filtering threshold
- Monitoring: Track render times, scroll FPS

**Risk: State management complexity**
- Mitigation: Simple Zustand store, comprehensive tests
- Monitoring: Error tracking for state-related bugs

**Risk: Accessibility regressions**
- Mitigation: Automated a11y checks in CI, manual testing
- Monitoring: Lighthouse scores in CI pipeline

**Risk: Browser compatibility issues**
- Mitigation: Cross-browser testing before rollout
- Monitoring: Track browser-specific errors

---

## Dependencies & Blockers

### External Dependencies
- shadcn/ui components (already in use)
- lucide-react icons (already in use)
- @tanstack/react-query (already in use)
- @tanstack/react-virtual (NEW - install in Phase 3)
- zustand (NEW - install in Phase 1)

### Internal Dependencies
- Existing API endpoints (no changes required)
- Existing ListingsTable component (reference for patterns)
- Existing valuation breakdown modal (reuse)

### Potential Blockers
- API performance with large datasets → Solution: Implement server-side filtering
- Design approval delays → Solution: Use example implementation as reference
- Resource availability → Solution: Phase-based rollout allows flexibility

---

## Post-Launch Enhancements

### Phase 2 Features (Future)
- [ ] Save filter presets ("My SFF deals", "Creator OLED")
- [ ] Smart sort options (multiple sort keys)
- [ ] Export compare results to CSV
- [ ] Deal alerts (notifications for filter matches)
- [ ] Bulk actions from compare drawer
- [ ] Drag-and-drop to reorder compare items
- [ ] Image gallery in detail view
- [ ] Price history charts

### Performance Optimizations (Future)
- [ ] Server-side pagination with cursor-based navigation
- [ ] GraphQL API for flexible data fetching
- [ ] Service worker caching for offline support
- [ ] Image lazy loading with blurhash placeholders

---

## Appendix

### Technical Debt to Address
- None identified (greenfield implementation)

### Testing Strategy Summary
- Unit tests: Zustand store, hooks, utilities
- Integration tests: Data flow, state sync
- E2E tests: Critical user paths
- Performance tests: Render times, scroll FPS
- Accessibility tests: Automated + manual

### Code Review Checklist
- [ ] Component memoization applied correctly
- [ ] No prop drilling (use context/store)
- [ ] Accessibility attributes present
- [ ] Error boundaries implemented
- [ ] Loading states handled
- [ ] TypeScript types strict (no `any`)
- [ ] Code follows existing patterns
- [ ] Tests cover edge cases

### Related ADRs (to be created)
- ADR: Choose Zustand over Context API for catalog state
- ADR: Client-side vs. server-side filtering strategy
- ADR: Virtual scrolling library selection

---

## Sign-Off

**Lead Architect:** Claude Code
**Date:** 2025-10-06
**Status:** Ready for Implementation

This implementation plan is approved and ready for execution. All technical specifications, dependencies, and quality gates are defined. Teams may proceed with Phase 1 development.
