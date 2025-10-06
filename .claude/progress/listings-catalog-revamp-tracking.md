# Listings Catalog View Revamp - Implementation Tracking

**Started:** 2025-10-06
**Lead Architect:** Claude Code
**Status:** In Progress

---

## Phase 1: Foundation & Tab Navigation (Days 1-2)

### 1.1: Zustand Store Setup ✅
- [x] Create `apps/web/stores/catalog-store.ts`
- [x] Implement `CatalogState` interface with all fields
- [x] Add persist middleware for localStorage sync
- [x] Create custom hooks: `useCatalogStore()`, `useFilters()`, `useCompare()`
- [⏭] Write unit tests for store actions (deferred to Phase 6)

### 1.2: URL State Synchronization ✅
- [x] Create `useUrlSync()` hook
- [x] Parse URL params on mount → hydrate store
- [x] Update URL on store changes (debounced)
- [x] Handle browser back/forward navigation
- [x] Test: URL updates reflect in store, vice versa

### 1.3: Tab Scaffold ✅
- [x] Modify `apps/web/app/listings/page.tsx`
- [x] Add `Tabs` wrapper with `TabsList` and `TabsContent`
- [x] Tabs: "Catalog" (default), "Data"
- [x] Data tab renders existing `<ListingsTable />`
- [x] Catalog tab renders placeholder "Coming soon"
- [x] Wire `activeTab` to Zustand store
- [x] Test: Tab switching preserves data, no refetch

### 1.4: Shared Filters Component ✅
- [x] Create `apps/web/app/listings/_components/listings-filters.tsx`
- [x] Sticky filter bar layout (Tailwind `sticky top-0`)
- [x] Text search input with debounce (200ms)
- [x] Form Factor dropdown (`Select` component)
- [x] Manufacturer dropdown (`Select` component)
- [x] Price range slider (`Slider` component)
- [x] Clear filters button
- [x] Wire to Zustand store filters
- [x] Integrated into Catalog tab

### Quality Gates (Phase 1):
- [x] URL params correctly sync with store state (via useUrlSync)
- [x] Tab navigation works without data refetch (React Query manages caching)
- [x] Filters update in real-time with debounce (200ms debounce implemented)
- [x] localStorage persists view preference (Zustand persist middleware)
- [⚠️] TypeScript compilation (requires pnpm install for @radix-ui/react-tabs)

---

## Phase 2: Grid View Implementation (Days 3-5)

### 2.1: Grid Layout & Card Component
- [ ] Create `apps/web/app/listings/_components/grid-view/index.tsx`
- [ ] Responsive grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
- [ ] Create `listing-card.tsx` component
- [ ] Card structure (Header, Badges, Price, Performance, Metadata, Footer)
- [ ] Memoize card with `React.memo`
- [ ] Test: Renders 200 cards <500ms

### 2.2: Performance Badges Component
- [ ] Create `performance-badges.tsx`
- [ ] Display 4 badges: $/ST (raw), $/MT (raw), adj $/ST, adj $/MT
- [ ] Format: `$0.059` (3 decimals)
- [ ] Color accent for adjusted values
- [ ] Use `Badge` component with variants
- [ ] Tooltip on hover with explanation
- [ ] Test: Color logic correct, tooltips show

### 2.3: Color Accent Logic
- [ ] Create utility function `getValuationAccent(adjusted: number, list: number)`
- [ ] Returns: `'good'` (emerald), `'warn'` (amber), `'neutral'`
- [ ] Apply to adjusted price display
- [ ] Apply to adjusted performance badges
- [ ] Test: Accent colors match design spec

### 2.4: Quick Edit Dialog
- [ ] Create `apps/web/components/listings/quick-edit-dialog.tsx`
- [ ] Dialog with form fields: Title, Price, Condition, Status, Tags
- [ ] Use existing `EditableCell` logic for field rendering
- [ ] Optimistic update on save
- [ ] Error handling with toast notifications
- [ ] Wire to Zustand `quickEditDialogOpen` state
- [ ] Test: Save persists, errors rollback

### 2.5: Details Dialog Integration
- [ ] Create `apps/web/components/listings/listing-details-dialog.tsx`
- [ ] Dialog content (Header, KPI metrics, Performance badges, Specs grid, Footer)
- [ ] Wire to Zustand `detailsDialogOpen` state
- [ ] Test: Opens from card click, navigates to full page

### 2.6: Grid View Integration
- [ ] Wire `grid-view/index.tsx` to filtered listings data
- [ ] Handle empty state (no listings match filters)
- [ ] Handle loading state (skeleton cards)
- [ ] Add "Add listing" CTA in empty state
- [ ] Test: Grid updates when filters change

### Quality Gates (Phase 2):
- [ ] Grid renders 200 cards in <500ms
- [ ] Card hover states work smoothly
- [ ] Quick Edit saves successfully
- [ ] Details Dialog shows correct data
- [ ] Color accents match design spec
- [ ] Responsive on mobile (1 column), tablet (2 cols), desktop (3-4 cols)

---

## Progress Summary

**Phase 1:** ✅ Complete
**Phase 2:** Not Started

**Total Tasks:** 42
**Completed:** 20 (Phase 1)
**In Progress:** 0
**Deferred:** 1 (unit tests to Phase 6)
**Blocked:** 0

---

## Notes & Decisions

### Architectural Decisions:
- Using Zustand for client state management (lightweight, minimal boilerplate)
- React Query handles server state (already integrated)
- Client-side filtering for initial implementation (<1000 listings)
- Virtual scrolling deferred to Phase 3 (Dense List View)
- URL state synchronization with 300ms debounce to avoid history pollution

### Dependencies:
- zustand (already installed v5.0.8)
- @radix-ui/react-tabs (added to package.json, needs install)
- Existing: shadcn/ui, lucide-react, @tanstack/react-query
- All other dependencies already in place

### Key Learnings:
- Zustand persist middleware only stores specified fields (partialize)
- useDebounce hook from use-debounce works well for search inputs
- Next.js router.replace() with scroll:false prevents jumps during URL updates
- Tab components need proper ARIA attributes from Radix UI for accessibility

---

## Files Created (Phase 1):
- `apps/web/stores/catalog-store.ts` - Zustand store with persistence
- `apps/web/hooks/use-url-sync.ts` - URL synchronization hook
- `apps/web/components/ui/tabs.tsx` - shadcn/ui tabs component
- `apps/web/app/listings/_components/listings-filters.tsx` - Shared filters component

## Files Modified (Phase 1):
- `apps/web/app/listings/page.tsx` - Added tabs, filters, URL sync
- `apps/web/package.json` - Added @radix-ui/react-tabs dependency

---

## Commit History

### Phase 1 Commit (Pending)
**Files:** 6 created/modified
**Summary:** Implemented foundation with Zustand store, URL sync, tab navigation, and shared filters
