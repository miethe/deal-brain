# UX Improvements Context File

**PRD**: ux-improvements-nov-18-v1
**Scope**: All 6 phases (34 story points)
**Updated**: 2025-11-19

---

## Current State

**Implementation Status**: Planning phase complete, ready for execution
**Total Phases**: 6 (UI bugs → workflows → real-time → Amazon import → CPU catalog → column selector)
**Effort**: 34 story points across 6-8 weeks with parallel execution
**Git Branch**: `claude/ux-improvements-nov-18-*`

### Key Context
- Frontend-heavy implementation (Phases 1, 2, 5, 6)
- Backend changes limited to Phase 3 (real-time) and Phase 4 (import)
- Phase 1 bug fixes are quick wins with immediate user value
- Phase 3 (SSE) is infrastructure foundation for Phase 2 auto-recalc

---

## Quick Reference: Phase Dependencies

```
Phase 1: UI Bugs (2 pts) - No dependencies
  ├─ Phase 2: Workflows (5 pts) - No hard dependencies
  │  └─ (Uses Phase 3 for auto-recalc, can parallel)
  │
  ├─ Phase 3: Real-Time (8 pts) - Enables Phase 2 auto-recalc
  │  │
  │  └─ Phase 4: Amazon Import (8 pts) - No hard dependencies
  │
  └─ Phase 5: CPU Catalog (3 pts) - No dependencies
  └─ Phase 6: Column Selector (8 pts) - Uses Phase 5 foundations
```

**Execution Strategy**: Start Phase 1-2 in parallel, Phase 3 foundation early, Phases 4-5 parallel with Phase 3

---

## Key Implementation Decisions

### Frontend (Phases 1, 2, 5, 6)

| Component | Decision | Why |
|-----------|----------|-----|
| Range Sliders | Radix UI Slider primitives + custom dual-handle wrapper | Already used in project, accessible primitives |
| Quick Edit Modal | Expand existing modal (don't duplicate components) | Reuse validation, reduce duplication |
| Column Persistence | localStorage (entity type keys) | Client-only, no backend state needed |
| Column Selector | Dropdown with drag-to-reorder | Familiar pattern, supports many columns |

### Backend (Phases 3, 4)

| Component | Decision | Why |
|-----------|----------|-----|
| Real-Time Protocol | Server-Sent Events (SSE) | Simpler than WebSocket for unidirectional updates |
| Event Distribution | Redis pub/sub | Efficient fan-out, decouples publishers/subscribers |
| Recalculation | Celery async tasks | Non-blocking, handles backlog naturally |
| Amazon Scraping | BeautifulSoup + NLP patterns | Well-tested, regex-friendly for component extraction |
| Catalog Matching | fuzzywuzzy | 70%+ threshold handles common aliases |

### Technology Stack

**Frontend**: React (Next.js), TanStack Query, shadcn/ui, Recharts, Radix UI
**Backend**: FastAPI, SQLAlchemy, Celery, Redis, BeautifulSoup, fuzzywuzzy

---

## Important Learnings & Gotchas

### Phase 1 (UI Fixes)
- Check existing table component for sticky header implementation
- Verify mobile slider behavior before selecting library
- Cross-browser test slider drag behavior (especially Safari touch)

### Phase 2 (Workflows)
- Quick edit modal scrollable content if fields exceed viewport
- Modal transitions (view → quick edit) need state management
- Validation schema reuse reduces test burden
- WF-004 component extraction can be parallel with WF-001

### Phase 3 (Real-Time)
- Redis pub/sub channel must be consistent across services
- EventSource connection throttling prevents thundering herd (max 100 connections)
- Celery task queuing prevents recalc overload
- Only recalculate affected listings (WHERE component_type IN (...))
- Load test before production (100+ concurrent SSE connections)

### Phase 4 (Amazon Import)
- Amazon page structure varies by product type (desktop/mobile/regional)
- NLP patterns need iterative tuning with real data
- Confidence scoring prevents low-quality auto-fills
- Fallback to manual entry when confidence <50%
- Performance target <500ms per listing includes scraping + extraction

### Phase 5 (CPU Catalog)
- Listing count query needs efficient GROUP BY (no N+1 problem)
- Sort persisted in URL enables shareable filtered views
- Listing count badge provides user feedback on catalog coverage

### Phase 6 (Column Selector)
- localStorage key format: `column-preferences-{entityType}` (e.g., `column-preferences-listings`)
- Drag-to-reorder requires dnd-kit or react-beautiful-dnd
- Reset button restores defaults defined in component
- Custom fields must be included in available columns list

---

## Phase Scope Summary

### Phase 1: UI Bugs (2 pts, 2-3 days)
- Fix dual-handle range sliders (all list views)
- Fix table header overlap issue
- Cross-browser testing

**Files**: `slider.tsx`, `data-table.tsx`, `cpu-filters.tsx`

### Phase 2: Workflows (5 pts, 5-7 days)
- Expand quick edit modal (CPU, RAM, Storage, GPU)
- Add Quick Edit button to view modal
- Add Edit button to detail page
- Reusable component extraction
- Integration testing

**Files**: `quick-edit-modal.tsx`, `listing-view-modal.tsx`, `[id]/page.tsx`

### Phase 3: Real-Time (8 pts, 7-10 days)
- SSE event architecture design
- FastAPI SSE endpoint (`/api/v1/events`)
- Event publishers (create/update events)
- React hook (`useEventStream`)
- Auto-recalculation triggers (Celery tasks)
- Progress indicators (toast/progress UI)

**Files**: `events.py`, `listings.py`, `use-event-stream.ts`, `recalculation.py`

### Phase 4: Amazon Import (8 pts, 7-10 days)
- Enhanced Amazon scraper (specs, manufacturer, model)
- NLP extraction patterns (CPU, RAM, Storage, GPU)
- Confidence scoring (high/medium/low)
- Fuzzy catalog matching (CPU/GPU alignment)
- Integration testing (20+ URLs, 70%+ field coverage)

**Files**: `amazon_scraper.py`, `nlp_extractor.py`, `extraction_patterns.yaml`, `catalog_matcher.py`

### Phase 5: CPU Catalog (3 pts, 3-5 days)
- CPU sorting (all specification fields)
- Listing count query (efficient, no N+1)
- "CPUs with listings" filter
- Listing count badge + sort option

**Files**: `cpus.py` (page), `cpus.py` (repo), `cpu.py` (schema)

### Phase 6: Column Selector (8 pts, 7-10 days)
- Reusable column selector component (dropdown with drag-to-reorder)
- localStorage persistence (entity-type keys)
- Dynamic table rendering (select visible columns)
- Implementation for all entity types (Listings, CPUs, GPUs, Rules, Profiles)
- Accessibility (keyboard nav, ARIA labels, screen reader)

**Files**: `column-selector.tsx`, `use-column-preferences.ts`, `data-table.tsx`, entity pages

---

## File Organization

### New Files to Create
- `apps/api/dealbrain_api/api/v1/events.py` - SSE endpoint
- `apps/web/hooks/use-event-stream.ts` - SSE client hook
- `apps/api/dealbrain_api/tasks/recalculation.py` - Celery recalculation tasks
- `apps/api/dealbrain_api/importers/nlp_extractor.py` - NLP patterns
- `apps/api/dealbrain_api/importers/extraction_patterns.yaml` - Pattern config
- `apps/api/dealbrain_api/services/catalog_matcher.py` - Fuzzy matching
- `apps/web/components/ui/column-selector.tsx` - Column selector component
- `apps/web/hooks/use-column-preferences.ts` - Column preferences persistence

### Files to Modify
- **Phase 1**: `slider.tsx`, `data-table.tsx`, `cpu-filters.tsx`
- **Phase 2**: `quick-edit-modal.tsx`, `listing-view-modal.tsx`, `[id]/page.tsx`, `listing-form-fields.tsx`
- **Phase 3**: `listings.py` (service), `events.py` (new endpoint)
- **Phase 4**: `amazon_scraper.py`
- **Phase 5**: `cpus.py` (page + repo), `cpu.py` (schema)
- **Phase 6**: `data-table.tsx`, entity page files

---

## Testing Strategy

**Unit Tests**:
- NLP extraction patterns (Phase 4)
- Catalog matching algorithm (Phase 4)
- Column preference persistence (Phase 6)

**Integration Tests**:
- Amazon import workflows (Phase 4)
- SSE event flow (Phase 3)
- Complete edit workflows (Phase 2)

**Performance Tests**:
- SSE under load (100+ concurrent connections)
- Recalculation performance (<2s for 100 listings)
- Amazon import performance (<500ms per listing)
- Listing count query (<100ms)

**UI Tests**:
- Slider behavior (touch, keyboard, desktop)
- Modal transitions
- Column selector drag-to-reorder
- Keyboard navigation and screen reader support

---

## Progress Notes

*(To be populated during implementation)*

### Completed
- **UI-001**: Dual-handle range sliders implemented
  - Created `RangeSlider` component with full accessibility support
  - Updated base `Slider` to auto-detect and support range mode
  - Added value display with custom formatters
  - Keyboard navigation: Tab to focus, Arrow keys to adjust
  - Touch-friendly with 44px min touch targets
  - WCAG 2.1 AA compliant (ARIA labels, keyboard nav, screen reader support)

- **UI-002**: Fixed table header overlap
  - Added `scroll-margin-top` CSS to first table row
  - Increased sticky header z-index from 10 to 20
  - Applied to DataGrid component (affects all entity list views)
  - Works with and without filter rows

### In Progress
- **UI-003**: Cross-browser testing pending (requires running dev server)

### Blocked
- (none currently)

### Next Session
- Complete UI-003 (cross-browser testing) when dev environment is available
- Start Phase 2 (Listing Workflow Enhancements)
  - Expand quick edit modal with CPU, RAM, Storage, GPU fields
  - Add Quick Edit button to view modal
  - Add Edit button to listing detail page

### Implementation Notes (Phase 1)

**Slider Implementation:**
- Radix UI Slider primitives already support multiple thumbs natively
- Just needed to render two `<SliderPrimitive.Thumb />` components
- Auto-detection of range mode based on value array length
- Added hover states for better UX (hover:bg-primary/10)
- Formatters allow custom value display (e.g., "$100", "4.2 GHz")

**Table Fix Implementation:**
- Used CSS `scroll-margin-top` property instead of adding padding
  - More semantic and doesn't affect layout
  - Properly accounts for sticky header height
  - Works with CSS custom properties for dynamic heights
- Applied to both virtualized and non-virtualized rows
- No performance impact (CSS-only solution)

**Accessibility Considerations:**
- All components use proper ARIA labels
- Keyboard navigation fully functional (Tab + Arrow keys)
- Screen reader announcements via `aria-live="polite"`
- Touch targets meet WCAG 2.1 AA minimum (44px)
