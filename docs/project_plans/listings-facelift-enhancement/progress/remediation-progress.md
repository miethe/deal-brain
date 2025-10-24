# Listings Facelift Remediation - Progress Tracker

**Document Created:** 2025-10-24
**Last Updated:** 2025-10-24
**Status:** Not Started

---

## Overview

This document tracks the progress of remediating issues and implementing enhancements identified during the Listings Facelift project. The work focuses on improving data display, adding missing functionality, and enhancing the user experience across the listing modal, detail page, and catalog views.

### Issue Categories

1. **Listing Detail Modal** - Missing CPU/GPU, product image, and URLs
2. **Detail Page** - Missing CPU display, incomplete specifications, missing tooltips
3. **Valuation Tab** - Incorrect rule count display
4. **Catalog View** - Missing CPU/GPU tooltips
5. **Tooltips System** - Comprehensive tooltips for all linked entities

---

## Issue Summary

| Component | Total Issues | Not Started | In Progress | Completed |
|-----------|--------------|-------------|-------------|-----------|
| Listing Detail Modal | 3 | 3 | 0 | 0 |
| Detail Page | 5 | 5 | 0 | 0 |
| Valuation Tab | 1 | 1 | 0 | 0 |
| Catalog View | 1 | 1 | 0 | 0 |
| Tooltips System | 4 | 4 | 0 | 0 |
| **TOTAL** | **14** | **14** | **0** | **0** |

---

## Task Breakdown

### 1. Listing Detail Modal Enhancements

**Status:** Not Started

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
- [ ] Fetch linked URLs from listing data
- [ ] Add URL display section to modal
- [ ] Format URLs appropriately (clickable links)
- [ ] Add URL icons/indicators (external link icon)
- [ ] Handle multiple URLs if applicable
- [ ] Test with various URL formats

**Files to Update:**
- Modal component
- URL display component (possibly reusable)

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
- [ ] Investigate why CPU field is empty in Specifications tab
- [ ] Verify data flow from API to Specifications component
- [ ] Update Specifications tab to display CPU correctly
- [ ] Add CPU link/tooltip functionality (see section 5.1)
- [ ] Test with various CPU configurations

**Files to Update:**
- Specifications tab component
- Data mapping logic

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

**Status:** Not Started

#### 3.1 Display Correct Rule Count and Summary
- [ ] Investigate why "0 rules applied" is shown when rules exist
- [ ] Identify where rule count is calculated/displayed
- [ ] Verify valuation breakdown data structure
- [ ] Update Valuation tab to correctly parse and display rule count
- [ ] Update Valuation tab to list contributing rules directly
- [ ] Ensure consistency with "View breakdown" modal data
- [ ] Test with listings that have:
  - [ ] No rules applied
  - [ ] One rule applied
  - [ ] Multiple rules applied
- [ ] Update display on both modal and detail page versions

**Files to Update:**
- Valuation tab component (modal version)
- Valuation tab component (detail page version)
- Valuation data parsing utilities

---

### 4. Catalog View Enhancements

**Status:** Not Started

#### 4.1 Add CPU/GPU Display with Tooltips
- [ ] **Grid View**
  - [ ] Add CPU name display to grid cards
  - [ ] Add GPU name display to grid cards
  - [ ] Add CPU tooltips on hover (see section 5.1)
  - [ ] Add GPU tooltips on hover (see section 5.2)
  - [ ] Handle long CPU/GPU names (truncation, wrapping)
- [ ] **Table View**
  - [ ] Add CPU column to table
  - [ ] Add GPU column to table
  - [ ] Add CPU tooltips on hover
  - [ ] Add GPU tooltips on hover
  - [ ] Make columns sortable/filterable
- [ ] Test layout with various CPU/GPU name lengths
- [ ] Ensure tooltips work on both views

**Files to Update:**
- Grid view component
- Table view component
- Catalog container component
- Tooltip system

---

### 5. Comprehensive Tooltip System

**Status:** Not Started

#### 5.1 CPU Tooltips
- [ ] Design CPU tooltip component
- [ ] Include specifications:
  - [ ] CPU Name
  - [ ] Cores
  - [ ] Threads
  - [ ] Base Clock
  - [ ] Boost Clock
  - [ ] TDP
  - [ ] Single-thread benchmark score
  - [ ] Multi-thread benchmark score
  - [ ] Other relevant specifications
- [ ] Fetch CPU data from API or use cached data
- [ ] Handle missing specifications gracefully
- [ ] Style consistently with design system
- [ ] Test with various CPU models
- [ ] Deploy to all locations where CPU is displayed

**Files to Update:**
- `/apps/web/components/tooltips/cpu-tooltip.tsx` (new)
- CPU data types
- API client for CPU data

#### 5.2 GPU Tooltips
- [ ] Design GPU tooltip component
- [ ] Include specifications:
  - [ ] GPU Name
  - [ ] VRAM Size
  - [ ] Base Clock
  - [ ] Boost Clock
  - [ ] Other relevant specifications
- [ ] Fetch GPU data from API or use cached data
- [ ] Handle missing specifications gracefully
- [ ] Style consistently with design system
- [ ] Test with various GPU models
- [ ] Deploy to all locations where GPU is displayed

**Files to Update:**
- `/apps/web/components/tooltips/gpu-tooltip.tsx` (new)
- GPU data types
- API client for GPU data

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

---

## Next Steps

1. Review and prioritize tasks based on impact and dependencies
2. Assign tasks to team members or development sessions
3. Begin with foundational work (API data availability, tooltip infrastructure)
4. Implement features incrementally, testing thoroughly at each stage
5. Update this document as tasks are completed

---

**Notes:**
- This document should be updated regularly as work progresses
- Mark checkboxes with `[x]` when tasks are completed
- Add implementation notes and decisions in the Change Log
- Update the Issue Summary table as sections are completed
