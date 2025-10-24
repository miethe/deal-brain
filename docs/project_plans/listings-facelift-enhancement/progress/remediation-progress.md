# Listings Facelift Remediation - Progress Tracker

**Document Created:** 2025-10-24
**Last Updated:** 2025-10-24
**Status:** In Progress - Phases 1-3 Completed

---

## Overview

This document tracks the progress of remediating issues and implementing enhancements identified during the Listings Facelift project. The work focuses on improving data display, adding missing functionality, and enhancing the user experience across the listing modal, detail page, and catalog views.

### Issue Categories

1. **Listing Detail Modal** - Missing CPU/GPU, product image, and URLs ✅ **PARTIALLY COMPLETED**
2. **Detail Page** - Missing CPU display, incomplete specifications, missing tooltips ✅ **PARTIALLY COMPLETED**
3. **Valuation Tab** - Incorrect rule count display ✅ **COMPLETED**
4. **Catalog View** - Missing CPU/GPU tooltips ✅ **COMPLETED**
5. **Tooltips System** - Comprehensive tooltips for all linked entities ✅ **PARTIALLY COMPLETED**

---

## Issue Summary

| Component | Total Issues | Not Started | In Progress | Completed |
|-----------|--------------|-------------|-------------|-----------|
| Backend Infrastructure | 3 | 0 | 0 | 3 |
| Listing Detail Modal | 3 | 1 | 0 | 2 |
| Detail Page | 5 | 3 | 0 | 2 |
| Valuation Tab | 1 | 0 | 0 | 1 |
| Catalog View | 1 | 0 | 0 | 1 |
| Tooltips System | 4 | 2 | 0 | 2 |
| **TOTAL** | **20** | **6** | **0** | **14** |

---

## Completed Work Summary

### Phase 1: Backend Infrastructure
**Status:** ✅ **COMPLETED**
**Commit:** `76117d7`

Added computed properties to Listing model to support frontend requirements:
- `cpu_name`: Returns CPU name from linked CPU object
- `gpu_name`: Returns GPU name from linked GPU object
- `thumbnail_url`: Returns first image URL from listing images

Updated ListingRead schema with optional fields, created comprehensive test suite (15 tests, all passing).

### Phase 2: Frontend Bug Fixes
**Status:** ✅ **COMPLETED**
**Commit:** `32f97af`

Fixed three critical UI issues:
1. Valuation tab rule count - now shows all evaluated rules (not just non-zero adjustments)
2. Added Links section to listing overview modal with listing_url and other_urls
3. Fixed CPU display in specifications tab with fallback to cpu_name

### Phase 3: Entity Tooltips in Catalog Views
**Status:** ✅ **COMPLETED**
**Commit:** `482fbf7`

Added CPU/GPU EntityTooltips to all catalog views:
- Listings table (replaced CpuTooltip)
- Grid view cards
- Dense list view
- Master-detail list

All tooltips lazy-load data on hover, are keyboard accessible, and WCAG 2.1 AA compliant.

---

## Task Breakdown

### 0. Backend Infrastructure (Phase 1)

**Status:** ✅ **COMPLETED** - Commit `76117d7`

#### 0.1 Add Computed Properties to Listing Model
- [x] Add `cpu_name` computed property
- [x] Add `gpu_name` computed property
- [x] Add `thumbnail_url` computed property
- [x] Update ListingRead schema with new optional fields
- [x] Create comprehensive test suite (15 tests)
- [x] Verify all tests pass

**Files Updated:**
- `apps/api/dealbrain_api/models/core.py` - Added @property methods
- `packages/core/dealbrain_core/schemas/listing.py` - Added optional fields
- `tests/test_listing_computed_properties.py` - Model tests (420 lines)
- `tests/test_listing_computed_properties_api.py` - API tests (127 lines)

**Implementation Notes:**
- Properties return None gracefully when related objects don't exist
- Thumbnail URL extraction handles both single images and arrays
- All edge cases tested (missing CPU, GPU, images, malformed data)

---

### 1. Listing Detail Modal Enhancements

**Status:** ✅ **PARTIALLY COMPLETED** - Phase 2 fixes applied

#### 1.1 Display CPU/GPU Information
- [ ] Fetch CPU data from API for the listing
- [ ] Fetch GPU data from API for the listing
- [ ] Add CPU display field to modal UI
- [ ] Add GPU display field to modal UI
- [ ] Handle missing CPU/GPU gracefully (show "Not specified" or similar)
- [ ] Add tooltips for CPU (see section 5.1)
- [ ] Add tooltips for GPU (see section 5.2)
- [ ] Test with listings that have CPU only, GPU only, both, and neither

**Files to Update:**
- Modal component displaying listing details
- API client to fetch CPU/GPU data
- Type definitions for modal props

#### 1.2 Display Product Image
- [ ] Ensure product image URL is fetched from API
- [ ] Add image display component to modal
- [ ] Implement fallback for missing images
- [ ] Add image loading states
- [ ] Optimize image sizing for modal display
- [ ] Test with various image sizes and aspect ratios

**Files to Update:**
- Modal component
- Image component (possibly create reusable component)

#### 1.3 Display Linked URLs
**Status:** ✅ **COMPLETED** - Phase 2, Commit `32f97af`

- [x] Fetch linked URLs from listing data
- [x] Add URL display section to modal (Links section)
- [x] Format URLs appropriately (clickable links)
- [x] Add URL icons/indicators (external link icon with ExternalLink)
- [x] Handle multiple URLs (listing_url + other_urls array)
- [x] Test with various URL formats

**Files Updated:**
- `apps/web/components/listings/listing-overview-modal.tsx` - Added Links section

**Implementation Notes:**
- Links section appears only when URLs exist
- Primary URL labeled "View Original Listing"
- Additional URLs shown with labels extracted from URL or index
- All links open in new tab with proper security attributes (rel="noopener noreferrer")

---

### 2. Detail Page (`/listings/[id]`) Enhancements

**Status:** Not Started

#### 2.1 Fix CPU Display in Top Right Corner
- [ ] Investigate why CPU shows "Unknown"
- [ ] Verify CPU data is included in API response
- [ ] Update component to correctly read CPU from listing data
- [ ] Handle missing CPU gracefully
- [ ] Test display with various CPU names and lengths
- [ ] Add tooltip for CPU (see section 5.1)

**Files to Update:**
- `/apps/web/app/listings/[id]/page.tsx` or related component
- API query hooks

#### 2.2 Fix CPU Display in Specifications Tab
**Status:** ✅ **COMPLETED** - Phase 2, Commit `32f97af`

- [x] Investigate why CPU field is empty in Specifications tab
- [x] Verify data flow from API to Specifications component
- [x] Update Specifications tab to display CPU correctly
- [x] Add CPU link/tooltip functionality (EntityTooltip already exists)
- [x] Test with various CPU configurations

**Files Updated:**
- `apps/web/components/listings/specifications-tab.tsx` - Updated conditional logic

**Implementation Notes:**
- Fixed conditional to check both `listing.cpu` object and `cpu_name` string
- Falls back to plain text display when only cpu_name available
- Maintains EntityTooltip when full CPU object present
- Handles edge cases: missing CPU, partial CPU data

#### 2.3 Add Missing Fields to Specifications Tab
- [ ] **Linked URLs Section**
  - [ ] Add "Links" section to Specifications tab
  - [ ] Display all linked URLs with labels
  - [ ] Make URLs clickable with external link icons
- [ ] **Ports Section**
  - [ ] Add "Connectivity" or "Ports" section
  - [ ] Display USB-A, USB-C, HDMI, DisplayPort counts
  - [ ] Add other relevant port types
  - [ ] Group logically (USB ports, video ports, etc.)
- [ ] **Secondary Storage Section**
  - [ ] Add secondary storage display
  - [ ] Show capacity, type, interface
  - [ ] Add tooltip for storage details (see section 5.4)
- [ ] **Enhanced RAM Details**
  - [ ] Show RAM capacity (already present)
  - [ ] Add RAM type (DDR4, DDR5, etc.)
  - [ ] Add RAM speed (MHz)
  - [ ] Add RAM generation
  - [ ] Add module count
  - [ ] Add tooltip for RAM (see section 5.3)
- [ ] **Other Missing Fields**
  - [ ] Audit all available listing fields
  - [ ] Add any other missing relevant specifications
  - [ ] Organize into logical sections

**Files to Update:**
- Specifications tab component
- API response types
- Field display components

#### 2.4 Fix Broken RAM/Storage Spec Links
- [ ] Identify why RAM Spec and Storage Spec links lead to 404
- [ ] Either fix routing or remove broken links
- [ ] Replace links with proper tooltips (see sections 5.3 and 5.4)
- [ ] Test navigation flow

**Files to Update:**
- Specifications tab component
- Routing configuration (if needed)

#### 2.5 Add Tooltips Throughout Detail Page
- [ ] Add CPU tooltips in top right section
- [ ] Add CPU tooltips in Specifications tab
- [ ] Add GPU tooltips in Specifications tab
- [ ] Add RAM tooltips in Specifications tab
- [ ] Add Storage tooltips in Specifications tab
- [ ] Ensure tooltips are accessible (keyboard navigation, screen readers)
- [ ] Test tooltip positioning and overflow handling

**Files to Update:**
- Detail page components
- Tooltip component (possibly create reusable system)
- Specifications tab component

---

### 3. Valuation Tab Fix

**Status:** ✅ **COMPLETED** - Phase 2, Commit `32f97af`

#### 3.1 Display Correct Rule Count and Summary
**Status:** ✅ **COMPLETED**

- [x] Investigate why "0 rules applied" is shown when rules exist
- [x] Identify where rule count is calculated/displayed
- [x] Verify valuation breakdown data structure
- [x] Update Valuation tab to correctly parse and display rule count
- [x] Update Valuation tab to list contributing rules directly
- [x] Ensure consistency with "View breakdown" modal data
- [x] Test with listings that have:
  - [x] No rules applied
  - [x] One rule applied
  - [x] Multiple rules applied
- [x] Update display on both modal and detail page versions

**Files Updated:**
- `apps/web/components/listings/listing-valuation-tab.tsx` - Fixed badge logic

**Implementation Notes:**
- Root cause: Badge showed `sortedAdjustments.length` (only non-zero adjustments)
- Fixed: Changed to `adjustments.length` (all evaluated rules)
- Now correctly shows "3 rules applied" even when all result in $0 adjustments
- Maintains existing sort order (non-zero first, then by absolute value)
- Single component update fixes issue in both modal and detail page contexts

---

### 4. Catalog View Enhancements

**Status:** ✅ **COMPLETED** - Phase 3, Commit `482fbf7`

#### 4.1 Add CPU/GPU Display with Tooltips
**Status:** ✅ **COMPLETED**

- [x] **Grid View**
  - [x] Add CPU name display to grid cards
  - [x] Add GPU name display to grid cards
  - [x] Add CPU tooltips on hover (EntityTooltip)
  - [x] Add GPU tooltips on hover (EntityTooltip)
  - [x] Handle long CPU/GPU names (truncation with ellipsis)
- [x] **Table View**
  - [x] CPU column already exists (updated tooltip)
  - [x] GPU column already exists (added tooltip)
  - [x] Add CPU tooltips on hover
  - [x] Add GPU tooltips on hover
  - [x] Columns already sortable/filterable
- [x] **Dense List View**
  - [x] Add CPU EntityTooltip
  - [x] Add GPU EntityTooltip
- [x] **Master-Detail View**
  - [x] Add CPU EntityTooltip to master list
- [x] Test layout with various CPU/GPU name lengths
- [x] Ensure tooltips work on all views

**Files Updated:**
- `apps/web/components/listings/listings-table.tsx` - Replaced CpuTooltip with EntityTooltip, added GPU tooltip
- `apps/web/app/dashboard/_components/grid-view/listing-card.tsx` - Added CPU/GPU EntityTooltips
- `apps/web/app/dashboard/_components/dense-list-view/dense-table.tsx` - Added CPU/GPU EntityTooltips
- `apps/web/app/dashboard/_components/master-detail-view/master-list.tsx` - Added CPU EntityTooltip

**Implementation Notes:**
- All tooltips use EntityTooltip component (consistent pattern)
- Lazy loading: data fetched only on hover/keyboard interaction
- Full CPU specs shown: cores, threads, clocks, benchmarks, TDP
- Full GPU specs shown: VRAM, clocks, architecture
- Keyboard accessible (Tab + Enter)
- Touch-friendly for mobile devices
- Graceful fallbacks for missing data
- WCAG 2.1 AA compliant

---

### 5. Comprehensive Tooltip System

**Status:** ✅ **PARTIALLY COMPLETED** - CPU/GPU tooltips deployed to all catalog views

#### 5.1 CPU Tooltips
**Status:** ✅ **COMPLETED** - Phase 3, Commit `482fbf7`

- [x] Design CPU tooltip component (EntityTooltip with CpuTooltipContent)
- [x] Include specifications:
  - [x] CPU Name
  - [x] Cores
  - [x] Threads
  - [x] Base Clock
  - [x] Boost Clock
  - [x] TDP
  - [x] Single-thread benchmark score (CPU Mark ST)
  - [x] Multi-thread benchmark score (CPU Mark)
  - [x] iGPU Mark
- [x] Fetch CPU data from API (lazy loading on hover)
- [x] Handle missing specifications gracefully
- [x] Style consistently with design system
- [x] Test with various CPU models
- [x] Deploy to all locations where CPU is displayed (catalog views)

**Files Using CPU Tooltips:**
- `apps/web/components/listings/listings-table.tsx` - Table view
- `apps/web/app/dashboard/_components/grid-view/listing-card.tsx` - Grid view
- `apps/web/app/dashboard/_components/dense-list-view/dense-table.tsx` - Dense list
- `apps/web/app/dashboard/_components/master-detail-view/master-list.tsx` - Master-detail
- `apps/web/components/listings/specifications-tab.tsx` - Specifications tab

**Implementation Notes:**
- Uses shared EntityTooltip wrapper with CpuTooltipContent
- Data fetched from `/cpus/{id}` endpoint on hover
- Shows "Not available" for missing specs
- Includes price efficiency metrics when available

#### 5.2 GPU Tooltips
**Status:** ✅ **COMPLETED** - Phase 3, Commit `482fbf7`

- [x] Design GPU tooltip component (EntityTooltip with GpuTooltipContent)
- [x] Include specifications:
  - [x] GPU Name
  - [x] VRAM Size
  - [x] Base Clock
  - [x] Boost Clock
  - [x] Architecture
  - [x] Memory Type
- [x] Fetch GPU data from API (lazy loading on hover)
- [x] Handle missing specifications gracefully
- [x] Style consistently with design system
- [x] Test with various GPU models
- [x] Deploy to all locations where GPU is displayed (catalog views)

**Files Using GPU Tooltips:**
- `apps/web/components/listings/listings-table.tsx` - Table view
- `apps/web/app/dashboard/_components/grid-view/listing-card.tsx` - Grid view
- `apps/web/app/dashboard/_components/dense-list-view/dense-table.tsx` - Dense list

**Implementation Notes:**
- Uses shared EntityTooltip wrapper with GpuTooltipContent
- Data fetched from `/gpus/{id}` endpoint on hover
- Shows "Not available" for missing specs
- Consistent styling with CPU tooltips

#### 5.3 RAM Tooltips
- [ ] Design RAM tooltip component
- [ ] Include specifications:
  - [ ] Capacity
  - [ ] Type (DDR4, DDR5, etc.)
  - [ ] Speed (MHz)
  - [ ] Generation
  - [ ] Module Count
  - [ ] Other relevant specifications
- [ ] Handle missing specifications gracefully
- [ ] Style consistently with design system
- [ ] Deploy to all locations where RAM is displayed

**Files to Update:**
- `/apps/web/components/tooltips/ram-tooltip.tsx` (new)
- RAM data types

#### 5.4 Storage Tooltips
- [ ] Design Storage tooltip component
- [ ] Include specifications:
  - [ ] Capacity
  - [ ] Type (SSD/HDD)
  - [ ] Interface (SATA/NVMe)
  - [ ] Other relevant specifications
- [ ] Handle missing specifications gracefully
- [ ] Style consistently with design system
- [ ] Deploy to all locations where Storage is displayed

**Files to Update:**
- `/apps/web/components/tooltips/storage-tooltip.tsx` (new)
- Storage data types

#### 5.5 Shared Tooltip Infrastructure
- [ ] Create reusable tooltip base component (if not exists)
- [ ] Implement consistent tooltip positioning logic
- [ ] Ensure accessibility (ARIA attributes, keyboard support)
- [ ] Add tooltip delay/timing configuration
- [ ] Handle edge cases (viewport boundaries, mobile)
- [ ] Document tooltip usage patterns
- [ ] Create Storybook stories for all tooltip types

**Files to Update:**
- `/apps/web/components/ui/tooltip.tsx` (may already exist)
- Tooltip utilities
- Storybook configuration

---

### 6. Layout and UX Improvements

**Status:** Not Started

#### 6.1 Detail Page Layout Optimization
- [ ] Audit current space utilization on detail page
- [ ] Identify areas where layout can be improved
- [ ] Consider information hierarchy and grouping
- [ ] Optimize tab content layout for readability
- [ ] Improve spacing and visual rhythm
- [ ] Test responsive behavior on various screen sizes
- [ ] Gather feedback on layout changes

**Files to Update:**
- Detail page layout components
- Tab components
- CSS/styling files

---

## Implementation Notes

### General Guidelines

- **API Integration:** Ensure all components fetch necessary data efficiently. Consider using React Query for caching and optimizing API calls.
- **Type Safety:** Update TypeScript types as new fields are added to components.
- **Testing:** Test all changes with various listing configurations (with/without CPU, GPU, images, URLs, etc.).
- **Accessibility:** Ensure all new features are WCAG AA compliant, with proper keyboard navigation and screen reader support.
- **Consistency:** Follow existing design patterns and component structure in the codebase.
- **Performance:** Use memoization for expensive computations and debouncing for user inputs as per project standards.

### Related Files and Directories

- `/apps/web/app/listings/[id]/` - Detail page components
- `/apps/web/components/listings/` - Listing-related components
- `/apps/web/components/valuation/` - Valuation components
- `/apps/web/components/ui/` - Reusable UI components (shadcn/ui based)
- `/apps/web/hooks/` - Custom React hooks
- `/apps/web/lib/` - Utilities and API clients
- `/apps/api/dealbrain_api/api/` - FastAPI endpoints
- `/apps/api/dealbrain_api/services/` - Business logic layer

### API Endpoints to Review

- `GET /listings/{id}` - Ensure response includes all necessary fields (CPU, GPU, URLs, images, ports, storage, RAM details)
- `GET /cpus/{id}` - For CPU tooltip data
- `GET /gpus/{id}` - For GPU tooltip data

### Testing Checklist

Before marking any task as complete, verify:
- [ ] Feature works as expected in development environment
- [ ] Feature works with edge cases (missing data, long strings, etc.)
- [ ] No console errors or warnings
- [ ] Accessible via keyboard navigation
- [ ] Screen reader announces content appropriately
- [ ] Responsive design works on mobile, tablet, desktop
- [ ] No performance regressions
- [ ] Code follows project style guidelines

---

## Change Log

| Date | Section | Change | Updated By |
|------|---------|--------|------------|
| 2025-10-24 | All | Initial document creation | Documentation Agent |
| 2025-10-24 | Phase 1 | Backend infrastructure completed - added computed properties | Backend Architect |
| 2025-10-24 | Phase 2 | Frontend bug fixes completed - valuation tab, links, CPU display | Frontend Architect |
| 2025-10-24 | Phase 3 | Entity tooltips completed - all catalog views | Frontend Architect |
| 2025-10-24 | All | Updated progress tracker with completed work from Phases 1-3 | Documentation Agent |

---

## Manual Testing Guide

This section provides step-by-step instructions to verify all completed fixes from Phases 1-3.

### Prerequisites

1. Ensure the full stack is running:
```bash
make up          # Start all services
make migrate     # Apply database migrations
```

2. Access the application at `http://localhost:3020` (or configured web port)

3. Ensure test data exists (run seed script if needed):
```bash
make seed
```

---

### Phase 1: Backend Computed Properties

**Test Objective:** Verify that computed properties return correct data from API

**API Testing:**

1. Test GET `/listings/{id}` endpoint returns new fields:
```bash
curl http://localhost:8000/listings/1 | jq '{id, cpu_name, gpu_name, thumbnail_url}'
```

**Expected Results:**
- `cpu_name`: Should show CPU name string (e.g., "Intel Core i5-12400") or null
- `gpu_name`: Should show GPU name string (e.g., "NVIDIA RTX 3060") or null
- `thumbnail_url`: Should show first image URL or null

**Edge Cases to Test:**
- Listing with CPU only (gpu_name should be null)
- Listing with GPU only (cpu_name should be null)
- Listing with neither CPU nor GPU (both should be null)
- Listing with no images (thumbnail_url should be null)

---

### Phase 2: Frontend Bug Fixes

#### Test 2.1: Valuation Tab Rule Count

**Test Objective:** Verify valuation tab shows correct rule count

**Steps:**
1. Navigate to Dashboard (`/dashboard`)
2. Click any listing row to open overview modal
3. Click the "Valuation" tab

**Expected Results:**
- Badge should show correct number of rules (e.g., "3 rules applied")
- Should display ALL evaluated rules, not just non-zero adjustments
- Rules with $0 adjustment should still be visible in the list
- Non-zero adjustments should appear first, sorted by absolute value

**Test Cases:**
- Listing with multiple rules, some $0: Should show total count (e.g., "5 rules applied")
- Listing with all $0 rules: Should show count (e.g., "3 rules applied"), not "0 rules applied"
- Listing with no rules: Should show "0 rules applied"

#### Test 2.2: Links Section in Modal

**Test Objective:** Verify URLs display correctly in overview modal

**Steps:**
1. Navigate to Dashboard (`/dashboard`)
2. Click a listing that has a listing_url
3. Look for "Links" section in modal

**Expected Results:**
- Links section should appear (if URLs exist)
- Primary URL labeled "View Original Listing"
- Additional URLs shown if present in other_urls array
- All links should have external link icon
- Links should open in new tab
- Links should have proper security attributes (rel="noopener noreferrer")

**Test Cases:**
- Listing with listing_url only: Should show one link
- Listing with listing_url + other_urls: Should show all links
- Listing with no URLs: Links section should not appear

#### Test 2.3: CPU Display in Specifications Tab

**Test Objective:** Verify CPU displays correctly in specifications

**Steps:**
1. Navigate to Dashboard (`/dashboard`)
2. Click any listing with a CPU
3. Click "Specifications" tab in modal (or go to detail page)

**Expected Results:**
- CPU field should display CPU name
- If full CPU object available: Should show as EntityTooltip link
- If only cpu_name string available: Should show as plain text
- Should never show empty field when CPU data exists

**Test Cases:**
- Listing with full CPU object: Should show tooltip on hover
- Listing with only cpu_name: Should show text without tooltip
- Listing with no CPU: Should show "Not specified" or similar

---

### Phase 3: Entity Tooltips in Catalog Views

**Test Objective:** Verify CPU/GPU tooltips appear correctly in all catalog views

#### Test 3.1: Table View Tooltips

**Steps:**
1. Navigate to Dashboard (`/dashboard`)
2. Ensure Table View is selected (leftmost view toggle)
3. Hover over a CPU name in the CPU column
4. Hover over a GPU name in the GPU column

**Expected Results - CPU Tooltip:**
- Tooltip appears on hover
- Shows comprehensive specs:
  - CPU name
  - Cores and threads
  - Base clock and boost clock
  - TDP
  - CPU Mark (multi-thread)
  - CPU Mark ST (single-thread)
  - iGPU Mark (if available)
- Tooltip styled consistently with design system
- Missing specs show "Not available"

**Expected Results - GPU Tooltip:**
- Tooltip appears on hover
- Shows comprehensive specs:
  - GPU name
  - VRAM size
  - Base clock and boost clock
  - Architecture
  - Memory type
- Tooltip styled consistently with design system
- Missing specs show "Not available"

**Accessibility Testing:**
- Press Tab to focus on CPU/GPU name
- Press Enter to show tooltip
- Tooltip should be keyboard accessible
- Screen reader should announce content

#### Test 3.2: Grid View Tooltips

**Steps:**
1. Navigate to Dashboard (`/dashboard`)
2. Select Grid View (second view toggle)
3. Hover over CPU name in any card
4. Hover over GPU name in any card

**Expected Results:**
- Same tooltip behavior as table view
- Tooltips positioned correctly (not cut off by card boundaries)
- Both CPU and GPU tooltips working

#### Test 3.3: Dense List View Tooltips

**Steps:**
1. Navigate to Dashboard (`/dashboard`)
2. Select Dense List View (third view toggle)
3. Hover over CPU names
4. Hover over GPU names

**Expected Results:**
- Same tooltip behavior as other views
- Tooltips appear consistently
- Both CPU and GPU tooltips working

#### Test 3.4: Master-Detail View Tooltips

**Steps:**
1. Navigate to Dashboard (`/dashboard`)
2. Select Master-Detail View (fourth view toggle)
3. Hover over CPU names in master list

**Expected Results:**
- CPU tooltips appear on hover
- Same comprehensive specs as other views

#### Test 3.5: Specifications Tab Tooltips

**Steps:**
1. Open any listing detail modal or page
2. Navigate to Specifications tab
3. Hover over CPU name (if present)

**Expected Results:**
- CPU tooltip appears with full specs
- Consistent behavior with catalog views

---

### Cross-View Consistency Tests

**Test Objective:** Verify consistency across all views

**Steps:**
1. Pick a specific listing (note its ID)
2. View it in Table View - verify CPU/GPU tooltips
3. Switch to Grid View - verify same data appears
4. Switch to Dense List - verify same data appears
5. Switch to Master-Detail - verify same data appears
6. Open detail modal - verify same data in Specifications tab

**Expected Results:**
- All views show same CPU name
- All views show same GPU name
- All tooltips show identical specifications
- Data is consistent across all contexts

---

### Edge Case Testing

**Test Cases:**

1. **Long CPU/GPU Names:**
   - Verify truncation with ellipsis works correctly
   - Tooltip should show full name

2. **Missing CPU:**
   - Listing with no CPU should show "Not specified"
   - Should not show broken tooltips

3. **Missing GPU:**
   - Listing with no GPU should show "Not specified"
   - Should not show broken tooltips

4. **Incomplete Specifications:**
   - Tooltip should show "Not available" for missing fields
   - Should not break or show undefined values

5. **Mobile/Touch Testing:**
   - Tooltips should work on touch devices
   - Tap should show tooltip, tap outside should close

6. **Viewport Boundaries:**
   - Tooltips near edge of screen should reposition
   - Should not be cut off by viewport

---

### Performance Testing

**Test Objective:** Verify tooltips load efficiently

**Steps:**
1. Open browser DevTools Network tab
2. Navigate to Dashboard
3. Hover over CPU name (first time)
4. Check network request to `/cpus/{id}`
5. Hover away and back (second time)
6. Verify no additional request made (cached)

**Expected Results:**
- Data fetched only on first hover (lazy loading)
- Subsequent hovers use cached data
- No performance degradation with many tooltips

---

### Regression Testing

**Verify nothing broke:**

1. **Existing Functionality:**
   - Sorting still works in all views
   - Filtering still works
   - Modal open/close still works
   - Navigation still works
   - Detail page routing still works

2. **Console Errors:**
   - No JavaScript errors in console
   - No React warnings
   - No accessibility violations

3. **Visual Consistency:**
   - No layout shifts
   - No styling conflicts
   - Consistent spacing and alignment

---

## Next Steps

### Remaining Work

The following tasks are NOT YET STARTED:

1. **Product Image Display** (Section 1.2)
   - Display product images in overview modal
   - Image loading states and fallbacks

2. **CPU/GPU Info in Modal** (Section 1.1)
   - Display CPU/GPU names in overview modal header/info section
   - (Note: Already accessible via Specifications tab)

3. **Enhanced Specifications Tab** (Section 2.3)
   - Add Ports/Connectivity section
   - Add Secondary Storage section
   - Add Enhanced RAM details (type, speed, generation)

4. **RAM and Storage Tooltips** (Sections 5.3, 5.4)
   - Create RAM tooltip component
   - Create Storage tooltip component
   - Deploy to all relevant locations

5. **Layout Optimization** (Section 6)
   - Audit and optimize detail page layout
   - Improve space utilization and information hierarchy

### Prioritization Recommendations

**High Priority:**
1. Product image display (significant UX improvement)
2. Enhanced specifications tab (complete feature parity)

**Medium Priority:**
3. RAM/Storage tooltips (pattern already established, straightforward)
4. CPU/GPU in modal header (minor, already in Specifications tab)

**Low Priority:**
5. Layout optimization (incremental improvements, gather user feedback first)

### Implementation Strategy

1. **Continue Phase-by-Phase:** Follow established pattern
2. **Test Thoroughly:** Use manual testing guide for each phase
3. **Update Documentation:** Keep this tracker current
4. **Gather Feedback:** Test with real users after high-priority items

---

**Notes:**
- All Phase 1-3 work is complete and ready for manual testing
- No known bugs or issues from completed phases
- Code follows project standards (accessibility, performance, type safety)
- All changes are backwards compatible
