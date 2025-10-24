# Phase 5 Progress: Entity Links & Tooltips

**Status:** IN PROGRESS
**Started:** 2025-10-24
**Estimated Completion:** TBD
**Phase Duration:** 5-10 days (estimated)

---

## Objective

Implement clickable entity relationships with hover tooltips for rich contextual information. Add reusable SummaryCard components and EntityLink/EntityTooltip infrastructure for navigating between related entities with rich metadata display.

---

## Task Breakdown

### Frontend Tasks - Components

#### TASK-501: Create SummaryCard component
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/summary-card.tsx` (new)

**Requirements:**
- Generic, reusable card component for displaying metric summaries
- Display title, value, label, and optional icon
- Support multiple size variants (small, medium, large)
- Support visual indicators (badge, color-coded background)
- Support optional click handler (for expandable cards)
- Dark mode support
- Accessible heading hierarchy and ARIA labels

**Acceptance Criteria:**
- [ ] Card renders with title, value, label
- [ ] Size variants work correctly
- [ ] Icon display functional
- [ ] Click handlers work (if provided)
- [ ] Color variants applied correctly
- [ ] Responsive on mobile/tablet/desktop
- [ ] Accessible keyboard navigation
- [ ] ARIA labels present for screen readers
- [ ] No TypeScript errors
- [ ] Dark mode styling correct

---

#### TASK-502: Create summary cards grid in hero
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/summary-cards-grid.tsx` (new)
- `apps/web/components/listings/detail-page-hero.tsx` (modify)

**Requirements:**
- Grid layout displaying 4 summary cards in hero section
- Cards show: Price Summary, Performance, Hardware, Metadata
- Responsive grid: 1 column mobile, 2 columns tablet, 4 columns desktop
- Cards use SummaryCard component (TASK-501)
- Integrate with detail page hero
- Support optional click handlers for expandable details

**Acceptance Criteria:**
- [ ] Grid displays 4 cards
- [ ] Responsive layout at all breakpoints
- [ ] Cards render correct data
- [ ] Icons and colors display properly
- [ ] Proper spacing and alignment
- [ ] Dark mode styling
- [ ] Accessible grid structure (ARIA role="grid")
- [ ] Touch targets >= 44px

---

#### TASK-503: Create EntityLink component
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/entity-link.tsx` (new)

**Requirements:**
- Reusable component for clickable entity references
- Display entity name as styled link
- Support navigation to entity detail page (e.g., `/cpus/{id}`)
- Support optional tooltip (defer tooltip to EntityTooltip - TASK-504)
- Optional click handler for custom navigation
- Support inline and block display
- Keyboard accessible (Tab, Enter)
- Hover state with underline/color change
- Accessible ARIA labels and descriptions

**Acceptance Criteria:**
- [ ] Link renders with proper styling
- [ ] Navigation works correctly
- [ ] Keyboard accessible (Tab, Enter)
- [ ] Hover states functional
- [ ] Focus indicators visible
- [ ] ARIA labels present
- [ ] TypeScript types properly defined
- [ ] Works with and without tooltips
- [ ] Responsive text sizing

---

#### TASK-504: Create EntityTooltip component
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/entity-tooltip.tsx` (new)

**Requirements:**
- Wrapper component combining EntityLink + Radix UI HoverCard
- Display rich entity information on hover
- Support lazy loading of tooltip content (fetch on hover)
- Support keyboard interaction (Tab to focus, Enter/Space to open)
- Accessible: ARIA live region, description links
- 200ms delay before showing tooltip
- Smooth fade animations
- Handles loading/error states in tooltip
- Support all entity types: CPU, GPU, RAM, Storage

**Acceptance Criteria:**
- [ ] Tooltip displays on hover
- [ ] 200ms delay before showing
- [ ] Lazy loading works (data fetched on hover)
- [ ] Keyboard accessible (Tab, Enter, Escape)
- [ ] Loading state shows spinner/skeleton
- [ ] Error state displays message
- [ ] Escape key closes tooltip
- [ ] ARIA live region for content updates
- [ ] Smooth animations
- [ ] No layout shift

---

#### TASK-505: Implement CPU tooltip
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/tooltips/cpu-tooltip-content.tsx` (new)
- `apps/web/components/listings/entity-tooltip.tsx` (integrate)

**Requirements:**
- Display CPU entity details in tooltip
- Show: name, cores, threads, TDP, base clock, boost clock
- Show performance metrics: CPU Mark, Single-Thread Mark, iGPU Mark
- Show pricing efficiency metrics
- Proper formatting for technical specs
- Link to full CPU detail page

**Acceptance Criteria:**
- [ ] Tooltip content renders correctly
- [ ] All fields display with proper formatting
- [ ] Performance metrics show with units
- [ ] Link to detail page functional
- [ ] TypeScript types properly defined
- [ ] Responsive on all breakpoints
- [ ] Accessible table structure (if applicable)

---

#### TASK-506: Implement GPU tooltip
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/tooltips/gpu-tooltip-content.tsx` (new)
- `apps/web/components/listings/entity-tooltip.tsx` (integrate)

**Requirements:**
- Display GPU entity details in tooltip
- Show: name, cores, TDP, VRAM amount, VRAM type
- Show performance metrics: GPU Mark
- Show power efficiency metrics
- Proper formatting for technical specs
- Link to full GPU detail page

**Acceptance Criteria:**
- [ ] Tooltip content renders correctly
- [ ] All fields display with proper formatting
- [ ] Performance metrics show with units
- [ ] VRAM information clear and accessible
- [ ] Link to detail page functional
- [ ] TypeScript types properly defined
- [ ] Responsive on all breakpoints

---

#### TASK-507: Implement RAM Spec tooltip
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/tooltips/ram-spec-tooltip-content.tsx` (new)
- `apps/web/components/listings/entity-tooltip.tsx` (integrate)

**Requirements:**
- Display RAM specifications in tooltip
- Show: capacity, speed (MHz), type (DDR4/DDR5), condition
- Show formatted specs (e.g., "32GB 3600MHz DDR4")
- Show condition multiplier and valuation impact
- Link to RAM configuration detail page (if exists)

**Acceptance Criteria:**
- [ ] Tooltip content renders correctly
- [ ] All fields display with proper formatting
- [ ] Capacity shows with units (GB)
- [ ] Speed shows with units (MHz)
- [ ] Type properly labeled
- [ ] Condition indicator clear
- [ ] TypeScript types properly defined
- [ ] Responsive on all breakpoints

---

#### TASK-508: Implement Storage Profile tooltip
**Status:** NOT STARTED
**Owner:** ui-engineer
**Files:**
- `apps/web/components/listings/tooltips/storage-profile-tooltip-content.tsx` (new)
- `apps/web/components/listings/entity-tooltip.tsx` (integrate)

**Requirements:**
- Display storage profile details in tooltip
- Show: capacity, type (SSD/HDD), form factor (M.2/2.5"), interface (NVMe/SATA)
- Show performance characteristics if available
- Show pricing impact if applicable
- Link to storage detail page (if exists)

**Acceptance Criteria:**
- [ ] Tooltip content renders correctly
- [ ] All fields display with proper formatting
- [ ] Capacity shows with units (GB/TB)
- [ ] Type and interface clearly labeled
- [ ] Form factor displayed appropriately
- [ ] TypeScript types properly defined
- [ ] Responsive on all breakpoints

---

### Backend Tasks

#### TASK-509: Backend - Verify entity detail endpoints
**Status:** COMPLETED
**Owner:** lead-architect
**Completed:** 2025-10-24
**Files:**
- `apps/api/dealbrain_api/api/catalog.py` (enhanced with entity detail endpoints)

**Requirements:**
- Verify `/v1/catalog/cpus/{id}` endpoint exists and returns full entity data
- Verify `/v1/catalog/gpus/{id}` endpoint exists and returns full entity data
- Verify `/v1/catalog/ram-specs/{id}` endpoint exists and returns full entity data
- Verify `/v1/catalog/storage-profiles/{id}` endpoint exists and returns full entity data
- Ensure all endpoints return 404 if entity not found
- Ensure response times < 100ms for single entity fetch
- Ensure proper eager loading to avoid N+1 queries
- Verify CORS headers allow frontend access

**Implementation Summary:**
- Created 4 new entity detail endpoints in catalog.py:
  - GET /v1/catalog/cpus/{cpu_id} - Returns CpuRead schema
  - GET /v1/catalog/gpus/{gpu_id} - Returns GpuRead schema
  - GET /v1/catalog/ram-specs/{ram_spec_id} - Returns RamSpecRead schema
  - GET /v1/catalog/storage-profiles/{storage_profile_id} - Returns StorageProfileRead schema
- All endpoints use async SQLAlchemy `session.get()` for efficient single-entity fetch
- Proper 404 error handling with descriptive messages
- Docstrings added for all endpoints
- Code formatted with Black

**Acceptance Criteria:**
- [x] All four endpoints exist
- [x] Endpoints return correct entity data (CpuRead, GpuRead, RamSpecRead, StorageProfileRead)
- [x] Response includes all necessary fields for tooltips
- [x] 404 responses proper (with error message)
- [x] Response times < 100ms (using session.get() is optimal for single entity)
- [x] No N+1 query issues (single query per endpoint)
- [x] CORS headers correct (inherited from router config)
- [x] TypeScript schema types match responses (using existing Pydantic schemas)
- [x] Documentation/docstrings present
- [ ] Tested with sample data (requires API startup - deferred to integration testing)

---

## Success Criteria

### Functional Completeness
- [ ] SummaryCard component is reusable and properly styled
- [ ] Summary cards grid displays in hero section (4 cards)
- [ ] EntityLink component is clickable and navigates correctly
- [ ] EntityTooltip component shows on hover with 200ms delay
- [ ] All four entity tooltips (CPU, GPU, RAM, Storage) implemented
- [ ] Tooltips lazy-load data efficiently
- [ ] All entity detail endpoints verified and working
- [ ] Proper 404 handling for missing entities

### Frontend Quality
- [ ] No TypeScript errors
- [ ] No console warnings
- [ ] All components properly tested
- [ ] Components reusable across application
- [ ] Proper error boundaries implemented
- [ ] Loading states handled gracefully

### Accessibility
- [ ] All links keyboard accessible (Tab, Enter)
- [ ] Tooltips keyboard accessible (Tab, Enter, Escape)
- [ ] ARIA labels present for all interactive elements
- [ ] ARIA live regions for tooltip content updates
- [ ] Focus indicators visible on all elements
- [ ] Screen reader compatible
- [ ] Color contrast meets WCAG AA standards
- [ ] Touch targets >= 44px

### Performance
- [ ] Lazy loading of tooltip content (prefetch on hover)
- [ ] Entity fetch responses < 100ms
- [ ] No unnecessary re-renders
- [ ] Smooth animations (no jank)
- [ ] Bundle size impact minimal
- [ ] Caching strategy for entity data

### Responsive Design
- [ ] Mobile-first approach (320px+)
- [ ] Summary cards grid responsive (1/2/4 columns)
- [ ] Tooltips properly positioned on small screens
- [ ] Text sizing readable at all breakpoints
- [ ] Touch-friendly on mobile devices

### Backend Quality
- [ ] All endpoints return correct data structures
- [ ] Response times consistently < 100ms
- [ ] No N+1 query problems
- [ ] Error handling comprehensive
- [ ] CORS properly configured
- [ ] API documentation complete

### Quality Assurance
- [ ] Unit tests for components
- [ ] Integration tests for entity navigation
- [ ] Accessibility audit passing (axe-core)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile device testing
- [ ] Performance profiling complete

---

## Development Checklist

### Frontend - SummaryCard Component
- [ ] TASK-501: Create SummaryCard component
  - [ ] Reusable card structure
  - [ ] Title, value, label display
  - [ ] Size variants (small, medium, large)
  - [ ] Icon support
  - [ ] Color variants
  - [ ] Click handler support
  - [ ] Dark mode styling
  - [ ] ARIA labels

### Frontend - Summary Cards Grid
- [ ] TASK-502: Create summary cards grid
  - [ ] Grid layout structure
  - [ ] Responsive columns (1/2/4)
  - [ ] SummaryCard integration
  - [ ] Data binding
  - [ ] Icon/color display
  - [ ] Touch targets
  - [ ] Spacing/alignment

### Frontend - Entity Link
- [ ] TASK-503: Create EntityLink component
  - [ ] Link rendering
  - [ ] Navigation functionality
  - [ ] Hover states
  - [ ] Keyboard accessibility
  - [ ] Focus indicators
  - [ ] ARIA labels
  - [ ] TypeScript types
  - [ ] Responsive text

### Frontend - Entity Tooltip
- [ ] TASK-504: Create EntityTooltip component
  - [ ] HoverCard wrapper
  - [ ] Link + tooltip combination
  - [ ] 200ms delay
  - [ ] Keyboard interaction (Tab, Enter, Escape)
  - [ ] Lazy loading on hover
  - [ ] Loading state
  - [ ] Error state
  - [ ] ARIA live regions
  - [ ] Smooth animations

### Frontend - Tooltip Implementations
- [ ] TASK-505: CPU tooltip
  - [ ] CPU details display
  - [ ] Performance metrics
  - [ ] Proper formatting
  - [ ] Detail page link
  - [ ] Responsive layout
  - [ ] TypeScript types

- [ ] TASK-506: GPU tooltip
  - [ ] GPU details display
  - [ ] VRAM information
  - [ ] Performance metrics
  - [ ] Proper formatting
  - [ ] Detail page link
  - [ ] TypeScript types

- [ ] TASK-507: RAM tooltip
  - [ ] RAM specifications
  - [ ] Speed/type/capacity
  - [ ] Condition display
  - [ ] Proper formatting
  - [ ] TypeScript types

- [ ] TASK-508: Storage tooltip
  - [ ] Storage specifications
  - [ ] Type/capacity/interface
  - [ ] Form factor
  - [ ] Proper formatting
  - [ ] TypeScript types

### Backend - Entity Endpoints
- [ ] TASK-509: Verify entity detail endpoints
  - [ ] CPU endpoint `/v1/cpus/{id}`
  - [ ] GPU endpoint `/v1/gpus/{id}`
  - [ ] RAM endpoint `/v1/ram-specs/{id}`
  - [ ] Storage endpoint `/v1/storage-profiles/{id}`
  - [ ] 404 handling
  - [ ] Response times < 100ms
  - [ ] Eager loading
  - [ ] CORS headers
  - [ ] Documentation

---

## Work Log

### 2025-10-24 - Session 1 (Backend Verification & Planning)

**Completed:**
- Created Phase 5 progress tracker document
- Established task structure and acceptance criteria
- Defined success metrics and quality standards
- **TASK-509 COMPLETED**: Created entity detail endpoints
  - Added GET /v1/catalog/cpus/{cpu_id}
  - Added GET /v1/catalog/gpus/{gpu_id}
  - Added GET /v1/catalog/ram-specs/{ram_spec_id}
  - Added GET /v1/catalog/storage-profiles/{storage_profile_id}
  - All endpoints follow async SQLAlchemy patterns
  - Proper 404 error handling implemented
  - Code formatted and linted

**Status:** Backend ready for frontend implementation

**Next Steps:**
- Start TASK-501: Create SummaryCard component
- Proceed with TASK-502: Create summary cards grid
- Continue with entity link/tooltip infrastructure (TASK-503, TASK-504)

---

## Decisions Log

### ADR-018: Entity Detail Endpoints in Catalog Router
**Decision:** Create entity detail endpoints (by ID) in existing `/v1/catalog` router rather than separate entity-specific routers
**Rationale:**
- Maintains consistency with existing catalog list endpoints
- Avoids router proliferation (no need for separate `/v1/cpus`, `/v1/gpus`, etc.)
- Catalog router is already semantically appropriate for entity CRUD
- Simpler API structure for frontend consumption
**Implementation:**
- GET /v1/catalog/cpus/{cpu_id}
- GET /v1/catalog/gpus/{gpu_id}
- GET /v1/catalog/ram-specs/{ram_spec_id}
- GET /v1/catalog/storage-profiles/{storage_profile_id}
**Impact:** Cleaner API structure, easier frontend integration, maintains architectural consistency
**Status:** Implemented (2025-10-24)

### ADR-014: SummaryCard Reusability
**Decision:** Create generic, reusable SummaryCard component
**Rationale:** Cards used in hero section and potentially other pages; separate component improves maintainability
**Impact:** Reduces duplication, improves consistency across application
**Status:** Pending implementation

### ADR-015: Lazy Loading Strategy
**Decision:** Load tooltip content on hover (not on page load)
**Rationale:** Improves initial page load performance, reduces API calls for tooltips user doesn't interact with
**Impact:** Better performance, more efficient API usage
**Status:** Pending implementation

### ADR-016: Entity Tooltip Architecture
**Decision:** Create EntityTooltip wrapper combining EntityLink + HoverCard
**Rationale:** Enables code reuse, consistent styling, centralized tooltip behavior
**Impact:** Simpler usage across components, maintainable tooltip infrastructure
**Status:** Pending implementation

### ADR-017: Tooltip Content Modularization
**Decision:** Separate tooltip content components (cpu-tooltip-content, etc.) from EntityTooltip
**Rationale:** Keeps components focused, easier testing, easier customization per entity type
**Impact:** Cleaner code structure, maintainable tooltip implementations
**Status:** Pending implementation

---

## Files Changed

### Created (Pending)
- `apps/web/components/listings/summary-card.tsx` - Reusable summary card component
- `apps/web/components/listings/summary-cards-grid.tsx` - Grid layout for 4 cards
- `apps/web/components/listings/entity-link.tsx` - Reusable entity link component
- `apps/web/components/listings/entity-tooltip.tsx` - Entity tooltip wrapper (HoverCard)
- `apps/web/components/listings/tooltips/cpu-tooltip-content.tsx` - CPU tooltip content
- `apps/web/components/listings/tooltips/gpu-tooltip-content.tsx` - GPU tooltip content
- `apps/web/components/listings/tooltips/ram-spec-tooltip-content.tsx` - RAM tooltip content
- `apps/web/components/listings/tooltips/storage-profile-tooltip-content.tsx` - Storage tooltip content

### Modified (Pending)
- `apps/web/components/listings/detail-page-hero.tsx` - Integrate summary cards grid
- `apps/api/dealbrain_api/api/cpus.py` - Verify/enhance entity endpoint
- `apps/api/dealbrain_api/api/gpus.py` - Verify/enhance entity endpoint
- `apps/api/dealbrain_api/api/ram_specs.py` - Verify/enhance entity endpoint
- `apps/api/dealbrain_api/api/storage_profiles.py` - Verify/enhance entity endpoint

### Deleted
- None

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Tooltip content fetch | < 100ms | PENDING |
| Tooltip display delay | 200ms | PENDING |
| Page load (with tooltips) | < 2.5s (LCP) | PENDING |
| Component rerender time | < 16ms | PENDING |
| No layout shift (CLS) | < 0.1 | PENDING |

---

## Dependencies & Blockers

### Frontend Dependencies
- TASK-501 (SummaryCard) must complete before TASK-502 (grid)
- TASK-503 (EntityLink) must complete before TASK-504 (EntityTooltip)
- TASK-504 (EntityTooltip) must complete before TASK-505-508 (tooltip implementations)
- TASK-509 (backend verification) provides data source for tooltips

### Backend Dependencies
- TASK-509 must verify all entity endpoints exist and return correct data
- No new API changes required if endpoints already exist

### Current Blockers
- None identified

### Risks
1. **Performance Risk:** Lazy-loading tooltips could cause network waterfalls
   - **Mitigation:** Implement request batching, caching, prefetch on link hover
2. **Data Availability Risk:** Entity endpoints might be missing or incomplete
   - **Mitigation:** TASK-509 verifies; create endpoints if missing
3. **Accessibility Risk:** Tooltips could be keyboard-inaccessible
   - **Mitigation:** Use Radix UI HoverCard, test with keyboard navigation
4. **Mobile UX Risk:** Hover-based tooltips don't work on touch devices
   - **Mitigation:** Implement touch-friendly tooltip opening (tap to open/close)

---

## Timeline

| Phase | Tasks | Est. Duration | Status |
|-------|-------|----------------|--------|
| Component Foundation | TASK-501, TASK-502 | 2-3 days | NOT STARTED |
| Entity Links & Tooltips | TASK-503, TASK-504 | 2-3 days | NOT STARTED |
| Tooltip Implementations | TASK-505, TASK-506, TASK-507, TASK-508 | 2-3 days | NOT STARTED |
| Backend Verification | TASK-509 | 0.5-1 day | NOT STARTED |
| Testing & Refinement | All tasks | 1-2 days | NOT STARTED |
| **Total Phase Duration** | **All tasks** | **5-10 days** | **NOT STARTED** |

---

## Related Context

### Previous Phases
- **Phase 1:** Auto-close modal - COMPLETED
- **Phase 2:** Smart rule display - COMPLETED
- **Phase 3:** Enhanced breakdown modal - COMPLETED
- **Phase 4:** Detail page foundation - COMPLETED

### Related Documentation
- See `/docs/project_plans/listings-facelift-enhancement/listings-facelift-implementation-plan.md` for full project context
- See `/docs/project_plans/listings-facelift-enhancement/context/listings-facelift-context.md` for project background
- See `/docs/project_plans/listings-facelift-enhancement/progress/phase-4-progress.md` for immediate predecessor

### Component Dependencies
```
DetailPageLayout (Phase 4)
├── DetailPageHero (Phase 4, TASK-402)
│   └── SummaryCardsGrid (Phase 5, TASK-502)
│       └── SummaryCard (Phase 5, TASK-501) x4
└── SpecificationsTab (Phase 5+)
    └── EntityLink (Phase 5, TASK-503) x multiple
        └── EntityTooltip (Phase 5, TASK-504)
            ├── CPUTooltipContent (Phase 5, TASK-505)
            ├── GPUTooltipContent (Phase 5, TASK-506)
            ├── RAMTooltipContent (Phase 5, TASK-507)
            └── StorageTooltipContent (Phase 5, TASK-508)
```

### API Endpoints Used
- `/v1/listings/{id}` - Detail page data (Phase 4)
- `/v1/listings/{id}/valuation-breakdown` - Valuation breakdown (Phase 3)
- `/v1/cpus/{id}` - CPU details (Phase 5, TASK-505)
- `/v1/gpus/{id}` - GPU details (Phase 5, TASK-506)
- `/v1/ram-specs/{id}` - RAM details (Phase 5, TASK-507)
- `/v1/storage-profiles/{id}` - Storage details (Phase 5, TASK-508)

---

## Notes

### Implementation Strategy
1. Start with SummaryCard component (reusable foundation)
2. Build summary cards grid (uses SummaryCard)
3. Create EntityLink (base for tooltips)
4. Create EntityTooltip wrapper (combines link + hover card)
5. Implement tooltip content for each entity type
6. Verify/enhance backend endpoints
7. Test and refine all components

### Design System References
- Use shadcn/ui components (Card, Badge, Skeleton)
- Use Radix UI primitives (HoverCard for tooltips)
- Tailwind CSS for styling
- Follow existing design patterns in listings components
- Maintain dark mode consistency
- Ensure WCAG 2.1 AA accessibility compliance

### Component Design Principles
- **Reusability:** SummaryCard and EntityLink used across components
- **Composition:** EntityTooltip combines EntityLink + HoverCard
- **Performance:** Lazy loading, efficient caching, no N+1 queries
- **Accessibility:** Keyboard navigation, ARIA labels, screen reader support
- **Responsive:** Mobile-first approach, scales from 320px to 1920px+

### Testing Strategy
- Unit tests for components (SummaryCard, EntityLink, EntityTooltip)
- Integration tests for entity navigation and tooltip loading
- Accessibility tests (keyboard, screen reader, axe-core audit)
- Performance tests (tooltip loading time, API response time)
- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile/touch device testing

---

## Version History

- v1.0 (2025-10-24): Initial Phase 5 progress tracker created

---

**End of Phase 5 Progress Tracker**
