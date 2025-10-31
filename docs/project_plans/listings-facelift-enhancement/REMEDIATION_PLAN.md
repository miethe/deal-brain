# Listings Facelift Remediation Plan

**Date**: 2025-10-24
**Status**: Ready for Implementation
**ADR Reference**: [ADR-009: Listings Facelift Remediation Architecture](/docs/architecture/decisions/ADR-009-listings-facelift-remediation.md)

## Executive Summary

This plan addresses post-implementation issues from the listings-facelift feature (Phases 1-6). Issues are categorized into architectural root causes with clear implementation tasks delegated to specialist agents.

## Issue Categories & Root Causes

### Category 1: Missing Computed Fields in API Response
**Root Cause**: The `Listing` SQLAlchemy model lacks computed properties for `cpu_name`, `gpu_name`, and `thumbnail_url`. The API returns nested objects but frontend components expect denormalized string fields.

**Impact**:
- CPU/GPU show as "Unknown" or blank in detail page and modal
- Product images don't appear
- Components must extract nested data inconsistently

**Affected Components**:
- Listing Overview Modal
- Detail Page Hero
- Specifications Tab
- Catalog views (table/grid)

### Category 2: Valuation Tab Logic Bug
**Root Cause**: Component filters adjustments to non-zero amounts before counting, causing "0 rules applied" message when all rules result in $0 adjustments (which is valid - rules were evaluated but conditions didn't trigger deductions).

**Impact**:
- Misleading "0 rules applied" message
- Users can't see which rules were evaluated
- Valuation breakdown modal shows correct data, but tab summary is wrong

**Affected Components**:
- `ListingValuationTab` (line 337)
- `ValuationTabPage` wrapper

### Category 3: Missing UI Rendering
**Root Cause**: Data exists in API response but components don't render it.

**Impact**:
- `listing_url` and `other_urls` not shown in modal
- Incomplete fields in specifications tab
- Missing entity tooltips in catalog views

**Affected Components**:
- Listing Overview Modal (URLs section missing)
- Listings Table (no CPU/GPU tooltips)
- Listings Grid (no CPU/GPU tooltips)

### Category 4: Incomplete Detail Page Display
**Root Cause**: Specifications tab has infrastructure for tooltips and full data, but doesn't leverage all available fields from API.

**Impact**:
- Users can't see all listing details
- Tooltips broken/missing for RAM and Storage specs

**Affected Components**:
- Specifications Tab
- Detail Page Hero (could show more data)

## Implementation Phases

### Phase 1: Backend Data Layer (PRIORITY: CRITICAL)
**Blocking**: All frontend fixes depend on this
**Estimated Time**: 1-2 hours
**Assigned to**: `python-backend-engineer`

#### Task 1.1: Add Computed Properties to Listing Model
**File**: `/mnt/containers/deal-brain/apps/api/dealbrain_api/models/core.py`

Add these computed properties to the `Listing` class:

```python
@property
def cpu_name(self) -> str | None:
    """Denormalized CPU name for frontend convenience."""
    return self.cpu.name if self.cpu else None

@property
def gpu_name(self) -> str | None:
    """Denormalized GPU name for frontend convenience."""
    return self.gpu.name if self.gpu else None

@property
def thumbnail_url(self) -> str | None:
    """Extract thumbnail URL from raw listing JSON or attributes."""
    if self.raw_listing_json:
        # Check common fields from marketplace adapters
        for key in ['image_url', 'thumbnail_url', 'imageUrl', 'thumbnailUrl', 'img_url']:
            if key in self.raw_listing_json and self.raw_listing_json[key]:
                return self.raw_listing_json[key]

    # Fallback to attributes_json
    if self.attributes_json:
        for key in ['image_url', 'thumbnail_url']:
            if key in self.attributes_json and self.attributes_json[key]:
                return self.attributes_json[key]

    return None
```

**Location**: Insert after the relationship definitions (around line 90-100)

#### Task 1.2: Update ListingRead Pydantic Schema
**File**: `/mnt/containers/deal-brain/packages/core/dealbrain_core/schemas/listing.py`

Verify these fields exist in `ListingRead` class (around line 142):

```python
class ListingRead(ListingBase):
    # ... existing fields ...
    cpu_name: str | None = None  # May already exist
    gpu_name: str | None = None  # May already exist
    thumbnail_url: str | None = None  # Add if missing
```

**Note**: Check if `cpu_name` and `gpu_name` already exist - they might be there but not populated.

#### Task 1.3: Write Tests
**File**: `/mnt/containers/deal-brain/tests/test_listing_computed_properties.py` (create new)

```python
import pytest
from dealbrain_api.models import Listing, Cpu, Gpu

def test_cpu_name_property(db_session):
    """Test cpu_name computed property."""
    cpu = Cpu(name="Intel Core i5-12400", manufacturer="Intel")
    listing = Listing(title="Test", price_usd=500, cpu=cpu)
    assert listing.cpu_name == "Intel Core i5-12400"

def test_cpu_name_when_null(db_session):
    """Test cpu_name returns None when no CPU."""
    listing = Listing(title="Test", price_usd=500)
    assert listing.cpu_name is None

def test_thumbnail_url_from_raw_json(db_session):
    """Test thumbnail_url extraction from raw_listing_json."""
    listing = Listing(
        title="Test",
        price_usd=500,
        raw_listing_json={"image_url": "https://example.com/image.jpg"}
    )
    assert listing.thumbnail_url == "https://example.com/image.jpg"
```

#### Task 1.4: Verify API Response
After deployment, test endpoint `/v1/listings/{id}` returns:

```json
{
  "id": 1,
  "title": "...",
  "cpu_name": "Intel Core i5-12400",
  "cpu": {
    "id": 1,
    "name": "Intel Core i5-12400",
    "manufacturer": "Intel",
    "cores": 6,
    "threads": 12,
    ...
  },
  "gpu_name": "Intel UHD Graphics 730",
  "gpu": {
    "id": 5,
    "name": "Intel UHD Graphics 730",
    ...
  },
  "thumbnail_url": "https://...",
  ...
}
```

### Phase 2: Frontend Bug Fixes (PRIORITY: HIGH)
**Dependencies**: Phase 1 must be deployed first
**Estimated Time**: 2-3 hours
**Assigned to**: `frontend-developer`

#### Task 2.1: Fix Valuation Tab "0 Rules Applied" Bug
**File**: `/mnt/containers/deal-brain/apps/web/components/listings/listing-valuation-tab.tsx`

**Current Code** (lines 166-177 and 336-342):
```typescript
const sortedAdjustments = useMemo(() => {
  return adjustments
    .filter(adj => Math.abs(adj.adjustment_amount) > 0)  // PROBLEM: Filters before counting
    .sort(...)
}, [adjustments]);

// Line 337 - Shows filtered count
<Badge variant="secondary">
  {sortedAdjustments.length} rule{sortedAdjustments.length === 1 ? "" : "s"} applied
</Badge>
```

**Fixed Code**:
```typescript
// Keep the sorted list for display (non-zero only)
const sortedAdjustments = useMemo(() => {
  return adjustments
    .filter(adj => Math.abs(adj.adjustment_amount) > 0)
    .sort((a, b) => {
      const absA = Math.abs(a.adjustment_amount);
      const absB = Math.abs(b.adjustment_amount);
      if (absA !== absB) {
        return absB - absA;
      }
      return a.rule_name.localeCompare(b.rule_name);
    });
}, [adjustments]);

// Line 337 - Show total count of all evaluated rules
<Badge variant="secondary">
  {adjustments.length} rule{adjustments.length === 1 ? "" : "s"} applied
</Badge>

// Update line 370-372 to reference correct count
{sortedAdjustments.length > 4 && (
  <li className="text-xs text-muted-foreground">
    {sortedAdjustments.length - 4} more rule{sortedAdjustments.length - 4 === 1 ? "" : "s"} with adjustments in breakdown
  </li>
)}
```

**Explanation**:
- Display count of ALL evaluated rules (`adjustments.length`)
- But only show impactful rules (non-zero) in the list
- Update "more rules" text to clarify it's showing rules WITH adjustments

#### Task 2.2: Add URLs Section to Listing Overview Modal
**File**: `/mnt/containers/deal-brain/apps/web/components/listings/listing-overview-modal.tsx`

Add this section after the Hardware section (after line 155, before the Metadata section):

```typescript
{(listing.listing_url || (listing.other_urls && listing.other_urls.length > 0)) && (
  <>
    <Separator />

    <Section title="Links">
      <div className="space-y-2">
        {listing.listing_url && (
          <div className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4 text-muted-foreground" />
            <a
              href={listing.listing_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              View Original Listing
            </a>
          </div>
        )}

        {listing.other_urls && listing.other_urls.map((link, index) => (
          <div key={index} className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4 text-muted-foreground" />
            <a
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              {link.label || `Additional Link ${index + 1}`}
            </a>
          </div>
        ))}
      </div>
    </Section>
  </>
)}
```

**Import**: Add `ExternalLink` to imports from `lucide-react`:
```typescript
import { ExternalLink } from "lucide-react";
```

#### Task 2.3: Verify Specifications Tab Completeness
**File**: `/mnt/containers/deal-brain/apps/web/components/listings/specifications-tab.tsx`

**Review checklist**:
- ✓ CPU with tooltip (already implemented - line 48-60)
- ✓ GPU with tooltip (already implemented - line 63-75)
- ✓ RAM with tooltip (already implemented - line 78-98)
- ✓ Primary Storage with tooltip (already implemented - line 101-121)
- ✓ Secondary Storage with tooltip (already implemented - line 124-144)
- ✓ Ports display (already implemented - line 147-180)
- ✓ URLs section (already implemented - line 211-242)

**Task**: Verify the CPU field actually displays when `listing.cpu` is populated. If not, debug why the condition on line 48 fails.

**Potential Issue**: Check if `listing.cpu.id` is always truthy. Change line 48 from:
```typescript
{listing.cpu && (
```

To:
```typescript
{(listing.cpu || listing.cpu_name) && (
```

This ensures CPU displays even if only `cpu_name` is available (fallback).

### Phase 3: Entity Tooltips in Catalog Views (PRIORITY: MEDIUM)
**Dependencies**: Phase 1 deployed
**Estimated Time**: 3-4 hours
**Assigned to**: `ui-engineer`

#### Task 3.1: Add EntityTooltip to Listings Table
**File**: `/mnt/containers/deal-brain/apps/web/components/listings/listings-table.tsx`

**Current State**: CPU/GPU displayed as plain text
**Target State**: CPU/GPU with hover tooltips showing full specs

**Implementation**:

1. Import EntityTooltip components:
```typescript
import { EntityTooltip } from "./entity-tooltip";
import { CpuTooltipContent } from "./tooltips/cpu-tooltip-content";
import { GpuTooltipContent } from "./tooltips/gpu-tooltip-content";
import { fetchEntityData } from "@/lib/api/entities";
```

2. Find CPU column rendering (search for `cpu_name`) and replace with:
```typescript
// CPU Column
{
  id: "cpu",
  header: "CPU",
  cell: ({ row }) => {
    const listing = row.original;

    if (!listing.cpu && !listing.cpu_name) {
      return <span className="text-muted-foreground">—</span>;
    }

    // If we have full CPU object with ID, show tooltip
    if (listing.cpu?.id) {
      return (
        <EntityTooltip
          entityType="cpu"
          entityId={listing.cpu.id}
          tooltipContent={(cpu) => <CpuTooltipContent cpu={cpu} />}
          fetchData={fetchEntityData}
          variant="inline"
        >
          {listing.cpu_name || listing.cpu.name || "Unknown"}
        </EntityTooltip>
      );
    }

    // Fallback to plain text if no ID
    return <span>{listing.cpu_name}</span>;
  },
}
```

3. Repeat for GPU column:
```typescript
// GPU Column
{
  id: "gpu",
  header: "GPU",
  cell: ({ row }) => {
    const listing = row.original;

    if (!listing.gpu && !listing.gpu_name) {
      return <span className="text-muted-foreground">—</span>;
    }

    if (listing.gpu?.id) {
      return (
        <EntityTooltip
          entityType="gpu"
          entityId={listing.gpu.id}
          tooltipContent={(gpu) => <GpuTooltipContent gpu={gpu} />}
          fetchData={fetchEntityData}
          variant="inline"
        >
          {listing.gpu_name || listing.gpu.name || "Unknown"}
        </EntityTooltip>
      );
    }

    return <span>{listing.gpu_name}</span>;
  },
}
```

#### Task 3.2: Add EntityTooltip to Listings Grid (if exists)
**File**: Search for grid view component (may be in same file or separate)

**Search command**: `find /mnt/containers/deal-brain/apps/web/components/listings -name "*grid*"`

If grid view exists, apply same pattern as table (Task 3.1).

#### Task 3.3: Test Tooltip Accessibility
**Manual Testing Checklist**:
- [ ] Tooltips appear on hover
- [ ] Tooltips appear on keyboard focus (Tab navigation)
- [ ] Tooltips have proper ARIA labels
- [ ] Screen reader announces tooltip content
- [ ] Tooltips don't interfere with table scrolling
- [ ] Tooltips work in both light and dark modes (if applicable)

### Phase 4: Testing & Validation (PRIORITY: MEDIUM)
**Dependencies**: All phases complete
**Estimated Time**: 1-2 hours
**Assigned to**: `debugger`

#### Task 4.1: Integration Testing

**Test Scenarios**:

1. **Listing with Complete Data**:
   - Verify CPU name shows in: modal, detail page hero, specifications tab, catalog table
   - Verify GPU name shows in: modal, detail page hero, specifications tab, catalog table
   - Verify thumbnail shows in: modal, detail page
   - Verify URLs show in: modal, specifications tab
   - Verify tooltips work in: catalog table, specifications tab

2. **Listing with Missing Data**:
   - Listing without CPU → shows "—" or "Unknown"
   - Listing without GPU → shows "—" or "None"
   - Listing without image → shows placeholder
   - Listing without URLs → section hidden

3. **Valuation Tab**:
   - Listing with rules applied → shows correct count and top 4 rules
   - Listing with zero-adjustment rules → shows count > 0, message explains no deductions
   - Listing with no rules → shows "0 rules applied"

4. **Edge Cases**:
   - Very long CPU/GPU names → truncation/wrapping works
   - Special characters in names → proper encoding
   - Null/undefined values → graceful fallback

#### Task 4.2: Performance Validation

**Metrics to Monitor**:
- API response time for `/v1/listings/{id}` (should be < 200ms)
- Catalog table render time with 50 listings (should be < 500ms)
- Tooltip appearance delay (should be < 100ms)
- No memory leaks from tooltip components

**Tools**:
- Chrome DevTools Performance tab
- React DevTools Profiler
- Network tab for API timing

#### Task 4.3: Create Bug Report Template

If issues found, use this template:

```markdown
## Bug Report: [Component/Feature]

**Severity**: [Critical/High/Medium/Low]
**Environment**: [Browser, OS]

### Steps to Reproduce
1.
2.
3.

### Expected Behavior


### Actual Behavior


### Screenshots/Logs


### Root Cause (if known)


### Suggested Fix

```

## Testing Strategy

### Unit Tests (Backend)
- ✅ Computed properties return correct values
- ✅ Computed properties handle null relationships
- ✅ Thumbnail URL extraction prioritizes correctly

### Integration Tests (API)
- ✅ `/v1/listings/{id}` includes `cpu_name`, `gpu_name`, `thumbnail_url`
- ✅ Nested `cpu` and `gpu` objects still present
- ✅ No performance regression

### Component Tests (Frontend)
- ✅ Valuation tab shows correct rule count
- ✅ Modal displays URLs when present
- ✅ Specifications tab displays all fields
- ✅ Tooltips render and fetch data correctly

### E2E Tests
- ✅ Full user flow: view catalog → open modal → view detail page
- ✅ Tooltip interactions work across all views
- ✅ Data consistency between views

## Rollout Plan

### Stage 1: Backend Deployment
1. Deploy backend changes to staging
2. Verify API response structure
3. Run smoke tests
4. Deploy to production
5. Monitor error rates and performance

### Stage 2: Frontend Deployment (Same Day)
1. Build frontend with updated types
2. Deploy to staging
3. Test all views manually
4. Deploy to production
5. Monitor for client-side errors

### Stage 3: Monitoring (First 24 Hours)
1. Watch error tracking (Sentry, etc.)
2. Monitor API performance (Prometheus/Grafana)
3. Check user feedback channels
4. Prepare hotfix if needed

## Success Criteria

- [ ] CPU/GPU names display correctly in all 6 locations (modal, detail hero, specs tab, table, grid, valuation tab)
- [ ] Product images appear in modal and detail page
- [ ] Valuation tab shows accurate rule count
- [ ] URLs display in modal and specifications tab
- [ ] Entity tooltips work in catalog table and grid
- [ ] No performance regression (< 5% increase in page load time)
- [ ] No accessibility regressions (WCAG 2.1 AA maintained)
- [ ] Zero critical bugs in first 24 hours

## Rollback Plan

If critical issues arise:

1. **Frontend Only Issues**: Revert frontend deployment, keep backend changes (backward compatible)
2. **Backend Issues**:
   - Revert backend changes
   - Frontend will use `cpu.name` instead of `cpu_name` (fallback logic)
3. **Performance Issues**:
   - Add database indexes if query slow
   - Implement API response caching if needed

## Future Enhancements

Post-remediation improvements to consider:

1. **Computed Fields**: Add `ram_summary`, `storage_summary` properties
2. **Image CDN**: Move thumbnail_url to CDN for better performance
3. **Tooltip Caching**: Cache entity data to reduce API calls
4. **Grid View**: If doesn't exist, create grid alternative to table view
5. **Bulk Operations**: Add bulk edit with tooltip previews

## References

- [ADR-009: Listings Facelift Remediation Architecture](/docs/architecture/decisions/ADR-009-listings-facelift-remediation.md)
- [Original PRD](/docs/project_plans/listings-facelift-enhancement/PRD.md)
- [Issues Document](/docs/project_plans/listings-facelift-enhancement/listings-facelift-enhancements.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Radix UI Tooltip](https://www.radix-ui.com/primitives/docs/components/tooltip)
