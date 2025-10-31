# Listings Enhancements v3 Working Context

**Purpose:** Token-efficient context for resuming work across AI turns

---

## Current State

**Branch:** main
**Last Commit:** 99f9edd
**Current Task:** Phase 1 initialization - preparing for performance optimization implementation

---

## Key Decisions

- **Architecture:** Using @tanstack/react-virtual for table virtualization (industry standard, stable)
- **Patterns:** Following Deal Brain layered architecture (API → Services → Domain → Database)
- **Trade-offs:** Virtualization adds complexity but required for 1,000+ row performance target

---

## Important Learnings

- **Phase 1 Focus:** Performance optimization for Data Tab - virtualization, pagination, rendering optimization
- **Virtualization Threshold:** Auto-enable at 100 rows to avoid complexity for small datasets
- **Backend Pagination:** Cursor-based for efficiency, supports filtering and sorting

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

### Key Files
- Frontend Table: apps/web/components/listings/listings-table.tsx
- Backend API: apps/api/dealbrain_api/api/listings.py
- Backend Service: apps/api/dealbrain_api/services/listings.py
- Backend Schema: apps/api/dealbrain_api/schemas/listings.py
- Backend Model: apps/api/dealbrain_api/models/core.py

---

## Phase 1 Scope

Achieve <200ms interaction latency for 1,000 listings through:
1. Row virtualization (only render visible rows)
2. Backend cursor-based pagination
3. React rendering optimizations (memo, useMemo, useCallback)
4. Performance monitoring instrumentation

**Success Metric:** <200ms interaction latency with 1,000+ rows at 60fps scroll
