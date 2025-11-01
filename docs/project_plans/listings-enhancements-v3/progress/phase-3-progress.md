# Phase 3 Progress Tracker: CPU Performance Metrics Layout

**Plan:** docs/project_plans/listings-enhancements-v3/PHASE_3_CPU_METRICS.md
**Started:** 2025-11-01
**Last Updated:** 2025-11-01
**Status:** In Progress

---

## Completion Status

### Success Criteria
- [ ] CPU Mark thresholds stored in ApplicationSettings
- [ ] API endpoint returns thresholds with defaults
- [ ] PerformanceMetricDisplay component displays base and adjusted values
- [ ] Color coding based on improvement percentage
- [ ] Tooltips explain calculations
- [ ] CPU metrics paired in Specifications tab (Score next to $/Mark)
- [ ] Responsive layout (desktop 2-column, mobile stacked)
- [ ] WCAG 2.1 AA accessibility compliance
- [ ] All tests passing (backend + frontend)
- [ ] Documentation complete

### Development Checklist
- [ ] METRICS-001: Create CPU Mark Thresholds Setting (Backend, 4h)
  - Add seed script for default thresholds
  - Add get_cpu_mark_thresholds() to SettingsService
  - Create CpuMarkThresholds Pydantic schema
  - Add unit tests
- [ ] METRICS-002: Create Performance Metric Display Component (Frontend, 12h)
  - PerformanceMetricDisplay component
  - cpu-mark-utils.ts utilities
  - use-cpu-mark-thresholds.ts hook
  - CSS variables for colors
  - Accessibility compliance
- [ ] METRICS-003: Update Specifications Tab Layout (Frontend, 8h)
  - Integrate PerformanceMetricDisplay
  - Pair CPU metrics layout
  - Responsive design
- [ ] Testing (12h)
  - Backend unit tests
  - Frontend component tests
  - E2E tests
  - Accessibility tests

---

## Work Log

### 2025-11-01 - Session 1

**Completed:**
- Phase 3 tracking infrastructure initialized
- Progress tracker created
- Working context updated

**Architectural Decisions Made:**
- Use existing ApplicationSettings table (no migration needed)
- Follow existing /settings/{key} endpoint pattern
- CPU Mark threshold values based on $/CPU mark ratios
- Layout: Desktop 2-column (Score | $/Mark), mobile stacked
- Display strategy: Show both base and adjusted values with delta
- Follow ValuationTooltip component pattern for consistency

**Subagents Used:**
- documentation-writer (self) - Documentation creation

**Commits:**
- (Pending)

**Blockers/Issues:**
- None

**Next Steps:**
- Coordinate with lead-architect for task orchestration
- Delegate METRICS-001 to python-backend-engineer
- Delegate METRICS-002 to ui-engineer (parallel)
- Create ADR for CPU performance metrics

---

## Decisions Log

- **[2025-11-01 10:00]** No database migration needed - ApplicationSettings table already exists
- **[2025-11-01 10:00]** Use existing /settings/{key} endpoint pattern - no new endpoint needed
- **[2025-11-01 10:00]** Follow ValuationTooltip component pattern for consistency
- **[2025-11-01 10:00]** CPU Mark threshold values will be stored as percentage improvement thresholds
- **[2025-11-01 10:00]** Layout pattern: Side-by-side (Score | $/Mark) on desktop, stacked on mobile
- **[2025-11-01 10:00]** Display both base and adjusted $/Mark values with delta indicator

---

## Files Changed

### To Be Created
- /apps/api/dealbrain_api/seeds/cpu_mark_thresholds_seed.py - Default thresholds seed script
- /apps/web/components/listings/performance-metric-display.tsx - Performance metric component
- /apps/web/lib/cpu-mark-utils.ts - CPU mark utility functions
- /apps/web/hooks/use-cpu-mark-thresholds.ts - React Query hook
- /docs/architecture/decisions/ADR-XXX-cpu-performance-metrics-thresholds.md - Architecture decision record

### To Be Modified
- /apps/api/dealbrain_api/services/settings.py - Add get_cpu_mark_thresholds() method
- /apps/api/dealbrain_api/schemas/settings.py - Add CpuMarkThresholdsResponse schema
- /apps/web/components/listings/specifications-tab.tsx - Integrate CPU metrics pairing
- /apps/web/styles/globals.css - Add CPU mark color CSS variables

### Modified (Documentation)
- docs/project_plans/listings-enhancements-v3/progress/phase-3-progress.md (created)
- docs/project_plans/listings-enhancements-v3/context/listings-enhancements-v3-context.md (updated)
