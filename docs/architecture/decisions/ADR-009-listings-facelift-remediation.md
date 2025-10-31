# ADR-009: Listings Facelift Remediation Architecture

**Status**: Approved
**Date**: 2025-10-24
**Deciders**: Lead Architect
**Context**: Post-implementation issues from listings-facelift feature (Phases 1-6)

## Context and Problem Statement

The listings-facelift feature implementation (Phases 1-6) has revealed several data flow and UI rendering issues:

1. CPU/GPU names not displaying in modal, detail page, and catalog views
2. Valuation tab incorrectly showing "0 rules applied" when rules have zero-amount adjustments
3. Product images not appearing in modal or detail page
4. Missing URL fields in detail views
5. Incomplete field rendering in specifications tab
6. Missing entity tooltips in catalog views (table/grid)

These issues stem from architectural mismatches between API data serialization and frontend expectations.

## Decision Drivers

- **Data Consistency**: Frontend needs both nested entity objects (for tooltips) and denormalized string fields (for simple display)
- **Performance**: Computed fields at API boundary prevent N+1 queries and reduce frontend transformation logic
- **Backward Compatibility**: Existing components rely on `cpu_name`, `gpu_name` string fields
- **User Experience**: Rich tooltips require full entity data, but simple displays need quick access to names
- **Maintainability**: Single source of truth for computed values prevents drift

## Considered Options

### Option 1: Frontend Transformation (REJECTED)
Transform API response in React components to extract `cpu_name` from nested `cpu.name`.

**Pros**:
- No backend changes required
- Frontend has full control

**Cons**:
- Repetitive transformation logic across components
- Performance overhead (happens on every render)
- Violates DRY principle
- Harder to maintain consistency

### Option 2: Separate API Endpoints (REJECTED)
Create `/v1/listings/{id}/summary` endpoint with denormalized data.

**Pros**:
- Clean separation of concerns
- Optimized payloads per use case

**Cons**:
- API duplication and maintenance burden
- More network requests for full data
- Complexity in keeping endpoints in sync

### Option 3: Computed Properties in SQLAlchemy Model (SELECTED)
Add `@property` methods to `Listing` model for `cpu_name`, `gpu_name`, `thumbnail_url`.

**Pros**:
- Single source of truth
- Automatic serialization via Pydantic
- Zero performance overhead (lazy evaluation)
- Backward compatible - existing `cpu` object remains
- Easy to maintain and test

**Cons**:
- Slightly larger payload size (negligible)

## Decision Outcome

**Chosen option**: Option 3 - Computed Properties in SQLAlchemy Model

### Implementation Strategy

#### Backend Changes (High Priority)

1. **Add Computed Properties to Listing Model**
   - File: `apps/api/dealbrain_api/models/core.py`
   - Properties: `cpu_name`, `gpu_name`, `thumbnail_url`
   - Implementation: Extract from related entities or JSON fields

2. **Update Pydantic Schema**
   - File: `packages/core/dealbrain_core/schemas/listing.py`
   - Add fields to `ListingRead`: `cpu_name`, `gpu_name`, `thumbnail_url`
   - Pydantic will automatically serialize from model properties

#### Frontend Changes (Medium Priority)

3. **Fix Valuation Tab Logic Bug**
   - File: `apps/web/components/listings/listing-valuation-tab.tsx`
   - Change line 337: Use `adjustments.length` instead of `sortedAdjustments.length`
   - Keep filtering for display list, but show accurate count

4. **Add URLs to Listing Overview Modal**
   - File: `apps/web/components/listings/listing-overview-modal.tsx`
   - Add URLs section displaying `listing_url` and `other_urls`
   - Follow existing pattern from specifications tab

5. **Enhance Specifications Tab**
   - File: `apps/web/components/listings/specifications-tab.tsx`
   - Already has most fields - verify all data is displayed
   - Add any missing fields like detailed ports

6. **Add Entity Tooltips to Catalog Views**
   - File: `apps/web/components/listings/listings-table.tsx`
   - Reuse `EntityTooltip` component for CPU/GPU columns
   - Follow pattern from specifications tab

7. **Update TypeScript Types**
   - File: `apps/web/types/listings.ts`
   - Verify `cpu_name`, `gpu_name`, `thumbnail_url` are in `ListingRecord` interface
   - Already present - no changes needed

### Data Flow Architecture

```
Database (Listing table with FK to CPU/GPU)
    ↓ (SQLAlchemy with lazy="joined")
Listing Model Instance
    ↓ (Computed Properties: cpu_name, gpu_name, thumbnail_url)
Pydantic ListingRead Schema
    ↓ (FastAPI Serialization)
API Response JSON {
    cpu_name: "Intel Core i5-12400",
    cpu: { id: 1, name: "Intel Core i5-12400", cores: 6, ... },
    gpu_name: "Intel UHD Graphics 730",
    gpu: { id: 5, name: "Intel UHD Graphics 730", ... },
    thumbnail_url: "https://...",
    ...
}
    ↓ (React Query)
Frontend Components
    ├─ Simple Display → Use cpu_name, gpu_name (strings)
    └─ Rich Tooltips → Use cpu, gpu (full objects)
```

### Component Responsibility Matrix

| Component | Uses cpu_name | Uses cpu object | Tooltip Needed |
|-----------|--------------|-----------------|----------------|
| Listing Overview Modal | ✓ | - | No (simple modal) |
| Detail Page Hero | ✓ | ✓ (cores/threads) | No |
| Specifications Tab | ✓ | ✓ (full specs) | Yes (hover) |
| Listings Table | ✓ | ✓ (for tooltip) | Yes (hover) |
| Listings Grid | ✓ | ✓ (for tooltip) | Yes (hover) |
| Valuation Tab | - | - | No |

## Consequences

### Positive

- **Single source of truth**: Computed values defined once in backend model
- **Performance**: No frontend transformation overhead
- **Flexibility**: Components can choose simple (string) or rich (object) display
- **Maintainability**: Easy to add more computed fields following same pattern
- **Backward compatibility**: Existing code using `cpu_name` continues to work

### Negative

- **Payload size**: Slight increase due to denormalized fields (~50 bytes per listing)
- **Backend dependency**: Frontend changes require backend deployment first

### Neutral

- **Testing**: Requires backend model tests for computed properties
- **Documentation**: Update API docs to reflect new fields

## Implementation Plan

### Phase 1: Backend Foundation (1-2 hours)
**Assigned to**: `python-backend-engineer`

1. Add computed properties to Listing model
2. Update ListingRead schema
3. Write unit tests for computed properties
4. Deploy and verify API response structure

### Phase 2: Frontend Bug Fixes (2-3 hours)
**Assigned to**: `frontend-developer`

1. Fix valuation tab "0 rules applied" logic bug
2. Add URLs section to listing overview modal
3. Verify all fields display in specifications tab
4. Update any remaining components using old patterns

### Phase 3: Entity Tooltips (3-4 hours)
**Assigned to**: `ui-engineer`

1. Add EntityTooltip to listings table CPU/GPU columns
2. Add EntityTooltip to listings grid (if exists)
3. Ensure tooltips work in all catalog views
4. Test accessibility (keyboard navigation, screen readers)

### Phase 4: Testing & Validation (1-2 hours)
**Assigned to**: `debugger`

1. Integration testing across all views
2. Verify data flow from API to UI
3. Test edge cases (missing CPU/GPU, no images)
4. Performance validation (no regressions)

## Related Decisions

- ADR-008: Listings Facelift Feature Architecture (if exists)
- Deal Brain Layered Architecture (API → Services → Domain Logic)
- React Query caching strategy

## Notes

- The `thumbnail_url` extraction logic prioritizes `raw_listing_json` over `attributes_json`
- Future enhancement: Consider CDN for product images
- Consider adding more computed fields: `ram_summary`, `storage_summary`, etc.
