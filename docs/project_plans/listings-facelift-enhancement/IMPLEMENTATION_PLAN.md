# Implementation Plan: Listings Enhancement

**Project:** Listings Detail Page & Modal Enhancement
**Version:** 1.0
**Date:** 2025-10-22
**Status:** Ready for Implementation
**Estimated Duration:** 7 weeks

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technical Architecture](#technical-architecture)
3. [File Manifest](#file-manifest)
4. [Implementation Phases](#implementation-phases)
5. [Testing Strategy](#testing-strategy)
6. [Deployment Plan](#deployment-plan)
7. [Risk Mitigation](#risk-mitigation)
8. [Success Criteria](#success-criteria)

---

## Project Overview

### Goals

Transform the listings experience with four key improvements:

1. **Auto-close creation modal** - Streamline workflow by automatically closing modal after successful listing creation
2. **Smart rule display** - Show only top 4 contributing valuation rules in modal for clarity
3. **Enhanced breakdown modal** - Organize rules into contributors/inactive sections with navigation
4. **Rich detail page** - Complete redesign with product images, entity links, and tabbed layout

### Key Deliverables

- Auto-closing creation modal with list refresh and highlighting
- Filtered valuation tab showing max 4 contributing rules
- Enhanced valuation breakdown modal with sorting and clickable rules
- Complete detail page (`/listings/[id]`) with hero section and tabs
- Reusable entity link and tooltip components
- Comprehensive test coverage (unit, integration, accessibility)

### Dependencies

**Frontend:**
- Next.js 14 App Router
- React Query v5
- Radix UI primitives (Dialog, Tabs, HoverCard, Collapsible)
- shadcn/ui components
- Tailwind CSS 3+

**Backend:**
- FastAPI with async SQLAlchemy
- Existing `/v1/listings/{id}` endpoint
- Enhanced `/v1/listings/{id}/valuation-breakdown` endpoint
- Entity detail endpoints (`/v1/cpus/{id}`, `/v1/gpus/{id}`, etc.)

---

## Technical Architecture

### Component Architecture

```
Frontend Component Hierarchy:

/listings/[id]/
├── page.tsx (Server Component)
│   ├── DetailPageLayout
│   │   ├── DetailPageHero
│   │   │   ├── ProductImage (with fallbacks)
│   │   │   └── SummaryCardsGrid
│   │   │       ├── PriceSummaryCard
│   │   │       ├── PerformanceSummaryCard
│   │   │       ├── HardwareSummaryCard
│   │   │       └── MetadataSummaryCard
│   │   └── DetailPageTabs
│   │       ├── SpecificationsTab
│   │       │   ├── HardwareSection (with EntityLinks)
│   │       │   ├── ProductDetailsSection
│   │       │   ├── PerformanceMetricsSection
│   │       │   └── CustomFieldsSection
│   │       ├── ValuationTab (reuses ListingValuationTab)
│   │       ├── HistoryTab
│   │       └── NotesTab (placeholder)
│   └── EntityTooltip (HoverCard wrapper)

Modal Components:
├── AddListingModal (enhanced with auto-close)
├── ListingValuationTab (enhanced with filtering)
└── ValuationBreakdownModal (enhanced with sections + navigation)

Reusable Components:
├── EntityLink (clickable link with optional tooltip)
├── EntityTooltip (hover card for CPU, GPU, RAM, Storage)
├── ProductImage (image with manufacturer-based fallbacks)
└── SummaryCard (reusable metric card)
```

### Data Flow

```
Creation Flow:
User submits form → API POST /v1/listings → Success (201)
  → React Query onSuccess callback
    → Close modal (200ms fade)
    → Invalidate queries: ['listings', 'records'], ['listings', 'count']
    → Refetch listings
    → Scroll to new item
    → Apply highlight animation (2s pulse)
    → Move focus to new item row
    → Show success toast

Detail Page Load:
Server Component → apiFetch(`/v1/listings/${id}`)
  → Eager load: CPU, GPU, RAM, Storage, Ports, Valuation Breakdown
  → Render hero + tabs
  → Client-side: Prefetch entity tooltips on hover

Valuation Breakdown:
Click "View Full Breakdown" → Open ValuationBreakdownModal
  → React Query fetch: `/v1/listings/${id}/valuation-breakdown`
  → Sort adjustments: contributors (by amount desc) + inactive (alphabetical)
  → Render sections with RuleGroup badges
  → Click rule name → Next.js navigate to `/valuation/rules/${ruleId}`
```

### State Management

**React Query Cache Keys:**
```typescript
['listings', 'records', { page, filters }]          // Listings table data
['listings', 'count', { filters }]                  // Total count
['listings', 'single', listingId]                   // Single listing detail
['listing', 'detail', listingId]                    // Detail page (server prefetch)
['listing', 'valuation', listingId]                 // Valuation breakdown
['cpu', cpuId]                                      // CPU tooltip data
['gpu', gpuId]                                      // GPU tooltip data
['ram-spec', ramSpecId]                             // RAM tooltip data
['storage-profile', storageProfileId]               // Storage tooltip data
['rulesets', 'active']                              // Active rulesets
```

**URL State:**
```typescript
/listings/[id]?tab=valuation                        // Active tab
/listings?highlight=123                             // Highlight new listing (optional)
```

**Zustand Store (Optional):**
```typescript
interface ListingsStore {
  recentListingId: number | null;                   // Last created listing
  setRecentListingId: (id: number | null) => void;
}
```

### API Enhancements

**Required Backend Changes:**

1. **Enhanced `/v1/listings/{id}` endpoint:**
   - Eager-load all relationships (CPU, GPU, RAM, Storage, Ports)
   - Include full entity data for tooltips (cores, TDP, marks, etc.)
   - Return 404 if listing not found

2. **Enhanced `/v1/listings/{id}/valuation-breakdown` endpoint:**
   - Add `rule_description` to each adjustment
   - Add `rule_group_id` and `rule_group_name` to each adjustment
   - Include ALL rules (active + inactive with zero adjustments)
   - Return parent ruleset information

**Example Enhanced Adjustment Schema:**
```python
class ValuationAdjustmentSchema(BaseModel):
    rule_id: int | None = None
    rule_name: str
    rule_description: str | None = None          # NEW
    rule_group_id: int | None = None             # NEW
    rule_group_name: str | None = None           # NEW
    adjustment_amount: Decimal
    actions: list[ValuationAdjustmentActionSchema]
```

---

## File Manifest

### New Files

**Frontend Components:**
```
apps/web/components/listings/
├── detail-page-layout.tsx                      # Layout wrapper with hero and tabs
├── detail-page-hero.tsx                        # Hero section with image and summary cards
├── specifications-tab.tsx                      # Specifications tab content
├── valuation-tab-page.tsx                      # Valuation tab wrapper (reuses ListingValuationTab)
├── history-tab.tsx                             # History/audit log tab
├── notes-tab.tsx                               # Notes tab (placeholder)
├── entity-link.tsx                             # Reusable clickable entity link
├── entity-tooltip.tsx                          # Reusable entity hover tooltip (HoverCard)
├── product-image.tsx                           # Image with fallback handling
└── summary-card.tsx                            # Reusable summary card component
```

**App Router Pages:**
```
apps/web/app/listings/[id]/
├── page.tsx                                    # Enhanced detail page (server component)
├── loading.tsx                                 # Loading skeleton
└── not-found.tsx                               # 404 page
```

**Tests:**
```
apps/web/components/listings/__tests__/
├── entity-link.test.tsx                        # Entity link component tests
├── entity-tooltip.test.tsx                     # Entity tooltip tests
├── valuation-tab.test.tsx                      # Enhanced valuation tab tests
├── breakdown-modal.test.tsx                    # Enhanced breakdown modal tests
└── detail-page.test.tsx                        # Detail page integration tests
```

**Backend:**
```
apps/api/dealbrain_api/api/
├── listings.py                                 # Enhanced with valuation breakdown metadata
```

### Modified Files

**Frontend:**
```
apps/web/components/listings/
├── add-listing-modal.tsx                       # Add auto-close on success
├── add-listing-form.tsx                        # Call onSuccess callback with new listing ID
├── listing-valuation-tab.tsx                   # Add rule filtering logic (max 4)
└── valuation-breakdown-modal.tsx               # Add sections, sorting, clickable rules
```

**Backend:**
```
apps/api/dealbrain_api/
├── api/listings.py                             # Enhanced endpoints
└── services/listings.py                        # Eager-load relationships
```

### Configuration Files

No configuration changes required.

---

## Implementation Phases

### Phase 1: Auto-Close Modal (Week 1)

**Objective:** Streamline creation workflow by auto-closing modal after successful listing creation.

**Tasks:**

- **TASK-101:** Modify `AddListingForm` to accept `onSuccess` callback with new listing ID
  - File: `apps/web/components/listings/add-listing-form.tsx`
  - Accept `onSuccess?: (listingId: number) => void` prop
  - Call `onSuccess(newListing.id)` in mutation's `onSuccess` callback
  - Preserve form state if modal stays open on error

- **TASK-102:** Enhance `AddListingModal` auto-close logic
  - File: `apps/web/components/listings/add-listing-modal.tsx`
  - Implement `handleSuccess` function that closes modal
  - Pass `handleSuccess` to `AddListingForm`
  - Add 200ms fade-out animation

- **TASK-103:** Implement list refresh and highlight in listings page/table
  - Files: `apps/web/app/listings/page.tsx`, `apps/web/components/listings/listings-table.tsx`
  - Store newly created listing ID in URL param: `?highlight=123`
  - Invalidate React Query cache on modal success
  - Apply CSS animation to highlighted row (2s pulse with `bg-accent/10`)
  - Scroll highlighted row into view if outside viewport

- **TASK-104:** Focus management after modal close
  - File: `apps/web/components/listings/add-listing-modal.tsx`
  - Move focus to highlighted listing row after modal closes
  - Use `ref` and `.focus()` for keyboard accessibility

- **TASK-105:** Add success toast notification
  - File: `apps/web/components/listings/add-listing-form.tsx`
  - Show toast: "Listing created successfully" (3s auto-dismiss)
  - Position: top-right
  - Green checkmark icon

**Acceptance Criteria:**

- ✅ Modal closes automatically after successful creation (201 response)
- ✅ Modal remains open on validation errors (400) or server errors (500)
- ✅ New listing appears in table within 2 seconds
- ✅ New listing is highlighted with 2-second pulse animation
- ✅ Focus moves to new listing row
- ✅ Success toast displays
- ✅ Keyboard navigation works throughout flow

**Time Estimate:** 3 days

---

### Phase 2: Smart Rule Display (Week 1-2)

**Objective:** Filter valuation tab to show only top 4 contributing rules with clear hierarchy.

**Tasks:**

- **TASK-201:** Implement rule filtering logic in `ListingValuationTab`
  - File: `apps/web/components/listings/listing-valuation-tab.tsx`
  - Filter adjustments where `adjustment_amount !== 0`
  - Sort by `Math.abs(adjustment_amount)` descending
  - Take first 4 rules
  - Memoize filtered/sorted results

- **TASK-202:** Update rule cards display
  - File: `apps/web/components/listings/listing-valuation-tab.tsx`
  - Show only top 4 contributing rules
  - Display count of remaining rules: "+ 8 more rules in breakdown"
  - Update "View Full Breakdown" button text to include total count

- **TASK-203:** Add empty state for zero contributors
  - File: `apps/web/components/listings/listing-valuation-tab.tsx`
  - Show dashed border card with message: "No rule-based adjustments were applied to this listing."
  - Hide "View Full Breakdown" button if zero rules

- **TASK-204:** Color-code adjustments
  - File: `apps/web/components/listings/listing-valuation-tab.tsx`
  - Green (`text-emerald-600`) for negative adjustments (savings)
  - Red (`text-red-600`) for positive adjustments (premiums)
  - Gray (`text-muted-foreground`) for zero adjustments

**Acceptance Criteria:**

- ✅ Max 4 rules displayed in modal valuation tab
- ✅ Rules sorted by absolute adjustment amount (descending)
- ✅ Color-coding applied: green (savings), red (premiums)
- ✅ "View Full Breakdown" button shows total rule count
- ✅ Empty state shown if zero contributing rules
- ✅ All rules still accessible via "View Full Breakdown"

**Time Estimate:** 2 days

---

### Phase 3: Enhanced Breakdown Modal (Week 2-3)

**Objective:** Reorganize breakdown modal with contributors/inactive sections, clickable rules, and RuleGroup badges.

**Tasks:**

- **TASK-301:** Backend - Enhance `/v1/listings/{id}/valuation-breakdown` endpoint
  - File: `apps/api/dealbrain_api/api/listings.py`
  - Add `rule_description`, `rule_group_id`, `rule_group_name` to adjustment schema
  - Include ALL rules (both active and inactive with zero adjustments)
  - Join with `RuleGroup` table to fetch group names
  - Update Pydantic schema: `ValuationAdjustmentSchema`

- **TASK-302:** Backend - Eager-load rule metadata in breakdown service
  - File: `apps/api/dealbrain_api/services/listings.py`
  - Modify `get_valuation_breakdown()` to join with rules and rule_groups tables
  - Return complete rule metadata for frontend display

- **TASK-303:** Frontend - Implement sorting logic in `ValuationBreakdownModal`
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Separate adjustments into two arrays:
    - `contributors`: `adjustment_amount !== 0`, sorted by `Math.abs(amount)` desc
    - `inactive`: `adjustment_amount === 0`, sorted alphabetically by `rule_name`
  - Memoize sorting logic for performance

- **TASK-304:** Frontend - Add section headers and separators
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Section 1: "ACTIVE CONTRIBUTORS (4)" with count
  - Separator (horizontal line)
  - Section 2: "INACTIVE RULES (8)" with count
  - Typography: `text-sm font-semibold uppercase tracking-wide text-muted-foreground`

- **TASK-305:** Frontend - Add RuleGroup badges to rule cards
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Display badge: `<Badge variant="outline">{rule_group_name}</Badge>`
  - Position: next to rule name or on same line
  - Small text, subtle background

- **TASK-306:** Frontend - Make rule names clickable
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Wrap rule name in Next.js `<Link>` component
  - Navigate to: `/valuation/rules/${rule_id}`
  - Styling: `text-primary hover:underline cursor-pointer`
  - Keyboard accessible (Enter/Space triggers navigation)

- **TASK-307:** Frontend - Implement collapsible inactive section
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Use Radix UI `Collapsible` primitive
  - Default: collapsed if >10 inactive rules
  - Toggle button: "Show 8 inactive rules" / "Hide inactive rules"
  - Smooth height transition animation

- **TASK-308:** Frontend - Add hover tooltips for rule descriptions
  - File: `apps/web/components/listings/valuation-breakdown-modal.tsx`
  - Use Radix UI `HoverCard` for rule description tooltips
  - Trigger: hover rule name after 200ms delay
  - Display: `rule_description` if available
  - Max width: 280px, padding: `p-3`

**Acceptance Criteria:**

- ✅ Backend returns `rule_description`, `rule_group_id`, `rule_group_name` for all adjustments
- ✅ Backend includes inactive rules (zero adjustment) in response
- ✅ Modal displays two sections: "Active Contributors" and "Inactive Rules"
- ✅ Contributors sorted by absolute amount descending
- ✅ Inactive rules sorted alphabetically
- ✅ RuleGroup badges visible on rule cards
- ✅ Rule names are clickable and navigate to rule detail page
- ✅ Hover tooltips show rule descriptions
- ✅ Inactive section is collapsible if >10 rules
- ✅ All interactive elements keyboard accessible

**Time Estimate:** 5 days

---

### Phase 4: Detail Page Foundation (Week 3-4)

**Objective:** Create basic detail page structure with hero section, breadcrumbs, and tab navigation.

**Tasks:**

- **TASK-401:** Backend - Enhance `/v1/listings/{id}` endpoint with eager loading
  - File: `apps/api/dealbrain_api/services/listings.py`
  - Eager-load all relationships: CPU, GPU, RAM, Storage, Ports
  - Use SQLAlchemy `selectinload()` for efficient loading
  - Include full entity data (not just IDs) for tooltips
  - Return 404 if listing not found

- **TASK-402:** Create detail page route
  - File: `apps/web/app/listings/[id]/page.tsx`
  - Server-side component using Next.js App Router
  - Fetch listing with `apiFetch<ListingDetail>(`/v1/listings/${id}`)`
  - Call `notFound()` if listing doesn't exist
  - Generate metadata with `generateMetadata()` for SEO

- **TASK-403:** Create loading skeleton
  - File: `apps/web/app/listings/[id]/loading.tsx`
  - Skeleton matching final layout (hero + tabs)
  - Shimmer animation for placeholders
  - Use shadcn/ui `Skeleton` component

- **TASK-404:** Create 404 not-found page
  - File: `apps/web/app/listings/[id]/not-found.tsx`
  - Custom message: "Listing not found or has been deleted."
  - Link back to listings table: "← Back to Listings"
  - Search box to find other listings
  - Accessible, semantic HTML

- **TASK-405:** Create `DetailPageLayout` component
  - File: `apps/web/components/listings/detail-page-layout.tsx`
  - Layout wrapper accepting `listing` prop
  - Render breadcrumb, hero section, and tabs
  - Responsive container with max width: `max-w-7xl`

- **TASK-406:** Create breadcrumb navigation
  - File: `apps/web/components/listings/detail-page-layout.tsx`
  - Breadcrumb: Dashboard > Listings > [Title]
  - Use Next.js `<Link>` for navigation
  - Typography: `text-sm text-muted-foreground`
  - Separators: `/` or `>`

- **TASK-407:** Create `DetailPageHero` component
  - File: `apps/web/components/listings/detail-page-hero.tsx`
  - Two-column layout: image left, summary cards right
  - Page title (h1): listing title
  - Status badge and quick actions (Edit, Delete, Duplicate)
  - Responsive: stacks vertically on mobile

- **TASK-408:** Create `ProductImage` component
  - File: `apps/web/components/listings/product-image.tsx`
  - Source priority: `thumbnail_url` → manufacturer icon → generic PC icon
  - Use Next.js `<Image>` component for optimization
  - Fallback icons: HardDrive, Cpu, Monitor (lucide-react)
  - Aspect ratio: 1:1 (square) or 4:3
  - Border, rounded corners, shadow
  - Alt text from listing title
  - Blur placeholder while loading

- **TASK-409:** Create tab navigation component
  - File: `apps/web/components/listings/detail-page-layout.tsx`
  - Use shadcn/ui `Tabs` component
  - Tabs: Specifications | Valuation | History | Notes
  - Tab state persisted in URL: `?tab=valuation`
  - Use `useSearchParams()` and `useRouter()` for URL state
  - Default tab: Specifications

- **TASK-410:** Implement responsive design
  - Files: All detail page components
  - Desktop (≥1024px): Two-column hero layout
  - Tablet (768-1023px): Stacked hero sections
  - Mobile (<768px): Single column, full-width image
  - Test on real devices

**Acceptance Criteria:**

- ✅ Backend endpoint returns listing with all relationships eager-loaded
- ✅ Page accessible at `/listings/[id]`
- ✅ Page returns 404 if listing not found
- ✅ SEO meta tags populated (title, description)
- ✅ Breadcrumb navigation functional
- ✅ Hero section displays with product image and layout
- ✅ Product image shows with appropriate fallback
- ✅ Tab navigation works with URL state persistence
- ✅ Responsive design verified across breakpoints
- ✅ Loading skeleton displays during SSR

**Time Estimate:** 5 days

---

### Phase 5: Entity Links & Tooltips (Week 4-5)

**Objective:** Implement clickable entity relationships with hover tooltips for rich contextual information.

**Tasks:**

- **TASK-501:** Create `SummaryCard` component
  - File: `apps/web/components/listings/summary-card.tsx`
  - Reusable card for price, performance, hardware, metadata
  - Props: `title`, `value`, `subtitle`, `icon`, `variant`
  - Variants: default, success, warning, error
  - Responsive text sizing

- **TASK-502:** Create summary cards grid in hero
  - File: `apps/web/components/listings/detail-page-hero.tsx`
  - Grid layout: 2 columns on desktop, 1 on mobile
  - Card 1: Price (list price, adjusted price, savings with color coding)
  - Card 2: Performance (composite score, CPU marks, perf/watt)
  - Card 3: Hardware (CPU, GPU, RAM, Storage summary)
  - Card 4: Condition (condition, seller, status)

- **TASK-503:** Create `EntityLink` component
  - File: `apps/web/components/listings/entity-link.tsx`
  - Props: `type`, `id`, `name`, `showTooltip`, `className`
  - Types: 'cpu' | 'gpu' | 'ram_spec' | 'storage_profile' | 'ports_profile'
  - Wrap in Next.js `<Link>` to entity detail page
  - Styling: `text-primary hover:underline`
  - Keyboard accessible

- **TASK-504:** Create `EntityTooltip` component
  - File: `apps/web/components/listings/entity-tooltip.tsx`
  - Use Radix UI `HoverCard` primitive
  - Trigger: hover after 200ms delay
  - Max width: 280px, padding: `p-3`
  - Display entity-specific data in grid layout

- **TASK-505:** Implement CPU tooltip
  - File: `apps/web/components/listings/entity-tooltip.tsx`
  - Fetch CPU data: `useQuery({ queryKey: ['cpu', cpuId], enabled: isHovered })`
  - Display: Cores/Threads, CPU Mark (Multi/Single), TDP, iGPU Model/Mark, Release Year
  - Grid: 2 columns (label/value pairs)

- **TASK-506:** Implement GPU tooltip
  - File: `apps/web/components/listings/entity-tooltip.tsx`
  - Fetch GPU data: `useQuery({ queryKey: ['gpu', gpuId], enabled: isHovered })`
  - Display: VRAM, TDP, Performance Tier, Release Year

- **TASK-507:** Implement RAM Spec tooltip
  - File: `apps/web/components/listings/entity-tooltip.tsx`
  - Display: DDR Generation, Speed (MHz), Module Count × Capacity, Total Capacity

- **TASK-508:** Implement Storage Profile tooltip
  - File: `apps/web/components/listings/entity-tooltip.tsx`
  - Display: Medium (SSD/HDD), Interface, Form Factor, Performance Tier

- **TASK-509:** Backend - Create entity detail endpoints
  - Files: `apps/api/dealbrain_api/api/catalog.py` (verify existing endpoints)
  - Ensure endpoints exist: `/v1/cpus/{id}`, `/v1/gpus/{id}`, `/v1/ram-specs/{id}`, `/v1/storage-profiles/{id}`
  - Return full entity data for tooltips

**Acceptance Criteria:**

- ✅ Summary cards display in hero section with responsive grid
- ✅ `EntityLink` component navigates to correct entity pages
- ✅ `EntityTooltip` shows on hover after 200ms delay
- ✅ CPU tooltip displays cores, threads, CPU marks, TDP, iGPU info
- ✅ GPU tooltip displays VRAM, TDP, performance tier
- ✅ RAM tooltip displays DDR generation, speed, capacity
- ✅ Storage tooltip displays medium, interface, form factor
- ✅ All tooltips keyboard accessible (focus triggers tooltip)
- ✅ Entity data prefetched on hover (React Query caching)

**Time Estimate:** 5 days

---

### Phase 6: Specifications & Valuation Tabs (Week 5-6)

**Objective:** Build specifications tab with entity links and integrate valuation tab into detail page.

**Tasks:**

- **TASK-601:** Create `SpecificationsTab` component
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Organize content into sections: Hardware, Product Details, Listing Info, Performance, Metadata, Custom Fields
  - Grid layout: 2-3 columns on desktop, 1 on mobile
  - Section headers: `text-lg font-semibold mb-4`

- **TASK-602:** Implement Hardware section
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Display: CPU (with EntityLink), GPU, RAM, Primary Storage, Secondary Storage
  - Use `EntityLink` components with tooltips enabled
  - Ports: display as compact badge list (e.g., "USB-C ×2, HDMI ×1")

- **TASK-603:** Implement Product Details section
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Display: Manufacturer, Series, Model Number, Form Factor
  - Label/value pairs in grid layout

- **TASK-604:** Implement Listing Info section
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Display: Seller, Listing URL (clickable with external link icon), Other URLs, Condition, Status
  - URLs: `text-primary hover:underline` with lucide-react `ExternalLink` icon

- **TASK-605:** Implement Performance Metrics section
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Display: Composite Score, CPU Multi/Single Scores, Perf/Watt, $/CPU Mark
  - Grid layout with label/value pairs
  - Format numbers: 2 decimal places

- **TASK-606:** Implement Metadata section
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Display: Created At, Updated At
  - Format timestamps: `new Date().toLocaleString()`

- **TASK-607:** Implement Custom Fields section
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Iterate over `listing.attributes` object
  - Render based on data type: text, number, select, boolean
  - Handle circular references gracefully

- **TASK-608:** Handle null/missing values
  - File: `apps/web/components/listings/specifications-tab.tsx`
  - Display "—" or "Not specified" for null values
  - Defensive null checks throughout

- **TASK-609:** Create `ValuationTabPage` component
  - File: `apps/web/components/listings/valuation-tab-page.tsx`
  - Wrapper component that imports and renders `ListingValuationTab`
  - Pass `listing` prop from detail page
  - Ensure React Query keys match between page and modal

- **TASK-610:** Create `HistoryTab` component
  - File: `apps/web/components/listings/history-tab.tsx`
  - Display: Created timestamp, Updated timestamp
  - Format: "Created on [date] at [time]"
  - Empty state: "No history available for this listing."
  - Placeholder for future audit log features

- **TASK-611:** Create `NotesTab` component (placeholder)
  - File: `apps/web/components/listings/notes-tab.tsx`
  - Display: "Notes feature coming soon."
  - Future: rich text editor for private notes

**Acceptance Criteria:**

- ✅ Specifications tab displays all listing data organized by section
- ✅ Hardware section shows CPU, GPU, RAM, Storage with clickable entity links
- ✅ Entity links trigger hover tooltips with detailed information
- ✅ Product details, listing info, performance metrics sections display correctly
- ✅ Custom fields render based on data type
- ✅ Null values display as "—" or "Not specified"
- ✅ URLs are clickable with external link icons
- ✅ Valuation tab reuses `ListingValuationTab` component with correct data
- ✅ History tab displays created/updated timestamps
- ✅ Notes tab shows placeholder message
- ✅ All tabs responsive across breakpoints

**Time Estimate:** 5 days

---

### Phase 7: Polish & Testing (Week 6-7)

**Objective:** Accessibility audit, performance optimization, cross-browser testing, and comprehensive test coverage.

**Tasks:**

- **TASK-701:** Accessibility audit with axe-core
  - Run axe-core automated testing on all new pages/components
  - Fix all critical and serious violations
  - Verify WCAG AA compliance
  - Test with screen readers (NVDA, VoiceOver)

- **TASK-702:** Keyboard navigation testing
  - Test all interactive elements (links, buttons, modals, tabs) with Tab, Enter, Space
  - Verify focus indicators visible on all focusable elements
  - Test modal focus trap (focus stays within modal)
  - Test tab navigation with arrow keys (if applicable)

- **TASK-703:** Performance optimization
  - Memoize expensive computations (rule sorting, filtering)
  - React.memo() for components that re-render frequently
  - Lazy load entity tooltip data (only fetch on hover)
  - Verify React Query caching working correctly (5-minute stale time)
  - Optimize images with Next.js Image component
  - Code split tabs (lazy load tab content)

- **TASK-704:** Cross-browser testing
  - Test on Chrome (latest 2 versions)
  - Test on Firefox (latest 2 versions)
  - Test on Safari (latest 2 versions)
  - Test on Mobile Safari (iOS 14+)
  - Test on Chrome Mobile (Android 10+)
  - Fix browser-specific issues

- **TASK-705:** Responsive testing on real devices
  - Test on mobile (375px - 767px)
  - Test on tablet (768px - 1023px)
  - Test on desktop (1024px - 1920px)
  - Test on ultra-wide (1920px+)
  - Verify touch targets ≥ 44×44 pixels on mobile
  - Test gestures (swipe, pinch-to-zoom, etc.)

- **TASK-706:** Write unit tests for new components
  - Files: `apps/web/components/listings/__tests__/*.test.tsx`
  - Test `EntityLink` component (navigation, tooltip trigger)
  - Test `EntityTooltip` component (data fetching, display)
  - Test `ProductImage` component (fallback logic)
  - Test `SummaryCard` component (variants, data display)
  - Test `SpecificationsTab` (section rendering, null handling)
  - Coverage target: >80%

- **TASK-707:** Write integration tests for flows
  - Test creation flow: submit form → modal closes → list refreshes → item highlighted
  - Test detail page load: navigate → hero renders → tabs switch
  - Test valuation breakdown: click button → modal opens → sections display → rule click navigates
  - Test entity tooltips: hover link → tooltip appears → data displays
  - Use React Testing Library

- **TASK-708:** Visual regression testing
  - Capture screenshots of all new pages/components
  - Use Percy, Chromatic, or manual comparison
  - Verify layout consistency across breakpoints
  - Test dark mode (if applicable)

- **TASK-709:** Performance benchmarking
  - Measure Core Web Vitals: LCP, FID, CLS
  - Target: LCP < 2.5s, FID < 100ms, CLS < 0.1
  - Use Lighthouse CI or Vercel Analytics
  - Test on 3G connection simulation
  - Verify API response times: p95 < 500ms

- **TASK-710:** User acceptance testing
  - Test all features with internal users
  - Collect feedback on usability
  - Fix critical UX issues
  - Document known issues for future releases

- **TASK-711:** Update documentation
  - Update README with new detail page features
  - Document new components in Storybook (optional)
  - Update API documentation if endpoints changed
  - Add inline code comments for complex logic
  - Update CHANGELOG

**Acceptance Criteria:**

- ✅ Zero critical accessibility violations (axe-core)
- ✅ All interactive elements keyboard accessible
- ✅ Focus indicators visible and clear
- ✅ Screen reader testing passed (NVDA, VoiceOver)
- ✅ Performance targets met: LCP < 2.5s, API < 500ms p95
- ✅ Cross-browser testing completed (Chrome, Firefox, Safari, mobile)
- ✅ Responsive design verified on real devices
- ✅ Unit test coverage >80% for new components
- ✅ Integration tests passing for all flows
- ✅ Visual regression tests passed
- ✅ User acceptance testing completed with no critical issues
- ✅ Documentation updated

**Time Estimate:** 7 days

---

## Testing Strategy

### Unit Tests

**Target Coverage:** >80% for new components

**Test Framework:** Jest + React Testing Library

**Components to Test:**

1. **EntityLink**
   - Renders correct link href
   - Triggers tooltip on hover (if `showTooltip=true`)
   - Keyboard navigation works (Enter/Space)
   - Different entity types navigate to correct paths

2. **EntityTooltip**
   - Fetches entity data on hover
   - Displays correct data for each entity type (CPU, GPU, RAM, Storage)
   - Handles loading state
   - Handles error state
   - Caches data correctly (React Query)

3. **ProductImage**
   - Displays `thumbnail_url` if available
   - Falls back to manufacturer icon if no thumbnail
   - Falls back to generic icon if no manufacturer
   - Uses Next.js Image component
   - Alt text set correctly

4. **SummaryCard**
   - Renders title, value, subtitle correctly
   - Applies correct variant styles (success, warning, error)
   - Icon displays
   - Responsive sizing

5. **SpecificationsTab**
   - Renders all sections
   - Handles null values gracefully
   - Displays entity links correctly
   - Custom fields render based on data type
   - Ports display as compact badges

6. **Enhanced ListingValuationTab**
   - Filters rules to max 4
   - Sorts by absolute adjustment amount descending
   - Displays "X more rules" indicator
   - Empty state shown if zero rules
   - Color-coding applied correctly

7. **Enhanced ValuationBreakdownModal**
   - Separates contributors and inactive rules
   - Sorts contributors by amount descending
   - Sorts inactive alphabetically
   - Displays RuleGroup badges
   - Rule names are clickable
   - Collapsible inactive section works
   - Hover tooltips display rule descriptions

### Integration Tests

**Test Scenarios:**

1. **Creation Flow**
   - User fills form and submits
   - API returns 201 Created
   - Modal closes automatically
   - List refreshes and shows new listing
   - New listing is highlighted
   - Focus moves to new listing row
   - Success toast displays

2. **Creation Error Flow**
   - User submits invalid data
   - API returns 400 Bad Request
   - Modal remains open
   - Validation errors display inline
   - Form data preserved

3. **Detail Page Navigation**
   - User clicks listing title in table
   - Navigate to `/listings/[id]`
   - Loading skeleton displays
   - Page renders with hero and tabs
   - Default tab (Specifications) active

4. **Tab Switching**
   - User clicks Valuation tab
   - URL updates: `?tab=valuation`
   - Tab content changes
   - State persists on page refresh

5. **Entity Link Navigation**
   - User clicks CPU name in specifications tab
   - Navigate to `/catalog/cpus/[id]`
   - CPU detail page loads

6. **Entity Tooltip Display**
   - User hovers over CPU link
   - Wait 200ms
   - Tooltip appears with CPU data
   - Tooltip disappears on mouse out

7. **Valuation Breakdown Flow**
   - User clicks "View Full Breakdown" button
   - Modal opens
   - Contributors section displays at top
   - Inactive section displays below
   - User clicks rule name
   - Navigate to `/valuation/rules/[id]`

### Accessibility Tests

**Automated Testing:**
- Run axe-core on all pages/components
- Fix all critical and serious violations
- Integrate into CI pipeline

**Manual Testing:**
- Keyboard navigation (Tab, Enter, Space, Arrow keys)
- Screen reader testing (NVDA on Windows, VoiceOver on macOS)
- Focus indicators visible
- Color contrast verification (WebAIM Contrast Checker)
- Touch targets ≥ 44×44 pixels on mobile

### Performance Tests

**Metrics:**
- **LCP (Largest Contentful Paint):** < 2.5s
- **FID (First Input Delay):** < 100ms
- **CLS (Cumulative Layout Shift):** < 0.1
- **API Response Time (p95):** < 500ms
- **Modal Open Time:** < 100ms

**Tools:**
- Lighthouse CI for automated performance audits
- Vercel Analytics for real-user monitoring
- Chrome DevTools Performance tab for profiling

### Visual Regression Tests

**Tool:** Percy, Chromatic, or manual screenshots

**Test Cases:**
- Detail page hero section (desktop, tablet, mobile)
- Specifications tab (all sections)
- Valuation tab (with 4 rules, with 10+ rules)
- Valuation breakdown modal (contributors + inactive)
- Entity tooltips (CPU, GPU, RAM, Storage)
- Highlighted listing in table
- 404 page
- Loading skeletons

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, accessibility)
- [ ] Performance benchmarks met (LCP < 2.5s, API < 500ms)
- [ ] Cross-browser testing completed
- [ ] Responsive testing on real devices completed
- [ ] User acceptance testing completed
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Database migrations prepared (if any)
- [ ] Feature flags configured (if applicable)

### Deployment Steps

**Backend Deployment:**

1. **Database Migrations** (if schema changes required)
   ```bash
   poetry run alembic upgrade head
   ```

2. **Deploy API Changes**
   ```bash
   # Build and deploy API service
   docker-compose build api
   docker-compose up -d api
   ```

3. **Verify API Endpoints**
   - Test `/v1/listings/{id}` returns enhanced data
   - Test `/v1/listings/{id}/valuation-breakdown` includes rule metadata

**Frontend Deployment:**

1. **Build Next.js App**
   ```bash
   cd apps/web
   pnpm build
   ```

2. **Deploy to Vercel/Production**
   ```bash
   # Automatic deployment via Git push (if using Vercel)
   git push origin main
   ```

3. **Verify Deployment**
   - Check detail page loads: `/listings/[id]`
   - Test creation flow end-to-end
   - Test entity links and tooltips
   - Verify responsive design on mobile

### Rollback Plan

**If Critical Issues Detected:**

1. **Revert Git Commit**
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

2. **Rollback Database Migration** (if applicable)
   ```bash
   poetry run alembic downgrade -1
   ```

3. **Redeploy Previous Version**
   - Trigger redeployment of previous stable commit
   - Verify rollback successful

### Post-Deployment Monitoring

**Monitor for 48 Hours:**
- Error rates (Sentry or equivalent)
- API response times (Prometheus/Grafana)
- User engagement metrics (detail page views, entity link clicks)
- Core Web Vitals (Vercel Analytics)
- User feedback (support tickets, bug reports)

**Success Indicators:**
- Error rate < 1%
- API p95 response time < 500ms
- Detail page engagement > 40% increase
- Entity link click-through rate > 25%
- Zero critical accessibility violations

---

## Risk Mitigation

### Technical Risks

**Risk 1: Performance degradation with large valuation rulesets (50+ rules)**
- **Mitigation:** Implement pagination or lazy loading for inactive rules section
- **Contingency:** Benchmark with 100+ rules during development, optimize sorting/filtering

**Risk 2: Image loading delays affecting LCP**
- **Mitigation:** Use Next.js Image component with blur placeholder, lazy load below-fold images
- **Contingency:** Implement CDN for image hosting, preload critical images

**Risk 3: React Query cache inconsistency between page and modal**
- **Mitigation:** Use identical query keys, comprehensive cache invalidation strategy
- **Contingency:** Integration tests for cache behavior, manual testing of edge cases

**Risk 4: Complex interactions not keyboard accessible**
- **Mitigation:** Comprehensive keyboard testing, use Radix UI primitives (built-in accessibility)
- **Contingency:** Automated testing with axe-core, manual screen reader testing

### UX Risks

**Risk 5: Users confused by auto-close behavior**
- **Mitigation:** Clear success toast message, highlight new item, user testing before launch
- **Contingency:** Add user preference to disable auto-close (future enhancement)

**Risk 6: Detail page too information-dense**
- **Mitigation:** Tabbed organization, progressive disclosure, user testing for information hierarchy
- **Contingency:** Simplify layout based on user feedback, hide less critical data

**Risk 7: Mobile experience cramped with complex layouts**
- **Mitigation:** Mobile-first design approach, responsive testing on real devices
- **Contingency:** Simplified mobile layout variants, collapsible sections

### Data Risks

**Risk 8: Missing entity relationships break tooltips**
- **Mitigation:** Graceful degradation (hide tooltip if no data), defensive null checks
- **Contingency:** Clear fallback states ("Data unavailable"), optional tooltips

**Risk 9: Circular references in attributes JSON**
- **Mitigation:** JSON stringify with error handling, max depth limit
- **Contingency:** Schema validation on backend, sanitize data before rendering

---

## Success Criteria

### Functional Completeness

- [x] Creation modal auto-closes on success with visual confirmation
- [x] Valuation tab shows max 4 contributing rules with clear hierarchy
- [x] Breakdown modal organizes rules into contributors and inactive sections
- [x] Rule names are clickable and navigate to rule detail pages
- [x] Detail page displays comprehensive listing information with tabs
- [x] Product images load with appropriate fallbacks
- [x] Entity relationships are clickable with hover tooltips
- [x] All tabs (Specifications, Valuation, History) are functional
- [x] Responsive design works across all breakpoints

### Quality Standards

- [x] Accessibility requirements met (WCAG AA, keyboard navigation, screen reader)
- [x] Performance targets achieved (LCP < 2.5s, API < 500ms p95)
- [x] All automated tests passing (unit, integration, accessibility)
- [x] Cross-browser testing completed (Chrome, Firefox, Safari)
- [x] User acceptance testing completed with no critical issues

### Adoption Metrics (Post-Launch)

**Week 1-2:**
- Creation modal auto-close success rate: 95%
- Time to see newly created listing: < 2 seconds
- Valuation tab rule count reduction: 50-75%

**Week 3-4:**
- Detail page engagement rate: > 40% increase
- Entity link click-through rate: > 25%
- Valuation breakdown modal open rate: > 35%

**Continuous:**
- Error rate < 1%
- LCP < 2.5s (75th percentile)
- API p95 < 500ms
- Zero critical accessibility violations

---

## Appendix

### Task Tracking Template

```markdown
## TASK-XXX: [Task Title]

**Phase:** [Phase Number and Name]
**Assignee:** [Developer Name]
**Status:** Not Started | In Progress | In Review | Done
**Priority:** High | Medium | Low

**Description:**
[Detailed task description]

**Files Changed:**
- `path/to/file1.tsx`
- `path/to/file2.py`

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Testing:**
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Manual testing completed

**Estimate:** X hours
**Actual:** X hours

**Notes:**
[Any additional notes, blockers, or dependencies]
```

### Code Review Checklist

**Functionality:**
- [ ] Code implements requirements as specified
- [ ] All acceptance criteria met
- [ ] Edge cases handled
- [ ] Error handling implemented

**Code Quality:**
- [ ] Code follows existing patterns and conventions
- [ ] No code duplication (DRY principle)
- [ ] Functions/components have single responsibility
- [ ] Meaningful variable/function names
- [ ] Comments added for complex logic

**Performance:**
- [ ] Expensive operations memoized
- [ ] React Query caching configured correctly
- [ ] No unnecessary re-renders
- [ ] Images optimized

**Accessibility:**
- [ ] Semantic HTML used
- [ ] ARIA labels where appropriate
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Color contrast sufficient

**Testing:**
- [ ] Unit tests written and passing
- [ ] Integration tests written and passing
- [ ] Manual testing completed
- [ ] Accessibility tests passed

**Documentation:**
- [ ] Code comments added where needed
- [ ] README updated (if applicable)
- [ ] API documentation updated (if applicable)
- [ ] CHANGELOG updated

### Glossary

**Terms:**

- **Auto-close:** Modal automatically closes after successful form submission
- **Contributor:** Valuation rule with non-zero adjustment amount
- **Entity Link:** Clickable link to CPU, GPU, RAM, or Storage detail page
- **Entity Tooltip:** Hover card displaying detailed entity information
- **Hero Section:** Top section of detail page with image and summary cards
- **Highlight Animation:** 2-second pulse animation applied to newly created listing
- **Inactive Rule:** Valuation rule with zero adjustment amount (did not match)
- **RuleGroup:** Logical grouping of valuation rules (e.g., "Hardware", "Time-based")
- **SSR:** Server-Side Rendering (Next.js App Router)
- **Valuation Breakdown:** Complete list of all rules and adjustments applied to a listing

---

**End of Implementation Plan**

**Version History:**
- v1.0 (2025-10-22): Initial implementation plan

**Review & Approval:**
- Technical Lead: [Pending]
- Product Owner: [Pending]
- Backend Engineer: [Pending]
- Frontend Engineer: [Pending]
