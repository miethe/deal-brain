# Phase 3-4 Progress Tracker

**Plan:** docs/project_plans/listings-facelift-enhancement/enhance-v2/implementation-plan-v2-ph3-4.md
**PRD:** docs/project_plans/listings-facelift-enhancement/enhance-v2/prd-listings-facelift-v2.md
**Started:** 2025-10-26
**Last Updated:** 2025-10-26
**Status:** Not Started

---

## Completion Status

### Phase 3: Visuals & Navigation

**Duration:** Week 3 (7 days)
**Goal:** Add rich visual context and create entity catalog pages

#### TASK-010: Create Product Image Component ⚠️ ASSETS NEEDED
**Effort:** M | **Feature:** FR-1 | **Dependencies:** None

- [ ] Create ProductImageDisplay component at `apps/web/components/listings/product-image-display.tsx`
- [ ] Implement fallback hierarchy logic (5 levels: listing image → manufacturer logo → CPU manufacturer → form factor → generic)
- [ ] Use Next.js Image component for optimization
- [ ] Add loading skeleton during image load
- [ ] Implement lightbox Dialog for full-size view
- [ ] Handle error states gracefully with fallback chain
- [ ] Image displays in overview modal
- [ ] Fallback hierarchy works for all 5 levels
- [ ] Loading skeleton appears during load
- [ ] Error state triggers fallback
- [ ] Lightbox opens on click
- [ ] Next.js Image optimization is active
- [ ] Images are lazy-loaded

**Files to Create:**
- `apps/web/components/listings/product-image-display.tsx`

**Assets Needed:**
- `public/images/fallbacks/intel-logo.svg`
- `public/images/fallbacks/amd-logo.svg`
- `public/images/fallbacks/mini-pc-icon.svg`
- `public/images/fallbacks/desktop-icon.svg`
- `public/images/fallbacks/generic-pc.svg`

---

#### TASK-011: Integrate Product Image in Modal
**Effort:** S | **Feature:** FR-1 | **Dependencies:** TASK-010

- [ ] Import ProductImageDisplay component into listing-overview-modal.tsx
- [ ] Add image section after modal header
- [ ] Adjust spacing and layout to maintain balance
- [ ] Test integration with various listing types
- [ ] Image displays correctly in modal
- [ ] Modal layout remains balanced
- [ ] Image doesn't cause layout shift
- [ ] Lightbox works from modal context

**Files to Modify:**
- `apps/web/components/listings/listing-overview-modal.tsx`

---

#### TASK-012: Verify Backend Entity Endpoints ⚠️ BACKEND REQUIRED
**Effort:** M | **Feature:** FR-7 | **Dependencies:** None

- [ ] Verify GET /v1/cpus/{id} endpoint exists
- [ ] Verify GET /v1/gpus/{id} endpoint exists
- [ ] Verify GET /v1/ram-specs/{id} endpoint exists
- [ ] Verify GET /v1/storage-profiles/{id} endpoint exists
- [ ] Create missing entity detail endpoints if needed
- [ ] Verify optional "Used in" endpoints
- [ ] All entity endpoints return 200 status
- [ ] Response schemas match TypeScript types
- [ ] Endpoints handle 404 gracefully
- [ ] Performance is acceptable (< 200ms)

**Required Endpoints:**
- `GET /v1/cpus/{id}` - Returns CPU details
- `GET /v1/gpus/{id}` - Returns GPU details
- `GET /v1/ram-specs/{id}` - Returns RAM spec details
- `GET /v1/storage-profiles/{id}` - Returns storage profile details

**Optional Endpoints (for "Used in" sections):**
- `GET /v1/cpus/{id}/listings` - Returns listings using this CPU
- `GET /v1/gpus/{id}/listings` - Returns listings using this GPU
- `GET /v1/ram-specs/{id}/listings` - Returns listings using this RAM spec
- `GET /v1/storage-profiles/{id}/listings` - Returns listings using this storage profile

**Backend Files to Check/Create:**
- `apps/api/dealbrain_api/api/cpus.py`
- `apps/api/dealbrain_api/api/gpus.py`
- `apps/api/dealbrain_api/api/ram_specs.py`
- `apps/api/dealbrain_api/api/storage_profiles.py`

---

#### TASK-013: Create CPU Detail Page ⚠️ NEW ROUTES
**Effort:** L | **Feature:** FR-7 | **Dependencies:** TASK-012

- [ ] Create catalog directory structure
- [ ] Implement server component for data fetching at /catalog/cpus/[id]
- [ ] Create CPU detail layout component
- [ ] Display CPU specifications (cores, threads, clocks, TDP, generation)
- [ ] Display benchmark scores (CPU Mark Multi, Single, iGPU Mark)
- [ ] Show "Used in" listings section
- [ ] Create loading skeleton page
- [ ] Create not-found error page
- [ ] CPU detail page loads without 404
- [ ] All specifications display correctly
- [ ] Benchmark scores are formatted properly
- [ ] "Used in" listings section shows related listings
- [ ] Page is mobile responsive
- [ ] Back navigation works correctly

**Files to Create:**
- `apps/web/app/catalog/cpus/[id]/page.tsx`
- `apps/web/app/catalog/cpus/[id]/loading.tsx`
- `apps/web/app/catalog/cpus/[id]/not-found.tsx`
- `apps/web/components/catalog/cpu-detail-layout.tsx`

---

#### TASK-014: Create GPU Detail Page
**Effort:** L | **Feature:** FR-7 | **Dependencies:** TASK-012

- [ ] Create catalog directory structure for GPU
- [ ] Implement server component for data fetching at /catalog/gpus/[id]
- [ ] Create GPU detail layout component
- [ ] Display GPU specifications (model, manufacturer, type)
- [ ] Display GPU memory info (VRAM capacity and type)
- [ ] Display benchmark scores (3D Mark, etc.)
- [ ] Display architecture and generation
- [ ] Show "Used in" listings section
- [ ] Create loading skeleton page
- [ ] Create not-found error page
- [ ] GPU detail page loads correctly
- [ ] Integrated/discrete badge displays
- [ ] VRAM info is formatted correctly
- [ ] Related listings show correctly

**Files to Create:**
- `apps/web/app/catalog/gpus/[id]/page.tsx`
- `apps/web/app/catalog/gpus/[id]/loading.tsx`
- `apps/web/app/catalog/gpus/[id]/not-found.tsx`
- `apps/web/components/catalog/gpu-detail-layout.tsx`

---

#### TASK-015: Create RAM Spec Detail Page
**Effort:** M | **Feature:** FR-7 | **Dependencies:** TASK-012

- [ ] Create catalog directory structure for RAM specs
- [ ] Implement server component for data fetching at /catalog/ram-specs/[id]
- [ ] Create RAM spec detail layout component
- [ ] Display RAM specifications (capacity, type, speed, latency, voltage, configuration)
- [ ] Show "Used in" listings section
- [ ] Create loading skeleton page
- [ ] Create not-found error page
- [ ] RAM spec detail page loads correctly
- [ ] All specifications display correctly
- [ ] Related listings show correctly

**Files to Create:**
- `apps/web/app/catalog/ram-specs/[id]/page.tsx`
- `apps/web/app/catalog/ram-specs/[id]/loading.tsx`
- `apps/web/app/catalog/ram-specs/[id]/not-found.tsx`
- `apps/web/components/catalog/ram-spec-detail-layout.tsx`

**RAM Spec Fields to Display:**
- Capacity (GB)
- Type (DDR4, DDR5, etc.)
- Speed (MHz)
- Latency (CAS latency)
- Voltage
- Configuration (e.g., "2x8GB")

---

#### TASK-016: Create Storage Profile Detail Page
**Effort:** M | **Feature:** FR-7 | **Dependencies:** TASK-012

- [ ] Create catalog directory structure for storage profiles
- [ ] Implement server component for data fetching at /catalog/storage-profiles/[id]
- [ ] Create storage profile detail layout component
- [ ] Display storage specifications (capacity, type, interface, speeds, IOPS, form factor)
- [ ] Show "Used in" listings section
- [ ] Create loading skeleton page
- [ ] Create not-found error page
- [ ] Storage profile detail page loads correctly
- [ ] Performance metrics are formatted correctly
- [ ] Related listings show correctly

**Files to Create:**
- `apps/web/app/catalog/storage-profiles/[id]/page.tsx`
- `apps/web/app/catalog/storage-profiles/[id]/loading.tsx`
- `apps/web/app/catalog/storage-profiles/[id]/not-found.tsx`
- `apps/web/components/catalog/storage-profile-detail-layout.tsx`

**Storage Profile Fields to Display:**
- Capacity (GB/TB)
- Type (NVMe, SSD, HDD, etc.)
- Interface (M.2, SATA, etc.)
- Sequential read/write speeds
- Random read/write IOPS
- Form factor

---

#### TASK-017: Update EntityLink Component
**Effort:** S | **Feature:** FR-7 | **Dependencies:** TASK-013, TASK-014, TASK-015, TASK-016

- [ ] Map entity types to catalog routes (cpu, gpu, ram-spec, storage-profile)
- [ ] Update href generation logic in EntityLink component
- [ ] Verify all entity links throughout app use EntityLink component
- [ ] All entity links route correctly
- [ ] No 404 errors when clicking entity links
- [ ] Links maintain proper styling
- [ ] Back navigation works from entity pages

**Files to Modify:**
- `apps/web/components/listings/entity-link.tsx`

---

#### TASK-018: Phase 3 Testing & Integration
**Effort:** L | **Dependencies:** TASK-010, TASK-011, TASK-012, TASK-013, TASK-014, TASK-015, TASK-016, TASK-017

- [ ] Product images display in overview modal
- [ ] All entity catalog pages load correctly
- [ ] Entity links navigate without errors
- [ ] "Used in" listings sections show correct data
- [ ] No regressions in existing functionality
- [ ] TypeScript compiles without errors
- [ ] Accessibility audit passes
- [ ] Mobile responsive behavior verified
- [ ] Performance benchmarked (image loading, page navigation)

---

### Phase 4: Polish & Testing

**Duration:** Week 4 (5 days)
**Goal:** Production-ready enhancements with comprehensive testing

#### TASK-019: End-to-End Testing
**Effort:** L

- [ ] Create E2E test file: `apps/web/__tests__/e2e/listings-modal.spec.ts`
- [ ] Create E2E test file: `apps/web/__tests__/e2e/detail-page.spec.ts`
- [ ] Create E2E test file: `apps/web/__tests__/e2e/entity-catalog.spec.ts`
- [ ] Test Overview Modal Journey: open modal, verify image, hover tooltips, click entity links, return to listings
- [ ] Test Detail Page Journey: navigate to detail page, verify tooltips, check specifications tab, view valuation tab, click entity links
- [ ] Test Entity Catalog Journey: navigate to CPU detail, view specs, click "Used in" listing, navigate back
- [ ] Use Playwright for E2E tests
- [ ] Use React Testing Library for component tests
- [ ] Use Jest for unit tests

---

#### TASK-020: Accessibility Audit
**Effort:** M

- [ ] Keyboard navigation works for all interactive elements
- [ ] Focus indicators are visible
- [ ] Screen reader announcements are appropriate
- [ ] Color contrast meets WCAG AA standards
- [ ] Images have proper alt text
- [ ] Forms have proper labels
- [ ] ARIA attributes are used correctly

**Tools to Use:**
- axe DevTools
- WAVE browser extension
- Lighthouse accessibility audit

---

#### TASK-021: Performance Optimization
**Effort:** M

- [ ] Implement lazy loading for images
- [ ] Optimize image sizes
- [ ] Use WebP format where supported
- [ ] Measure Core Web Vitals impact
- [ ] Add React.memo where appropriate
- [ ] Optimize component re-renders
- [ ] Profile with React DevTools
- [ ] Implement proper caching strategies
- [ ] Debounce expensive operations
- [ ] Optimize React Query configuration
- [ ] Achieve Lighthouse score > 90
- [ ] Time to Interactive < 3s
- [ ] Largest Contentful Paint < 2.5s

---

#### TASK-022: Bug Fixes & Refinements
**Effort:** M

- [ ] Review edge case handling
- [ ] Improve error states
- [ ] Refine loading states
- [ ] Apply visual polish
- [ ] Code cleanup and refactoring

---

#### TASK-023: Documentation Updates
**Effort:** S

- [ ] Update component documentation (JSDoc)
- [ ] Document API endpoints
- [ ] Create user-facing changelog
- [ ] Update developer README

---

#### TASK-024: Production Deployment
**Effort:** S

- [ ] All tests passing
- [ ] TypeScript compilation successful
- [ ] No console errors or warnings
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Rollback plan documented
- [ ] Merge feature branch to main
- [ ] Run database migrations
- [ ] Deploy backend services
- [ ] Deploy frontend application
- [ ] Monitor error tracking
- [ ] Verify in production

---

## Work Log

### 2025-10-26 - Session 1

**Status:** Initializing Phase 3-4 execution

**Subagents Used:**
- documentation-writer - Creating progress tracker

**Next Steps:**
- Delegate to lead-architect for Phase 3-4 orchestration
- Begin TASK-010 (Product Image Component) with ui-engineer
- Execute TASK-012 (Backend Endpoints) with python-backend-engineer in parallel

---

## Decisions Log

_To be populated during execution_

---

## Files Changed

### Created
_To be populated during execution_

### Modified
_To be populated during execution_

### Deleted
_To be populated during execution_

---

## Subagent Coordination

### Recommended Subagents by Task Type

| Task | Recommended Subagent | Estimated Duration |
|------|---------------------|-------------------|
| TASK-010 (Product Image Component) | ui-engineer | 2-3 hours |
| TASK-011 (Image Integration) | ui-engineer | 1-2 hours |
| TASK-012 (Backend Endpoints) | python-backend-engineer | 2-3 hours |
| TASK-013 (CPU Detail Page) | frontend-developer | 3-4 hours |
| TASK-014 (GPU Detail Page) | frontend-developer | 2-3 hours |
| TASK-015 (RAM Spec Detail Page) | frontend-developer | 2 hours |
| TASK-016 (Storage Profile Detail Page) | frontend-developer | 2 hours |
| TASK-017 (EntityLink Update) | ui-engineer | 1 hour |
| TASK-018 (Phase 3 Testing) | lead-architect (coordinate) | 4-6 hours |
| TASK-019 (E2E Testing) | qa-engineer or frontend-developer | 4-6 hours |
| TASK-020 (Accessibility) | web-accessibility-checker | 2-3 hours |
| TASK-021 (Performance) | react-performance-optimizer | 3-4 hours |
| TASK-022 (Bug Fixes) | debugger or lead-architect | 2-4 hours |
| TASK-023 (Documentation) | documentation-writer | 2 hours |
| TASK-024 (Deployment) | lead-architect | 1-2 hours |

**Total Estimated Duration:** ~50-70 hours (2 weeks with parallel work)

---

## Dependencies

### Task Dependencies Map

```
TASK-010 ─┐
          ├─→ TASK-011 ─┐
TASK-012 ─┤            ├─→ TASK-018 ─→ Phase 3 Complete
          ├─→ TASK-013 ─┤
          ├─→ TASK-014 ─┤
          ├─→ TASK-015 ─┤
          ├─→ TASK-016 ─┤
          └─→ TASK-017 ─┘

Phase 3 Complete ─→ TASK-019 ─┐
                    TASK-020 ─┤
                    TASK-021 ─┼─→ TASK-022 ─→ TASK-023 ─→ TASK-024 ─→ Complete
                    (Parallel) ─┘
```

### Critical Path

1. TASK-012 (Backend endpoints) - Must complete first
2. TASK-010 (Product image) - Needed for integration
3. TASK-013, TASK-014, TASK-015, TASK-016 (Detail pages) - Can work in parallel once backend ready
4. TASK-011, TASK-017 (Integrations) - Depend on feature components
5. TASK-018 (Phase 3 testing) - Verification before Phase 4
6. TASK-019-024 (Phase 4 tasks) - Sequential polish and deployment

---

## Notes

### Assets Status
- **Required:** Fallback images for TASK-010 (intel-logo.svg, amd-logo.svg, mini-pc-icon.svg, desktop-icon.svg, generic-pc.svg)
- **Source:** Need to create or source from design team
- **Blocking:** TASK-010 until assets are available

### Backend Dependencies
- **TASK-012:** Must verify/create entity detail endpoints before frontend development
- **Impact:** Blocks TASK-013, TASK-014, TASK-015, TASK-016
- **Recommended:** Coordinate with python-backend-engineer early

### Frontend Dependencies
- **TASK-010:** ProductImageDisplay component needed for TASK-011
- **TASK-012:** Entity endpoints needed for all detail pages (TASK-013-016)
- **TASK-013-016:** Must complete before TASK-017 (EntityLink routing)

### Testing Strategy
- **Phase 3 Testing (TASK-018):** Integration testing of new features
- **Phase 4 E2E (TASK-019):** Full user journey testing
- **Accessibility (TASK-020):** WCAG AA compliance verification
- **Performance (TASK-021):** Core Web Vitals optimization

### Deployment Considerations
- Backward compatibility with existing API
- Database migrations if schema changes needed
- Environment variable configuration for API endpoints
- Rollback plan for production safety

### Quality Gates

Before advancing to next task:
1. Code compiles without TypeScript errors
2. Unit tests passing for component
3. No console errors or warnings
4. Accessibility baseline met
5. Mobile responsive verified

---

## Reference Links

- **Implementation Plan:** `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/enhance-v2/implementation-plan-v2-ph3-4.md`
- **PRD:** `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/enhance-v2/prd-listings-facelift-v2.md`
- **Phase 1-2 Progress:** `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/enhance-v2/progress/phase-1-2-progress.md`
- **Tooltip Investigation:** `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/investigations/tooltip-investigation-report.md`
- **Original Requirements:** `/mnt/containers/deal-brain/docs/project_plans/listings-facelift-enhancement/enhance-v2/listings-facelift-enhancements-v2.md`
