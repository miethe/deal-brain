# Product Requirements Document: Listings Detail Page & Modal Enhancement

**Version:** 1.0
**Date:** October 22, 2025
**Status:** Draft
**Author:** Documentation Team

---

## 1. Executive Summary

### 1.1 Overview

This PRD defines the requirements for a comprehensive enhancement of the Listings detail page and modal experiences in Deal Brain. The project addresses four key improvement areas: automatic modal closure after successful creation, intelligent valuation rule filtering, enhanced valuation breakdown displays, and a complete redesign of the detail page to provide a rich, comprehensive view of listing information.

### 1.2 Problem Statement

**Current Pain Points:**

1. **Manual Modal Dismissal:** After creating a new listing, users must manually close the creation modal before seeing their new entry in the list view, creating an unnecessary extra step
2. **Visual Clutter in Valuation Tab:** The valuation tab in the listing modal shows all rules (including those with zero contribution), making it difficult to identify which rules actually affected the price
3. **Limited Valuation Breakdown:** The full valuation breakdown screen doesn't clearly separate active contributors from inactive rules, lacks organizational context (RuleGroup/Ruleset labels), and doesn't provide navigation to rule details
4. **Basic Detail Page:** The dedicated detail page at `/listings/[id]` is minimal and doesn't leverage available rich data, including product images, entity relationships, full specifications, or interactive elements

**Business Impact:**

- Reduced workflow efficiency due to manual modal management
- Decreased ability to understand pricing adjustments quickly
- Missed opportunities to surface valuable product information
- Lower user engagement with listing details

### 1.3 Goals

**Primary Goals:**

1. **Streamlined Creation Workflow:** Auto-close creation modal and show new listing immediately
2. **Smart Valuation Display:** Show only relevant rules in modal, with clear visual hierarchy for contributors
3. **Comprehensive Breakdown View:** Provide complete rule visibility with organizational context and navigation
4. **Rich Detail Page:** Transform basic detail page into a comprehensive, visually appealing product showcase

**Secondary Goals:**

- Maintain WCAG AA accessibility compliance across all enhanced components
- Preserve existing performance optimizations (memoization, React Query caching)
- Ensure responsive design for all viewport sizes
- Create reusable patterns for entity detail displays (applicable to CPU, GPU, etc.)

### 1.4 Success Metrics

**Quantitative Metrics:**

- Creation modal auto-close success rate: 100%
- Time to see newly created listing: < 2 seconds (from save to view)
- Valuation tab rule count reduction: 50-75% (showing only contributors by default)
- Detail page engagement rate: > 40% increase in time spent on detail pages
- Entity link click-through rate: > 25% for clickable CPU/GPU/RAM links
- Valuation breakdown modal open rate: > 35% from detail page

**Qualitative Metrics:**

- Users express satisfaction with automatic workflow progression
- Valuation information is immediately understandable without training
- Detail page provides comprehensive product understanding
- Entity relationships are discoverable and navigable

### 1.5 Scope

**In Scope:**

- Auto-close creation modal with list refresh and new item highlight
- Smart rule filtering in modal valuation tab (max 4 contributors, hide zero-impact)
- Enhanced valuation breakdown modal with sorting and navigation
- Complete detail page redesign with tabbed layout
- Product image display (from URL or icon fallback)
- Clickable entity relationships with hover tooltips
- Summary cards with key specifications
- Valuation tab matching modal layout

**Out of Scope:**

- Listing editing from detail page (remains in table/grid views)
- Bulk listing operations from detail page
- Comparison features (multi-listing comparison)
- Price history tracking/visualization
- Seller profile pages
- Review/rating system
- GPU detail tooltips (separate PRD)

---

## 2. Feature Requirements

### 2.1 Auto-Close Creation Modal

#### 2.1.1 Modal Behavior Enhancement

**User Story:**

As a Deal Brain user, I want the creation modal to close automatically after I successfully create a new listing, so that I can immediately see my new listing in the list view without manual dismissal.

**Acceptance Criteria:**

1. **Successful Creation Flow:**
   - After successful API response (201 Created), modal automatically closes
   - List view automatically refreshes to include new listing
   - New listing is highlighted/scrolled into view (if not already visible)
   - Success toast notification displays: "Listing created successfully"

2. **Error Handling:**
   - On validation errors (400), modal remains open with error messages
   - On server errors (500), modal remains open with retry option
   - Network errors show appropriate error state without closing modal
   - Form data preserved if modal remains open for corrections

3. **User Feedback:**
   - Loading state visible during save operation
   - Optimistic UI updates (item appears before full refresh)
   - Smooth transition from modal close to list update
   - Visual indicator on newly created item (highlight animation, badge, etc.)

4. **Accessibility:**
   - Focus returns to appropriate location in list view (newly created item row)
   - Screen reader announces creation success
   - Keyboard navigation works throughout flow

**UI/UX Specifications:**

- **Close Animation:** 200ms fade-out for modal
- **List Refresh:** React Query invalidation triggers automatic refetch
- **Highlight Duration:** 2 seconds with subtle background color pulse
- **Scroll Behavior:** Smooth scroll if new item outside viewport
- **Toast Position:** Top-right, auto-dismiss after 3 seconds

**Technical Considerations:**

- Use React Query's `onSuccess` mutation callback for modal close
- Invalidate queries: `['listings', 'records']` and `['listings', 'count']`
- Store newly created listing ID for highlight targeting
- Use Zustand store or URL params for highlight state management
- Consider optimistic updates for perceived performance

**Edge Cases:**

- Multiple rapid creations (prevent race conditions)
- Creation while filters active (ensure new item visible or notify)
- Creation in paginated list (navigate to page containing new item)
- Concurrent edits by other users (show latest state)

---

### 2.2 Smart Rule Display in Valuation Tab

#### 2.2.1 Intelligent Rule Filtering

**User Story:**

As a Deal Brain user viewing a listing's valuation tab, I want to see only the rules that actually contributed to the price adjustment (up to 4 most significant), so that I can quickly understand what affected the price without visual clutter from inactive rules.

**Acceptance Criteria:**

1. **Rule Display Logic:**
   - Show maximum of 4 rules with non-zero adjustments
   - Sort by absolute adjustment amount (descending)
   - Display total count of hidden rules if more than 4 contributors exist
   - Show "No active rules" message if zero contributors

2. **Contributor Identification:**
   - Rule has non-zero `adjustment_amount` value
   - Display both positive (price increases) and negative (price decreases) adjustments
   - Color-code adjustments: green for savings (negative), red for premiums (positive)

3. **View All Option:**
   - "View Full Breakdown" button always visible
   - Opens `ValuationBreakdownModal` with all rules
   - Button shows count: "View Full Breakdown (12 rules)"

4. **Visual Design:**
   - Each rule card shows: name, adjustment amount, action count
   - Compact card layout optimized for 4-item display
   - Clear visual hierarchy (most impactful at top)
   - Consistent with existing modal design patterns

**UI/UX Specifications:**

- **Rule Card Layout:**
  - Border: rounded-md with border
  - Padding: p-3
  - Font: rule name (text-sm font-medium), amount (font-semibold)
  - Color: adjustment amounts use semantic colors

- **Sorting Priority:**
  1. Absolute adjustment amount (highest first)
  2. Rule name alphabetically (tiebreaker)

- **Empty State:**
  - Border-dashed card with muted text
  - Message: "No rule-based adjustments were applied to this listing."
  - No "View Full Breakdown" button if zero rules

**Technical Considerations:**

- Filter logic in `ListingValuationTab` component
- Memoize filtered/sorted results for performance
- Ensure adjustment amounts accurate (from API response)
- Handle null/undefined adjustment amounts gracefully

**Mockup Reference:**

```
┌─────────────────────────────────────────┐
│ Current valuation                        │
│ Calculated using Ruleset Alpha.          │
│                                           │
│ ┌─────────────────────────────────────┐ │
│ │ Base Price    Adjusted    Savings   │ │
│ │ $450.00       $375.00     -$75.00   │ │
│ └─────────────────────────────────────┘ │
│                                           │
│ ⚡ 4 rules applied                        │
│ [View Full Breakdown (12 rules)]         │
│                                           │
│ ┌─────────────────────────────────────┐ │
│ │ RAM Deduction - 16GB                │ │
│ │ 2 actions              -$50.00      │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ CPU Age Adjustment                  │ │
│ │ 1 action               -$25.00      │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Condition Factor - Refurbished      │ │
│ │ 1 action               +$10.00      │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Form Factor Premium - Mini PC       │ │
│ │ 1 action               -$10.00      │ │
│ └─────────────────────────────────────┘ │
│                                           │
│ + 8 more rules in breakdown              │
└─────────────────────────────────────────┘
```

---

### 2.3 Enhanced Valuation Breakdown Screen

#### 2.3.1 Comprehensive Rule Display

**User Story:**

As a Deal Brain user viewing the full valuation breakdown, I want to see all rules organized with contributors at the top and inactive rules below, with clear labels for RuleGroups/Rulesets and clickable rule names, so that I can fully understand the pricing logic and navigate to rule details.

**Acceptance Criteria:**

1. **Rule Organization:**
   - **Section 1: Contributors** - Rules with non-zero adjustments, sorted by absolute amount (descending)
   - **Section 2: Inactive Rules** - Rules with zero adjustment, sorted alphabetically by name
   - Section headers clearly label each category
   - Separator between sections

2. **Rule Card Enhancements:**
   - Display RuleGroup name (if rule belongs to a group): small badge/label
   - Display parent Ruleset name: contextual label or breadcrumb
   - Rule name is clickable (navigates to rule detail or edit page)
   - Hover state for clickable rule names
   - Tooltip on hover showing rule description (if available)

3. **Visual Indicators:**
   - Contributors: bold card border, prominent adjustment display
   - Inactive: muted border, gray text, collapsible (optional)
   - RuleGroup badge: subtle background, small text
   - Ruleset context: displayed in header or per-rule

4. **Interaction Design:**
   - Click rule name → navigate to `/valuation/rules/[id]`
   - Hover rule name → show tooltip with description
   - Click RuleGroup badge → filter to show only rules in that group (future)
   - Collapsible inactive section (expand/collapse toggle)

5. **Accessibility:**
   - All clickable elements keyboard accessible
   - Clear focus indicators on interactive elements
   - Screen reader announces section headers
   - ARIA labels for badges and interactive elements

**UI/UX Specifications:**

- **Section Headers:**
  - Typography: text-sm font-semibold uppercase tracking-wide text-muted-foreground
  - Margin: mt-6 mb-3 for section separation

- **Rule Cards:**
  - Contributor cards: border-2 (thicker), hover:bg-accent/5
  - Inactive cards: border (standard), text-muted-foreground
  - RuleGroup badge: Badge variant="outline" with small text
  - Ruleset: displayed in modal header ("Calculated using [Ruleset Name]")

- **Clickable Rule Names:**
  - Color: text-primary (inherit link color)
  - Hover: underline, cursor-pointer
  - Font: font-semibold for contributors, font-medium for inactive

- **Collapsible Inactive Section:**
  - Default state: collapsed if >10 inactive rules
  - Toggle: "Show 8 inactive rules" / "Hide inactive rules"
  - Animated expansion with smooth height transition

**Technical Considerations:**

- Extend `ValuationBreakdownModal` component
- Fetch rule metadata (group, ruleset) from API if not already included
- Modify `/v1/listings/{id}/valuation-breakdown` endpoint to include:
  - `rule_group_name` for each adjustment
  - `rule_description` for tooltips
- Use Next.js `Link` component for navigation
- Memoize sorting logic for performance
- Implement collapsible section with Radix UI Collapsible primitive

**API Changes Required:**

```typescript
// Enhanced ValuationAdjustment interface
interface ValuationAdjustment {
  rule_id?: number | null;
  rule_name: string;
  rule_description?: string | null;  // NEW
  rule_group_id?: number | null;     // NEW
  rule_group_name?: string | null;   // NEW
  adjustment_amount: number;
  actions: ValuationAdjustmentAction[];
}
```

**Mockup Reference:**

```
┌─────────────────────────────────────────────────────┐
│ Valuation Breakdown                                  │
│ Calculated using Ruleset: Production Rules v2        │
├─────────────────────────────────────────────────────┤
│                                                       │
│ [Image] Title: Intel NUC i7-1165G7 16GB              │
│         Listing ID #1234                             │
│         Base: $450 → Adjusted: $375 (-$75)           │
│                                                       │
├─────────────────────────────────────────────────────┤
│ ACTIVE CONTRIBUTORS (4)                              │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 RAM Deduction - 16GB    [Hardware] -$50.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Deduct $25 per 8GB RAM                    │   │
│ │    • Apply condition multiplier                │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 CPU Age Adjustment      [Time-based] -$25.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Deduct $5 per year since release         │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 Form Factor Premium     [Metadata]  -$10.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Add premium for Mini PC form factor      │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 Condition Factor        [Quality]   +$10.00│   │
│ │    Ruleset: Production Rules v2                │   │
│ │    • Refurbished: 102% of base               │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
├─────────────────────────────────────────────────────┤
│ ▼ INACTIVE RULES (8)                                 │
│                                                       │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🔗 Brand Premium Rule      [Metadata]    $0.00│   │
│ │    Did not match: manufacturer != 'Intel'     │   │
│ └───────────────────────────────────────────────┘   │
│                                                       │
│ [... 7 more collapsed ...]                           │
└─────────────────────────────────────────────────────┘
```

---

### 2.4 Complete Detail Page Redesign

#### 2.4.1 Page Layout & Structure

**User Story:**

As a Deal Brain user, I want to view a comprehensive, visually rich detail page for each listing with product images, tabbed sections, and interactive entity relationships, so that I can fully evaluate a product without navigating away or opening multiple pages.

**Acceptance Criteria:**

1. **Page Route:**
   - Accessible at `/listings/[id]`
   - Server-side rendered (Next.js App Router)
   - Returns 404 if listing not found
   - Meta tags populated with listing title and description

2. **Header Section:**
   - Full listing title (prominent, h1 typography)
   - Breadcrumb navigation: Dashboard > Listings > [Title]
   - Quick actions: Edit, Delete, Duplicate (icon buttons)
   - Status badge (Available, Sold, Archived, etc.)

3. **Hero Section:**
   - Left: Product image (responsive, max 400px width on desktop)
     - Source priority: `thumbnail_url` → manufacturer-based icon → generic PC icon
     - Image alt text from listing title
     - Rounded corners, border, shadow
   - Right: Summary cards with key details
     - Price card: List price, adjusted price, savings (color-coded)
     - Performance card: Composite score, CPU marks, perf/watt
     - Hardware card: CPU, GPU, RAM, Storage summary
     - Condition card: Condition, seller, status

4. **Tabbed Content Section:**
   - Tab navigation: Specifications | Valuation | History | Notes
   - Tab content area with consistent padding
   - Tab state persisted in URL query param: `/listings/123?tab=valuation`

5. **Responsive Design:**
   - Desktop (≥1024px): Two-column layout (image left, summary right)
   - Tablet (768-1023px): Two-column stacked (image top, summary bottom)
   - Mobile (<768px): Single column, image full-width

**UI/UX Specifications:**

- **Header:**
  - Background: gradient or subtle pattern
  - Title: text-3xl font-bold tracking-tight
  - Breadcrumb: text-sm text-muted-foreground with separators

- **Product Image:**
  - Aspect ratio: 1:1 (square) or 4:3
  - Border radius: rounded-lg
  - Shadow: shadow-md
  - Loading: skeleton placeholder while fetching

- **Summary Cards:**
  - Grid: 2 columns on desktop, 1 on mobile
  - Card style: border, rounded, p-4
  - Icon indicators for each card type
  - Responsive text sizing

- **Tabs:**
  - Component: shadcn/ui Tabs
  - Style: underline (default) or pills (optional)
  - Spacing: mb-6 below tab list

**Technical Considerations:**

- Use Next.js `generateMetadata` for SEO
- Fetch full listing with all relationships (CPU, GPU, RAM spec, etc.)
- Use `notFound()` for missing listings
- Image optimization with Next.js `<Image>` component
- Fallback icons: HardDrive, Cpu, Monitor (lucide-react)
- Tab state via `useSearchParams` and `useRouter`

---

#### 2.4.2 Specifications Tab

**User Story:**

As a Deal Brain user, I want to see all listing specifications organized by category with clickable entity relationships, so that I can explore detailed information about components without leaving the detail page.

**Acceptance Criteria:**

1. **Content Organization:**
   - **Hardware Section:** CPU, GPU, RAM, Primary Storage, Secondary Storage, Ports
   - **Product Details:** Manufacturer, Series, Model Number, Form Factor
   - **Listing Info:** Seller, Listing URL, Other URLs, Condition, Status
   - **Performance Metrics:** All computed scores and efficiency metrics
   - **Metadata:** Created At, Updated At timestamps
   - **Custom Fields:** All custom field values from `attributes` object

2. **Entity Relationships (Clickable):**
   - CPU name → link to `/catalog/cpus/[id]`
   - GPU name → link to `/catalog/gpus/[id]`
   - RAM Spec → link to `/catalog/ram-specs/[id]`
   - Storage Profile → link to `/catalog/storage-profiles/[id]`
   - Ports Profile → inline expansion showing all ports

3. **Hover Tooltips:**
   - CPU name hover: show quick tooltip with cores, threads, TDP, CPU marks
   - GPU name hover: show quick tooltip with VRAM, TDP, performance tier
   - RAM Spec hover: show module count, speed, DDR generation
   - Storage Profile hover: show interface, form factor, performance tier

4. **Visual Design:**
   - Section headers: text-lg font-semibold mb-4
   - Spec rows: label (text-muted-foreground) and value (font-medium)
   - Grid layout: 2-3 columns on desktop, 1 on mobile
   - Clickable links: text-primary underline-offset-4 hover:underline

5. **Data Handling:**
   - Null values display as "—" or "Not specified"
   - URLs display as clickable links with external link icon
   - Ports display as compact badge list (e.g., "USB-C ×2, HDMI ×1")
   - Custom fields render based on data type (text, number, select, boolean)

**UI/UX Specifications:**

- **Section Layout:**
  ```
  ┌─────────────────────────────────────────────┐
  │ HARDWARE                                     │
  │ ┌──────────────┬──────────────┬───────────┐│
  │ │ CPU          │ GPU          │ RAM       ││
  │ │ i7-1165G7 🔗 │ Iris Xe 🔗   │ 16GB DDR4 ││
  │ └──────────────┴──────────────┴───────────┘│
  │ ┌──────────────┬──────────────────────────┐│
  │ │ Primary      │ Secondary                ││
  │ │ 512GB NVMe 🔗│ 1TB HDD 🔗                ││
  │ └──────────────┴──────────────────────────┘│
  │ Ports: USB-C ×2, USB-A ×4, HDMI ×1         │
  │                                              │
  │ PRODUCT DETAILS                              │
  │ ┌──────────────┬──────────────┬───────────┐│
  │ │ Manufacturer │ Form Factor  │ Series    ││
  │ │ Intel        │ Mini PC      │ NUC       ││
  │ └──────────────┴──────────────┴───────────┘│
  └─────────────────────────────────────────────┘
  ```

- **Tooltip Popover:**
  - Max width: 280px
  - Padding: p-3
  - Background: popover (from theme)
  - Trigger: hover after 200ms delay
  - Content: grid of label/value pairs

**Technical Considerations:**

- Prefetch entity data for tooltips (include in main query)
- Use Radix UI HoverCard for tooltips
- Implement link prefetching for entity navigation
- Memoize computed values (port summaries, formatted dates)
- Handle circular references in attributes JSON gracefully

---

#### 2.4.3 Valuation Tab

**User Story:**

As a Deal Brain user viewing the detail page, I want to see the same comprehensive valuation information available in the modal, so that I have a consistent experience regardless of how I access listing details.

**Acceptance Criteria:**

1. **Content Parity:**
   - Show same information as `ListingValuationTab` in modal
   - Display current valuation summary (base, adjusted, total adjustment)
   - Show top 4 contributing rules (matching modal filter logic)
   - Include ruleset override controls
   - "View Full Breakdown" button opens `ValuationBreakdownModal`

2. **Layout Differences:**
   - Full-width cards (not constrained by modal width)
   - Larger spacing for readability
   - Side-by-side layout for summary stats on desktop

3. **Interactive Elements:**
   - All modal interactions preserved (ruleset selection, enable/disable)
   - Save/reset buttons functional
   - Full breakdown modal opens on button click

4. **Data Synchronization:**
   - Changes made on detail page reflect in modal (and vice versa)
   - React Query cache invalidation ensures consistency
   - Optimistic updates for responsive feel

**UI/UX Specifications:**

- **Layout:** Same card-based design as modal, but full-width
- **Summary Cards:** 3-column grid on desktop (base, adjusted, savings)
- **Rule Cards:** Max 4 visible, same styling as modal
- **Override Controls:** Same toggle and select UI as modal

**Technical Considerations:**

- Reuse `ListingValuationTab` component directly
- Pass `listing` prop from page component
- Ensure React Query keys match between page and modal
- Test override functionality from both contexts

---

#### 2.4.4 History Tab

**User Story:**

As a Deal Brain user, I want to see the history of changes to a listing, so that I can track price changes, status updates, and modifications over time.

**Acceptance Criteria:**

1. **Timeline Display:**
   - Created timestamp: "Created on [date] at [time]"
   - Updated timestamp: "Last updated on [date] at [time]"
   - Future: audit log entries showing field changes

2. **Price History:**
   - If price changed: show previous prices with dates
   - Visual chart/graph of price over time (future enhancement)
   - Current state: show only current timestamps

3. **Status Changes:**
   - Current status: Available, Sold, Archived, etc.
   - Future: timeline of status transitions

4. **Empty State:**
   - If no history beyond creation: "No history available for this listing."
   - Placeholder for future audit log features

**UI/UX Specifications:**

- **Timeline:** Vertical line with dots for events
- **Event Cards:** Date/time, description, changed fields
- **Typography:** text-sm for dates, text-base for descriptions

**Technical Considerations:**

- Phase 1: Display only created_at and updated_at
- Phase 2: Implement audit logging (separate feature)
- Use shadcn/ui Timeline component (or build custom)

---

#### 2.4.5 Notes Tab (Future)

**User Story:**

As a Deal Brain user, I want to add private notes to a listing, so that I can track my thoughts, questions, or research findings.

**Acceptance Criteria:**

1. **Note Editor:**
   - Rich text editor (Markdown or WYSIWYG)
   - Auto-save on blur or manual save button
   - Character limit: 5000 characters

2. **Note Display:**
   - Rendered Markdown if using Markdown editor
   - Formatted HTML if using WYSIWYG

3. **Empty State:**
   - Placeholder: "No notes yet. Click to add notes."

**UI/UX Specifications:**

- **Editor:** Textarea with toolbar (if rich text)
- **Save State:** Auto-save indicator, last saved timestamp

**Technical Considerations:**

- Phase 1: Not implemented (tab shows "Coming soon" message)
- Phase 2: Add `notes` field to Listing model, implement editor

---

## 3. Technical Requirements

### 3.1 Frontend Requirements

#### 3.1.1 Component Architecture

**New Components:**

```
apps/web/app/listings/[id]/
├── page.tsx                          # Main detail page (server component)
├── loading.tsx                       # Loading skeleton
└── not-found.tsx                     # 404 page

apps/web/components/listings/
├── detail-page-layout.tsx            # Layout wrapper with hero and tabs
├── specifications-tab.tsx            # Specifications tab content
├── valuation-tab-page.tsx            # Valuation tab (wraps existing component)
├── history-tab.tsx                   # History/audit log tab
├── entity-link.tsx                   # Reusable clickable entity link
├── entity-tooltip.tsx                # Reusable entity hover tooltip
├── product-image.tsx                 # Image with fallback handling
└── summary-card.tsx                  # Reusable summary card component
```

**Modified Components:**

```
apps/web/components/listings/
├── listing-valuation-tab.tsx         # Add rule filtering logic
├── valuation-breakdown-modal.tsx     # Add sorting, sections, clickable rules
└── listing-form-modal.tsx            # Add auto-close on success (if separate component)
```

#### 3.1.2 State Management

**React Query:**

- Cache listing detail: `['listing', 'detail', id]`
- Cache valuation breakdown: `['listing', 'valuation', id]`
- Cache entity details for tooltips: `['cpu', id]`, `['gpu', id]`, etc.
- Invalidation on save: all listing-related queries

**URL State:**

- Tab selection: `/listings/123?tab=valuation`
- Highlight new item: `/listings?highlight=123`

**Zustand Store (Optional):**

- Modal open/close state
- Recent listing IDs (for navigation)

#### 3.1.3 Data Fetching

**Server-Side (Detail Page):**

```typescript
// apps/web/app/listings/[id]/page.tsx
async function getListingDetail(id: string): Promise<ListingDetail> {
  const listing = await apiFetch<ListingDetail>(`/v1/listings/${id}`);
  // Prefetch related entities for tooltips
  return listing;
}
```

**Client-Side (Tooltips, Modals):**

```typescript
// Entity tooltip data fetching
const { data: cpu } = useQuery({
  queryKey: ['cpu', cpuId],
  queryFn: () => apiFetch(`/v1/cpus/${cpuId}`),
  enabled: isHovered && !!cpuId,
  staleTime: 10 * 60 * 1000, // 10 minutes
});
```

### 3.2 Backend Requirements

#### 3.2.1 API Endpoint Enhancements

**Enhanced Listing Detail Endpoint:**

```
GET /v1/listings/{id}
```

**Response Includes:**

- Full listing with all relationships eager-loaded
- CPU with all fields (for tooltip data)
- GPU with all fields
- RAM Spec with all fields
- Storage Profiles (primary and secondary) with all fields
- Ports Profile with ports array
- Valuation breakdown (or separate endpoint call)

**Example Response:**

```json
{
  "id": 123,
  "title": "Intel NUC i7-1165G7 16GB 512GB",
  "price_usd": 450.00,
  "adjusted_price_usd": 375.00,
  "thumbnail_url": "https://example.com/image.jpg",
  "seller": "TechDeals",
  "status": "available",
  "condition": "refurbished",
  "manufacturer": "Intel",
  "series": "NUC",
  "model_number": "NUC11PAHi7",
  "form_factor": "mini_pc",
  "cpu": {
    "id": 45,
    "name": "Intel Core i7-1165G7",
    "manufacturer": "Intel",
    "cores": 4,
    "threads": 8,
    "tdp_w": 28,
    "cpu_mark_multi": 10500,
    "cpu_mark_single": 3200,
    "igpu_model": "Intel Iris Xe Graphics",
    "igpu_mark": 1800,
    "release_year": 2020
  },
  "gpu": null,
  "ram_spec": {
    "id": 12,
    "label": "16GB DDR4-3200",
    "ddr_generation": "DDR4",
    "speed_mhz": 3200,
    "module_count": 2,
    "capacity_per_module_gb": 8,
    "total_capacity_gb": 16
  },
  "primary_storage_profile": {
    "id": 8,
    "label": "512GB NVMe SSD",
    "medium": "ssd",
    "interface": "nvme",
    "form_factor": "m.2",
    "capacity_gb": 512,
    "performance_tier": "high"
  },
  "ports_profile": {
    "id": 5,
    "name": "NUC Standard Ports",
    "ports": [
      {"port_type": "usb-c", "quantity": 2, "version": "3.2"},
      {"port_type": "usb-a", "quantity": 4, "version": "3.0"},
      {"port_type": "hdmi", "quantity": 1, "version": "2.0"},
      {"port_type": "ethernet", "quantity": 1, "version": "gigabit"}
    ]
  },
  "valuation_breakdown": {
    "listing_price": 450.00,
    "adjusted_price": 375.00,
    "total_adjustment": -75.00,
    "matched_rules_count": 12,
    "ruleset": {"id": 1, "name": "Production Rules v2"},
    "adjustments": [
      {
        "rule_id": 10,
        "rule_name": "RAM Deduction - 16GB",
        "rule_description": "Deduct value for RAM capacity",
        "rule_group_id": 2,
        "rule_group_name": "Hardware",
        "adjustment_amount": -50.00,
        "actions": [
          {
            "action_type": "deduct_fixed",
            "metric": "ram_gb",
            "value": -50.00
          }
        ]
      }
      // ... more adjustments
    ]
  },
  "attributes": {
    "custom_field_1": "value",
    "warranty_months": 12
  },
  "created_at": "2025-10-15T14:30:00Z",
  "updated_at": "2025-10-20T09:15:00Z"
}
```

**Valuation Breakdown Endpoint Enhancement:**

```
GET /v1/listings/{id}/valuation-breakdown
```

**Changes:**

- Add `rule_description`, `rule_group_id`, `rule_group_name` to adjustments
- Ensure all inactive rules included (with zero adjustment amounts)

**Backend Implementation:**

```python
# apps/api/dealbrain_api/services/listings.py

async def get_listing_detail_with_relationships(
    session: AsyncSession,
    listing_id: int
) -> Listing:
    """
    Fetch listing with all relationships eager-loaded.
    """
    stmt = (
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.cpu),
            selectinload(Listing.gpu),
            selectinload(Listing.ram_spec),
            selectinload(Listing.primary_storage_profile),
            selectinload(Listing.secondary_storage_profile),
            selectinload(Listing.ports_profile).selectinload(PortsProfile.ports)
        )
    )
    result = await session.execute(stmt)
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
```

#### 3.2.2 Database Schema Changes

**No schema changes required.** All necessary fields already exist in the database.

**Optional Future Enhancement:**

```sql
-- Audit log table for history tab
CREATE TABLE listing_history (
  id SERIAL PRIMARY KEY,
  listing_id INTEGER REFERENCES listings(id) ON DELETE CASCADE,
  changed_by VARCHAR(255),
  changed_at TIMESTAMP DEFAULT NOW(),
  field_name VARCHAR(100),
  old_value TEXT,
  new_value TEXT,
  change_type VARCHAR(50)
);
```

### 3.3 Performance Requirements

#### 3.3.1 Loading Performance

- **Time to First Byte (TTFB):** < 200ms for detail page
- **First Contentful Paint (FCP):** < 1.5 seconds
- **Largest Contentful Paint (LCP):** < 2.5 seconds
- **Modal open time:** < 100ms (cached data)
- **Valuation breakdown load:** < 500ms (API call)

#### 3.3.2 Optimization Strategies

- Server-side render detail page (Next.js App Router)
- Prefetch related entities during initial load
- Memoize expensive computations (rule sorting, filtering)
- React Query caching with 5-minute stale time
- Image optimization with Next.js Image component
- Code splitting for tabs (lazy load content)

### 3.4 Accessibility Requirements

#### 3.4.1 WCAG AA Compliance

- **Keyboard Navigation:**
  - All interactive elements accessible via Tab
  - Modal dialogs trap focus appropriately
  - Links have visible focus indicators
  - Skip links for main content

- **Screen Reader Support:**
  - Semantic HTML (nav, main, article, section)
  - ARIA labels for icon buttons
  - ARIA live regions for dynamic content (toasts, loading states)
  - Alt text for all images

- **Visual Accessibility:**
  - Color contrast ratio ≥ 4.5:1 for text
  - Color not sole indicator of information (use icons + color)
  - Resizable text up to 200% without loss of functionality
  - Touch targets ≥ 44×44 pixels

#### 3.4.2 Testing Requirements

- Automated testing with axe-core
- Manual keyboard navigation testing
- Screen reader testing (NVDA, JAWS, VoiceOver)
- Color contrast verification with tools

---

## 4. User Experience Requirements

### 4.1 User Flows

#### 4.1.1 Creation Flow

```
User fills listing form
  ↓
Clicks "Create Listing" button
  ↓
Loading state: button disabled, spinner visible
  ↓
API request succeeds (201)
  ↓
Success toast appears: "Listing created successfully"
  ↓
Modal closes automatically (200ms fade)
  ↓
List view refreshes (React Query invalidation)
  ↓
New listing appears, highlighted (2s animation)
  ↓
Focus moves to new listing row
```

#### 4.1.2 Detail Page Navigation Flow

```
User clicks listing title in table/grid
  ↓
Navigate to /listings/[id]
  ↓
Loading skeleton displays
  ↓
Server renders page with data
  ↓
Hero section displays (image + summary cards)
  ↓
Specifications tab active by default
  ↓
User clicks entity link (e.g., CPU name)
  ↓
Navigate to /catalog/cpus/[id]
```

#### 4.1.3 Valuation Exploration Flow

```
User views listing detail page
  ↓
Clicks "Valuation" tab
  ↓
Tab content loads (shows top 4 rules)
  ↓
User clicks "View Full Breakdown (12 rules)"
  ↓
Modal opens with all rules
  ↓
Contributors section at top (4 rules)
  ↓
Inactive section below (8 rules, collapsed)
  ↓
User clicks rule name
  ↓
Navigate to /valuation/rules/[id]
```

### 4.2 Error Handling

#### 4.2.1 Creation Errors

**Validation Errors (400):**
- Modal remains open
- Error messages display inline below fields
- Form scrolls to first error
- Focus moves to first error field

**Server Errors (500):**
- Modal remains open
- Toast: "Server error. Please try again."
- Retry button enabled
- Error details logged to console

**Network Errors:**
- Modal remains open
- Toast: "Network error. Check your connection."
- Retry button enabled

#### 4.2.2 Detail Page Errors

**Listing Not Found (404):**
- Display custom 404 page
- Message: "Listing not found or has been deleted."
- Link back to listings table
- Search box to find other listings

**API Errors:**
- Display error state in content area
- Message: "Unable to load listing details."
- Retry button
- Link back to listings table

### 4.3 Responsive Design Breakpoints

**Desktop (≥1024px):**
- Two-column hero layout (image left, summary right)
- Three-column summary cards
- Full-width content area (max-w-7xl)

**Tablet (768px - 1023px):**
- Two-column hero (image top, summary bottom)
- Two-column summary cards
- Reduced spacing/padding

**Mobile (<768px):**
- Single column layout
- Image full-width
- Single column summary cards
- Stacked tabs (scrollable if needed)
- Larger touch targets

---

## 5. Design Specifications

### 5.1 Visual Design

#### 5.1.1 Color Palette

**Valuation Color Coding:**
- **Great Deal (savings ≥ threshold):** `text-emerald-600` (green)
- **Good Deal (savings < threshold):** `text-blue-600` (blue)
- **Premium (price increase):** `text-red-600` (red)
- **Neutral (no change):** `text-muted-foreground` (gray)

**Status Badges:**
- Available: `bg-green-100 text-green-800`
- Sold: `bg-gray-100 text-gray-800`
- Archived: `bg-yellow-100 text-yellow-800`
- Draft: `bg-blue-100 text-blue-800`

**Interactive Elements:**
- Links: `text-primary hover:underline`
- Hover cards: `bg-accent/5 border-accent`
- Focus: `ring-2 ring-offset-2 ring-ring`

#### 5.1.2 Typography

**Headings:**
- Page title (h1): `text-3xl font-bold tracking-tight`
- Section headers (h2): `text-2xl font-semibold`
- Subsection headers (h3): `text-lg font-semibold`
- Card titles (h4): `text-base font-semibold`

**Body Text:**
- Default: `text-sm` or `text-base`
- Muted: `text-sm text-muted-foreground`
- Emphasis: `font-medium` or `font-semibold`

**Data Display:**
- Labels: `text-xs uppercase tracking-wide text-muted-foreground`
- Values: `text-sm font-medium` or `text-base`
- Metrics: `text-lg font-semibold` or `text-2xl font-bold`

#### 5.1.3 Spacing & Layout

**Container Widths:**
- Max width: `max-w-7xl` (1280px)
- Modal max width: `max-w-3xl` (768px)
- Valuation breakdown modal: `max-w-3xl`

**Padding/Margin:**
- Section spacing: `space-y-6` or `space-y-8`
- Card padding: `p-4` or `p-6`
- Content padding: `px-4 sm:px-6 lg:px-8`

**Grid Layouts:**
- Summary cards: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`
- Specifications: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3`

### 5.2 Component Specifications

#### 5.2.1 Summary Card

**Structure:**
```tsx
<Card>
  <CardHeader>
    <div className="flex items-center gap-2">
      <Icon className="h-5 w-5 text-muted-foreground" />
      <CardTitle className="text-sm font-medium">Label</CardTitle>
    </div>
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">$450.00</div>
    <p className="text-xs text-muted-foreground mt-1">Subtitle</p>
  </CardContent>
</Card>
```

**Variants:**
- Price card (currency icon, green/red color coding)
- Performance card (zap icon, numeric scores)
- Hardware card (cpu icon, component list)
- Metadata card (info icon, status/condition)

#### 5.2.2 Entity Link

**Structure:**
```tsx
<EntityLink
  type="cpu"
  id={45}
  name="Intel Core i7-1165G7"
  showTooltip={true}
/>
```

**Props:**
```typescript
interface EntityLinkProps {
  type: 'cpu' | 'gpu' | 'ram_spec' | 'storage_profile' | 'ports_profile';
  id: number;
  name: string;
  showTooltip?: boolean;
  className?: string;
}
```

**Behavior:**
- Click → navigate to entity detail page
- Hover (if `showTooltip` true) → show tooltip after 200ms
- Keyboard: Enter/Space triggers navigation

#### 5.2.3 Entity Tooltip

**Structure:**
```tsx
<HoverCard>
  <HoverCardTrigger asChild>
    <button>Hover me</button>
  </HoverCardTrigger>
  <HoverCardContent className="w-80">
    <div className="space-y-2">
      <h4 className="text-sm font-semibold">{entityName}</h4>
      <dl className="grid grid-cols-2 gap-2 text-xs">
        <dt className="text-muted-foreground">Label:</dt>
        <dd className="font-medium">Value</dd>
      </dl>
    </div>
  </HoverCardContent>
</HoverCard>
```

**Content by Entity Type:**

**CPU Tooltip:**
- Cores / Threads
- CPU Mark (Multi) / (Single)
- TDP
- iGPU Model / Mark
- Release Year

**GPU Tooltip:**
- VRAM
- TDP
- Performance Tier
- Release Year

**RAM Spec Tooltip:**
- DDR Generation
- Speed (MHz)
- Module Count × Capacity per Module
- Total Capacity

**Storage Profile Tooltip:**
- Medium (SSD/HDD)
- Interface
- Form Factor
- Performance Tier

---

## 6. Non-Functional Requirements

### 6.1 Performance

- **Page Load:** Detail page loads in < 2 seconds on 3G connection
- **Modal Open:** Breakdown modal opens in < 300ms
- **API Response Time:** Listing detail endpoint responds in < 500ms (p95)
- **Image Loading:** Progressive loading with blur placeholder

### 6.2 Security

- **Authorization:** Verify user has permission to view listing (if multi-tenant)
- **Input Validation:** Sanitize listing ID parameter to prevent injection
- **XSS Prevention:** Escape all user-generated content (notes, custom fields)
- **CORS:** API endpoints properly configured for Next.js frontend

### 6.3 Compatibility

**Browser Support:**
- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Mobile Safari (iOS 14+)
- Chrome Mobile (Android 10+)

**Screen Sizes:**
- Mobile: 375px - 767px
- Tablet: 768px - 1023px
- Desktop: 1024px - 1920px
- Ultra-wide: 1920px+

### 6.4 Scalability

- **Data Volume:** Support listings with 50+ valuation rules without performance degradation
- **Image Sizes:** Handle images up to 5MB with optimization
- **Custom Fields:** Support 20+ custom fields per listing
- **Concurrent Users:** Handle 100+ concurrent users viewing detail pages

---

## 7. Success Metrics

### 7.1 Adoption Metrics

**Creation Workflow:**
- **Target:** 95% of users complete creation workflow without manually closing modal
- **Measurement:** Track modal close events (auto vs manual)
- **Timeline:** Measure for 2 weeks post-launch

**Detail Page Engagement:**
- **Target:** 50% of listing views use detail page (vs. modal-only)
- **Measurement:** Page view analytics
- **Timeline:** Measure for 1 month post-launch

**Entity Navigation:**
- **Target:** 30% of detail page visits result in entity link clicks
- **Measurement:** Link click tracking
- **Timeline:** Measure for 1 month post-launch

### 7.2 Performance Metrics

**Page Load Performance:**
- **Target:** LCP < 2.5s for 75% of page loads
- **Measurement:** Core Web Vitals (via Vercel Analytics or Google Analytics)
- **Timeline:** Continuous monitoring

**API Performance:**
- **Target:** p95 response time < 500ms for listing detail endpoint
- **Measurement:** API monitoring (Prometheus/Grafana)
- **Timeline:** Continuous monitoring

### 7.3 Quality Metrics

**Accessibility:**
- **Target:** Zero critical accessibility violations (automated testing)
- **Measurement:** axe-core CI integration
- **Timeline:** Every deployment

**Error Rate:**
- **Target:** < 1% of detail page loads result in errors
- **Measurement:** Error tracking (Sentry or similar)
- **Timeline:** Continuous monitoring

---

## 8. Out of Scope

The following features are explicitly **out of scope** for this phase:

### 8.1 Editing Features
- Inline editing from detail page (remains in table/grid modals)
- Bulk editing of multiple listings
- Quick edit mode with auto-save

### 8.2 Advanced Valuation Features
- Historical valuation comparison
- "What-if" valuation scenarios
- Custom ruleset simulation from detail page

### 8.3 Social/Collaboration Features
- Comments/notes from multiple users
- Sharing listings via link with access control
- Watchlist/favorites functionality

### 8.4 Analytics Features
- Price trend charts over time
- Market comparison (similar listings)
- Seller reputation/history

### 8.5 Image Management
- Image upload from detail page
- Multiple image gallery
- Image editing/cropping

### 8.6 Export/Integration
- Export listing as PDF
- Share listing to external platforms
- Integration with external inventory systems

---

## 9. Dependencies

### 9.1 Technical Dependencies

**Required:**
- Next.js 14+ (App Router)
- React Query v5+
- Radix UI primitives (Dialog, Tabs, HoverCard, Collapsible)
- Tailwind CSS 3+
- shadcn/ui component library

**Optional:**
- Vercel Analytics (for performance monitoring)
- Sentry (for error tracking)
- Posthog (for user analytics)

### 9.2 API Dependencies

**Endpoints:**
- `GET /v1/listings/{id}` - Must include all relationships
- `GET /v1/listings/{id}/valuation-breakdown` - Enhanced with rule metadata
- `GET /v1/cpus/{id}` - For tooltip data
- `GET /v1/gpus/{id}` - For tooltip data
- `GET /v1/ram-specs/{id}` - For tooltip data
- `GET /v1/storage-profiles/{id}` - For tooltip data

**Backend Services:**
- Listings service with eager loading support
- Valuation service with rule metadata

### 9.3 Design Dependencies

**Assets Needed:**
- Placeholder images for manufacturers (Intel, AMD, etc.)
- Generic PC icons by form factor (mini, desktop, laptop)
- Icon set for specification categories (Lucide React already available)

### 9.4 Data Dependencies

**Required Data Quality:**
- CPU benchmark data populated (CPU Mark, Single-Thread)
- Valuation rules with descriptions
- RuleGroups properly assigned to rules
- Thumbnail URLs valid and accessible

---

## 10. Risk Assessment

### 10.1 Technical Risks

**Risk: Performance degradation with large valuation rulesets**
- **Likelihood:** Medium
- **Impact:** High
- **Mitigation:** Implement pagination or lazy loading for inactive rules section; benchmark with 100+ rules during development

**Risk: Image loading delays affecting LCP**
- **Likelihood:** High
- **Impact:** Medium
- **Mitigation:** Use Next.js Image component with blur placeholder; implement lazy loading for below-fold images; CDN for image hosting

**Risk: React Query cache inconsistency between page and modal**
- **Likelihood:** Medium
- **Impact:** Medium
- **Mitigation:** Use identical query keys; comprehensive cache invalidation strategy; integration tests for cache behavior

### 10.2 User Experience Risks

**Risk: Users confused by auto-close behavior**
- **Likelihood:** Low
- **Impact:** Low
- **Mitigation:** Clear success toast message; highlight new item; user testing before launch; option to disable in settings (future)

**Risk: Detail page too information-dense**
- **Likelihood:** Medium
- **Impact:** Medium
- **Mitigation:** Tabbed organization; progressive disclosure; user testing for information hierarchy

**Risk: Mobile experience cramped with complex layouts**
- **Likelihood:** Medium
- **Impact:** High
- **Mitigation:** Mobile-first design approach; responsive testing on real devices; simplified mobile layout variants

### 10.3 Data Risks

**Risk: Missing entity relationships break tooltips**
- **Likelihood:** Medium
- **Impact:** Low
- **Mitigation:** Graceful degradation (hide tooltip if no data); defensive null checks; clear fallback states

**Risk: Circular references in attributes JSON**
- **Likelihood:** Low
- **Impact:** Medium
- **Mitigation:** JSON stringify with error handling; max depth limit; schema validation on backend

### 10.4 Accessibility Risks

**Risk: Complex interactions not keyboard accessible**
- **Likelihood:** Medium
- **Impact:** High
- **Mitigation:** Comprehensive keyboard testing; Radix UI primitives (built-in accessibility); automated testing with axe-core

**Risk: Color-only indicators fail accessibility**
- **Likelihood:** Low
- **Impact:** High
- **Mitigation:** Always pair color with icons/text; contrast ratio verification; colorblind simulation testing

---

## 11. Implementation Phases

### 11.1 Phase 1: Auto-Close Modal (Week 1)

**Tasks:**
- Modify creation modal to auto-close on success
- Implement React Query cache invalidation
- Add highlight animation for new listings
- Focus management after modal close
- Testing: creation flow, error scenarios

**Deliverables:**
- Working auto-close behavior
- Unit tests for modal lifecycle
- Integration tests for creation flow

### 11.2 Phase 2: Smart Rule Display (Week 1-2)

**Tasks:**
- Add filtering logic to `ListingValuationTab`
- Implement max 4 rules display
- Sort by adjustment amount
- Update "View Full Breakdown" button with count
- Testing: various rule scenarios (0, 1, 4, 10+ rules)

**Deliverables:**
- Enhanced valuation tab UI
- Unit tests for filtering/sorting logic
- Visual regression tests

### 11.3 Phase 3: Enhanced Breakdown Modal (Week 2-3)

**Tasks:**
- Add section headers (contributors vs inactive)
- Implement sorting logic (amount desc, then alphabetical)
- Add RuleGroup badges
- Make rule names clickable
- Implement collapsible inactive section
- Backend: enhance API with rule metadata
- Testing: navigation, tooltips, collapsible behavior

**Deliverables:**
- Enhanced breakdown modal component
- Backend API changes deployed
- Integration tests for modal interactions

### 11.4 Phase 4: Detail Page Layout (Week 3-4)

**Tasks:**
- Create page route and layout components
- Implement hero section (image + summary cards)
- Add breadcrumb navigation
- Implement tab navigation with URL state
- Product image component with fallbacks
- Responsive design for all breakpoints
- Testing: responsive layouts, navigation

**Deliverables:**
- Basic detail page structure
- Responsive layout working
- SEO meta tags implemented

### 11.5 Phase 5: Specifications Tab (Week 4-5)

**Tasks:**
- Build specifications tab component
- Implement entity links
- Create entity tooltip components (CPU, GPU, RAM, Storage)
- Add custom fields display
- Testing: entity navigation, tooltips, data handling

**Deliverables:**
- Complete specifications tab
- Reusable entity link/tooltip components
- Unit tests for all entity types

### 11.6 Phase 6: Valuation & History Tabs (Week 5-6)

**Tasks:**
- Integrate `ListingValuationTab` into page
- Create history tab (basic version with timestamps)
- Test data synchronization between page and modal
- Testing: valuation overrides from page, history display

**Deliverables:**
- Working valuation tab on detail page
- Basic history tab
- Integration tests for data sync

### 11.7 Phase 7: Polish & Testing (Week 6-7)

**Tasks:**
- Accessibility audit and fixes
- Performance optimization (memoization, lazy loading)
- Cross-browser testing
- Mobile testing on real devices
- User acceptance testing
- Documentation updates

**Deliverables:**
- Accessibility compliance verified
- Performance targets met
- All tests passing
- User documentation

---

## 12. Appendix

### 12.1 Wireframes

**Detail Page Layout (Desktop):**

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo] Dashboard > Listings > Intel NUC...       [Edit] [Del] │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌─────────────────────────────────────────┐│
│  │              │  │ Price                  Performance       ││
│  │   Product    │  │ List: $450       ⚡ Composite: 85.3     ││
│  │    Image     │  │ Adjusted: $375      CPU Multi: 10500   ││
│  │   400×400    │  │ Savings: $75        CPU Single: 3200   ││
│  │              │  │                                          ││
│  └──────────────┘  │ Hardware               Metadata         ││
│                    │ 🖥️ i7-1165G7 🔗       📦 Refurbished    ││
│                    │ 🎨 Iris Xe 🔗         👤 TechDeals      ││
│                    │ 💾 16GB DDR4          ✅ Available       ││
│                    │ 💿 512GB NVMe 🔗                         ││
│                    └─────────────────────────────────────────┘│
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ [Specifications] [Valuation] [History] [Notes]           │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                           │ │
│  │  HARDWARE                                                │ │
│  │  ┌────────────┬────────────┬─────────────┐              │ │
│  │  │ CPU        │ GPU        │ RAM         │              │ │
│  │  │ i7-1165G7🔗│ Iris Xe🔗  │ 16GB DDR4🔗 │              │ │
│  │  └────────────┴────────────┴─────────────┘              │ │
│  │                                                           │ │
│  │  PRODUCT DETAILS                                         │ │
│  │  ┌────────────┬────────────┬─────────────┐              │ │
│  │  │ Mfr        │ Form       │ Series      │              │ │
│  │  │ Intel      │ Mini PC    │ NUC         │              │ │
│  │  └────────────┴────────────┴─────────────┘              │ │
│  │                                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

**Valuation Breakdown Modal (Enhanced):**

```
┌─────────────────────────────────────────────────────────┐
│ Valuation Breakdown                             [×]     │
│ Calculated using Ruleset: Production Rules v2           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [Thumbnail]  Intel NUC i7-1165G7 16GB                   │
│              Listing ID #123                            │
│              Base: $450 → Adjusted: $375 (-$75)         │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ACTIVE CONTRIBUTORS (4)                                 │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 🔗 RAM Deduction - 16GB         [Hardware]       │   │
│ │ Ruleset: Production Rules v2          -$50.00    │   │
│ │                                                   │   │
│ │ • Deduct $25 per 8GB RAM                         │   │
│ │ • Apply condition multiplier (0.95)              │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 🔗 CPU Age Adjustment           [Time-based]     │   │
│ │ Ruleset: Production Rules v2          -$25.00    │   │
│ │                                                   │   │
│ │ • Deduct $5 per year since release (2020)       │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ [... 2 more contributor cards ...]                      │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ▼ INACTIVE RULES (8)                                    │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 🔗 Brand Premium Rule           [Metadata]       │   │
│ │ Ruleset: Production Rules v2           $0.00     │   │
│ │                                                   │   │
│ │ ⚠️ Did not match: manufacturer != 'Dell'          │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ [... collapsed, click to expand ...]                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 12.2 Data Models

**Frontend TypeScript Interfaces:**

```typescript
// Enhanced Listing Detail
interface ListingDetail extends ListingRecord {
  cpu: CpuRecord | null;
  gpu: GpuRecord | null;
  ram_spec: RamSpecRecord | null;
  primary_storage_profile: StorageProfileRecord | null;
  secondary_storage_profile: StorageProfileRecord | null;
  ports_profile: PortsProfileRecord | null;
  valuation_breakdown: ValuationBreakdown | null;
}

// Enhanced Valuation Adjustment
interface ValuationAdjustment {
  rule_id?: number | null;
  rule_name: string;
  rule_description?: string | null;      // NEW
  rule_group_id?: number | null;         // NEW
  rule_group_name?: string | null;       // NEW
  adjustment_amount: number;
  actions: ValuationAdjustmentAction[];
}

// Entity Link Props
interface EntityLinkProps {
  type: 'cpu' | 'gpu' | 'ram_spec' | 'storage_profile' | 'ports_profile';
  id: number;
  name: string;
  showTooltip?: boolean;
  className?: string;
}

// Summary Card Props
interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'success' | 'warning' | 'error';
}
```

### 12.3 API Contracts

**GET /v1/listings/{id}**

**Request:**
```
GET /v1/listings/123
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 123,
  "title": "Intel NUC i7-1165G7 16GB 512GB",
  "price_usd": 450.00,
  "adjusted_price_usd": 375.00,
  "thumbnail_url": "https://cdn.example.com/listings/123.jpg",
  "seller": "TechDeals",
  "status": "available",
  "condition": "refurbished",
  "cpu": { /* full CPU object */ },
  "gpu": null,
  "ram_spec": { /* full RAM spec */ },
  "primary_storage_profile": { /* full storage profile */ },
  "ports_profile": { /* full ports profile with ports array */ },
  "valuation_breakdown": { /* full breakdown */ },
  "attributes": { /* custom fields */ },
  "created_at": "2025-10-15T14:30:00Z",
  "updated_at": "2025-10-20T09:15:00Z"
}
```

**GET /v1/listings/{id}/valuation-breakdown**

**Request:**
```
GET /v1/listings/123/valuation-breakdown
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "listing_id": 123,
  "listing_title": "Intel NUC i7-1165G7 16GB 512GB",
  "base_price_usd": 450.00,
  "adjusted_price_usd": 375.00,
  "total_adjustment": -75.00,
  "matched_rules_count": 12,
  "ruleset_id": 1,
  "ruleset_name": "Production Rules v2",
  "adjustments": [
    {
      "rule_id": 10,
      "rule_name": "RAM Deduction - 16GB",
      "rule_description": "Deduct value based on RAM capacity",
      "rule_group_id": 2,
      "rule_group_name": "Hardware",
      "adjustment_amount": -50.00,
      "actions": [
        {
          "action_type": "deduct_fixed",
          "metric": "ram_gb",
          "value": -25.00
        },
        {
          "action_type": "multiply",
          "metric": "condition_multiplier",
          "value": -25.00,
          "details": { "multiplier": 0.95 }
        }
      ]
    }
    // ... more adjustments
  ],
  "legacy_lines": []
}
```

### 12.4 Testing Scenarios

**Creation Flow Tests:**

1. **Happy path:** Create listing, modal auto-closes, listing appears highlighted
2. **Validation error:** Create with invalid data, modal stays open, errors shown
3. **Server error:** API returns 500, modal stays open, retry available
4. **Network error:** Connection fails, modal stays open, clear error message
5. **Rapid creation:** Create multiple listings quickly, no race conditions

**Valuation Display Tests:**

1. **Zero rules:** No rules applied, empty state shown
2. **One rule:** Single rule shown, no "more" indicator
3. **Four rules:** All four shown, no "more" indicator
4. **Ten rules:** Top 4 shown, "6 more in breakdown" indicator
5. **Mixed contributors:** Positive and negative adjustments sorted correctly

**Breakdown Modal Tests:**

1. **All contributors:** Rules sorted by absolute amount descending
2. **All inactive:** Inactive section shows all zero-adjustment rules
3. **Mixed:** Contributors at top, inactive below, separated
4. **Rule navigation:** Click rule name navigates to rule detail
5. **Collapsible:** Inactive section can expand/collapse

**Detail Page Tests:**

1. **Valid listing:** Page loads with all data displayed
2. **Missing relationships:** Null CPU/GPU handled gracefully
3. **Missing image:** Fallback icon shown
4. **Tab navigation:** URL updates, tab content changes
5. **Entity links:** Click CPU name navigates to CPU page
6. **Entity tooltips:** Hover shows correct data, no errors
7. **Responsive:** Layout adapts to mobile/tablet/desktop
8. **404:** Invalid listing ID shows error page

---

## 13. Acceptance Criteria Summary

**This project will be considered complete when:**

1. ✅ Creation modal auto-closes on success with visual confirmation
2. ✅ Valuation tab shows max 4 contributing rules with clear hierarchy
3. ✅ Breakdown modal organizes rules into contributors and inactive sections
4. ✅ Rule names are clickable and navigate to rule detail pages
5. ✅ Detail page displays comprehensive listing information with tabs
6. ✅ Product images load with appropriate fallbacks
7. ✅ Entity relationships are clickable with hover tooltips
8. ✅ All tabs (Specifications, Valuation, History) are functional
9. ✅ Responsive design works across all breakpoints (mobile, tablet, desktop)
10. ✅ Accessibility requirements met (WCAG AA, keyboard navigation, screen reader)
11. ✅ Performance targets achieved (LCP < 2.5s, API < 500ms p95)
12. ✅ All automated tests passing (unit, integration, accessibility)
13. ✅ Cross-browser testing completed (Chrome, Firefox, Safari)
14. ✅ User acceptance testing completed with no critical issues

---

**End of PRD**

**Version History:**
- v1.0 (2025-10-22): Initial draft

**Review & Approval:**
- Technical Lead: [Pending]
- Product Owner: [Pending]
- UX Designer: [Pending]
