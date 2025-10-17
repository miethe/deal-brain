# PRD: Listings Catalog View Revamp

**Status:** In Planning
**Version:** 1.0
**Last Updated:** 2025-10-06
**Lead Architect:** Claude Code

---

## Executive Summary

Transform the Deal Brain listings page from a pure data-grid interface into a modern, multi-view catalog experience optimized for deal discovery, bulk operations, and detailed comparison. The new catalog views will sit alongside the existing table view, accessible via tabs, maintaining backward compatibility while introducing three distinct interaction patterns tailored to different user workflows.

---

## Problem Statement

### Current State
The existing `/listings` page presents all data in a single comprehensive table view:
- **Strengths:** Complete data visibility, inline editing, powerful filtering, bulk operations
- **Limitations:**
  - High cognitive load when scanning hundreds of listings
  - Performance metrics buried in columns requiring horizontal scrolling
  - Limited visual hierarchy makes value discovery difficult
  - No side-by-side comparison capability
  - Dense layout unsuitable for quick triage workflows

### User Pain Points
1. **Deal hunters** struggle to quickly identify best value opportunities across large datasets
2. **Operations users** need faster bulk editing without losing spreadsheet-like efficiency
3. **Comparison shoppers** lack tooling to evaluate alternatives without losing context
4. **Mobile users** face poor UX due to table-centric design

---

## Goals & Success Metrics

### Primary Goals
1. **Accelerate deal discovery** with visual hierarchy and performance metric prominence
2. **Maintain operational efficiency** while reducing cognitive load
3. **Enable contextual comparison** without page navigation
4. **Preserve existing functionality** including inline editing, filtering, and bulk updates

### Success Metrics
- Time to identify top 5 deals reduced by 40% (measured via user testing)
- User satisfaction score increase from current baseline
- Zero regression in bulk operation completion time
- 90%+ feature parity with existing table view

### Non-Goals
- Migration away from existing table view (it remains available)
- Real-time collaboration features (future enhancement)
- Mobile-native app development
- AI-powered recommendations

---

## User Stories & Acceptance Criteria

### Epic 1: Card Grid View (Discovery Mode)

**User Story 1.1: Visual Deal Scanning**
```
As a deal hunter
I want to see listings as cards with prominent pricing and performance metrics
So that I can quickly identify value opportunities without deep analysis
```

**Acceptance Criteria:**
- [ ] Card grid displays 2-4 columns responsive to viewport width
- [ ] Each card shows: Title, CPU name, Device type, Manufacturer, Price (sticker), Adjusted Price (with color accent)
- [ ] Performance badges visible: $/ST, $/MT, adj $/ST, adj $/MT
- [ ] Color semantics: adjusted < price = emerald accent, adjusted > price = amber accent
- [ ] Cards show up to 2 tags maximum
- [ ] Hover state reveals quick actions: Quick Edit, Open (external link)
- [ ] Click card to open Details Dialog

**User Story 1.2: Inline Quick Editing**
```
As an operations user
I want to edit key fields directly from the card view
So that I can update listings without switching to table mode
```

**Acceptance Criteria:**
- [ ] Quick Edit button opens focused inline editor
- [ ] Editor includes: Title, Price, Condition, Status, Tags
- [ ] Changes save on blur with optimistic UI updates
- [ ] Error states display inline with rollback on failure
- [ ] Editor respects field validation from schema

---

### Epic 2: Dense List View (Operations Mode)

**User Story 2.1: High-Density Operations**
```
As an operations manager
I want a compact list view with maximum information density
So that I can process large batches efficiently with keyboard shortcuts
```

**Acceptance Criteria:**
- [ ] Compact table format with columns: Title, CPU, Price, Adjusted, $/ST, $/MT, Actions
- [ ] Row hover reveals action cluster: Details, Quick Edit, More
- [ ] Keyboard navigation: Arrow keys for row selection, Enter to open details
- [ ] Bulk selection via checkboxes with shift+click range selection
- [ ] Consistent styling with existing data-grid patterns

**User Story 2.2: Spreadsheet-Like Efficiency**
```
As a power user
I want keyboard shortcuts and inline editing
So that I can update listings as fast as in a spreadsheet
```

**Acceptance Criteria:**
- [ ] Tab key navigates editable cells
- [ ] Escape cancels inline edits
- [ ] Copy/paste support for text fields
- [ ] Bulk edit panel appears when rows selected
- [ ] Undo/redo for recent changes (nice-to-have)

---

### Epic 3: Master/Detail Split View (Comparison Mode)

**User Story 3.1: Contextual Comparison**
```
As a buyer evaluating options
I want to compare listings side-by-side without losing my place
So that I can make informed decisions efficiently
```

**Acceptance Criteria:**
- [ ] Left panel: Scrollable master list (title, CPU, adjusted price, compare checkbox)
- [ ] Right panel: Detailed view of selected listing with KPI tiles
- [ ] KPI tiles display: Price, Adjusted, $/ST, $/MT with color accents
- [ ] Detail view includes: CPU info, RAM, Storage, Vendor, Condition, Ports
- [ ] Selection state persists during scrolling
- [ ] Keyboard shortcuts: j/k for navigation, c to toggle compare

**User Story 3.2: Multi-Listing Compare Drawer**
```
As a comparison shopper
I want to stack multiple listings side-by-side
So that I can evaluate relative value across alternatives
```

**Acceptance Criteria:**
- [ ] Compare checkboxes in master list accumulate selections
- [ ] Bottom sheet drawer opens with "Compare (N)" button
- [ ] Drawer displays 1-6 mini-cards in horizontal grid
- [ ] Each card shows: Title, Adjusted Price, $/MT, CPU name, Scores, Performance badges
- [ ] Remove from comparison via card close button
- [ ] Export comparison to CSV (nice-to-have)

---

### Epic 4: Shared UX Components

**User Story 4.1: Consistent Filtering**
```
As any user
I want the same powerful filters across all views
So that I can switch views without losing my context
```

**Acceptance Criteria:**
- [ ] Sticky filter bar at top with: Text search, Form Factor dropdown, Manufacturer dropdown, Price slider
- [ ] Filters apply to all views consistently
- [ ] Filter state persists across view switches
- [ ] Quick clear all filters button
- [ ] Filter pills show active selections

**User Story 4.2: Details Dialog Everywhere**
```
As any user
I want consistent access to full listing details
So that I can drill down from any view
```

**Acceptance Criteria:**
- [ ] Click any card/row opens Details Dialog
- [ ] Dialog shows: KPI metrics, Performance badges, Full specs, Thumbnail image, External link
- [ ] "Expand full page" button navigates to `/listings/[id]`
- [ ] Dialog includes Quick Edit button
- [ ] Keyboard shortcut to close (Escape)

**User Story 4.3: Tab Navigation**
```
As any user
I want to switch between Catalog and Data table views
So that I can choose the interface that fits my task
```

**Acceptance Criteria:**
- [ ] Persistent tab switcher: "Catalog" (default), "Data"
- [ ] Tab state persists in URL params (e.g., `?view=catalog`)
- [ ] Data tab loads existing table component
- [ ] View preference saved to localStorage
- [ ] No data refetch on view switch

---

## Technical Requirements

### Frontend Architecture

**Component Hierarchy:**
```
/app/(dealbrain)/listings/page.tsx
├── ListingsTabs (Catalog | Data)
│   ├── CatalogView
│   │   ├── ListingsFilters (shared)
│   │   ├── ViewSwitcher (Grid | List | Master-Detail)
│   │   ├── GridView
│   │   │   └── ListingCard[]
│   │   ├── DenseListView
│   │   │   └── DenseTable
│   │   └── MasterDetailView
│   │       ├── MasterList
│   │       ├── DetailPanel
│   │       └── CompareDrawer
│   └── DataView (existing ListingsTable)
└── Shared Dialogs
    ├── ListingDetailsDialog
    ├── QuickEditDialog
    └── ValuationBreakdownModal (existing)
```

**State Management:**
- **Server State:** React Query for listings data, schema, CPU/GPU options
- **Client State:** Zustand store for:
  - Active view mode (grid | list | md)
  - Active tab (catalog | data)
  - Filter state (search query, form factor, manufacturer, price range)
  - Compare selections (listing IDs array)
  - Selected listing ID for detail view
  - Dialog open states

**Data Fetching Strategy:**
- Reuse existing `/v1/listings` endpoint
- Memoized filtering on client side for <1000 listings
- For larger datasets: Implement server-side filtering via query params
- Prefetch CPU/GPU catalogs on mount
- Optimistic updates for inline edits

**Performance Optimizations:**
- Virtual scrolling for lists >100 items (via `react-window` or `@tanstack/react-virtual`)
- Memoize card components with React.memo
- Debounce search input (200ms)
- Lazy load detail panel images
- Code-split catalog views (dynamic imports)

---

### API Integration

**Existing Endpoints (No Changes Required):**
- `GET /v1/listings` - Fetch all listings
- `GET /v1/listings/schema` - Fetch field schema
- `PATCH /v1/listings/{id}` - Update single listing
- `POST /v1/listings/bulk-update` - Bulk update listings
- `GET /v1/listings/{id}/valuation-breakdown` - Breakdown modal
- `GET /v1/catalog/cpus` - CPU options
- `GET /v1/catalog/gpus` - GPU options

**Optional Future Enhancements:**
- `GET /v1/listings?filters={...}&sort={...}&limit={...}` - Server-side filtering
- `POST /v1/listings/compare` - Compare endpoint with optimization hints

---

### Data Model Requirements

**Performance Metrics (Already in Schema):**
- `dollar_per_cpu_mark_single` (raw $/ST)
- `dollar_per_cpu_mark_single_adjusted` (adjusted $/ST)
- `dollar_per_cpu_mark_multi` (raw $/MT)
- `dollar_per_cpu_mark_multi_adjusted` (adjusted $/MT)

**Display Formatting:**
- Currency: Whole dollars in cards/lists (`$599`), cents in detail view (`$599.99`)
- CPU Marks: Thousands-separated, no decimals (`ST 10,000 / MT 48,500`)
- Performance ratios: 3 decimal places (`$0.059 per point`)

**Color Thresholds (Use Existing Settings):**
- Adjusted < Price = Good deal (emerald-500)
- Adjusted > Price = Premium (amber-500)
- Neutral = muted-foreground

---

### Accessibility Requirements

**WCAG AA Compliance:**
- All interactive elements keyboard accessible
- Focus traps in dialogs/sheets
- ARIA labels for icon-only buttons
- Color never sole information carrier (use text labels + icons)
- Minimum contrast ratio 4.5:1 for text
- Screen reader announcements for dynamic content
- Skip links for filter navigation

**Keyboard Shortcuts:**
- `/` - Focus search input
- `j/k` - Navigate master list (Master-Detail view)
- `c` - Toggle compare on selected item
- `Enter` - Open details dialog
- `Escape` - Close dialog/drawer
- `Tab` - Cycle through editable fields
- `Shift+Click` - Range select in lists

---

## Design Specifications

### Visual Design Principles
1. **Progressive Disclosure:** Show critical metrics upfront, details on demand
2. **Visual Hierarchy:** Size, color, spacing guide eye to value signals
3. **Consistent Semantics:** Emerald = good, Amber = caution, always with text labels
4. **Responsive Layout:** Mobile-first grid, tablet-optimized list, desktop master-detail

### Component Library (shadcn/ui)
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` - View switcher
- `Card`, `CardHeader`, `CardContent`, `CardTitle` - Grid cards
- `Badge` - CPU, performance metrics, tags, device type
- `Button` - Actions, quick edit, external links
- `Input` - Search, inline text editing
- `Select` - Dropdowns for filters, enum fields
- `Checkbox` - Compare selections, bulk select
- `Dialog`, `DialogContent` - Details modal
- `Sheet`, `SheetContent` - Compare drawer (bottom sheet)
- `Tooltip` - Contextual help for metrics
- `Slider` - Price range filter
- `Table` - Dense list view
- `ScrollArea` - Scrollable master list

### Icons (lucide-react)
- `Cpu` - CPU badge
- `Gauge` - Performance metrics
- `DollarSign` - Pricing indicators
- `ArrowUpRight` - External links
- `Filter` - Filter controls
- `Columns2` - Grid view icon
- `SquarePen` - Edit actions
- `Layers3` - Compare drawer
- `MoreHorizontal` - More actions menu

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Deliverables:**
- [ ] Zustand store setup for catalog state
- [ ] Tab navigation scaffold (Catalog | Data)
- [ ] Shared `ListingsFilters` component
- [ ] Base layout with sticky filters
- [ ] URL state synchronization

**Success Criteria:**
- Tabs switch without data refetch
- Filters update URL params
- State persists across page refresh

---

### Phase 2: Grid View (Week 2)
**Deliverables:**
- [ ] `ListingCard` component with responsive grid
- [ ] Performance badge components
- [ ] Color accent logic for adjusted pricing
- [ ] Quick Edit dialog
- [ ] Details dialog integration

**Success Criteria:**
- Cards render 100+ items <500ms
- Inline edit saves optimistically
- Color semantics match design spec
- Keyboard navigation works

---

### Phase 3: Dense List View (Week 3)
**Deliverables:**
- [ ] `DenseTable` component
- [ ] Hover action clusters
- [ ] Keyboard navigation hooks
- [ ] Bulk selection integration
- [ ] Row expand for details

**Success Criteria:**
- Table scrolls smoothly with 1000+ rows (virtualized)
- Keyboard shortcuts functional
- Bulk edit panel appears on selection
- Consistent with existing table styling

---

### Phase 4: Master/Detail View (Week 4)
**Deliverables:**
- [ ] Split layout with resizable panels
- [ ] Master list with scrollable area
- [ ] Detail panel with KPI tiles
- [ ] Compare drawer (bottom sheet)
- [ ] Multi-select compare logic

**Success Criteria:**
- Panel resize works smoothly
- Compare drawer holds 1-6 items
- Detail view updates on selection change
- j/k keyboard shortcuts work

---

### Phase 5: Integration & Polish (Week 5)
**Deliverables:**
- [ ] View state persistence (localStorage)
- [ ] Error boundaries for each view
- [ ] Loading skeletons
- [ ] Empty states with helpful CTAs
- [ ] Mobile responsive testing
- [ ] Accessibility audit

**Success Criteria:**
- All views pass WCAG AA automated checks
- Mobile layout usable on 375px viewport
- Error states recover gracefully
- Zero console warnings

---

### Phase 6: Testing & Documentation (Week 6)
**Deliverables:**
- [ ] Unit tests for state management
- [ ] Integration tests for data flow
- [ ] E2E tests for critical paths (Playwright)
- [ ] Component Storybook stories
- [ ] User documentation
- [ ] Performance benchmarks

**Success Criteria:**
- 80% test coverage for new components
- All user stories verified via E2E tests
- Performance budgets met (see below)
- Documentation approved by stakeholders

---

## Performance Budgets

**Rendering Performance:**
- Grid view initial render: <500ms for 200 items
- List view scroll: 60fps with virtual scrolling
- Filter debounce: 200ms
- Inline edit save: Optimistic UI + <1s server roundtrip

**Bundle Size:**
- Catalog view code split: <100KB gzipped
- Shared dependencies: No duplication with existing table

**Accessibility:**
- Lighthouse Accessibility score: 95+
- Axe DevTools: 0 violations
- Keyboard nav test: 100% navigable

---

## Risks & Mitigations

### Risk 1: Performance with Large Datasets
**Impact:** High
**Probability:** Medium
**Mitigation:**
- Implement virtual scrolling for lists >100 items
- Client-side filtering for <1000 items, server-side beyond
- Memoize expensive components
- Monitor real-world usage patterns

### Risk 2: Feature Parity Gaps
**Impact:** High
**Probability:** Low
**Mitigation:**
- Maintain existing table view as fallback
- Incremental rollout with feature flags
- User feedback collection via in-app prompts
- Clear documentation of differences

### Risk 3: Accessibility Regressions
**Impact:** Medium
**Probability:** Low
**Mitigation:**
- Automated a11y checks in CI pipeline
- Manual keyboard testing checklist
- Screen reader testing on macOS/Windows
- Community accessibility review

### Risk 4: State Management Complexity
**Impact:** Medium
**Probability:** Medium
**Mitigation:**
- Simple Zustand store with clear separation of concerns
- React Query handles server state
- Comprehensive state tests
- Documented state flow diagrams

---

## Open Questions

1. **Server-side filtering threshold:** At what listing count should we switch from client to server filtering?
   - **Recommendation:** Implement client-side for <1000, server-side for 1000+

2. **Compare drawer limit:** Maximum number of items in compare drawer?
   - **Recommendation:** 6 items max with scroll if more needed

3. **Default view:** Which view should be default on first visit?
   - **Recommendation:** Grid view for new users, persist last-used for returning users

4. **Mobile strategy:** Should we hide Master-Detail on mobile or adapt it?
   - **Recommendation:** Stack vertically on mobile, full split on tablet+

5. **Export functionality:** Should compare drawer export to CSV/JSON?
   - **Recommendation:** Phase 2 enhancement, not MVP

---

## Success Criteria Summary

**Launch Readiness Checklist:**
- [ ] All three views functional with feature parity
- [ ] Tab navigation preserves state
- [ ] Filters work consistently across views
- [ ] Inline editing saves successfully
- [ ] Details dialog accessible from all views
- [ ] Compare drawer functional in Master-Detail
- [ ] Accessibility audit passed
- [ ] Performance budgets met
- [ ] E2E tests cover critical paths
- [ ] User documentation complete
- [ ] Stakeholder sign-off received

---

## Appendix

### Related Documents
- [Design Overview](/mnt/containers/deal-brain/docs/project_plans/requests/listings-revamp/listings-ui-reskin.md)
- [Example Implementation](/mnt/containers/deal-brain/docs/project_plans/requests/listings-revamp/listings.tsx.example)
- [Existing Table Component](/mnt/containers/deal-brain/apps/web/components/listings/listings-table.tsx)

### Glossary
- **$/ST:** Dollars per single-thread CPU mark (lower = better value)
- **$/MT:** Dollars per multi-thread CPU mark (lower = better value)
- **Adjusted Price:** Price after RAM/storage/OS valuation rule deductions
- **KPI Tile:** Key performance indicator card in detail view
- **Master-Detail:** Split view pattern with list + detail panel

### Stakeholder Contacts
- **Product Owner:** TBD
- **Lead Architect:** Claude Code
- **UX Designer:** TBD
- **QA Lead:** TBD
