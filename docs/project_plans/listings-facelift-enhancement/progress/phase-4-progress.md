# Phase 4 Progress: Detail Page Foundation

**Status:** In Progress
**Plan:** docs/project_plans/listings-facelift-enhancement/listings-facelift-implementation-plan.md
**Started:** 2025-10-23
**Last Updated:** 2025-10-23
**Phase Duration:** Expected 5 days

---

## Objective

Create basic detail page structure with hero section, breadcrumbs, and tab navigation. Establish foundation for rich detail page with comprehensive listing information display.

---

## Task Breakdown

### Backend Tasks

#### TASK-401: Enhance /v1/listings/{id} endpoint with eager loading
**Status:** Not Started
**Owner:** python-backend-engineer
**Files:**
- `apps/api/dealbrain_api/api/listings.py`
- `apps/api/dealbrain_api/services/listings.py`

**Requirements:**
- Eager-load all relationships (CPU, GPU, RAM, Storage, Ports)
- Include full entity data for tooltips (cores, TDP, marks, etc.)
- Return 404 if listing not found
- Keep response time < 500ms (p95)

**Acceptance Criteria:**
- [ ] Endpoint returns CPU with full specs (cores, TDP, CPU Mark, Single-Thread Mark, iGPU Mark)
- [ ] Endpoint returns GPU with full specs (cores, TDP, VRAM, GPU Mark)
- [ ] Endpoint returns RAM specs (capacity, speed, type, condition)
- [ ] Endpoint returns Storage specs (capacity, type, form factor, interface)
- [ ] Endpoint returns Ports array with all connectivity info
- [ ] 404 response when listing ID not found
- [ ] No N+1 queries (use SQLAlchemy selectinload)
- [ ] Response time < 500ms for 100KB payload

**Database Schema Available:**
- `Listing` model with relationships to CPU, GPU, RAM, Storage, Ports
- `CPU` model with cores, TDP, cpu_mark, single_thread_mark, igpu_mark
- `GPU` model with cores, TDP, vram, gpu_mark
- `RAMSpec` model with capacity, speed, type, condition
- `StorageProfile` model with capacity, type, form_factor, interface
- `PortsProfile` model with ports array

---

### Frontend Tasks

#### TASK-402: Create detail page route
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/app/listings/[id]/page.tsx`

**Requirements:**
- Create Next.js dynamic route at `/listings/[id]`
- Implement as Server Component for optimal performance
- Fetch listing data using `apiFetch()` from server
- Handle 404 responses by throwing `notFound()`
- Use `generateMetadata()` for SEO (title, description, OG tags)
- Pass listing data to client components

**Acceptance Criteria:**
- [ ] Route renders at `/listings/[id]`
- [ ] Server-side data fetching working
- [ ] 404 properly handled and displayed
- [ ] Page metadata includes listing name and valuation
- [ ] No hydration mismatches
- [ ] TypeScript types properly defined

---

#### TASK-403: Create loading skeleton
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/app/listings/[id]/loading.tsx`

**Requirements:**
- Create Next.js loading skeleton component
- Display skeleton of hero section + tabs
- Use Skeleton UI component from shadcn/ui
- Match layout of actual detail page
- Smooth transition from skeleton to content

**Acceptance Criteria:**
- [ ] Loading skeleton displays while page data fetches
- [ ] Skeleton matches detail page layout
- [ ] Smooth CSS transition to content
- [ ] No jank or layout shift (CLS = 0)
- [ ] Displays for ~500-1000ms under normal conditions

---

#### TASK-404: Create 404 not-found page
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/app/listings/[id]/not-found.tsx`

**Requirements:**
- Create Next.js not-found page component
- Display helpful message with link back to listings
- Show "Listing not found" with listing ID (if available)
- Provide navigation options (Go back, Browse listings, Home)
- Match overall design system

**Acceptance Criteria:**
- [ ] Not-found page displays when listing ID doesn't exist
- [ ] Page shows listing ID that was not found
- [ ] Navigation links functional
- [ ] Design matches rest of application
- [ ] Accessible keyboard navigation

---

#### TASK-405: Create DetailPageLayout component
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/components/listings/detail-page-layout.tsx`

**Requirements:**
- Wrapper component for detail page structure
- Contains hero section and tab navigation
- Responsive padding/margins
- Scroll behavior management
- Dark mode support

**Component Structure:**
```tsx
export interface DetailPageLayoutProps {
  listing: ListingDetail;
  breadcrumbs?: BreadcrumbItem[];
  children?: React.ReactNode;
}

export function DetailPageLayout({ listing, breadcrumbs, children }: DetailPageLayoutProps) {
  // Layout structure:
  // 1. Breadcrumb navigation
  // 2. DetailPageHero component
  // 3. Tab navigation container
  // 4. Tab content (children)
}
```

**Acceptance Criteria:**
- [ ] Renders breadcrumbs at top
- [ ] Renders DetailPageHero below breadcrumbs
- [ ] Renders tab navigation and content
- [ ] Responsive on mobile/tablet/desktop
- [ ] Proper vertical spacing between sections
- [ ] Dark mode styling correct

---

#### TASK-406: Create breadcrumb navigation
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/components/listings/breadcrumb-nav.tsx`

**Requirements:**
- Display breadcrumb path: "Listings > [Product] > Details"
- Links functional (navigate back to listings)
- Current page non-clickable with different styling
- Use Breadcrumb component from shadcn/ui
- Mobile-responsive (collapse on small screens)

**Breadcrumb Path:**
```
Home > Listings > HP ProDesk 400 G8 Mini > Details
```

**Acceptance Criteria:**
- [ ] Breadcrumb displays correct path
- [ ] Links navigate correctly
- [ ] Current page is non-interactive
- [ ] Mobile responsive (shows abbreviated version on small screens)
- [ ] Keyboard navigable
- [ ] ARIA labels present

---

#### TASK-407: Create DetailPageHero component
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/components/listings/detail-page-hero.tsx`

**Requirements:**
- Display product image (left side)
- Display summary cards (right side)
- Responsive layout (stacked on mobile)
- Include ProductImage component
- Include SummaryCard components (price, performance, hardware, metadata)

**Hero Structure:**
```
┌─────────────────────────────────────────────────────────┐
│ ProductImage (left)    │ SummaryCards Grid (right)      │
│                        ├─ Price Card                    │
│                        ├─ Performance Card              │
│                        ├─ Hardware Card                 │
│                        └─ Metadata Card                 │
└─────────────────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- [ ] ProductImage displays on left
- [ ] Summary cards grid on right
- [ ] Responsive: stacked on mobile, side-by-side on desktop
- [ ] All cards display correct data
- [ ] Proper spacing and alignment
- [ ] Dark mode support

---

#### TASK-408: Create ProductImage component
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/components/listings/product-image.tsx`

**Requirements:**
- Display primary product image
- Fallback to manufacturer logo if image unavailable
- Fallback to generic PC icon if logo unavailable
- Use Next.js Image component for optimization
- Proper aspect ratio (square)
- Loading state and error handling

**Image Fallback Strategy:**
1. Primary: `listing.image_url` (from import/upload)
2. Fallback 1: Manufacturer logo (based on CPU/GPU manufacturer)
3. Fallback 2: Generic PC/Workstation icon
4. Error state: Gray background with icon

**Acceptance Criteria:**
- [ ] Displays product image when available
- [ ] Falls back to manufacturer logo
- [ ] Falls back to generic icon
- [ ] Next.js Image optimization working
- [ ] Proper aspect ratio maintained
- [ ] Loading state smooth
- [ ] Alt text descriptive

---

#### TASK-409: Create tab navigation component
**Status:** Not Started
**Owner:** ui-engineer
**Files:** `apps/web/components/listings/detail-page-tabs.tsx`

**Requirements:**
- Tab navigation for Specifications, Valuation, History, Notes
- Use Radix UI Tabs primitive (shadcn/ui)
- URL-based tab state (e.g., `/listings/[id]?tab=specifications`)
- Smooth content transitions
- Keyboard accessible

**Tab Structure:**
```
┌───────────────────────────────────────────┐
│ Specifications │ Valuation │ History │ Notes │
├───────────────────────────────────────────┤
│ Tab content area                          │
│ (content changes based on active tab)     │
└───────────────────────────────────────────┘
```

**Tabs:**
- **Specifications** - Hardware details, custom fields, product metadata
- **Valuation** - Pricing breakdown, contributing rules (reuses ListingValuationTab)
- **History** - Audit log, price history, rule changes
- **Notes** - User notes/comments (placeholder for Phase 5+)

**Acceptance Criteria:**
- [ ] Four tabs render correctly
- [ ] Tab switching works smoothly
- [ ] URL updates when switching tabs
- [ ] Back button navigates between tabs
- [ ] Keyboard navigation (Tab, Arrow keys)
- [ ] ARIA roles and labels present
- [ ] Mobile responsive (consider horizontal scroll on small screens)

---

#### TASK-410: Implement responsive design
**Status:** Not Started
**Owner:** ui-engineer
**Files:** All new detail page components

**Requirements:**
- Mobile-first responsive design
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Hero section responsive (stacked on mobile)
- Breadcrumbs abbreviated on mobile
- Tab navigation scrollable on mobile
- Summary cards responsive grid
- Product image responsive sizing

**Responsive Behavior:**
- **Mobile (<640px):** Stacked layout, single column
- **Tablet (640-1024px):** 2-column grid for cards
- **Desktop (>1024px):** Full layout with image + sidebar

**Acceptance Criteria:**
- [ ] Layout works on 320px width (mobile)
- [ ] Layout works on 768px width (tablet)
- [ ] Layout works on 1920px width (desktop)
- [ ] No horizontal scroll (except tables)
- [ ] Touch targets >= 44px
- [ ] Text readable at all breakpoints
- [ ] Images scale properly

---

## Success Criteria

### Functional Completeness
- [ ] Detail page route renders at `/listings/[id]`
- [ ] Loading skeleton displays during data fetch
- [ ] 404 page displays when listing not found
- [ ] Hero section displays product image and summary cards
- [ ] Breadcrumb navigation functional
- [ ] Tab navigation switches between tabs
- [ ] All tabs content displays (even if placeholder)
- [ ] Responsive design works on mobile/tablet/desktop

### Backend Quality
- [ ] No N+1 queries in /v1/listings/{id} endpoint
- [ ] Response time < 500ms (p95)
- [ ] All required relationships eager-loaded
- [ ] TypeScript types complete and accurate
- [ ] Error handling (404, validation) working

### Frontend Quality
- [ ] No TypeScript errors
- [ ] No console warnings
- [ ] No hydration mismatches
- [ ] All components properly memoized
- [ ] No layout shifts (CLS = 0)
- [ ] Accessibility: keyboard navigation working
- [ ] Accessibility: screen reader compatible
- [ ] Dark mode support correct

### Performance
- [ ] LCP < 2.5s (75th percentile)
- [ ] FID < 100ms (75th percentile)
- [ ] CLS < 0.1 (75th percentile)
- [ ] Images optimized with Next.js Image
- [ ] No unnecessary re-renders

---

## Development Checklist

### Backend
- [ ] TASK-401: Enhance /v1/listings/{id} endpoint
  - [ ] Add eager loading for CPU relationship
  - [ ] Add eager loading for GPU relationship
  - [ ] Add eager loading for RAM relationship
  - [ ] Add eager loading for Storage relationship
  - [ ] Add eager loading for Ports relationship
  - [ ] Handle 404 responses
  - [ ] Test with multiple listings
  - [ ] Verify response time

### Frontend - Pages & Layout
- [ ] TASK-402: Create detail page route
  - [ ] Create /listings/[id]/page.tsx
  - [ ] Implement server-side data fetching
  - [ ] Add generateMetadata function
  - [ ] Handle 404 properly
  - [ ] Test TypeScript compilation

- [ ] TASK-403: Create loading skeleton
  - [ ] Create /listings/[id]/loading.tsx
  - [ ] Design skeleton UI
  - [ ] Verify smooth transition
  - [ ] Test CLS metric

- [ ] TASK-404: Create 404 not-found page
  - [ ] Create /listings/[id]/not-found.tsx
  - [ ] Add helpful messaging
  - [ ] Add navigation links
  - [ ] Test accessibility

### Frontend - Components
- [ ] TASK-405: Create DetailPageLayout component
  - [ ] Basic structure
  - [ ] Breadcrumb integration
  - [ ] Hero component integration
  - [ ] Tab navigation integration
  - [ ] Responsive styling
  - [ ] Dark mode support

- [ ] TASK-406: Create breadcrumb navigation
  - [ ] Breadcrumb component
  - [ ] Path generation logic
  - [ ] Link navigation
  - [ ] Mobile responsiveness
  - [ ] Accessibility testing

- [ ] TASK-407: Create DetailPageHero component
  - [ ] Hero layout structure
  - [ ] ProductImage integration
  - [ ] SummaryCard integration
  - [ ] Data binding
  - [ ] Responsive grid
  - [ ] Dark mode styling

- [ ] TASK-408: Create ProductImage component
  - [ ] Primary image display
  - [ ] Manufacturer logo fallback
  - [ ] Generic icon fallback
  - [ ] Next.js Image optimization
  - [ ] Loading state
  - [ ] Error handling
  - [ ] Alt text

- [ ] TASK-409: Create tab navigation component
  - [ ] Tab structure
  - [ ] Tab switching logic
  - [ ] URL state management
  - [ ] Content transitions
  - [ ] Keyboard navigation
  - [ ] ARIA labels
  - [ ] Mobile responsiveness

- [ ] TASK-410: Implement responsive design
  - [ ] Mobile layout (320px)
  - [ ] Tablet layout (768px)
  - [ ] Desktop layout (1920px)
  - [ ] Touch target sizing
  - [ ] Text readability
  - [ ] Image scaling
  - [ ] All breakpoints tested

---

## Work Log

### 2025-10-23 - Session 1

**Completed:**
- Created Phase 4 progress tracker document

**Subagents Used:**
- None yet

**Commits:**
- None yet

**Blockers/Issues:**
- None

**Next Steps:**
- Begin TASK-401 (Backend endpoint enhancement)
- Verify API schema with backend engineer
- Start TASK-402-410 in parallel after backend is ready

---

## Decisions Log

### ADR-010: Server Component for Detail Page
**Decision:** Implement detail page as Next.js Server Component for optimal performance
**Rationale:** Server-side data fetching reduces client-side JavaScript, improves LCP, simplifies data management
**Impact:** Detail page loads faster, better SEO, reduced bundle size
**Status:** Pending implementation

### ADR-011: Eager Loading Strategy
**Decision:** Use SQLAlchemy selectinload for all relationships in /v1/listings/{id}
**Rationale:** Prevents N+1 queries, ensures response time < 500ms
**Impact:** Single query for listing + all relationships
**Status:** Pending implementation

### ADR-012: Image Fallback Hierarchy
**Decision:** Primary image → Manufacturer logo → Generic icon
**Rationale:** Provides visual feedback even when images unavailable, improves UX
**Impact:** Better user experience, graceful degradation
**Status:** Pending implementation

### ADR-013: URL-Based Tab State
**Decision:** Use URL query parameter for active tab (e.g., `?tab=specifications`)
**Rationale:** Allows sharing specific tabs, back button works correctly, bookmarkable state
**Impact:** Improved navigation experience, SEO-friendly URLs
**Status:** Pending implementation

---

## Files Changed

### Created
- `apps/web/app/listings/[id]/page.tsx` - Detail page route
- `apps/web/app/listings/[id]/loading.tsx` - Loading skeleton
- `apps/web/app/listings/[id]/not-found.tsx` - 404 page
- `apps/web/components/listings/detail-page-layout.tsx` - Layout wrapper
- `apps/web/components/listings/detail-page-hero.tsx` - Hero section
- `apps/web/components/listings/breadcrumb-nav.tsx` - Breadcrumb navigation
- `apps/web/components/listings/product-image.tsx` - Product image component
- `apps/web/components/listings/detail-page-tabs.tsx` - Tab navigation

### Modified
- `apps/api/dealbrain_api/api/listings.py` - Enhanced endpoint
- `apps/api/dealbrain_api/services/listings.py` - Service layer updates

### Deleted
- None

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| LCP | < 2.5s (75th) | TBD |
| FID | < 100ms (75th) | TBD |
| CLS | < 0.1 | TBD |
| API p95 | < 500ms | TBD |
| Image optimization | Next.js Image | TBD |
| Bundle size | < 50KB (gzip) | TBD |

---

## Testing Plan

### Unit Tests
- [ ] Detail page route component
- [ ] DetailPageLayout component
- [ ] DetailPageHero component
- [ ] BreadcrumbNav component
- [ ] ProductImage component (with fallbacks)
- [ ] DetailPageTabs component

### Integration Tests
- [ ] End-to-end detail page navigation
- [ ] Tab switching and URL state
- [ ] Image loading and fallback behavior
- [ ] 404 handling for missing listings
- [ ] Loading skeleton display

### Accessibility Tests
- [ ] Keyboard navigation (Tab, Arrow keys, Enter)
- [ ] Screen reader compatibility
- [ ] ARIA labels and roles
- [ ] Color contrast verification
- [ ] Focus indicators visible

### Performance Tests
- [ ] LCP measurement
- [ ] CLS verification
- [ ] Image optimization
- [ ] Bundle size monitoring

---

## Dependencies & Blockers

### Frontend Dependencies
- Requires TASK-401 backend work before full testing
- Depends on existing SummaryCard component (from Phase 5, may need placeholder)
- Depends on ListingValuationTab reuse (already exists)

### Backend Dependencies
- None blocking

### Blockers
- None currently

---

## Notes

### Implementation Notes
- Phase 4 focuses on basic structure and layout
- Phase 5 will add entity links and tooltips
- Phase 6 will add detailed tab content
- Components should be designed for reuse in other parts of app

### Related Context
- See `/docs/project_plans/listings-facelift-enhancement/context/listings-facelift-context.md` for full project context
- Phase 1, 2, 3 already completed (auto-close modal, smart rule display, enhanced breakdown)
- Phase 4 is foundation for Phases 5-7

### Component Dependencies
```
DetailPageLayout
├── BreadcrumbNav (independent)
├── DetailPageHero
│   ├── ProductImage
│   └── SummaryCard (x4) - May need placeholder from design system
└── DetailPageTabs
    ├── SpecificationsTab (Phase 5+)
    ├── ValuationTabPage (reuses ListingValuationTab - exists)
    ├── HistoryTab (Phase 6+)
    └── NotesTab (placeholder for Phase 6+)
```

### Design System References
- Use shadcn/ui components (Breadcrumb, Tabs, Skeleton)
- Tailwind CSS for styling
- Radix UI for underlying primitives
- Follow existing design patterns in listings components
- Maintain dark mode consistency

---

**End of Phase 4 Progress Tracker**

**Version History:**
- v1.0 (2025-10-23): Initial Phase 4 progress tracker
