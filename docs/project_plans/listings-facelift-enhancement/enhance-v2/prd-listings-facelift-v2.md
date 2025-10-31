# Product Requirements Document: Listings Facelift Enhancements V2

**Project:** Deal Brain - Listings Display Enhancement
**Version:** 2.0
**Date:** 2025-10-26
**Status:** Draft
**Owner:** Product & Engineering

---

## Executive Summary

This PRD outlines enhancements to the Deal Brain listings display system across three key surfaces: the overview modal, the detail page, and new entity catalog pages. These improvements focus on increasing information density, improving visual hierarchy, enhancing discoverability through better routing, and providing richer context through inline tooltips and expanded specifications.

The enhancements will make Deal Brain more useful for users evaluating PC deals by surfacing critical information faster and providing clearer navigation paths to component details.

---

## Problem Statement

### Current Pain Points

1. **Limited Visual Context**: Product images are not displayed in the overview modal, making it harder for users to quickly identify and remember listings
2. **Incomplete Hardware Info**: GPU information is not prominently displayed in modal headers
3. **Flat Specifications Display**: The specifications tab lacks clear organizational structure, making it difficult to scan for specific information types
4. **Missing Contextual Tooltips**: The detail page overview section does not provide hover tooltips for linked entities
5. **Inefficient Layout**: Current detail page layout could be optimized for better space utilization
6. **Opaque Valuation Display**: The Valuation tab shows "No rule-based adjustments" instead of listing actual contributing rules
7. **Broken Entity Navigation**: Clicking entity links results in 404 errors due to missing catalog detail pages

### User Impact

Users must navigate to external sites or drill into multiple pages to understand listing details, slowing down their deal evaluation workflow and reducing platform engagement.

---

## Goals & Success Metrics

### Primary Goals

1. Reduce time-to-insight for listing evaluation by 40%
2. Increase user engagement with entity information by providing seamless navigation
3. Improve listing detail page usability through better organization
4. Surface valuation logic more transparently

### Success Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| Average time on listing detail page | Baseline TBD | -20% | Analytics tracking |
| Entity link click-through rate | 0% (404 errors) | 15% | Event tracking |
| Tooltip hover interactions | 0 | 200+/week | Event tracking |
| User-reported issues with navigation | Multiple | 0 | Support tickets |
| Valuation breakdown view rate | Unknown | +30% | Analytics tracking |

---

## User Stories

### Epic 1: Rich Visual Context

**US-001**: As a deal hunter, I want to see product images in the overview modal so I can quickly identify listings visually
**US-002**: As a power user, I want to see GPU information prominently displayed so I understand graphics capabilities at a glance

### Epic 2: Enhanced Specifications

**US-003**: As a technical user, I want specifications organized into logical subsections so I can quickly find specific hardware details
**US-004**: As a data curator, I want to see "Add +" buttons for empty specification sections so I can quickly populate missing data

### Epic 3: Contextual Navigation

**US-005**: As a component researcher, I want hover tooltips on entity links in the overview section so I can preview details without navigating away
**US-006**: As a comparison shopper, I want to click entity links and view detailed component pages so I can understand component specifications across listings

### Epic 4: Transparent Valuation

**US-007**: As a deal evaluator, I want to see which valuation rules were applied to a listing so I understand how the adjusted price was calculated

---

## Feature Requirements

### FR-1: Product Image Display

**Priority:** High
**Complexity:** Medium

#### Requirements

1.1. Display product images in the overview modal (`listing-overview-modal.tsx`)
1.2. Implement fallback image hierarchy:
   - Level 1: `listing.thumbnail_url` or `listing.image_url`
   - Level 2: Manufacturer logo (if `listing.manufacturer` exists)
   - Level 3: CPU manufacturer logo (Intel/AMD)
   - Level 4: Form factor icon (Mini PC, Desktop, etc.)
   - Level 5: Generic PC placeholder icon

1.3. Image sizing and styling:
   - Max width: 400px
   - Rounded corners (8px border-radius)
   - Centered horizontally
   - Loading skeleton during fetch
   - Error state handling

1.4. Image should be clickable to open full-size view in a lightbox

#### Technical Notes

- Leverage existing `ProductImage` component if available, or create new reusable component
- Use Next.js Image component for optimization
- Store fallback icons in `public/images/fallbacks/`

#### Acceptance Criteria

- [ ] Product images display in overview modal
- [ ] Fallback hierarchy works correctly for all 5 levels
- [ ] Images are properly sized and styled
- [ ] Loading and error states are handled
- [ ] Lightbox opens on image click

---

### FR-2: Additional Modal Information

**Priority:** Medium
**Complexity:** Low

#### Requirements

2.1. **GPU Display in Modal Header**
   - Add GPU name to hardware section grid (already present, verify prominence)
   - Display GPU model name with tooltip support
   - Show "(Integrated)" badge for iGPUs

2.2. **Clickable URL Links**
   - Display `listing_url` as primary external link with icon
   - Display `other_urls` array as labeled secondary links
   - All links open in new tab with `rel="noopener noreferrer"`
   - Show link count indicator if more than 3 additional URLs

#### Technical Notes

- URLs are already displayed in the modal (lines 263-299 of `listing-overview-modal.tsx`)
- Verify GPU is prominently shown (currently lines 150-169)
- Add ExternalLink icon from `lucide-react`

#### Acceptance Criteria

- [ ] GPU information is visually prominent in modal
- [ ] All URLs are clickable and properly styled
- [ ] Links open in new tabs securely
- [ ] Link overflow is handled gracefully

---

### FR-3: Enhanced Specifications Tab

**Priority:** High
**Complexity:** High

#### Requirements

3.1. **Subsection Organization**

Create dedicated subsections within the Specifications tab:

**Compute Subsection:**
- CPU (model, cores, threads, base/boost clocks, TDP, benchmark scores)
- GPU (model, VRAM, type: integrated/discrete)
- Performance scores (CPU Mark Multi, CPU Mark Single, GPU Mark)

**Memory Subsection:**
- RAM capacity
- RAM type (DDR4, DDR5, etc.)
- RAM speed (MHz)
- RAM configuration (e.g., "2x8GB")
- RAM spec link

**Storage Subsection:**
- Primary storage (capacity, type, profile link)
- Secondary storage (capacity, type, profile link)
- Storage performance metrics (if available)

**Connectivity Subsection:**
- Ports (USB-A, USB-C, HDMI, DisplayPort counts)
- Network (WiFi, Ethernet details)
- Audio ports
- Other I/O

3.2. **Empty State Handling**
- Show "No data available" message for empty subsections
- Display "Add +" button next to empty state message
- Button opens quick-add dialog for that specific data type
- Maintain visual consistency with non-empty sections

3.3. **Visual Design**
- Each subsection has a clear heading (h4 or h5)
- Subsections use Card components for visual separation
- Consistent spacing between subsections (24px)
- Grid layout for fields (3 columns on desktop, 2 on tablet, 1 on mobile)

#### Technical Notes

- Modify `apps/web/components/listings/specifications-tab.tsx`
- Create new quick-add dialogs for each data type
- Leverage existing `FieldGroup` component
- Use existing `Card`, `CardHeader`, `CardTitle`, `CardContent` from shadcn/ui

#### Acceptance Criteria

- [ ] Four main subsections exist: Compute, Memory, Storage, Connectivity
- [ ] Each subsection shows all relevant data when available
- [ ] Empty subsections show "No data available" message
- [ ] "Add +" buttons open appropriate quick-add dialogs
- [ ] Visual design is consistent and polished
- [ ] Layout is responsive across screen sizes

---

### FR-4: Detail Page Overview Tooltips

**Priority:** Medium
**Complexity:** Medium

#### Requirements

4.1. **Tooltip Implementation**
- Add hover tooltips to all entity links in the detail page overview section
- Tooltip content should match what appears in the Specifications tab
- Use existing `EntityTooltip` component with Popover pattern
- Tooltips should appear on hover after 200ms delay
- Tooltips should be dismissible by clicking outside or pressing Escape

4.2. **Supported Entities**
- CPU: Show model, cores, threads, TDP, benchmark scores
- GPU: Show model, VRAM, type, benchmark scores
- RAM Spec: Show capacity, type, speed, configuration
- Storage Profile: Show capacity, type, interface, performance metrics

4.3. **Tooltip Content**
- Use existing tooltip content components:
  - `CpuTooltipContent`
  - `GpuTooltipContent`
  - `RamSpecTooltipContent`
  - `StorageProfileTooltipContent`
- Ensure API endpoints are correct (not `/listings/entities/...`)

#### Technical Notes

- Modify `apps/web/components/listings/detail-page-hero.tsx` (or equivalent overview section component)
- Leverage existing `EntityTooltip` component (already working in specifications tab)
- Use `fetchEntityData` from `lib/api/entities.ts`
- API endpoints should be `/v1/cpus/{id}`, `/v1/gpus/{id}`, etc.

#### Acceptance Criteria

- [ ] CPU links in overview show tooltip on hover
- [ ] GPU links in overview show tooltip on hover
- [ ] RAM links in overview show tooltip on hover
- [ ] Storage links in overview show tooltip on hover
- [ ] Tooltips use correct API endpoints
- [ ] Tooltip styling is consistent with app design system

---

### FR-5: Layout Optimization

**Priority:** Low
**Complexity:** Medium

#### Requirements

5.1. **Detail Page Audit**
- Review current detail page layout (`apps/web/app/listings/[id]/page.tsx` and `detail-page-layout.tsx`)
- Identify wasted space and opportunities for better information hierarchy
- Prioritize most-accessed information in the visual hierarchy

5.2. **Proposed Improvements**
- Tighten vertical spacing between sections (reduce from current to 16px)
- Use 2-column layout for overview section on wider screens
- Move less-critical metadata (timestamps, IDs) to collapsed sections
- Increase font sizes for primary metrics (pricing, scores)
- Add subtle visual separators between major sections

5.3. **Mobile Optimization**
- Ensure single-column layout on mobile
- Touch targets are at least 44x44px
- Font sizes remain readable (minimum 14px for body text)

#### Technical Notes

- Modify `apps/web/components/listings/detail-page-layout.tsx`
- Update spacing tokens to use Tailwind classes consistently
- Test on multiple screen sizes (mobile, tablet, desktop, ultrawide)

#### Acceptance Criteria

- [ ] Detail page layout is visually balanced
- [ ] Most important information is prominent
- [ ] Vertical spacing is optimized
- [ ] Layout is responsive and works on all screen sizes
- [ ] Changes improve perceived performance (less scrolling needed)

---

### FR-6: Valuation Tab Rules Display

**Priority:** High
**Complexity:** Low

#### Requirements

6.1. **Display Contributing Rules**
- Replace "No rule-based adjustments were applied to this listing" message
- Show all rules from the valuation breakdown, including:
  - Active rules (with non-zero adjustments)
  - Inactive rules (with zero adjustments)
- Display rule name, description, and adjustment amount
- Group rules by rule group if applicable

6.2. **Data Source**
- Fetch from existing `/v1/listings/{id}/valuation-breakdown` endpoint
- Use `adjustments` array from response
- Inactive rules are already included (lines 437-462 in `listings.py`)

6.3. **Visual Design**
- Use table or list format for rules
- Show rule name as primary text
- Show adjustment amount with color coding (green for positive, red for negative, gray for zero)
- Show rule description in expandable accordion or tooltip

#### Technical Notes

- Modify `apps/web/components/listings/listing-valuation-tab.tsx` or `valuation-tab-page.tsx`
- Backend already returns inactive rules with `adjustment_amount: 0.0`
- No backend changes required

#### Acceptance Criteria

- [ ] Valuation tab shows all contributing rules
- [ ] Inactive rules (zero adjustment) are displayed
- [ ] Rules are grouped logically
- [ ] Adjustment amounts are color-coded
- [ ] Rule descriptions are accessible via tooltip or expansion

---

### FR-7: Entity Link Routing

**Priority:** High
**Complexity:** High

#### Requirements

7.1. **Create Entity Detail Pages**

Create new detail pages for each entity type:

**7.1.1. CPU Detail Page**
- Route: `/catalog/cpus/[id]`
- Display: Model, manufacturer, generation, cores, threads, base clock, boost clock, TDP, benchmark scores
- Show: List of all listings using this CPU
- Include: Comparison with similar CPUs

**7.1.2. GPU Detail Page**
- Route: `/catalog/gpus/[id]`
- Display: Model, manufacturer, generation, VRAM, type (integrated/discrete), benchmark scores
- Show: List of all listings using this GPU
- Include: Comparison with similar GPUs

**7.1.3. RAM Spec Detail Page**
- Route: `/catalog/ram-specs/[id]`
- Display: Capacity, type, speed, latency, voltage
- Show: List of all listings using this RAM spec

**7.1.4. Storage Profile Detail Page**
- Route: `/catalog/storage-profiles/[id]`
- Display: Capacity, type, interface, sequential read/write, random read/write
- Show: List of all listings using this storage profile

7.2. **Backend API Endpoints**

Ensure these endpoints exist and return proper data:
- `GET /v1/cpus/{id}` - Returns CPU details
- `GET /v1/gpus/{id}` - Returns GPU details
- `GET /v1/ram-specs/{id}` - Returns RAM spec details
- `GET /v1/storage-profiles/{id}` - Returns storage profile details
- `GET /v1/cpus/{id}/listings` - Returns listings using this CPU (optional, for "Used in" section)

7.3. **Update Entity Links**

Ensure all entity links throughout the app use correct routes:
- Listings table
- Overview modal
- Detail page
- Specifications tab

#### Technical Notes

- Create new directory: `apps/web/app/catalog/`
- Create subdirectories: `cpus/[id]/`, `gpus/[id]/`, `ram-specs/[id]/`, `storage-profiles/[id]/`
- Create `page.tsx` for each entity type
- Verify backend endpoints exist (may need to create)
- Update `EntityLink` component to handle all entity types

#### Acceptance Criteria

- [ ] CPU detail pages load without 404 errors
- [ ] GPU detail pages load without 404 errors
- [ ] RAM spec detail pages load without 404 errors
- [ ] Storage profile detail pages load without 404 errors
- [ ] Entity detail pages display comprehensive information
- [ ] "Used in" listings section shows related listings
- [ ] All entity links throughout app navigate correctly
- [ ] Back button navigation works correctly

---

## Technical Constraints

1. **Performance**: All image loading must use Next.js Image component for optimization
2. **Accessibility**: All new components must meet WCAG 2.1 AA standards
3. **Mobile-First**: All layouts must be responsive and mobile-optimized
4. **Type Safety**: All new code must be fully typed with TypeScript
5. **Testing**: All new components must have unit tests (target: 80% coverage)
6. **API Compatibility**: Backend changes must maintain backward compatibility

---

## Dependencies

### Internal Dependencies

- Existing `EntityTooltip` component (refactored in recent work)
- Valuation breakdown API endpoint
- Existing entity data fetching utilities
- shadcn/ui component library

### External Dependencies

- None

### Backend Requirements

- Entity detail endpoints (`/v1/cpus/{id}`, etc.) must exist or be created
- Valuation breakdown endpoint must include inactive rules (already implemented)
- Listing detail endpoint must include all necessary image URLs

---

## Out of Scope

The following items are explicitly **not** included in this project:

1. Bulk editing of listings
2. Advanced image editing or manipulation
3. Real-time collaborative editing
4. Integration with external pricing APIs
5. Advanced filtering on entity catalog pages
6. Comparison tool for multiple entities
7. Export functionality for entity data
8. Mobile app development

---

## Timeline & Milestones

### Phase 1: Foundation (Week 1)
- [ ] FR-2: Additional Modal Information (GPU prominence, URL links)
- [ ] FR-4: Detail Page Overview Tooltips (leverage existing implementation)
- [ ] FR-6: Valuation Tab Rules Display

**Deliverable:** Enhanced modal and detail page with better information density

### Phase 2: Structure (Week 2)
- [ ] FR-3: Enhanced Specifications Tab (subsections, empty states, quick-add buttons)
- [ ] FR-5: Layout Optimization (spacing, hierarchy improvements)

**Deliverable:** Reorganized specifications tab with better UX

### Phase 3: Visuals & Navigation (Week 3)
- [ ] FR-1: Product Image Display (with fallback hierarchy)
- [ ] FR-7: Entity Link Routing (create catalog pages, fix 404s)

**Deliverable:** Rich visual context and working entity navigation

### Phase 4: Polish & Testing (Week 4)
- [ ] End-to-end testing
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] Bug fixes and refinements

**Deliverable:** Production-ready enhancements

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Backend entity endpoints don't exist | High | Medium | Create endpoints early in Phase 3 |
| Image loading impacts performance | Medium | Low | Use Next.js Image optimization, lazy loading |
| Specifications tab becomes too complex | Medium | Medium | Conduct user testing, iterate on design |
| Entity detail pages lack sufficient data | Medium | Low | Start with MVP, enhance over time |

---

## Appendix

### Related Documents

- `docs/project_plans/listings-facelift-enhancement/listings-facelift-enhancements-v2.md` (Original requirements)
- `docs/project_plans/listings-facelift-enhancement/tooltip-investigation-report.md` (Tooltip implementation reference)

### Design References

- Current overview modal: `apps/web/components/listings/listing-overview-modal.tsx`
- Current detail page: `apps/web/app/listings/[id]/page.tsx`
- Current specifications tab: `apps/web/components/listings/specifications-tab.tsx`
- Entity tooltip implementation: `apps/web/components/listings/entity-tooltip.tsx`

### API Reference

- Listings endpoint: `/v1/listings/{id}`
- Valuation breakdown endpoint: `/v1/listings/{id}/valuation-breakdown`
- Entity endpoints: `/v1/cpus/{id}`, `/v1/gpus/{id}`, `/v1/ram-specs/{id}`, `/v1/storage-profiles/{id}` (to be verified/created)
