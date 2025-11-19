# All-Phases Progress: UX Improvements & Data Enhancement

**Status**: NOT STARTED
**Last Updated**: 2025-11-18
**Completion**: 0% (0 of 34 story points)
**PRD**: [ux-improvements-nov-18-v1.md](../../../docs/project_plans/PRDs/enhancements/ux-improvements-nov-18-v1.md)
**Implementation Plan**: [ux-improvements-nov-18-v1.md](../../../docs/project_plans/implementation_plans/enhancements/ux-improvements-nov-18-v1.md)

---

## Phase Overview

| Phase | Title | Effort | Status | Completion | Key Files |
|-------|-------|--------|--------|-----------|-----------|
| 1 | Critical UI Bug Fixes | 2 pts | NOT STARTED | 0% | `slider.tsx`, `data-table.tsx` |
| 2 | Listing Workflow Enhancements | 5 pts | NOT STARTED | 0% | `quick-edit-modal.tsx`, `listing-view-modal.tsx` |
| 3 | Real-Time Updates Infrastructure | 8 pts | NOT STARTED | 0% | `events.py`, `use-event-stream.ts` |
| 4 | Amazon Import Enhancement | 8 pts | NOT STARTED | 0% | `amazon_scraper.py`, `nlp_extractor.py` |
| 5 | CPU Catalog Improvements | 3 pts | NOT STARTED | 0% | `cpus/page.tsx`, `cpu-filters.tsx` |
| 6 | Column Selector | 8 pts | NOT STARTED | 0% | `column-selector.tsx`, `use-column-preferences.ts` |

**Total**: 34 story points

---

## Phase 1: Critical UI Bug Fixes

**Assigned Subagent(s)**: ui-engineer-enhanced, test-automator
**Effort**: 2 story points
**Duration**: 2-3 days
**Status**: NOT STARTED

### Completion Checklist

- [ ] **UI-001**: Implement dual-handle range sliders (1 pt)
      **Assigned Subagent(s)**: ui-engineer-enhanced
      **Description**: Replace single-handle sliders with dual-handle components for min/max range selection
      **Files**: `apps/web/components/ui/slider.tsx`, `apps/web/components/ui/range-slider.tsx`, `apps/web/components/cpus/cpu-filters.tsx`
      **Acceptance Criteria**:
      - All range sliders show two handles (min and max)
      - Current range values displayed (e.g., "1.5 GHz - 4.2 GHz")
      - Touch-friendly on mobile devices
      - Accessible (keyboard navigation, ARIA labels)

- [ ] **UI-002**: Fix hidden table rows (0.5 pt)
      **Assigned Subagent(s)**: ui-engineer-enhanced
      **Description**: Adjust table layout to prevent first row hiding behind sticky header
      **Files**: `apps/web/components/ui/data-table.tsx`, `apps/web/app/listings/page.tsx`, `apps/web/app/cpus/page.tsx`
      **Acceptance Criteria**:
      - First row fully visible without scrolling
      - Sticky header doesn't overlap content
      - Fix applies to all list views (listings, CPUs, etc.)

- [ ] **UI-003**: Cross-browser testing (0.5 pt)
      **Assigned Subagent(s)**: test-automator
      **Description**: Test slider and table fixes across browsers and devices
      **Acceptance Criteria**:
      - Verified on Chrome, Firefox, Safari
      - Tested on desktop and mobile (iOS, Android)
      - No regressions in existing UI functionality

### Success Criteria

- [ ] All range sliders have two handles and display current range
- [ ] Sliders accessible via keyboard (tab, arrow keys)
- [ ] First table row fully visible in all list views
- [ ] Cross-browser compatibility verified
- [ ] Mobile-responsive on iOS and Android

### Key Files

- `apps/web/components/ui/slider.tsx` - Base slider component
- `apps/web/components/ui/range-slider.tsx` - New dual-handle slider
- `apps/web/components/ui/data-table.tsx` - Table component fix
- `apps/web/components/cpus/cpu-filters.tsx` - CPU filter sliders

### Notes

- Evaluate slider libraries: shadcn/ui Slider, react-range, rc-slider
- Ensure WCAG AA accessibility compliance
- Test on all pages with range sliders (CPU filters, price ranges, etc.)

---

## Phase 2: Listing Workflow Enhancements

**Assigned Subagent(s)**: ui-engineer-enhanced, frontend-developer, test-automator
**Effort**: 5 story points
**Duration**: 5-7 days
**Status**: NOT STARTED
**Dependencies**: None

### Completion Checklist

- [ ] **WF-001**: Expand quick edit modal fields (2 pts)
      **Assigned Subagent(s)**: ui-engineer-enhanced
      **Description**: Add CPU, RAM, Storage, GPU fields to quick edit modal
      **Files**: `apps/web/components/listings/quick-edit-modal.tsx`, `apps/web/components/listings/listing-form-fields.tsx`, `apps/web/lib/validations/listing-schema.ts`
      **Acceptance Criteria**:
      - Fields match full edit page (components, validation)
      - Searchable dropdowns for CPU/GPU
      - RAM: capacity + type dropdowns
      - Storage: capacity + type dropdowns
      - Pre-populated with current listing data
      - Modal scrolls if content exceeds viewport

- [ ] **WF-002**: Add Quick Edit button to view modal (1 pt)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Add "Quick Edit" button to listing view modal toolbar
      **Files**: `apps/web/components/listings/listing-view-modal.tsx`
      **Acceptance Criteria**:
      - Button appears in bottom toolbar of view modal
      - Opens quick edit modal directly
      - Modal pre-populated with listing data
      - No navigation away from view modal

- [ ] **WF-003**: Add Edit button to listing detail page (0.5 pt)
      **Assigned Subagent(s)**: ui-engineer-enhanced
      **Description**: Add "Edit" button to listing detail page header
      **Files**: `apps/web/app/listings/[id]/page.tsx`
      **Acceptance Criteria**:
      - Button in top-right corner next to "Delete"
      - Opens full edit page: `/listings/[id]/edit`
      - Consistent styling with other action buttons

- [ ] **WF-004**: Update quick edit modal component library (1 pt)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Extract quick edit fields as reusable components
      **Files**: `apps/web/components/listings/listing-form-fields.tsx`
      **Acceptance Criteria**:
      - Components reusable across contexts (full edit, quick edit)
      - TypeScript types defined
      - Props match full edit page
      - Validation schemas shared

- [ ] **WF-005**: Integration testing for workflows (0.5 pt)
      **Assigned Subagent(s)**: test-automator
      **Description**: Test complete edit workflows (view → quick edit → save)
      **Acceptance Criteria**:
      - View → Quick Edit workflow works end-to-end
      - Detail page → Edit workflow works
      - Data persists correctly to backend
      - No regressions in existing edit flows

### Success Criteria

- [ ] Quick edit modal includes CPU, RAM, Storage, GPU fields
- [ ] Fields match full edit page (validation, components, UX)
- [ ] Quick Edit button appears in view modal footer
- [ ] Quick Edit opens pre-populated with listing data
- [ ] Edit button appears on listing detail page header
- [ ] Edit button navigates to full edit page
- [ ] All workflows tested end-to-end
- [ ] Mobile-responsive on small screens

### Key Files

- `apps/web/components/listings/quick-edit-modal.tsx` - Quick edit modal
- `apps/web/components/listings/listing-view-modal.tsx` - View modal
- `apps/web/components/listings/listing-form-fields.tsx` - Shared form fields
- `apps/web/app/listings/[id]/page.tsx` - Listing detail page
- `apps/web/lib/validations/listing-schema.ts` - Validation schemas

### Notes

- Reuse field components from full edit page for consistency
- Ensure validation matches between quick edit and full edit
- Test modal overflow behavior on small screens

---

## Phase 3: Real-Time Updates Infrastructure

**Assigned Subagent(s)**: backend-architect, python-backend-engineer, frontend-developer
**Effort**: 8 story points
**Duration**: 7-10 days
**Status**: NOT STARTED
**Dependencies**: None

### Completion Checklist

- [ ] **RT-001**: Design SSE event architecture (1 pt)
      **Assigned Subagent(s)**: backend-architect
      **Description**: Design event types, payload schemas, pub/sub patterns
      **Deliverables**: Architecture document with event types, schemas, Redis pub/sub strategy
      **Acceptance Criteria**:
      - Event types documented (`listing.created`, `listing.updated`, `listing.deleted`, `valuation.recalculated`)
      - Payload schemas defined (TypeScript + Python)
      - Redis pub/sub channel design (`dealbrain:events`)

- [ ] **RT-002**: Implement SSE endpoint in FastAPI (2 pts)
      **Assigned Subagent(s)**: python-backend-engineer
      **Description**: Create SSE endpoint for streaming events to clients
      **Files**: `apps/api/dealbrain_api/api/v1/events.py`
      **Acceptance Criteria**:
      - `/api/v1/events` endpoint created
      - Handles client connections via EventSourceResponse
      - Streams events from Redis pub/sub
      - Supports client reconnection
      - Graceful disconnect handling

- [ ] **RT-003**: Implement event publishers (1 pt)
      **Assigned Subagent(s)**: python-backend-engineer
      **Description**: Add event publishing to listing create/update endpoints
      **Files**: `apps/api/dealbrain_api/services/listings.py`
      **Acceptance Criteria**:
      - Publishes `listing.created` event on create
      - Publishes `listing.updated` event on update (with changed fields)
      - Publishes `listing.deleted` event on delete
      - Event payloads include listing ID, timestamp, changes

- [ ] **RT-004**: Implement frontend SSE client (2 pts)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Create React hook for SSE connection and event handling
      **Files**: `apps/web/hooks/use-event-stream.ts`, `apps/web/hooks/use-listing-updates.ts`
      **Acceptance Criteria**:
      - `useEventStream` hook created for generic SSE connection
      - Handles connection lifecycle (connect, disconnect, error)
      - Parses event types and payloads
      - Auto-reconnects on disconnect (exponential backoff)
      - `useListingUpdates` hook for listing-specific events

- [ ] **RT-005**: Implement auto-recalculation triggers (1.5 pts)
      **Assigned Subagent(s)**: python-backend-engineer
      **Description**: Trigger valuation recalc when listings/rules change
      **Files**: `apps/api/dealbrain_api/services/listings.py`, `apps/api/dealbrain_api/services/valuation_rules.py`, `apps/api/dealbrain_api/tasks/recalculation.py`
      **Acceptance Criteria**:
      - Recalc queued on price/component change (CPU, GPU, RAM, Storage)
      - Recalc queued on valuation rule change (all affected listings)
      - Only affected listings recalculated (not full catalog)
      - Recalculation completes in <2s for 100 listings
      - Celery task for background recalculation

- [ ] **RT-006**: Add recalculation progress indicators (0.5 pt)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Show UI feedback during background recalculation
      **Files**: `apps/web/components/listings/recalculation-status.tsx`
      **Acceptance Criteria**:
      - Toast notification on recalc start
      - Progress indicator if recalc takes >5s
      - Completion notification with count of updated listings

### Success Criteria

- [ ] SSE endpoint handles 100+ concurrent connections
- [ ] Events published correctly on listing create/update/delete
- [ ] Frontend receives events and updates UI within 2s
- [ ] Auto-reconnection works on connection loss
- [ ] Recalculation triggers only for affected listings
- [ ] Recalculation completes in <2s for 100 listings
- [ ] No memory leaks from long-lived connections
- [ ] Load testing passed (100+ concurrent users)

### Key Files

**Backend**:
- `apps/api/dealbrain_api/api/v1/events.py` - SSE endpoint
- `apps/api/dealbrain_api/services/listings.py` - Event publishers
- `apps/api/dealbrain_api/services/valuation_rules.py` - Rule change triggers
- `apps/api/dealbrain_api/tasks/recalculation.py` - Celery recalculation task

**Frontend**:
- `apps/web/hooks/use-event-stream.ts` - SSE client hook
- `apps/web/hooks/use-listing-updates.ts` - Listing event handler
- `apps/web/components/listings/recalculation-status.tsx` - Progress UI

### Notes

- Use `sse-starlette` library for FastAPI SSE support
- Redis pub/sub channel: `dealbrain:events`
- Event format: `{ type: string, data: object, timestamp: string }`
- Frontend: Use EventSource API for SSE connection
- Ensure graceful degradation if SSE not available (fallback to polling)

---

## Phase 4: Amazon Import Enhancement

**Assigned Subagent(s)**: python-backend-engineer, ai-engineer, test-automator
**Effort**: 8 story points
**Duration**: 7-10 days
**Status**: NOT STARTED
**Dependencies**: None

### Completion Checklist

- [ ] **AI-001**: Enhance Amazon scraper (2 pts)
      **Assigned Subagent(s)**: python-backend-engineer
      **Description**: Improve scraping to extract more structured data from product pages
      **Files**: `apps/api/dealbrain_api/importers/amazon_scraper.py`
      **Acceptance Criteria**:
      - Extracts specifications table from product page
      - Extracts manufacturer and model number
      - Handles page structure variations (desktop vs mobile)
      - Graceful degradation if elements missing
      - Rate limiting to avoid Amazon blocks

- [ ] **AI-002**: Implement NLP extraction patterns (2.5 pts)
      **Assigned Subagent(s)**: ai-engineer
      **Description**: Create regex/NLP patterns to extract component data from titles/descriptions
      **Files**: `apps/api/dealbrain_api/importers/nlp_extractor.py`, `apps/api/dealbrain_api/importers/extraction_patterns.yaml`
      **Acceptance Criteria**:
      - Patterns for CPU (Intel Core i7-12700, AMD Ryzen 5 5600X, etc.)
      - Patterns for RAM (16GB DDR4, 32GB DDR5, etc.)
      - Patterns for Storage (512GB NVMe SSD, 1TB HDD, etc.)
      - Patterns for GPU (RTX 3060, RX 6600, etc.)
      - Patterns configurable in YAML file
      - Extraction accuracy >85%

- [ ] **AI-003**: Implement extraction confidence scoring (1 pt)
      **Assigned Subagent(s)**: ai-engineer
      **Description**: Score extraction confidence (high/medium/low) for user review
      **Files**: `apps/api/dealbrain_api/importers/confidence_scorer.py`
      **Acceptance Criteria**:
      - Confidence algorithm defined (pattern strength + catalog match)
      - Low-confidence extractions flagged for user review
      - Confidence scores returned with extracted data
      - User can review/correct low-confidence extractions

- [ ] **AI-004**: Implement catalog matching (1.5 pts)
      **Assigned Subagent(s)**: python-backend-engineer
      **Description**: Match extracted CPU/GPU names to catalog entries (fuzzy matching)
      **Files**: `apps/api/dealbrain_api/services/catalog_matcher.py`
      **Acceptance Criteria**:
      - Fuzzy matching algorithm (fuzzywuzzy library)
      - Handles variations (i7-12700K vs Core i7-12700K)
      - Match threshold configurable (default 70%)
      - Fallback to manual entry if no match
      - Support for CPU and GPU catalogs

- [ ] **AI-005**: Integration testing (1 pt)
      **Assigned Subagent(s)**: test-automator
      **Description**: Test import with 20+ Amazon URLs across product types
      **Acceptance Criteria**:
      - 70%+ fields populated from test URLs
      - Extraction accuracy validated
      - Performance <500ms per listing
      - No false positives (incorrect extractions)

### Success Criteria

- [ ] Amazon imports populate 70%+ of available fields
- [ ] NLP extraction correctly identifies CPU, RAM, Storage, GPU
- [ ] Low-confidence extractions flagged for user review
- [ ] Import time reduced from 5 min to <1 min per listing
- [ ] Extraction completes in <500ms per listing
- [ ] Catalog matching handles common name variations
- [ ] Graceful degradation if scraping fails
- [ ] Tested with 20+ real Amazon URLs

### Key Files

**Backend**:
- `apps/api/dealbrain_api/importers/amazon_scraper.py` - Scraping logic
- `apps/api/dealbrain_api/importers/nlp_extractor.py` - NLP extraction
- `apps/api/dealbrain_api/importers/extraction_patterns.yaml` - Extraction patterns
- `apps/api/dealbrain_api/importers/confidence_scorer.py` - Confidence scoring
- `apps/api/dealbrain_api/services/catalog_matcher.py` - Catalog matching

### Notes

- Use BeautifulSoup for HTML parsing
- Patterns in YAML for easy updates without code changes
- Cache scraped data (24hr TTL) to reduce re-scraping
- Provide manual override for failed extractions
- Monitor scraping success rate and alert on failures

---

## Phase 5: CPU Catalog Improvements

**Assigned Subagent(s)**: frontend-developer, python-backend-engineer
**Effort**: 3 story points
**Duration**: 3-5 days
**Status**: NOT STARTED
**Dependencies**: None

### Completion Checklist

- [ ] **CPU-001**: Implement CPU sorting (1 pt)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Add sorting controls for all CPU fields
      **Files**: `apps/web/app/cpus/page.tsx`, `apps/web/components/cpus/cpu-sort-controls.tsx`
      **Acceptance Criteria**:
      - Sort by: name, clock speed, core count, thread count, TDP, CPU Mark, Single Thread
      - Ascending/descending toggle
      - Sort persisted in URL query params (shareable links)
      - Responsive sort controls on mobile

- [ ] **CPU-002**: Implement listing count query (1 pt)
      **Assigned Subagent(s)**: python-backend-engineer
      **Description**: Add backend query to get listing count per CPU
      **Files**: `apps/api/dealbrain_api/api/v1/cpus.py`, `apps/api/dealbrain_api/repositories/cpus.py`, `apps/api/dealbrain_api/schemas/cpu.py`
      **Acceptance Criteria**:
      - API endpoint returns CPUs with listing count
      - Efficient query (no N+1, uses JOIN + GROUP BY)
      - Query performance <100ms
      - Cached for performance (5min TTL)

- [ ] **CPU-003**: Implement listing filters (1 pt)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Add "CPUs with listings" filter and listing count sort
      **Files**: `apps/web/app/cpus/page.tsx`, `apps/web/components/cpus/cpu-filters.tsx`, `apps/web/components/cpus/cpu-card.tsx`
      **Acceptance Criteria**:
      - Filter toggle: "Only show CPUs with listings"
      - Sort option: "Listing count" (descending by default)
      - Listing count badge displayed on CPU cards
      - Filter/sort state persisted in URL

### Success Criteria

- [ ] CPUs sortable by all specification fields
- [ ] Sort persisted in URL (shareable links)
- [ ] "CPUs with listings" filter works correctly
- [ ] Listing count displayed on CPU cards
- [ ] Sort by listing count works (most popular first)
- [ ] Performance: Listing count query <100ms
- [ ] Mobile-responsive sort/filter controls

### Key Files

**Frontend**:
- `apps/web/app/cpus/page.tsx` - CPU catalog page
- `apps/web/components/cpus/cpu-sort-controls.tsx` - Sort controls
- `apps/web/components/cpus/cpu-filters.tsx` - Filter controls
- `apps/web/components/cpus/cpu-card.tsx` - CPU card with listing count badge

**Backend**:
- `apps/api/dealbrain_api/api/v1/cpus.py` - CPU endpoints
- `apps/api/dealbrain_api/repositories/cpus.py` - Listing count query
- `apps/api/dealbrain_api/schemas/cpu.py` - CPU DTO with listing count

### Notes

- Use URL query params for filter/sort state
- Implement caching for listing count query (Redis, 5min TTL)
- Ensure sort/filter state syncs with backend API params

---

## Phase 6: Column Selector

**Assigned Subagent(s)**: ui-designer, ui-engineer-enhanced, frontend-developer, web-accessibility-checker
**Effort**: 8 story points
**Duration**: 7-10 days
**Status**: NOT STARTED
**Dependencies**: None

### Completion Checklist

- [ ] **COL-001**: Design column selector component (2 pts)
      **Assigned Subagent(s)**: ui-designer, ui-engineer-enhanced
      **Description**: Create reusable column selector UI component
      **Files**: `apps/web/components/ui/column-selector.tsx`
      **Acceptance Criteria**:
      - Dropdown/modal UI designed (prefer dropdown for quick access)
      - Checkbox list for columns
      - Drag-to-reorder functionality (dnd-kit)
      - "Reset to Default" button
      - Apply button to save changes

- [ ] **COL-002**: Implement column persistence (1 pt)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Save column preferences to localStorage
      **Files**: `apps/web/hooks/use-column-preferences.ts`
      **Acceptance Criteria**:
      - Preferences keyed by entity type (`listings`, `cpus`, etc.)
      - Load preferences on component mount
      - Update on selection change
      - Reset to default functionality

- [ ] **COL-003**: Implement dynamic table rendering (1.5 pts)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Render table columns based on selected columns
      **Files**: `apps/web/components/ui/data-table.tsx`
      **Acceptance Criteria**:
      - Table adapts to selected columns
      - Column order matches selector order
      - Hidden columns not rendered (performance)
      - Table re-renders efficiently on column change

- [ ] **COL-004**: Implement for Listings entity (1.5 pts)
      **Assigned Subagent(s)**: ui-engineer-enhanced
      **Description**: Add column selector to listings page
      **Files**: `apps/web/app/listings/page.tsx`
      **Acceptance Criteria**:
      - All listing fields available in selector (including custom fields)
      - Default columns defined (manufacturer, model, CPU, RAM, storage, price, adjusted price)
      - Column selector integrated into page header
      - Preferences persist across sessions

- [ ] **COL-005**: Implement for other entities (1.5 pts)
      **Assigned Subagent(s)**: frontend-developer
      **Description**: Add column selector to CPUs, GPUs, Valuation Rules, Profiles
      **Files**: `apps/web/app/cpus/page.tsx`, `apps/web/app/gpus/page.tsx`, etc.
      **Acceptance Criteria**:
      - Consistent UI across all entity pages
      - Entity-specific field lists
      - Separate preferences per entity type
      - Default columns defined per entity

- [ ] **COL-006**: Accessibility and testing (0.5 pt)
      **Assigned Subagent(s)**: web-accessibility-checker
      **Description**: Ensure keyboard navigation and screen reader support
      **Acceptance Criteria**:
      - Keyboard navigable (tab through checkboxes)
      - Space/Enter to toggle selections
      - ARIA labels for all interactive elements
      - Screen reader tested (announces selected columns)
      - Meets WCAG AA standards

### Success Criteria

- [ ] Column selector component reusable across entities
- [ ] Drag-to-reorder columns works intuitively
- [ ] Column preferences persist across sessions
- [ ] Reset to default restores original column set
- [ ] Implemented for Listings, CPUs, GPUs, Valuation Rules, Profiles
- [ ] All entity fields (including custom fields) available
- [ ] Keyboard accessible (tab navigation, space to toggle)
- [ ] Screen reader announces selected columns
- [ ] Mobile-responsive (simplified UI on small screens)

### Key Files

**Frontend**:
- `apps/web/components/ui/column-selector.tsx` - Reusable column selector
- `apps/web/hooks/use-column-preferences.ts` - Column persistence hook
- `apps/web/components/ui/data-table.tsx` - Dynamic table rendering
- `apps/web/app/listings/page.tsx` - Listings with column selector
- `apps/web/app/cpus/page.tsx` - CPUs with column selector
- `apps/web/app/gpus/page.tsx` - GPUs with column selector

### Notes

- Use `@dnd-kit/core` for drag-and-drop functionality
- localStorage key format: `column-preferences-{entityType}`
- Consider preset column sets: "Basic", "Advanced", "All"
- Ensure mobile UX is simplified (no drag-and-drop on mobile, simpler list)

---

## Integration & Testing

### Cross-Phase Testing

- [ ] **INT-001**: Test real-time updates with all workflows
      - Create listing → SSE event → UI updates
      - Edit listing → Recalc triggered → Valuation updated → SSE event
      - Import listing → SSE event → UI updates

- [ ] **INT-002**: Test Amazon import end-to-end
      - Import from URL → Scraping → NLP extraction → Catalog matching → Field population
      - Verify 70%+ fields populated
      - Test with various Amazon product types

- [ ] **INT-003**: Test column selector across entities
      - Verify preferences isolated per entity
      - Test column reordering
      - Test reset to default

- [ ] **INT-004**: Performance testing
      - SSE: 100+ concurrent connections
      - Recalculation: 100+ listings in <2s
      - Import: <500ms per listing
      - Column selector: <100ms load time

- [ ] **INT-005**: Accessibility audit
      - WCAG AA compliance across all new components
      - Keyboard navigation functional
      - Screen reader tested

---

## Blockers & Risks

### Current Blockers

*None at this time*

### Risks

1. **Amazon Scraping Reliability** (High Impact, Medium Probability)
   - Mitigation: Fallback to NLP, monitoring, caching

2. **NLP Extraction Accuracy** (Medium Impact, Low Probability)
   - Mitigation: Pattern tuning, user feedback, confidence scoring

3. **SSE Performance** (High Impact, Low Probability)
   - Mitigation: Connection throttling, Redis pub/sub, load testing

4. **Schedule Delays** (Medium Impact, Medium Probability)
   - Mitigation: Parallel work, prioritize high-value phases, descope Phase 6 if needed

---

## Notes

### General

- All phases follow WCAG AA accessibility standards
- Code coverage target: 80%+ for new code
- Documentation updated for each phase (component docs, API docs)

### Phase Dependencies

- Phase 3 (Real-Time Updates) enables auto-recalculation in Phase 2
- No other hard dependencies between phases
- Parallel work opportunities: Phases 1-2, Phases 4-5

### Next Steps

1. Review and approve progress tracking
2. Kick off Phase 1 (Critical UI Bug Fixes)
3. Begin Phase 2 planning in parallel
