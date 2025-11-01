# Listings Enhancements v3 Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** feat/listings-enhancements-v3
**Last Commit:** 3075ccc (Phase 1 complete)
**Current Task:** Phase 2 - Adjusted Value Renaming & Tooltips (UX-001 starting)

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

---

## Important Learnings

**Phase 1 (Complete):**
- **Performance Delivered:** Virtualization, pagination, and monitoring implemented successfully
- **Virtualization Threshold:** Auto-enable at 100 rows to avoid complexity for small datasets
- **Backend Pagination:** Cursor-based for efficiency, supports filtering and sorting
- **Monitoring:** Lightweight dev-mode instrumentation with zero production overhead

**Phase 2 (In Progress):**
- **Terminology Consistency:** "Adjusted Value" better reflects valuation methodology than "Adjusted Price"
- **Tooltip Strategy:** Show calculation summary with top rules, link to full breakdown modal
- **No Breaking Changes Required:** UI labels can update without affecting API contracts
- **Accessibility First:** WCAG 2.1 AA compliance for all interactive elements

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
- New Component: apps/web/components/listings/valuation-tooltip.tsx (to be created)
- Detail Page: apps/web/components/listings/detail-page-layout.tsx
- Radix UI Tooltip: apps/web/components/ui/tooltip.tsx

---

## Phase 1 Scope (✅ Complete)

Achieve <200ms interaction latency for 1,000 listings through:
1. Row virtualization (only render visible rows)
2. Backend cursor-based pagination
3. React rendering optimizations (memo, useMemo, useCallback)
4. Performance monitoring instrumentation

**Success Metric:** <200ms interaction latency with 1,000+ rows at 60fps scroll

---

## Phase 2 Scope (🟡 In Progress)

Improve user experience through:
1. Consistent terminology ("Adjusted Value" vs "Adjusted Price")
2. Interactive valuation tooltips with calculation summary
3. Quick access to full breakdown modal
4. Full accessibility (keyboard, screen reader support)

**Success Metrics:**
- Zero breaking API changes
- WCAG 2.1 AA compliant tooltips
- All tests passing
