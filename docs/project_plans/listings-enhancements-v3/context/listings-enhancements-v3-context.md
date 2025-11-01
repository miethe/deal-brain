# Listings Enhancements v3 - Working Context

**Purpose:** Token-efficient context for resuming Phase 4 work

---

## Current State

**Branch:** feat/listings-enhancements-v3
**Phase:** 4 - Image Management System
**Current Task:** IMG-001 - Configuration file creation
**Last Updated:** 2025-11-01T12:35:33-04:00

---

## Key Decisions

### Architecture
- **Configuration-driven approach:** JSON file with Zod validation
- **7-level fallback hierarchy:** Listing URLs → Model → Series → Manufacturer → CPU/GPU vendor → Form factor → Generic
- **Performance target:** <1ms image resolution time
- **Backward compatibility:** 100% maintained during transition

### Patterns
- Static config import (no runtime loading)
- Early exit optimization in resolver
- TypeScript types generated from Zod schema (single source of truth)
- Radix UI components for image display

### Trade-offs
- **Config file vs Database:** Chose JSON for simplicity, no deployment needed for image additions
- **Two components vs One:** Keep both during transition for backward compatibility
- **GPU vendor separation:** Added new directory for clarity (not in original plan)

---

## Important Learnings

### Current Implementation Analysis
- **Two image components exist:** `ProductImageDisplay` (6-level fallback) and `ProductImage` (3-level fallback)
- **Hardcoded constants:** `MANUFACTURER_LOGOS` has CPU and GPU vendors mixed
- **Inconsistent fallback:** Different components use different fallback strategies

### Gotchas
- **ProductImageDisplay** uses error state handling (async, slower)
- **ProductImage** uses hardcoded constants (faster but inflexible)
- Must maintain both during transition to avoid breaking existing features

---

## Quick Reference

### Environment Setup
```bash
# Frontend development
pnpm install
pnpm --filter "./apps/web" dev

# Type checking
pnpm --filter "./apps/web" typecheck

# Testing
pnpm --filter "./apps/web" test

# Build
pnpm --filter "./apps/web" build
```

### Key Files
- Image components: `apps/web/components/listings/product-image-display.tsx`, `apps/web/components/listings/product-image.tsx`
- Future config: `apps/web/config/product-images.json`
- Future types: `apps/web/types/product-images.ts`
- Future resolver: `apps/web/lib/image-resolver.ts`
- Future validation: `apps/web/lib/validate-image-config.ts`

---

## Phase 4 Scope

**Goal:** Replace hardcoded image fallback logic with maintainable JSON configuration

**Tasks:**
1. IMG-001: Configuration file + validation (4h)
2. IMG-002: Image resolver utility (8h)
3. IMG-003: Refactor ProductImageDisplay (12h)
4. IMG-004: Reorganize image directories (4h)
5. IMG-005: User documentation (4h)

**Success Metric:** Non-technical users can add images in <5 minutes without code changes

---

## Architectural Enhancements

### Original Plan Enhancements
1. **GPU vendor support:** Added `gpuVendors` field to config
2. **Model-specific images:** Added level 3 fallback for granular control
3. **Manufacturer subdirectories:** Support nested directories for series images

### Quality Requirements
- WCAG 2.1 AA accessibility maintained
- <1ms image resolution performance
- 100% backward compatibility
- Visual regression tests pass

---

## Phase 4 Task Breakdown

### IMG-001: Configuration File (4h)
- Create JSON schema with manufacturers, formFactors, cpuVendors, fallbacks
- Generate TypeScript types from schema
- Implement Zod validation logic
- Document all config fields

### IMG-002: Image Resolver (8h)
- Implement 7-level fallback hierarchy
- Optimize for <1ms performance target
- Add debug helper for fallback type
- Handle missing/invalid config gracefully

### IMG-003: Component Refactor (12h)
- Replace hardcoded logic with resolver
- Maintain all existing variants (card, hero, thumbnail)
- Preserve error handling and accessibility
- Add visual regression tests

### IMG-004: Directory Reorganization (4h)
- Create subdirectories: manufacturers/, cpu-vendors/, form-factors/, fallbacks/
- Migrate existing images
- Add README files to each directory
- Verify no broken images

### IMG-005: User Documentation (4h)
- Write step-by-step guide for adding images
- Include troubleshooting section
- Add screenshots and examples
- Optional: video tutorial

---

## Previous Phases Summary

### Phase 1 (✅ Complete)
**Performance Optimization:**
- Virtualization, pagination, and monitoring implemented
- <200ms interaction latency achieved for 1,000+ rows
- Backend cursor-based pagination

### Phase 2 (✅ Complete)
**UX Improvements:**
- "Adjusted Value" terminology standardized (14 occurrences, 11 files)
- ValuationTooltip component with WCAG 2.1 AA compliance
- Zero breaking API changes

### Phase 3 (✅ Complete)
**CPU Performance Metrics:**
- PerformanceMetricDisplay component with color-coded thresholds
- Dual CPU Mark metrics (single-thread and multi-thread)
- Integration into Specifications tab
- ApplicationSettings for threshold configuration
