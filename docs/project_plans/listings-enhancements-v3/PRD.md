# Deal Brain Listings Enhancements v3 - Product Requirements Document

**Version:** 1.0
**Created:** October 31, 2025
**Updated:** October 31, 2025
**Status:** Planning
**Owner:** Product & Engineering

---

## Executive Summary

This PRD outlines three critical enhancements to the Deal Brain listings system to improve performance, usability, and maintainability. These improvements directly address user feedback and technical debt while positioning the platform for future scale.

### Enhancement Areas

1. **Data Tab Performance Optimization** - Resolve performance degradation with large datasets
2. **Detail Page UX Improvements** - Enhanced clarity and usability for pricing metrics
3. **Image Management System** - Centralized, extensible configuration without code changes

### Business Impact

- **Performance:** Target 3x improvement in Data tab responsiveness with 500+ listings
- **User Experience:** Clearer pricing explanations increase user confidence and engagement
- **Maintainability:** Image management system reduces engineering overhead by 80%
- **Scalability:** Architecture supports growth to 10,000+ listings

### Success Metrics

- Data tab interaction latency < 200ms (P95) for datasets up to 1,000 listings
- 90% reduction in "how is this calculated?" support queries
- New manufacturer images added in < 5 minutes without deployments
- Zero regression in existing functionality

---

## Problem Statement

### Current Pain Points

**1. Data Tab Performance Degradation**

*User Impact:* Users report the Data tab on `/listings` becomes "very slow to respond" when viewing larger datasets. Interactions like sorting, filtering, and scrolling experience noticeable lag, particularly beyond 200 listings.

*Technical Debt:* While basic optimizations exist (memoization, debouncing), the component lacks advanced virtualization and efficient render strategies for large datasets. The 50-row default pagination helps but doesn't prevent performance issues during data processing.

**2. Unclear Adjusted Pricing**

*User Impact:* Users don't understand how "Adjusted Price" differs from list price or how valuations are calculated. The field name is confusing (price vs. value), and there's no contextual help.

*Current State:* Clicking the info button opens a full modal, which is heavyweight for quick reference. No hover tooltips explain the calculation inline.

**3. CPU Performance Metrics Layout**

*User Impact:* On `/listings/{id}` Specifications tab, CPU performance metrics are separated:
- Scores listed first
- $/CPU Mark fields listed separately below

This makes it hard to compare related metrics (e.g., Single-Thread Score vs. $/Single-Thread Mark).

*Missing Features:* Catalog cards show base/adjusted dual values, but detail page shows only one value per metric. Users can't see value improvement at a glance.

**4. Image Management Complexity**

*Developer Impact:* Adding manufacturer or form factor images requires:
1. Adding SVG files to `/apps/web/public/images/`
2. Updating hardcoded fallback logic in `ProductImageDisplay` component
3. Deploying code changes
4. Testing fallback hierarchy

*Inconsistency:* Image display differs between catalog cards and detail page hero sections, causing user confusion.

---

## Goals & Objectives

### Primary Goals

**G1: Performance Excellence**
- Achieve sub-200ms interaction latency on Data tab for 1,000+ listing datasets
- Maintain 60fps scroll performance with virtualization
- Reduce initial render time by 50%

**G2: Pricing Transparency**
- Rename "Adjusted Price" to "Adjusted Value" across entire application
- Provide inline contextual help via hover tooltips
- Explain valuation calculation without requiring modal navigation

**G3: Metrics Readability**
- Pair related CPU performance metrics for easy comparison
- Display base and adjusted values side-by-side
- Apply visual indicators (color coding) for deal quality

**G4: Image Management Simplicity**
- Enable non-developers to add manufacturer/form factor images
- Unify image display logic across catalog and detail pages
- Support image additions without code deployments

### Success Criteria

| Goal | Metric | Current | Target |
|------|--------|---------|--------|
| G1 | P95 interaction latency (1000 listings) | ~800ms | <200ms |
| G1 | Scroll FPS (virtualized) | Variable | 60fps |
| G2 | Support tickets (pricing questions) | 15/month | <2/month |
| G2 | Tooltip engagement rate | N/A | >40% |
| G3 | Time to compare metrics | ~8 sec | <3 sec |
| G4 | Time to add manufacturer image | ~30 min | <5 min |
| G4 | Code deployments for images | Required | Zero |

### Non-Goals

- Redesigning the entire listings UI (out of scope)
- Adding new performance metrics beyond existing fields
- Migrating to a different table library
- Supporting video/animated product media

---

## User Stories & Use Cases

### User Personas

**P1: Deal Hunter (Primary User)**
- Scans dozens of listings daily looking for best value
- Needs quick comparison of price-to-performance metrics
- Values transparency in pricing calculations

**P2: Content Manager (Secondary User)**
- Adds manufacturer/product images to improve catalog
- Non-technical, prefers UI-based workflows
- Frustrated by waiting for developers to add images

**P3: Power Analyst (Advanced User)**
- Works with 500+ listings in Data tab
- Performs bulk filtering, sorting, grouping operations
- Requires responsive interface for productivity

### Use Cases

#### UC1: High-Volume Data Analysis
**Actor:** Power Analyst
**Precondition:** 500+ listings in database
**Flow:**
1. User navigates to `/listings` → Data tab
2. User applies filters (form factor, price range, manufacturer)
3. User sorts by $/CPU Mark (adjusted)
4. User scrolls through results
5. User selects multiple rows for bulk edit

**Current Experience:** Steps 3-4 experience 500-800ms lag, scrolling is janky
**Target Experience:** All interactions < 200ms, smooth 60fps scrolling

**Acceptance Criteria:**
- [ ] Data tab supports 1,000 listings with <200ms interaction latency
- [ ] Virtualization enables smooth scrolling at 60fps
- [ ] Filtering/sorting completes in <150ms
- [ ] Column resize feels instantaneous

---

#### UC2: Understanding Adjusted Value
**Actor:** Deal Hunter
**Precondition:** Viewing listing with adjusted value different from list price
**Flow:**
1. User sees "Adjusted Value: $450" next to "List Price: $500"
2. User hovers over "Adjusted Value" field
3. Tooltip appears explaining calculation
4. User reads: "Adjusted based on 3 valuation rules: RAM deduction (-$30), Condition penalty (-$20), View full breakdown →"
5. User clicks link to open full modal (optional)

**Current Experience:** No tooltip; must click info button to open modal
**Target Experience:** Inline hover explanation with modal link

**Acceptance Criteria:**
- [ ] "Adjusted Price" renamed to "Adjusted Value" globally
- [ ] Tooltip appears on hover within 100ms
- [ ] Tooltip shows: calculation summary, rule count, link to modal
- [ ] Tooltip is accessible (keyboard navigable, screen reader compatible)
- [ ] Tooltip styling matches application design system

---

#### UC3: Comparing CPU Performance Metrics
**Actor:** Deal Hunter
**Precondition:** Viewing `/listings/{id}` Specifications tab
**Flow:**
1. User navigates to Compute section
2. User sees paired metrics:
   - **Single-Thread Score:** 3,450 | **$/Single-Thread Mark:** $0.12 → $0.10 (16% better)
   - **Multi-Thread Score:** 18,200 | **$/Multi-Thread Mark:** $0.025 → $0.022 (12% better)
3. User hovers over adjusted value ($0.10) to see tooltip
4. Tooltip explains: "Adjusted value based on condition and component quality"
5. User sees green color indicator (good deal threshold)

**Current Experience:** Metrics separated; only one value shown; no color coding
**Target Experience:** Side-by-side pairing with dual values and visual indicators

**Acceptance Criteria:**
- [ ] Single-Thread metrics appear on same row
- [ ] Multi-Thread metrics appear on same row
- [ ] Both base and adjusted values displayed for $/CPU Mark
- [ ] Percentage improvement/degradation shown
- [ ] Color coding applied based on configurable thresholds
- [ ] Tooltip on adjusted value explains calculation

---

#### UC4: Adding Manufacturer Images
**Actor:** Content Manager
**Precondition:** New manufacturer (e.g., "Minisforum") needs logo
**Flow:**
1. Content manager obtains manufacturer SVG logo
2. User uploads SVG to designated folder via file manager or UI
3. User references manufacturer name in configuration file
4. System automatically uses logo for all Minisforum listings
5. Fallback chain still works if logo missing

**Current Experience:** Requires developer to update code, commit, deploy
**Target Experience:** Self-service upload without code changes

**Acceptance Criteria:**
- [ ] Configuration file (JSON/YAML) maps manufacturers to image paths
- [ ] Images stored in organized directory structure
- [ ] Fallback hierarchy maintains backwards compatibility
- [ ] New images appear immediately (no deployment)
- [ ] Documentation guides non-technical users through process
- [ ] Support for manufacturer logos, form factor icons, series images

---

## Detailed Requirements

### 6.1 Data Tab Performance Optimization

#### Performance Benchmarks

| Dataset Size | Current P95 Latency | Target P95 Latency | Optimization Strategy |
|--------------|---------------------|--------------------|-----------------------|
| 100 listings | 150ms | <100ms | Memoization, lazy rendering |
| 500 listings | 600ms | <150ms | Virtualization, pagination |
| 1,000 listings | 1,200ms | <200ms | Full virtualization, chunked loading |
| 5,000 listings | N/A (untested) | <300ms | Backend pagination, aggressive caching |

#### Required Optimizations

**RO1: Table Virtualization**
- Implement row virtualization using `@tanstack/react-virtual` or similar
- Render only visible rows + overscan buffer (10 rows)
- Maintain scroll position during sort/filter operations
- Enable virtualization automatically when row count > 100

**RO2: Column Optimization**
- Lazy-load heavy columns (valuation breakdown, custom fields)
- Implement column-level memoization for expensive renders
- Debounce column resize to 150ms (already implemented)
- Cache computed column values in useMemo

**RO3: Data Processing Efficiency**
- Move filtering/sorting to backend for datasets > 500 rows
- Implement cursor-based pagination for large datasets
- Add indexing to frequently sorted columns (price, adjusted_price, cpu_mark)
- Use Web Workers for heavy client-side calculations

**RO4: Render Optimization**
- Ensure ValuationCell and DualMetricCell are memoized (already done)
- Implement shouldComponentUpdate checks for row components
- Use CSS containment for table rows (`contain: layout style paint`)
- Reduce DOM complexity in complex cells

**RO5: State Management**
- Debounce state updates (search, filters) to 200ms (already done)
- Batch setState calls in event handlers
- Use useTransition for non-urgent updates (React 18)
- Optimize localStorage persistence (debounce to 500ms)

#### Interaction Responsiveness Targets

- **Column sort:** <100ms (visual feedback), <200ms (completion)
- **Filter application:** <150ms
- **Row selection:** <50ms
- **Scroll:** 60fps (16.67ms per frame)
- **Column resize:** Feels instant with 150ms debounce

#### Monitoring & Metrics

- Add performance instrumentation using React Profiler
- Track render counts, render duration per component
- Log interaction latency to analytics
- Add /metrics endpoint for server-side pagination performance

---

### 6.2 Adjusted Value Renaming & Tooltips

#### UI/UX Specifications

**Field Naming Changes:**

| Current Term | New Term | Locations |
|--------------|----------|-----------|
| Adjusted Price | Adjusted Value | Detail page hero, Data tab column header, Specifications tab |
| adjusted_price_usd | (keep as-is) | Backend field name (no breaking change) |
| adjustedPrice | adjustedValue | Frontend TypeScript interfaces (optional aliasing) |

**Tooltip Specifications:**

**Trigger:** Hover over "Adjusted Value" label or value
**Delay:** 100ms hover delay before showing
**Position:** Above field (top placement), auto-adjust if near viewport edge
**Dismissal:** Mouse leave, Escape key

**Content Structure:**
```
┌────────────────────────────────────────────┐
│ Adjusted Value Calculation                 │
├────────────────────────────────────────────┤
│ List Price:        $500.00                 │
│ Adjustments:       -$50.00                 │
│ Adjusted Value:    $450.00 (10% savings)   │
│                                            │
│ Applied 3 valuation rules:                 │
│ • RAM deduction: -$30                      │
│ • Condition (Used): -$15                   │
│ • Missing storage: -$5                     │
│                                            │
│ [View Full Breakdown →]                    │
└────────────────────────────────────────────┘
```

**Implementation Notes:**
- Use existing tooltip component from UI library (shadcn/ui Tooltip)
- Content dynamically generated from `listing.valuation_breakdown` JSON
- Show top 3-5 rules by absolute impact
- Link opens existing ValuationBreakdownModal
- Tooltip max-width: 320px

**Component Updates Needed:**

1. **Detail Page Hero** (`/components/listings/detail-page-layout.tsx`)
   - Change "Adjusted Price" label to "Adjusted Value"
   - Wrap label/value in Tooltip trigger
   - Add tooltip content component

2. **Data Tab Column** (`/components/listings/listings-table.tsx`)
   - Rename column header to "Adjusted Value"
   - Add tooltip to header (explain column)
   - Maintain ValuationCell component functionality

3. **Specifications Tab** (`/components/listings/specifications-tab.tsx`)
   - Update any references to "Adjusted Price"
   - Add tooltips where adjusted values appear

4. **Valuation Tab** (`/components/listings/valuation-tab.tsx`)
   - Update terminology throughout
   - Ensure consistency with tooltip content

**Accessibility Requirements:**

- Tooltip triggerable via keyboard (focus on element, show on Enter/Space)
- Screen reader announces tooltip content via `aria-describedby`
- Tooltip has `role="tooltip"` and appropriate ARIA labels
- Link in tooltip is keyboard navigable
- Meets WCAG AA contrast requirements (4.5:1 for text)

---

### 6.3 CPU Performance Metrics Layout

#### Visual Layout Specification

**Current Layout (Specifications → Compute section):**

```
┌─────────────────────────────────────────┐
│ Compute                                 │
├─────────────────────────────────────────┤
│ CPU: Intel i5-12600K [dropdown]         │
│ GPU: Intel UHD 770                      │
│                                         │
│ Single-Thread Score: 3,450              │
│ Multi-Thread Score: 18,200              │
│                                         │
│ $/Single-Thread Mark: $0.12             │
│ $/Multi-Thread Mark: $0.025             │
└─────────────────────────────────────────┘
```

**Target Layout (Paired Metrics):**

```
┌─────────────────────────────────────────────────────────────────┐
│ Compute                                                         │
├─────────────────────────────────────────────────────────────────┤
│ CPU: Intel i5-12600K [dropdown]                                 │
│ GPU: Intel UHD 770                                              │
│                                                                 │
│ Single-Thread Performance                                       │
│ ├─ Score: 3,450                                                 │
│ └─ $/Mark: $0.12 → $0.10 (16% better) ℹ️                       │
│                                                                 │
│ Multi-Thread Performance                                        │
│ ├─ Score: 18,200                                                │
│ └─ $/Mark: $0.025 → $0.022 (12% better) ℹ️                     │
│                                                                 │
│ Overall Efficiency: 0.145 perf/watt                            │
└─────────────────────────────────────────────────────────────────┘
```

**Alternative Grid Layout:**

```
┌───────────────────────────────────────────────────────────────────────┐
│ Compute                                                               │
├───────────────────────────────────────────────────────────────────────┤
│ CPU: Intel i5-12600K [dropdown]  │  GPU: Intel UHD 770               │
│                                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Single-Thread                 │ Multi-Thread                    │ │
│ ├───────────────────────────────┼─────────────────────────────────┤ │
│ │ Score: 3,450                  │ Score: 18,200                   │ │
│ │ $/Mark: $0.12 → $0.10 ℹ️      │ $/Mark: $0.025 → $0.022 ℹ️      │ │
│ │ (16% better)                  │ (12% better)                    │ │
│ └───────────────────────────────┴─────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

**Recommendation:** Use hierarchical list layout for better mobile responsiveness.

#### Dual-Value Display Format

**Reuse Existing Component:** `DualMetricCell` (`/components/listings/dual-metric-cell.tsx`)

**Current Implementation:**
```typescript
<DualMetricCell
  raw={0.12}
  adjusted={0.10}
  prefix="$"
  decimals={3}
/>
// Renders: $0.120 / $0.100 (16.7% ↓)
```

**Adapt for Detail Page:**
- Larger font size (mobile-friendly)
- Horizontal layout instead of slash separator
- Add tooltip trigger on adjusted value
- Add color coding based on thresholds

**Proposed Component:**
```tsx
<PerformanceMetricDisplay
  label="$/Single-Thread Mark"
  baseValue={0.12}
  adjustedValue={0.10}
  thresholds={cpuMarkThresholds}
  tooltipContent="Adjusted based on condition and component quality"
/>
```

#### Tooltip Specifications

**Similar to Adjusted Value tooltip:**

```
┌──────────────────────────────────────────┐
│ Price-to-Performance Calculation         │
├──────────────────────────────────────────┤
│ Base Price:     $500.00                  │
│ CPU Mark:       3,450 (Single-Thread)    │
│ Base $/Mark:    $0.145                   │
│                                          │
│ Adjusted Price: $450.00                  │
│ Adjusted $/Mark: $0.130 (10% better)     │
│                                          │
│ Applied condition penalty: -$50          │
│                                          │
│ [View Full Breakdown →]                  │
└──────────────────────────────────────────┘
```

#### Color-Coding Thresholds

**Threshold Configuration (ApplicationSettings):**

Add new setting: `cpu_mark_thresholds`

```json
{
  "excellent": 20.0,    // ≥20% better than base
  "good": 10.0,         // 10-20% better
  "fair": 5.0,          // 5-10% better
  "neutral": 0.0,       // 0-5% better or worse
  "poor": -10.0,        // 10%+ worse
  "premium": -20.0      // 20%+ worse (significant premium)
}
```

**Color Mapping (Reuse Valuation Colors):**

| Threshold | Background | Text | Icon |
|-----------|------------|------|------|
| Excellent (≥20%) | Dark green | White | ⬇️ |
| Good (10-20%) | Medium green | Dark green | ⬇️ |
| Fair (5-10%) | Light green | Dark green | ⬇️ |
| Neutral (±5%) | Gray | Dark gray | ➖ |
| Poor (-10% to -5%) | Light red | Dark red | ⬆️ |
| Premium (<-10%) | Dark red | White | ⬆️ |

**CSS Variables (Add to Global Styles):**
```css
:root {
  --cpu-mark-excellent-bg: hsl(142, 71%, 25%);
  --cpu-mark-excellent-fg: hsl(0, 0%, 100%);
  --cpu-mark-good-bg: hsl(142, 71%, 45%);
  --cpu-mark-good-fg: hsl(142, 71%, 15%);
  --cpu-mark-fair-bg: hsl(142, 71%, 85%);
  --cpu-mark-fair-fg: hsl(142, 71%, 25%);
  --cpu-mark-neutral-bg: hsl(0, 0%, 90%);
  --cpu-mark-neutral-fg: hsl(0, 0%, 20%);
  --cpu-mark-poor-bg: hsl(0, 84%, 85%);
  --cpu-mark-poor-fg: hsl(0, 84%, 25%);
  --cpu-mark-premium-bg: hsl(0, 84%, 40%);
  --cpu-mark-premium-fg: hsl(0, 0%, 100%);
}
```

#### Settings Configuration Schema

**Backend (ApplicationSettings Model):**

Add migration to create default settings:

```python
# apps/api/alembic/versions/xxx_add_cpu_mark_thresholds.py

from alembic import op
from dealbrain_api.models.core import ApplicationSettings

def upgrade():
    # Add cpu_mark_thresholds setting
    op.execute(
        """
        INSERT INTO application_settings (key, value, description, created_at, updated_at)
        VALUES (
            'cpu_mark_thresholds',
            '{"excellent": 20.0, "good": 10.0, "fair": 5.0, "neutral": 0.0, "poor": -10.0, "premium": -20.0}',
            'Thresholds for color-coding CPU performance metrics (percentage improvement)',
            NOW(),
            NOW()
        )
        ON CONFLICT (key) DO NOTHING;
        """
    )
```

**Frontend (React Query Hook):**

```typescript
// apps/web/hooks/use-cpu-mark-thresholds.ts

export function useCpuMarkThresholds() {
  return useQuery<CpuMarkThresholds>({
    queryKey: ['settings', 'cpu_mark_thresholds'],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/settings/cpu_mark_thresholds`);
      if (!response.ok) return DEFAULT_CPU_MARK_THRESHOLDS;
      return response.json();
    },
    staleTime: 5 * 60 * 1000,
    placeholderData: DEFAULT_CPU_MARK_THRESHOLDS,
  });
}
```

---

### 6.4 Image Management System

#### Configuration File Format

**Proposed Format: JSON Configuration**

**Location:** `/apps/web/config/product-images.json`

**Schema:**
```json
{
  "version": "1.0",
  "baseUrl": "/images",
  "manufacturers": {
    "hpe": {
      "logo": "/manufacturers/hpe.svg",
      "fallback": "generic"
    },
    "minisforum": {
      "logo": "/manufacturers/minisforum.svg",
      "series": {
        "elitemini": "/manufacturers/minisforum/elitemini.svg",
        "um690": "/manufacturers/minisforum/um690.png"
      },
      "fallback": "generic"
    },
    "dell": {
      "logo": "/manufacturers/dell.svg",
      "series": {
        "optiplex": "/manufacturers/dell/optiplex.svg",
        "precision": "/manufacturers/dell/precision.svg"
      }
    }
  },
  "formFactors": {
    "mini_pc": {
      "icon": "/fallbacks/mini-pc-icon.svg",
      "generic": "/fallbacks/mini-pc-generic.svg"
    },
    "desktop": {
      "icon": "/fallbacks/desktop-icon.svg",
      "generic": "/fallbacks/desktop-generic.svg"
    },
    "sff": {
      "icon": "/fallbacks/sff-icon.svg"
    }
  },
  "cpuManufacturers": {
    "intel": "/fallbacks/intel.svg",
    "amd": "/fallbacks/amd.svg",
    "arm": "/fallbacks/arm.svg"
  },
  "fallbacks": {
    "generic": "/fallbacks/generic-pc.svg",
    "noImage": "/fallbacks/no-image.svg"
  }
}
```

**Alternative: YAML Format** (more readable for non-developers)

```yaml
version: 1.0
baseUrl: /images

manufacturers:
  hpe:
    logo: /manufacturers/hpe.svg
    fallback: generic

  minisforum:
    logo: /manufacturers/minisforum.svg
    series:
      elitemini: /manufacturers/minisforum/elitemini.svg
      um690: /manufacturers/minisforum/um690.png
    fallback: generic

formFactors:
  mini_pc:
    icon: /fallbacks/mini-pc-icon.svg
    generic: /fallbacks/mini-pc-generic.svg

cpuManufacturers:
  intel: /fallbacks/intel.svg
  amd: /fallbacks/amd.svg

fallbacks:
  generic: /fallbacks/generic-pc.svg
```

**Recommendation:** Use JSON for better TypeScript integration and validation.

#### Image Asset Organization

**Directory Structure:**

```
apps/web/public/images/
├── manufacturers/
│   ├── hpe.svg
│   ├── dell.svg
│   ├── lenovo.svg
│   ├── minisforum/
│   │   ├── logo.svg              (brand logo)
│   │   ├── elitemini.svg         (series image)
│   │   ├── um690.png             (specific model)
│   │   └── README.md             (series documentation)
│   └── README.md
├── form-factors/
│   ├── mini-pc.svg
│   ├── desktop.svg
│   ├── sff.svg
│   ├── rack-mount.svg
│   └── README.md
├── cpu-vendors/
│   ├── intel.svg
│   ├── amd.svg
│   ├── arm.svg
│   └── README.md
├── fallbacks/
│   ├── generic-pc.svg
│   ├── no-image.svg
│   └── README.md
└── config.json                    (image configuration)
```

**Image Requirements:**
- Format: SVG preferred (PNG/WebP for photos)
- Max size: 200KB per file
- Dimensions: 512x512px for logos, 1024x1024px for product images
- Naming: kebab-case (e.g., `elite-mini.svg`)

#### Fallback Hierarchy Specification

**Priority Order:**

1. **Listing-Specific Image**
   - `listing.thumbnail_url` (external URL from marketplace)
   - `listing.image_url` (external URL)

2. **Model-Specific Image**
   - Match `listing.model_number` to config manufacturer series
   - Example: Minisforum UM690 → `manufacturers.minisforum.series.um690`

3. **Series-Specific Image**
   - Match `listing.series` to config manufacturer series
   - Example: Dell OptiPlex → `manufacturers.dell.series.optiplex`

4. **Manufacturer Logo**
   - Match `listing.manufacturer` to config manufacturers
   - Example: HPE → `manufacturers.hpe.logo`

5. **CPU Vendor Logo**
   - Match `listing.cpu.manufacturer` to config cpuManufacturers
   - Example: Intel → `cpuManufacturers.intel`

6. **Form Factor Icon**
   - Match `listing.form_factor` to config formFactors
   - Example: Mini PC → `formFactors.mini_pc.icon`

7. **Generic Fallback**
   - `fallbacks.generic` (last resort)

**Logic Implementation:**

```typescript
// apps/web/lib/image-resolver.ts

import imageConfig from '@/config/product-images.json';

export function resolveProductImage(listing: ListingDetail): string {
  // 1. Listing-specific URLs
  if (listing.thumbnail_url) return listing.thumbnail_url;
  if (listing.image_url) return listing.image_url;

  const manufacturer = listing.manufacturer?.toLowerCase();
  const series = listing.series?.toLowerCase();
  const modelNumber = listing.model_number?.toLowerCase();

  // 2. Model-specific image
  if (manufacturer && modelNumber) {
    const modelImage = imageConfig.manufacturers[manufacturer]?.series?.[modelNumber];
    if (modelImage) return `${imageConfig.baseUrl}${modelImage}`;
  }

  // 3. Series-specific image
  if (manufacturer && series) {
    const seriesImage = imageConfig.manufacturers[manufacturer]?.series?.[series];
    if (seriesImage) return `${imageConfig.baseUrl}${seriesImage}`;
  }

  // 4. Manufacturer logo
  if (manufacturer) {
    const logoImage = imageConfig.manufacturers[manufacturer]?.logo;
    if (logoImage) return `${imageConfig.baseUrl}${logoImage}`;
  }

  // 5. CPU vendor logo
  if (listing.cpu?.manufacturer) {
    const cpuVendor = listing.cpu.manufacturer.toLowerCase();
    const cpuLogo = imageConfig.cpuManufacturers[cpuVendor];
    if (cpuLogo) return `${imageConfig.baseUrl}${cpuLogo}`;
  }

  // 6. Form factor icon
  if (listing.form_factor) {
    const formFactor = listing.form_factor.toLowerCase().replace(/\s+/g, '_');
    const formFactorImage = imageConfig.formFactors[formFactor]?.icon;
    if (formFactorImage) return `${imageConfig.baseUrl}${formFactorImage}`;
  }

  // 7. Generic fallback
  return `${imageConfig.baseUrl}${imageConfig.fallbacks.generic}`;
}
```

#### Adding New Images Workflow

**For Non-Technical Users:**

**Step 1: Prepare Image**
- Obtain manufacturer logo or product image (SVG preferred)
- Ensure image meets requirements (size, format, dimensions)
- Name file using kebab-case (e.g., `minisforum.svg`)

**Step 2: Upload Image**
- Navigate to `/images/manufacturers/` directory
- Upload SVG file via file manager or FTP

**Step 3: Update Configuration**
- Open `/config/product-images.json`
- Add entry under `manufacturers`:
  ```json
  "minisforum": {
    "logo": "/manufacturers/minisforum.svg"
  }
  ```
- Save file

**Step 4: Verify**
- Refresh listings page
- Manufacturer logo appears automatically for all Minisforum listings
- No code deployment required

**For Developers (CI/CD Pipeline):**
- Add validation step to check image file sizes
- Optimize SVGs automatically (SVGO)
- Generate WebP versions for PNGs
- Update config schema validation
- Run automated tests to ensure fallback chain works

#### Unified Image Display Component

**Consolidate Logic:** Update `ProductImageDisplay` to use `resolveProductImage()`

**Component Signature:**
```typescript
interface ProductImageDisplayProps {
  listing: ListingDetail | ListingRecord;
  size?: 'sm' | 'md' | 'lg' | 'xl';  // Responsive sizing
  variant?: 'card' | 'hero' | 'thumbnail';
  showLightbox?: boolean;
  className?: string;
}

export function ProductImageDisplay({
  listing,
  size = 'md',
  variant = 'card',
  showLightbox = false,
  className
}: ProductImageDisplayProps) {
  const imageSrc = resolveProductImage(listing);
  const [imgError, setImgError] = useState(false);

  // Handle error with next fallback
  // Show lightbox modal on click if enabled
  // Apply variant-specific styling
}
```

**Usage Consistency:**

```tsx
// Catalog card
<ProductImageDisplay
  listing={listing}
  size="md"
  variant="card"
/>

// Detail page hero
<ProductImageDisplay
  listing={listing}
  size="xl"
  variant="hero"
  showLightbox
/>

// Table thumbnail
<ProductImageDisplay
  listing={listing}
  size="sm"
  variant="thumbnail"
/>
```

#### Migration Plan

**Phase 1: Create Infrastructure**
1. Create `/apps/web/config/product-images.json`
2. Reorganize `/public/images/` directory structure
3. Move existing images to new structure
4. Create README.md files with instructions

**Phase 2: Update Code**
1. Implement `resolveProductImage()` utility
2. Update `ProductImageDisplay` component to use resolver
3. Add TypeScript types for config schema
4. Add validation for config file

**Phase 3: Testing**
1. Test all fallback scenarios
2. Verify backward compatibility
3. Test image loading performance
4. Validate accessibility (alt text, ARIA labels)

**Phase 4: Documentation**
1. Write user guide for adding images
2. Create developer documentation for config schema
3. Add inline comments in config file
4. Record video tutorial (optional)

**Phase 5: Deployment**
1. Deploy infrastructure changes
2. Migrate existing images
3. Update listings to use new system
4. Monitor for broken images

**Rollback Plan:**
- Keep old `ProductImageDisplay` logic as `ProductImageDisplayLegacy`
- Feature flag: `USE_IMAGE_CONFIG` (default: true)
- If issues arise, flip flag to false, revert to hardcoded logic

---

## Technical Considerations

### Architecture Patterns

**Frontend Architecture:**
- Component-based design with clear separation of concerns
- Hooks for reusable logic (useValuationThresholds, useCpuMarkThresholds, useImageResolver)
- Memoization for expensive renders (React.memo, useMemo, useCallback)
- Configuration-driven rendering (image resolver, threshold colors)

**Backend Architecture:**
- Settings stored in ApplicationSettings model
- API endpoints for settings retrieval (`/settings/{key}`)
- Alembic migrations for default settings
- No business logic changes (reuse existing valuation_breakdown)

**Data Flow:**
- Settings fetched via React Query (5-min cache)
- Image config loaded at build time (static import)
- Performance metrics calculated server-side
- Client-side rendering optimized with virtualization

### Performance Constraints

**Data Tab Performance:**
- Target: <200ms interaction latency for 1,000 listings
- Constraint: TanStack React Table library (no migration planned)
- Solution: Add virtualization layer, optimize renders, backend pagination

**Image Loading:**
- Lazy load images below fold
- Use Next.js Image component (automatic optimization)
- Preload manufacturer logos (common fallbacks)
- Set explicit width/height to prevent layout shift

**Bundle Size:**
- Image config JSON: <10KB
- New components: <15KB (gzipped)
- No new dependencies (reuse existing libraries)

### Backwards Compatibility

**Database:**
- No schema changes (reuse existing fields)
- New settings added via migration (non-breaking)
- `adjusted_price_usd` field name unchanged

**API:**
- No breaking endpoint changes
- New endpoint: `GET /settings/cpu_mark_thresholds` (additive)
- Existing endpoints return same response shape

**Frontend:**
- Rename "Adjusted Price" in UI only (no prop name changes initially)
- ProductImageDisplay maintains same public API
- Optional gradual migration for prop names (adjustedPrice → adjustedValue)

### Security & Accessibility

**Security:**
- Image config file is static (no user input)
- Validate image URLs (same-origin policy)
- Sanitize external image URLs (CSP headers)
- No XSS risk (images rendered via Next.js Image component)

**Accessibility:**
- All tooltips keyboard accessible (Tab, Enter, Escape)
- Screen reader support (ARIA labels, describedby)
- Color contrast ratios meet WCAG AA (4.5:1)
- Focus indicators visible on all interactive elements
- Images have descriptive alt text

**Performance Accessibility:**
- Reduced motion preference respected (disable animations)
- High contrast mode supported (system colors)
- Keyboard navigation optimized (skip links, focus management)

---

## UI/UX Specifications

### Visual Design Requirements

**Design System Consistency:**
- Use existing shadcn/ui components (Tooltip, Badge, Card)
- Follow existing color palette (CSS variables)
- Maintain 8px grid spacing
- Use Inter font family (already in use)

**Color Scheme:**
- Reuse valuation color variables for CPU Mark thresholds
- Ensure sufficient contrast for accessibility
- Support dark mode (CSS variables automatically adapt)

**Typography:**
- Tooltip text: 14px (0.875rem)
- Metric labels: 14px medium weight
- Metric values: 16px semibold
- Percentage indicators: 12px

**Spacing:**
- Tooltip padding: 12px
- Metric row gap: 8px
- Section spacing: 16px
- Modal padding: 24px

### Interaction Patterns

**Hover Interactions:**
- Tooltip appears after 100ms hover delay
- Tooltip dismisses on mouse leave
- Hover state on interactive elements (underline, color change)

**Click Interactions:**
- Info icon (ℹ️) opens modal
- "View Full Breakdown →" link opens modal
- Metric rows clickable to expand details (optional enhancement)

**Keyboard Interactions:**
- Tab navigates to focusable elements
- Enter/Space triggers actions (open modal, show tooltip)
- Escape dismisses tooltips and modals
- Arrow keys navigate within tables

**Loading States:**
- Skeleton loaders for data fetching
- Spinner for async operations
- Disable interactions during loading
- Show error states with retry option

### Responsive Behavior

**Breakpoints:**
- Mobile: <640px
- Tablet: 640px-1024px
- Desktop: >1024px

**Data Tab (Mobile):**
- Switch to card view (hide table)
- Sticky filters bar
- Reduced column count
- Horizontal scroll for wide tables

**Detail Page (Mobile):**
- Stack metrics vertically
- Single-column layout for performance metrics
- Collapsible sections
- Fixed bottom action bar

**Tooltips (Mobile):**
- Convert to bottom sheet on small screens
- Tap to open (no hover on touch devices)
- Swipe down to dismiss
- Full-width on mobile

---

## Dependencies & Constraints

### External Dependencies

**New Libraries (Minimal):**
- `@tanstack/react-virtual` - For table virtualization (if not already installed)
- `react-hook-form` - For settings management (likely already installed)

**Existing Libraries:**
- `@tanstack/react-query` - Data fetching (already in use)
- `@tanstack/react-table` - Table management (already in use)
- `shadcn/ui` - UI components (already in use)
- `next/image` - Image optimization (already in use)

### Technical Limitations

**Browser Support:**
- Modern browsers only (Chrome 90+, Firefox 88+, Safari 14+)
- No IE11 support (already dropped)
- CSS Grid and Flexbox required

**Data Volume:**
- Data tab optimized for up to 5,000 listings
- Beyond 5,000: requires server-side pagination
- Image config file limited to 100KB (performance)

**Image Formats:**
- SVG, PNG, WebP supported
- GIF/JPEG allowed but not recommended
- No video or animated formats

### Timeline Considerations

**Development Phases:**
- Phase 1 (Data Tab Performance): 2 weeks
- Phase 2 (Adjusted Value & Tooltips): 1 week
- Phase 3 (CPU Metrics Layout): 1 week
- Phase 4 (Image Management System): 2 weeks
- **Total:** 6 weeks (1.5 sprints)

**Dependencies Between Phases:**
- Phase 2 and Phase 3 can run in parallel
- Phase 4 independent, can start anytime
- Phase 1 should complete before Phase 3 (shared Data tab)

**Testing & QA:**
- 1 week for comprehensive testing
- Parallel with Phase 4 development
- Include performance benchmarking

---

## Success Metrics

### Performance KPIs

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| Data tab load time (500 listings) | 1,200ms | <300ms | React Profiler, Lighthouse |
| Data tab interaction latency (P95) | 600ms | <150ms | Performance.measure API |
| Scroll FPS (virtualized) | 30-45fps | 60fps | Chrome DevTools FPS meter |
| Image load time (P90) | 800ms | <500ms | Network timing API |
| Bundle size increase | N/A | <20KB | Webpack bundle analyzer |

### User Engagement Metrics

| Metric | Baseline | Target | Tracking |
|--------|----------|--------|----------|
| Tooltip usage rate | N/A | >40% of users | Analytics event tracking |
| Modal open rate (from tooltip) | N/A | >20% of tooltip users | Click tracking |
| Time to compare metrics | ~8 sec (estimated) | <3 sec | User testing |
| Support tickets (pricing questions) | 15/month | <2/month | Support ticket analysis |
| Image fallback rate | ~60% | <40% | Error rate tracking |

### Error Rate Targets

| Error Type | Current | Target |
|------------|---------|--------|
| Image load failures | ~5% | <2% |
| Config parsing errors | N/A | 0% |
| Tooltip render errors | N/A | <0.1% |
| Performance regressions | N/A | 0 (automated checks) |

### Adoption Metrics

| Feature | Target | Measurement |
|---------|--------|-------------|
| Data tab usage (vs. Catalog tab) | >30% of sessions | Tab view analytics |
| Detail page dwell time | +20% increase | Time tracking |
| Settings customization rate | >10% of admin users | Settings update events |
| Image uploads (self-service) | >5 new images/month | File upload tracking |

---

## Risks & Mitigation

### Technical Risks

**Risk 1: Virtualization Breaks Existing Features**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:**
  - Thorough testing of sorting, filtering, row selection
  - Feature flag for gradual rollout
  - Keep non-virtualized mode as fallback

**Risk 2: Image Config File Becomes Too Large**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Set strict file size limits (100KB)
  - Lazy-load config sections
  - Code-split by manufacturer if needed
  - Monitor file size in CI/CD

**Risk 3: Performance Regression on Mobile**
- **Probability:** Medium
- **Impact:** High
- **Mitigation:**
  - Test on low-end devices (e.g., Moto G4)
  - Use Chrome DevTools throttling
  - Implement separate mobile optimizations
  - Monitor real user metrics (RUM)

### User Adoption Risks

**Risk 1: Users Don't Discover Tooltips**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Add onboarding tour highlighting new features
  - Use subtle animation on first hover
  - Include help text in UI ("Hover for details")
  - Track tooltip engagement, iterate if low

**Risk 2: Content Managers Struggle with Image Uploads**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Provide detailed documentation with screenshots
  - Record video tutorial
  - Add validation errors with helpful messages
  - Offer onboarding session for first upload

### Rollback Strategies

**Rollback Plan 1: Feature Flags**
- Implement feature flags for each enhancement
- Flags: `ENABLE_VIRTUALIZATION`, `ENABLE_IMAGE_CONFIG`, `ENABLE_CPU_MARK_COLORING`
- Can disable individual features without full rollback

**Rollback Plan 2: Database Rollback**
- Settings stored in database (easy to delete)
- Migration rollback script provided
- No data loss risk (only adds new settings)

**Rollback Plan 3: Code Rollback**
- Keep old components as `*Legacy` versions
- Git revert prepared for emergency
- Deployment pipeline supports instant rollback

---

## Timeline & Milestones

### High-Level Phases

**Phase 1: Foundation (Week 1-2)**
- Set up infrastructure (config files, directory structure)
- Create base utilities (image resolver, threshold hooks)
- Design database migrations
- Write technical specifications

**Phase 2: Data Tab Performance (Week 2-3)**
- Implement table virtualization
- Add backend pagination endpoints
- Optimize render performance
- Performance testing and tuning

**Phase 3: UX Improvements (Week 3-5)**
- Rename Adjusted Price to Adjusted Value
- Implement tooltips (adjusted value, CPU metrics)
- Update CPU metrics layout
- Add color coding for CPU Mark

**Phase 4: Image Management (Week 5-6)**
- Migrate images to new structure
- Implement unified image display component
- Create documentation for non-technical users
- User acceptance testing

**Phase 5: Testing & QA (Week 6-7)**
- Comprehensive testing (unit, integration, E2E)
- Performance benchmarking
- Accessibility audit
- Bug fixes

**Phase 6: Deployment & Monitoring (Week 7-8)**
- Staged rollout (internal → beta → production)
- Monitor metrics and error rates
- Gather user feedback
- Iterate based on feedback

### Key Deliverables

| Milestone | Deliverable | Due Date | Owner |
|-----------|-------------|----------|-------|
| M1: Design Complete | PRD, Implementation Plan, Wireframes | Week 1 | Product, Design |
| M2: Backend Ready | Migrations, API endpoints, settings | Week 2 | Backend Engineer |
| M3: Virtualization Done | Data tab with virtualization, tests | Week 3 | Frontend Engineer |
| M4: UX Complete | Tooltips, renaming, CPU layout, coloring | Week 5 | Frontend Engineer |
| M5: Images Migrated | Image config, unified component, docs | Week 6 | Frontend + Content |
| M6: QA Complete | Test reports, performance benchmarks | Week 7 | QA Engineer |
| M7: Production Deploy | Deployed to production, monitoring | Week 8 | DevOps |

### Review Gates

**Gate 1: Design Review (End of Week 1)**
- Stakeholder approval of PRD
- UX/UI mockups approved
- Technical feasibility confirmed

**Gate 2: Backend Review (End of Week 2)**
- Migrations tested
- API endpoints functional
- Settings management working

**Gate 3: Performance Review (End of Week 3)**
- Virtualization meets latency targets
- No regressions on existing features
- Passes load testing

**Gate 4: UX Review (End of Week 5)**
- Tooltips user-tested
- Color coding validated with users
- Accessibility audit passed

**Gate 5: Launch Readiness (End of Week 7)**
- All tests passing
- Documentation complete
- Rollback plan validated
- Monitoring dashboards ready

---

## Appendix

### Glossary

| Term | Definition |
|------|------------|
| Adjusted Value | Listing price after applying valuation rules (previously "Adjusted Price") |
| CPU Mark | PassMark benchmark score (single-thread or multi-thread) |
| $/CPU Mark | Price-to-performance ratio (price divided by CPU Mark score) |
| Valuation Breakdown | JSON object containing applied rules and adjustments |
| Valuation Rule | Configurable pricing adjustment (e.g., RAM deduction, condition penalty) |
| Form Factor | PC case type (mini PC, desktop, SFF, rack mount, etc.) |
| Virtualization | Rendering only visible rows in a table for performance |
| Dual Metric Display | Showing both base and adjusted values side-by-side |
| Fallback Hierarchy | Ordered list of image sources to try if primary fails |

### References

- `CLAUDE.md` - Project architecture and development guidelines
- `architecture.md` - Overall system architecture documentation
- `/apps/api/dealbrain_api/models/core.py` - Database schema
- `/apps/web/components/listings/` - Listings UI components
- `/apps/web/lib/valuation-utils.ts` - Valuation logic and utilities
- TanStack Table Docs: https://tanstack.com/table/v8
- React Virtual Docs: https://tanstack.com/virtual/v3
- WCAG 2.1 AA Guidelines: https://www.w3.org/WAI/WCAG21/quickref/

### Related Tickets/Issues

- #TBD - Data tab performance degradation (user report)
- #TBD - Unclear adjusted pricing (support tickets)
- #TBD - Add Minisforum manufacturer logo (content request)
- #TBD - CPU metrics hard to compare (user feedback)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-31 | Product Team | Initial PRD created |

---

**Next Steps:**
1. Stakeholder review and approval
2. Create detailed Implementation Plan
3. Design UI mockups for CPU metrics layout
4. Assign engineering resources
5. Schedule kickoff meeting
