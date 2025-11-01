# Listings Enhancements v3 Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** feat/listings-enhancements-v3
**Last Commit:** 72826b8 fix(tasks): resolve async event loop conflicts in Celery workers
**Current Phase:** Phase 3 - CPU Performance Metrics Layout
**Current Task:** Creating tracking documents and preparing for implementation

---

## Key Decisions

**Phase 1 (Performance):**
- **Architecture:** Using @tanstack/react-virtual for table virtualization (industry standard, stable)
- **Patterns:** Following Deal Brain layered architecture (API → Services → Domain → Database)
- **Trade-offs:** Virtualization adds complexity but required for 1,000+ row performance target

**Phase 2 (UX/Tooltips):**
- **Tooltip Component:** Using Radix UI Tooltip for consistent, accessible hover interactions
- **Terminology:** "Adjusted Value" replaces "Adjusted Price" to better reflect valuation methodology
- **Component Architecture:** Reusable ValuationTooltip with configurable content and modal integration
- **No Breaking Changes:** Maintain existing API/prop names (adjustedPrice) while updating display labels

**Phase 3 (CPU Metrics):**
- **Architecture:** Use existing ApplicationSettings table, SettingsService, /settings/{key} endpoint
- **Component Pattern:** Follow ValuationTooltip approach for PerformanceMetricDisplay
- **Threshold Values:** Percentage improvement thresholds (excellent: 20%, good: 10%, fair: 5%, neutral: 0%, poor: -10%, premium: -20%)
- **Layout:** Desktop 2-column (Score | $/Mark), mobile stacked
- **Display Strategy:** Show both base and adjusted values with delta percentage
- **Color Coding:** Green (excellent/good), gray (neutral/fair), red (poor/premium) with text labels for accessibility
- **No Migration Needed:** ApplicationSettings table already exists

---

## Important Learnings

**Phase 1 (Complete):**
- **Performance Delivered:** Virtualization, pagination, and monitoring implemented successfully
- **Virtualization Threshold:** Auto-enable at 100 rows to avoid complexity for small datasets
- **Backend Pagination:** Cursor-based for efficiency, supports filtering and sorting
- **Monitoring:** Lightweight dev-mode instrumentation with zero production overhead

**Phase 2 (✅ Complete):**
- **Terminology Consistency:** "Adjusted Value" implemented across 14 occurrences, 11 files
- **Tooltip Component:** Production-ready ValuationTooltip with WCAG 2.1 AA compliance
- **Integration:** Tooltip integrated in DetailPageHero with modal link
- **Zero Breaking Changes:** All API contracts preserved (adjustedPrice props unchanged)
- **Ahead of Schedule:** Completed in 1 day vs 3-4 estimated

**Phase 3 (In Progress - Started 2025-11-01):**
- **ApplicationSettings Exists:** No migration needed, just seed data
- **Existing Data:** dollar_per_cpu_mark_single/multi fields already in Listing model
- **Component Pattern Reuse:** ValuationTooltip pattern works well, follow for PerformanceMetricDisplay
- **Color Accessibility:** Must include text labels, not just color coding
- **Threshold API:** Must handle failures gracefully with hardcoded defaults
- **Performance:** Memoize PerformanceMetricDisplay component for table rendering

**Root Cause Analysis - Adjusted CPU Mark Fields Not Populating (2025-11-01):**

*Previous Fix Attempts:*
1. **Commit 76d92a0** (2025-10-31): Added `apply_listing_metrics()` call to URL ingestion pipeline
   - Fixed NULL base metrics for URL-ingested listings
   - Added metrics calculation immediately after listing creation/update in `ingestion.py:1102-1114`
   - Successfully populated base `dollar_per_cpu_mark_single` and `dollar_per_cpu_mark_multi` fields

2. **Commit 72826b8** (2025-11-01): Fixed async event loop conflicts in Celery workers
   - Added `dispose_engine()` calls before async execution in tasks
   - Resolved "Task got Future attached to a different loop" errors
   - Fixed test suite (all 34 async task tests passing)
   - Prevented event loop conflicts in valuation and ingestion tasks

*Root Cause:*
- `apply_listing_metrics()` function (`services/listings.py:288-437`) calculates base CPU Mark fields at lines 416-424 only
  - ✅ Sets `dollar_per_cpu_mark_single` (calculated)
  - ✅ Sets `dollar_per_cpu_mark_multi` (calculated)
  - ❌ Does NOT set `dollar_per_cpu_mark_single_adjusted` (missing)
  - ❌ Does NOT set `dollar_per_cpu_mark_multi_adjusted` (missing)
- Dedicated function `calculate_cpu_performance_metrics()` exists (lines 710-738) that properly calculates ALL four metrics (base and adjusted)
- `apply_listing_metrics()` doesn't use it - manually calculates only base fields instead
- Other functions (`update_listing_metrics` at line 772, `bulk_update_listing_metrics` at line 810) correctly use `calculate_cpu_performance_metrics()`

*Fix Strategy:*
- Replace manual calculation at lines 416-424 in `apply_listing_metrics()` with call to `calculate_cpu_performance_metrics()`
- Apply all returned metrics using same pattern as `update_listing_metrics()` (lines 775-776: iterate metrics dict, use setattr)

---

## Quick Reference

### Environment Setup
```bash
# Backend API
export PYTHONPATH="$PWD/apps/api"
poetry install

# Frontend Web
pnpm install
pnpm --filter "./apps/web" dev

# Database
make migrate

# Full stack
make up
```

### Phase 1 Key Files
- Frontend Table: apps/web/components/listings/listings-table.tsx
- Backend API: apps/api/dealbrain_api/api/listings.py
- Backend Service: apps/api/dealbrain_api/services/listings.py
- Backend Schema: apps/api/dealbrain_api/schemas/listings.py
- Backend Model: apps/api/dealbrain_api/models/core.py
- Performance Utils: apps/web/lib/performance.ts

### Phase 2 Key Files
- Terminology Updates: apps/web/components/listings/*.tsx (multiple files)
- Valuation Tooltip: apps/web/components/listings/valuation-tooltip.tsx
- Detail Page Hero: apps/web/components/listings/detail-page-hero.tsx
- Radix UI Tooltip: apps/web/components/ui/tooltip.tsx

### Phase 3 Key Files
- Backend Settings Service: apps/api/dealbrain_api/services/settings.py
- Backend Settings Schemas: apps/api/dealbrain_api/schemas/settings.py
- Backend Listing Model: apps/api/dealbrain_api/models/core.py (has dollar_per_cpu_mark fields)
- Seed Script (to create): apps/api/dealbrain_api/seeds/cpu_mark_thresholds_seed.py
- Performance Metric Component (to create): apps/web/components/listings/performance-metric-display.tsx
- CPU Mark Utilities (to create): apps/web/lib/cpu-mark-utils.ts
- CPU Mark Hook (to create): apps/web/hooks/use-cpu-mark-thresholds.ts
- Specifications Tab: apps/web/components/listings/specifications-tab.tsx
- Theme Styles: apps/web/styles/globals.css

---

## Phase 1 Scope (✅ Complete)

Achieve <200ms interaction latency for 1,000 listings through:
1. Row virtualization (only render visible rows)
2. Backend cursor-based pagination
3. React rendering optimizations (memo, useMemo, useCallback)
4. Performance monitoring instrumentation

**Success Metric:** <200ms interaction latency with 1,000+ rows at 60fps scroll

---

## Phase 2 Scope (✅ Complete - 2025-11-01)

Improved user experience through:
1. ✅ Consistent terminology ("Adjusted Value" vs "Adjusted Price") - 14 occurrences updated
2. ✅ Interactive valuation tooltips with calculation summary
3. ✅ Quick access to full breakdown modal
4. ✅ Full accessibility (keyboard, screen reader support)

**Success Metrics Achieved:**
- ✅ Zero breaking API changes (all adjustedPrice props preserved)
- ✅ WCAG 2.1 AA compliant tooltips
- ✅ Unit tests passing (15+ test cases)
- ⚠️ E2E tests pending manual verification

**Deliverables:**
- 1 new component (ValuationTooltip - 188 lines)
- 12 files modified (terminology + integration)
- 629 lines of test code
- 5 comprehensive documentation files

---

## Phase 3 Scope (In Progress - Started 2025-11-01)

Implement color-coded CPU performance metrics with paired layout (Score next to $/Mark). Show base and adjusted values with improvement delta. Configurable thresholds stored in ApplicationSettings.

**Tasks:**
1. [ ] METRICS-001: Create CPU Mark Thresholds Setting (Backend, 4h)
2. [ ] METRICS-002: Create Performance Metric Display Component (Frontend, 12h)
3. [ ] METRICS-003: Update Specifications Tab Layout (Frontend, 8h)
4. [ ] Testing (12h)

**Success Metric:** Users can quickly assess CPU value efficiency via color-coded $/CPU Mark metrics in Specifications tab

**Estimated Effort:** 36h (4h backend + 12h frontend component + 8h integration + 12h testing)

**Key Patterns:**
- **Settings Pattern:** See valuation_thresholds implementation in SettingsService
- **Component Pattern:** See ValuationTooltip component
- **Hook Pattern:** See use-valuation-thresholds.ts
- **Color Coding:** See getValuationStyle() in valuation-utils.ts
