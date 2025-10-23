# Feature Requirements: Rich Detail Page

**Status:** Draft
**Priority:** High
**Affects:** Listing visibility, user engagement, information discovery

---

## Overview

Transform the basic detail page (`/listings/[id]`) into a comprehensive, visually engaging product showcase featuring a hero section with product images and summary cards, tabbed content navigation, entity links with hover tooltips, and responsive design across all screen sizes.

---

## User Story

As a Deal Brain user, I want to view a comprehensive, visually rich detail page for each listing with product images, tabbed sections, and interactive entity relationships, so that I can fully evaluate a product without navigating away or opening multiple pages.

---

## Page Requirements

### Page Route & Metadata

1. Accessible at `/listings/[id]`
2. Server-side rendered (Next.js App Router)
3. Returns 404 if listing not found
4. Meta tags populated with listing title and description (SEO)

### Header Section

1. Full listing title (prominent, h1 typography)
2. Breadcrumb navigation: Dashboard > Listings > [Title]
3. Quick actions: Edit, Delete, Duplicate (icon buttons)
4. Status badge (Available, Sold, Archived, etc.)

### Hero Section

**Left Column:**
- Product image (responsive, max 400px width on desktop)
- Source priority: `thumbnail_url` → manufacturer-based icon → generic PC icon
- Image alt text from listing title
- Rounded corners, border, shadow
- Loading skeleton while fetching

**Right Column:**
- Summary cards grid with key details:
  - Price card: List price, adjusted price, savings (color-coded)
  - Performance card: Composite score, CPU marks, perf/watt
  - Hardware card: CPU, GPU, RAM, Storage summary
  - Condition card: Condition, seller, status

### Tabbed Content Section

1. Tab navigation: Specifications | Valuation | History | Notes
2. Tab content area with consistent padding
3. Tab state persisted in URL query param: `/listings/123?tab=valuation`
4. Default tab: Specifications

### Responsive Design

- **Desktop (≥1024px):** Two-column layout (image left, summary right)
- **Tablet (768-1023px):** Two-column stacked (image top, summary bottom)
- **Mobile (<768px):** Single column, image full-width

---

## Tab Requirements

### Specifications Tab

**Content Organization:**

1. **Hardware Section:** CPU, GPU, RAM, Primary Storage, Secondary Storage, Ports
2. **Product Details:** Manufacturer, Series, Model Number, Form Factor
3. **Listing Info:** Seller, Listing URL, Other URLs, Condition, Status
4. **Performance Metrics:** All computed scores and efficiency metrics
5. **Metadata:** Created At, Updated At timestamps
6. **Custom Fields:** All custom field values from `attributes` object

**Entity Relationships (Clickable):**

- CPU name → link to `/catalog/cpus/[id]`
- GPU name → link to `/catalog/gpus/[id]`
- RAM Spec → link to `/catalog/ram-specs/[id]`
- Storage Profile → link to `/catalog/storage-profiles/[id]`
- Ports Profile → inline expansion showing all ports

**Hover Tooltips:**

- CPU hover: cores, threads, TDP, CPU marks
- GPU hover: VRAM, TDP, performance tier
- RAM Spec hover: module count, speed, DDR generation
- Storage Profile hover: interface, form factor, performance tier

**Data Handling:**

- Null values display as "—" or "Not specified"
- URLs display as clickable links with external link icon
- Ports display as compact badge list (e.g., "USB-C ×2, HDMI ×1")
- Custom fields render based on data type (text, number, select, boolean)

### Valuation Tab

1. Show same information as `ListingValuationTab` in modal
2. Display current valuation summary (base, adjusted, total adjustment)
3. Show top 4 contributing rules (matching modal filter logic)
4. Include ruleset override controls
5. "View Full Breakdown" button opens `ValuationBreakdownModal`
6. Full-width cards (not constrained by modal width)

### History Tab

1. Created timestamp: "Created on [date] at [time]"
2. Updated timestamp: "Last updated on [date] at [time]"
3. Future: audit log entries showing field changes
4. Empty state: "No history available for this listing."

### Notes Tab (Future)

1. Display: "Notes feature coming soon."
2. Future: Rich text editor for private notes with auto-save

---

## UI/UX Specifications

### Layout & Spacing

**Container Widths:**
- Max width: `max-w-7xl` (1280px)
- Responsive padding: `px-4 sm:px-6 lg:px-8`

**Hero Section:**
- Image: responsive, max 400px width on desktop
- Summary cards grid: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`
- Section spacing: `space-y-6` or `space-y-8`

**Specifications Section:**
- Grid layout: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3`
- Section headers: `text-lg font-semibold mb-4`

### Typography

- Page title (h1): `text-3xl font-bold tracking-tight`
- Section headers (h2): `text-lg font-semibold`
- Label text: `text-xs uppercase tracking-wide text-muted-foreground`
- Value text: `text-sm font-medium` or `text-base`

### Component Specs

**Summary Card:**
```tsx
<Card>
  <CardHeader>
    <div className="flex items-center gap-2">
      <Icon className="h-5 w-5 text-muted-foreground" />
      <CardTitle className="text-sm font-medium">Label</CardTitle>
    </div>
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">Value</div>
    <p className="text-xs text-muted-foreground mt-1">Subtitle</p>
  </CardContent>
</Card>
```

**Entity Link:**
- Color: `text-primary hover:underline`
- Keyboard accessible (Enter/Space triggers navigation)
- Optional tooltip on hover (200ms delay)

**Tabs:**
- Component: shadcn/ui Tabs
- Style: underline (default) or pills (optional)
- Spacing: `mb-6` below tab list

---

## Technical Considerations

### Server-Side Rendering

- Use Next.js `generateMetadata` for SEO
- Fetch full listing with all relationships (CPU, GPU, RAM spec, etc.)
- Use `notFound()` for missing listings
- Image optimization with Next.js `<Image>` component

### Fallbacks & Error Handling

- Fallback icons: HardDrive, Cpu, Monitor (lucide-react)
- Missing images: generic PC icon
- Missing entity relationships: graceful fallback text
- Null values: "—" or "Not specified"

### Performance

- Prefetch entity data for tooltips (include in main query)
- Use Radix UI HoverCard for tooltips
- Implement link prefetching for entity navigation
- Memoize computed values (port summaries, formatted dates)
- Handle circular references in attributes JSON gracefully

---

## Mockup Reference

### Detail Page Layout (Desktop)

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

---

## Implementation Tasks

See [Implementation Plan - Phases 4-6](../../IMPLEMENTATION_PLAN.md#phase-4-detail-page-foundation-week-3-4) for detailed tasks:

**Phase 4 - Foundation (Week 3-4):**
- TASK-401 to TASK-410: Detail page route, hero section, tabs, responsive design

**Phase 5 - Entity Links & Tooltips (Week 4-5):**
- TASK-501 to TASK-509: Entity links, tooltips, summary cards

**Phase 6 - Tabs (Week 5-6):**
- TASK-601 to TASK-611: Specifications, valuation, history tabs

---

## Success Criteria (QA)

- [ ] Backend endpoint returns listing with all relationships eager-loaded
- [ ] Page accessible at `/listings/[id]`
- [ ] Page returns 404 if listing not found
- [ ] SEO meta tags populated (title, description)
- [ ] Breadcrumb navigation functional
- [ ] Hero section displays with product image and layout
- [ ] Product image shows with appropriate fallback
- [ ] Tab navigation works with URL state persistence
- [ ] All tabs (Specifications, Valuation, History) functional
- [ ] Entity links trigger correct navigation
- [ ] Entity tooltips display on hover with correct data
- [ ] Responsive design verified across breakpoints (mobile, tablet, desktop)
- [ ] Loading skeleton displays during SSR
- [ ] Custom fields render based on data type
- [ ] Null values display appropriately
- [ ] Touch targets ≥ 44×44 pixels on mobile

---

## Related Documentation

- **[Implementation Plan - Phases 4-6](../../IMPLEMENTATION_PLAN.md#phase-4-detail-page-foundation-week-3-4)**
- **[Data Model - API Contracts](./data-model.md)** - Enhanced listing detail schema
- **[Technical Requirements](./technical.md)** - Component architecture, state management
- **[Design - UI/UX Specs](../design/ui-ux.md)** - Color palette, typography, component specs
- **[Accessibility Guidelines](../design/accessibility.md)** - WCAG AA compliance
