# Deal Brain Listings Enhancements v3 - Implementation Plan

**Version:** 1.0
**Created:** October 31, 2025
**Updated:** October 31, 2025
**Status:** Ready for Development
**Engineering Lead:** TBD

---

## Executive Summary

This implementation plan provides a detailed technical roadmap for the four enhancement areas defined in the PRD:

1. **Data Tab Performance Optimization** - Implement virtualization and optimize rendering
2. **Adjusted Value Renaming & Tooltips** - Rename terminology and add contextual help
3. **CPU Metrics Layout** - Pair related metrics with dual values and color coding
4. **Image Management System** - Create configuration-driven image resolution

### Effort Estimate

| Phase | Backend | Frontend | Testing | Total |
|-------|---------|----------|---------|-------|
| Phase 1: Performance | 16h | 40h | 16h | 72h (9 days) |
| Phase 2: Adjusted Value | 4h | 16h | 8h | 28h (3.5 days) |
| Phase 3: CPU Metrics | 8h | 24h | 12h | 44h (5.5 days) |
| Phase 4: Image Management | 8h | 32h | 12h | 52h (6.5 days) |
| **TOTAL** | **36h** | **112h** | **48h** | **196h (24.5 days)** |

**Timeline:** 6-8 weeks (with testing, review, and deployment)

### Key Technical Decisions

1. **Virtualization:** Use `@tanstack/react-virtual` for table virtualization
2. **Backend Pagination:** Add cursor-based pagination for datasets > 500 rows
3. **Image Config:** JSON configuration file for maintainability and TypeScript integration
4. **Settings Storage:** Reuse ApplicationSettings model for thresholds
5. **Backward Compatibility:** Feature flags for gradual rollout

### Critical Dependencies

- **External:** No new major dependencies
- **Internal:** Completion of Phase 2 before Phase 3 (shared tooltip component)
- **Team:** Frontend engineer availability (112 hours needed)

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser / Client                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Listings Page    │  │ Detail Page      │  │ Image Config │ │
│  │                  │  │                  │  │ (Static JSON)│ │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │              │ │
│  │ │ Catalog Tab  │ │  │ │ Specs Tab    │ │  │ Loaded at    │ │
│  │ └──────────────┘ │  │ │ - CPU Metrics│ │  │ Build Time   │ │
│  │ ┌──────────────┐ │  │ │ - Tooltips   │ │  │              │ │
│  │ │ Data Tab     │ │  │ └──────────────┘ │  │              │ │
│  │ │ - Virtual    │ │  │ ┌──────────────┐ │  │              │ │
│  │ │   Table      │ │  │ │ Hero Section │ │  │              │ │
│  │ │ - Pagination │ │  │ │ - Image      │ │  │              │ │
│  │ └──────────────┘ │  │ │ - Tooltip    │ │  │              │ │
│  └──────────────────┘  │ └──────────────┘ │  │              │ │
│           │             └──────────────────┘  └──────────────┘ │
│           │                     │                      │        │
│           ▼                     ▼                      ▼        │
│  ┌────────────────────────────────────────────────────────────┐│
│  │               React Query Cache (5min TTL)                 ││
│  └────────────────────────────────────────────────────────────┘│
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP/REST
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                         │  │
│  │  GET /v1/listings (with pagination params)               │  │
│  │  GET /v1/listings/{id}                                   │  │
│  │  GET /v1/settings/valuation_thresholds                   │  │
│  │  GET /v1/settings/cpu_mark_thresholds (NEW)              │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│                   ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Services Layer                              │  │
│  │  - ListingsService (CRUD, metrics calculation)           │  │
│  │  - SettingsService (threshold management)                │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│                   ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy ORM                              │  │
│  │  - Listing model (existing fields)                       │  │
│  │  - ApplicationSettings model (NEW: cpu_mark_thresholds)  │  │
│  └────────────────┬─────────────────────────────────────────┘  │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
           ┌──────────────────┐
           │   PostgreSQL     │
           │   Database       │
           └──────────────────┘
```

### Data Flow: Adjusted Value Tooltip

```
User hovers over "Adjusted Value"
         │
         ▼
Tooltip component renders
         │
         ▼
Extract listing.valuation_breakdown JSON
         │
         ├─> listing_price: $500
         ├─> adjusted_price: $450
         ├─> matched_rules: [...]
         │   └─> Sort by absolute adjustment
         │       └─> Take top 3-5 rules
         ▼
Format tooltip content
  "List Price: $500.00"
  "Adjustments: -$50.00"
  "Adjusted Value: $450.00 (10% savings)"
  "Applied 3 valuation rules:"
  "• RAM deduction: -$30"
  "• Condition (Used): -$15"
  "• Missing storage: -$5"
  [View Full Breakdown →]
         │
         ▼
Render tooltip with link to modal
```

### Data Flow: CPU Mark Color Coding

```
Listing loaded from API
         │
         ▼
Extract metrics:
  - price_usd: $500
  - adjusted_price_usd: $450
  - cpu.cpu_mark_multi: 18,200
  - cpu.cpu_mark_single: 3,450
         │
         ▼
Calculate base $/CPU Mark:
  - base_multi = $500 / 18,200 = $0.0275
  - base_single = $500 / 3,450 = $0.145
         │
         ▼
Calculate adjusted $/CPU Mark:
  - adj_multi = $450 / 18,200 = $0.0247
  - adj_single = $450 / 3,450 = $0.130
         │
         ▼
Calculate improvement:
  - multi_improvement = (base - adj) / base * 100 = 10.2%
  - single_improvement = (base - adj) / base * 100 = 10.3%
         │
         ▼
Fetch cpu_mark_thresholds from settings:
  {excellent: 20%, good: 10%, fair: 5%, ...}
         │
         ▼
Apply threshold logic:
  - multi_improvement (10.2%) → "good" threshold
  - single_improvement (10.3%) → "good" threshold
         │
         ▼
Apply color styling:
  - Background: Medium green
  - Text: Dark green
  - Icon: ⬇️
         │
         ▼
Render colored metric display
```

---

## Implementation Phases

### Phase 1: Data Tab Performance Optimization

**Objectives:**
- Achieve <200ms interaction latency for 1,000 listings
- Implement row virtualization for smooth 60fps scrolling
- Add backend pagination for large datasets
- Optimize React rendering performance

**Prerequisites:**
- None (independent phase)

**Estimated Duration:** 2 weeks

---

#### PERF-001: Install and Configure React Virtual

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] `@tanstack/react-virtual` installed and configured
- [ ] TypeScript types available
- [ ] No peer dependency conflicts

**Implementation Steps:**

1. Install dependency:
   ```bash
   cd apps/web
   pnpm add @tanstack/react-virtual
   ```

2. Verify TypeScript types:
   ```typescript
   import { useVirtualizer } from '@tanstack/react-virtual';
   ```

3. Test basic virtualization in isolated component

**Testing Requirements:**
- [ ] Build succeeds with new dependency
- [ ] No type errors

---

#### PERF-002: Implement Table Row Virtualization

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 16 hours
**Dependencies:** PERF-001

**Acceptance Criteria:**
- [ ] Table renders only visible rows + overscan buffer (10 rows)
- [ ] Scroll performance at 60fps with 1,000+ rows
- [ ] Virtualization auto-enabled when row count > 100
- [ ] Scroll position maintained during sort/filter
- [ ] Row selection works with virtualized rows

**Implementation Steps:**

1. **Update ListingsTable component** (`apps/web/components/listings/listings-table.tsx`):

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const VIRTUALIZATION_THRESHOLD = 100;
const OVERSCAN_COUNT = 10;

export function ListingsTable({ enableInlineEdit = false }: ListingsTableProps) {
  const { data: records = [], isLoading } = useListingsRecords();

  // Existing table setup...
  const table = useReactTable({...});

  // Virtualization setup
  const tableContainerRef = useRef<HTMLDivElement>(null);
  const { rows } = table.getRowModel();

  const shouldVirtualize = rows.length > VIRTUALIZATION_THRESHOLD;

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 48, // Row height in pixels
    overscan: OVERSCAN_COUNT,
    enabled: shouldVirtualize,
  });

  const virtualRows = shouldVirtualize
    ? rowVirtualizer.getVirtualItems()
    : rows.map((_, index) => ({ index, start: index * 48, size: 48 }));

  const paddingTop = shouldVirtualize && virtualRows.length > 0
    ? virtualRows[0]?.start || 0
    : 0;
  const paddingBottom = shouldVirtualize && virtualRows.length > 0
    ? rowVirtualizer.getTotalSize() - (virtualRows[virtualRows.length - 1]?.end || 0)
    : 0;

  return (
    <div ref={tableContainerRef} className="overflow-auto h-[600px]">
      <table>
        <thead>{/* Existing header */}</thead>
        <tbody>
          {paddingTop > 0 && (
            <tr>
              <td style={{ height: `${paddingTop}px` }} />
            </tr>
          )}
          {virtualRows.map((virtualRow) => {
            const row = rows[virtualRow.index];
            return (
              <tr key={row.id} data-index={virtualRow.index}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            );
          })}
          {paddingBottom > 0 && (
            <tr>
              <td style={{ height: `${paddingBottom}px` }} />
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
```

2. **Add virtualization toggle in table settings:**
   - Allow users to disable virtualization if needed
   - Store preference in localStorage

3. **Test scroll position preservation:**
   - Apply filter → verify scroll position maintained
   - Sort column → verify scroll position maintained
   - Select rows → verify selection persists

**Testing Requirements:**
- [ ] Unit test: Virtualization enabled when row count > 100
- [ ] Unit test: All rows render when count <= 100
- [ ] E2E test: Scroll performance with 1,000 rows
- [ ] E2E test: Row selection with virtualized rows

---

#### PERF-003: Add Backend Pagination Endpoint

**Type:** Backend
**Priority:** P1-High
**Effort:** 8 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] New endpoint supports cursor-based pagination
- [ ] Query parameters: `limit`, `cursor`, `sort_by`, `sort_order`
- [ ] Returns total count for UI pagination
- [ ] Performance: <100ms for 500-row page

**Implementation Steps:**

1. **Update listings API** (`apps/api/dealbrain_api/api/listings.py`):

```python
from typing import Optional
from fastapi import Query

@router.get("/v1/listings/paginated", response_model=PaginatedListingsResponse)
async def get_listings_paginated(
    limit: int = Query(50, ge=1, le=500),
    cursor: Optional[str] = None,
    sort_by: str = Query("updated_at", regex="^[a-z_]+$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    # Filter params
    form_factor: Optional[str] = None,
    manufacturer: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Paginated listings endpoint for large datasets.
    Uses cursor-based pagination for efficient querying.
    """
    result = await listings_service.get_listings_paginated(
        session,
        limit=limit,
        cursor=cursor,
        sort_by=sort_by,
        sort_order=sort_order,
        filters={
            "form_factor": form_factor,
            "manufacturer": manufacturer,
            "min_price": min_price,
            "max_price": max_price,
        },
    )
    return result
```

2. **Add service method** (`apps/api/dealbrain_api/services/listings.py`):

```python
from typing import Optional, Dict, Any
from sqlalchemy import select, func, desc, asc
from dealbrain_api.schemas.listings import PaginatedListingsResponse

async def get_listings_paginated(
    session: AsyncSession,
    limit: int,
    cursor: Optional[str],
    sort_by: str,
    sort_order: str,
    filters: Dict[str, Any],
) -> PaginatedListingsResponse:
    """
    Cursor-based pagination for listings.
    Cursor format: base64-encoded JSON {"id": 123, "sort_value": "2025-10-31"}
    """
    # Build base query
    query = select(Listing).options(
        selectinload(Listing.cpu),
        selectinload(Listing.gpu),
        selectinload(Listing.ports_profile),
    )

    # Apply filters
    if filters.get("form_factor"):
        query = query.where(Listing.form_factor == filters["form_factor"])
    if filters.get("manufacturer"):
        query = query.where(Listing.manufacturer == filters["manufacturer"])
    if filters.get("min_price"):
        query = query.where(Listing.price_usd >= filters["min_price"])
    if filters.get("max_price"):
        query = query.where(Listing.price_usd <= filters["max_price"])

    # Decode cursor
    if cursor:
        cursor_data = decode_cursor(cursor)
        sort_col = getattr(Listing, sort_by)
        if sort_order == "desc":
            query = query.where(
                (sort_col < cursor_data["sort_value"]) |
                ((sort_col == cursor_data["sort_value"]) & (Listing.id < cursor_data["id"]))
            )
        else:
            query = query.where(
                (sort_col > cursor_data["sort_value"]) |
                ((sort_col == cursor_data["sort_value"]) & (Listing.id > cursor_data["id"]))
            )

    # Apply sorting
    sort_col = getattr(Listing, sort_by)
    order_func = desc if sort_order == "desc" else asc
    query = query.order_by(order_func(sort_col), order_func(Listing.id))

    # Fetch limit + 1 to check if there are more results
    query = query.limit(limit + 1)
    result = await session.execute(query)
    listings = result.scalars().all()

    # Check for next page
    has_next = len(listings) > limit
    if has_next:
        listings = listings[:limit]

    # Generate next cursor
    next_cursor = None
    if has_next and listings:
        last_listing = listings[-1]
        next_cursor = encode_cursor({
            "id": last_listing.id,
            "sort_value": getattr(last_listing, sort_by),
        })

    # Get total count (cached for 5 minutes)
    total_count = await get_cached_total_count(session, filters)

    return PaginatedListingsResponse(
        items=listings,
        total=total_count,
        limit=limit,
        next_cursor=next_cursor,
        has_next=has_next,
    )

def encode_cursor(data: Dict[str, Any]) -> str:
    """Base64-encode cursor data."""
    import base64
    import json
    json_str = json.dumps(data, default=str)
    return base64.b64encode(json_str.encode()).decode()

def decode_cursor(cursor: str) -> Dict[str, Any]:
    """Base64-decode cursor data."""
    import base64
    import json
    json_str = base64.b64decode(cursor.encode()).decode()
    return json.loads(json_str)
```

3. **Add response schema** (`apps/api/dealbrain_api/schemas/listings.py`):

```python
from pydantic import BaseModel
from typing import List, Optional

class PaginatedListingsResponse(BaseModel):
    items: List[ListingRead]
    total: int
    limit: int
    next_cursor: Optional[str] = None
    has_next: bool
```

**Testing Requirements:**
- [ ] Unit test: Pagination with various limits
- [ ] Unit test: Cursor encoding/decoding
- [ ] Integration test: Pagination with filters and sorting
- [ ] Performance test: <100ms response time for 500-row page

---

#### PERF-004: Optimize React Component Rendering

**Type:** Frontend
**Priority:** P1-High
**Effort:** 12 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] All heavy components use React.memo
- [ ] Expensive calculations wrapped in useMemo
- [ ] Event handlers wrapped in useCallback
- [ ] CSS containment applied to table rows
- [ ] Render count reduced by 50%+

**Implementation Steps:**

1. **Audit component renders** using React Profiler:
   ```bash
   # Add profiling in development
   npm run dev -- --profile
   ```

2. **Optimize ValuationCell** (already memoized, verify):
   ```typescript
   export const ValuationCell = React.memo(function ValuationCellComponent({
     adjustedPrice,
     listPrice,
     thresholds,
     onDetailsClick,
   }: ValuationCellProps) {
     // Use useMemo for expensive calculations
     const { delta, deltaPercent, style } = useMemo(() => {
       const d = listPrice - adjustedPrice;
       const dp = (d / listPrice) * 100;
       return {
         delta: d,
         deltaPercent: dp,
         style: getValuationStyle(dp, thresholds),
       };
     }, [adjustedPrice, listPrice, thresholds]);

     // Use useCallback for event handlers
     const handleClick = useCallback(() => {
       onDetailsClick?.();
     }, [onDetailsClick]);

     return (
       <div className={style.containerClass}>
         {/* Render valuation */}
       </div>
     );
   }, (prevProps, nextProps) => {
     // Custom comparison function
     return (
       prevProps.adjustedPrice === nextProps.adjustedPrice &&
       prevProps.listPrice === nextProps.listPrice &&
       prevProps.thresholds === nextProps.thresholds
     );
   });
   ```

3. **Apply CSS containment to table rows:**
   ```css
   /* apps/web/styles/listings-table.css */
   .listing-table-row {
     contain: layout style paint;
     content-visibility: auto;
     contain-intrinsic-size: auto 48px;
   }
   ```

4. **Optimize column definitions** (memoize outside component):
   ```typescript
   const COLUMN_DEFS = [
     // Define columns outside component to prevent recreation
   ];

   export function ListingsTable() {
     const columns = useMemo(() => COLUMN_DEFS, []);
     // Use memoized columns
   }
   ```

**Testing Requirements:**
- [ ] Performance test: Measure render count before/after
- [ ] Performance test: Interaction latency <150ms
- [ ] E2E test: No visual regressions

---

#### PERF-005: Add Performance Monitoring

**Type:** Frontend
**Priority:** P2-Medium
**Effort:** 8 hours
**Dependencies:** PERF-002, PERF-004

**Acceptance Criteria:**
- [ ] Track interaction latency (sort, filter, scroll)
- [ ] Track render performance (component render time)
- [ ] Log metrics to analytics
- [ ] Display performance metrics in dev mode

**Implementation Steps:**

1. **Add performance instrumentation:**
   ```typescript
   // apps/web/lib/performance.ts

   export function measureInteraction(name: string, fn: () => void) {
     const start = performance.now();
     fn();
     const duration = performance.now() - start;

     // Log to analytics
     logMetric('interaction_latency', {
       name,
       duration,
       timestamp: Date.now(),
     });

     // Warn if exceeds target
     if (duration > 200) {
       console.warn(`Slow interaction: ${name} took ${duration}ms`);
     }
   }
   ```

2. **Wrap table interactions:**
   ```typescript
   const handleSort = useCallback((columnId: string) => {
     measureInteraction('column_sort', () => {
       table.setSorting([{ id: columnId, desc: !sorting[0]?.desc }]);
     });
   }, [table, sorting]);
   ```

3. **Add React Profiler:**
   ```typescript
   import { Profiler } from 'react';

   function onRenderCallback(
     id: string,
     phase: 'mount' | 'update',
     actualDuration: number,
   ) {
     if (actualDuration > 50) {
       console.warn(`Slow render: ${id} took ${actualDuration}ms`);
     }
   }

   export function ListingsTable() {
     return (
       <Profiler id="listings-table" onRender={onRenderCallback}>
         {/* Table content */}
       </Profiler>
     );
   }
   ```

**Testing Requirements:**
- [ ] Verify metrics logged correctly
- [ ] Test dev mode performance overlay

---

### Phase 2: Adjusted Value Renaming & Tooltips

**Objectives:**
- Rename "Adjusted Price" to "Adjusted Value" across application
- Add hover tooltips explaining valuation calculation
- Ensure accessibility (keyboard, screen readers)

**Prerequisites:**
- None (independent phase)

**Estimated Duration:** 3-4 days

---

#### UX-001: Global Find-and-Replace for "Adjusted Price"

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] All UI labels changed to "Adjusted Value"
- [ ] Code comments updated
- [ ] No breaking changes to API or props

**Implementation Steps:**

1. **Find all occurrences:**
   ```bash
   cd apps/web
   grep -r "Adjusted Price" --include="*.tsx" --include="*.ts"
   ```

2. **Update component files:**
   - `apps/web/components/listings/detail-page-layout.tsx`
   - `apps/web/components/listings/specifications-tab.tsx`
   - `apps/web/components/listings/valuation-tab.tsx`
   - `apps/web/components/listings/listings-table.tsx`
   - `apps/web/components/listings/catalog-card.tsx`

3. **Update type definitions:**
   - Keep `adjustedPrice` prop names (no breaking changes)
   - Update comments and labels only

4. **Verify no missed instances:**
   ```bash
   grep -r "Adjusted Price" apps/web
   # Should return zero results
   ```

**Testing Requirements:**
- [ ] Visual regression test: All pages display "Adjusted Value"
- [ ] E2E test: Verify terminology in all views

---

#### UX-002: Create Valuation Tooltip Component

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 8 hours
**Dependencies:** UX-001

**Acceptance Criteria:**
- [ ] Reusable ValuationTooltip component
- [ ] Shows calculation summary (list price, adjustments, adjusted value)
- [ ] Lists top 3-5 rules by impact
- [ ] Link to full breakdown modal
- [ ] Accessible (keyboard, screen reader)

**Implementation Steps:**

1. **Create component** (`apps/web/components/listings/valuation-tooltip.tsx`):

```typescript
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { InfoIcon } from 'lucide-react';
import { formatCurrency } from '@/lib/utils';

interface ValuationTooltipProps {
  listPrice: number;
  adjustedValue: number;
  valuationBreakdown?: any; // ValuationBreakdown type
  onViewDetails?: () => void;
  children?: React.ReactNode;
}

export function ValuationTooltip({
  listPrice,
  adjustedValue,
  valuationBreakdown,
  onViewDetails,
  children,
}: ValuationTooltipProps) {
  const delta = listPrice - adjustedValue;
  const deltaPercent = (delta / listPrice) * 100;

  // Extract top rules by absolute impact
  const topRules = useMemo(() => {
    if (!valuationBreakdown?.matched_rules) return [];
    return valuationBreakdown.matched_rules
      .sort((a, b) => Math.abs(b.adjustment) - Math.abs(a.adjustment))
      .slice(0, 5);
  }, [valuationBreakdown]);

  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children || (
            <button
              className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
              aria-label="View valuation details"
            >
              <InfoIcon className="h-4 w-4" />
            </button>
          )}
        </TooltipTrigger>
        <TooltipContent
          side="top"
          className="max-w-[320px] p-3"
          aria-label="Valuation calculation details"
        >
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Adjusted Value Calculation</h4>

            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">List Price:</span>
                <span className="font-medium">{formatCurrency(listPrice)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Adjustments:</span>
                <span className={delta > 0 ? 'text-green-600' : 'text-red-600'}>
                  {delta > 0 ? '-' : '+'}{formatCurrency(Math.abs(delta))}
                </span>
              </div>
              <div className="flex justify-between border-t pt-1">
                <span className="font-medium">Adjusted Value:</span>
                <span className="font-semibold">{formatCurrency(adjustedValue)}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                ({deltaPercent > 0 ? '' : '+'}{deltaPercent.toFixed(1)}% {deltaPercent > 0 ? 'savings' : 'premium'})
              </div>
            </div>

            {topRules.length > 0 && (
              <div className="space-y-1 border-t pt-2">
                <p className="text-xs text-muted-foreground">
                  Applied {valuationBreakdown.matched_rules_count} valuation rules:
                </p>
                <ul className="space-y-1 text-xs">
                  {topRules.map((rule) => (
                    <li key={rule.rule_id} className="flex justify-between">
                      <span className="truncate mr-2">• {rule.rule_name}</span>
                      <span className={rule.adjustment < 0 ? 'text-green-600' : 'text-red-600'}>
                        {rule.adjustment < 0 ? '' : '+'}{formatCurrency(rule.adjustment)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {onViewDetails && (
              <button
                onClick={onViewDetails}
                className="w-full mt-2 text-xs text-primary hover:underline flex items-center justify-center gap-1"
              >
                View Full Breakdown →
              </button>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
```

2. **Add keyboard accessibility:**
   - Tooltip triggers on focus (Tab key)
   - Dismisses on Escape key
   - Link is keyboard navigable

3. **Add screen reader support:**
   - Use `aria-label` and `aria-describedby`
   - Announce tooltip content

**Testing Requirements:**
- [ ] Unit test: Tooltip renders with correct content
- [ ] Unit test: Top rules sorted by impact
- [ ] A11y test: Keyboard navigation works
- [ ] A11y test: Screen reader announces content

---

#### UX-003: Integrate Tooltip in Detail Page

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** UX-002

**Acceptance Criteria:**
- [ ] Tooltip appears on "Adjusted Value" in hero section
- [ ] Tooltip links to existing breakdown modal
- [ ] Styling consistent with design system

**Implementation Steps:**

1. **Update DetailPageLayout** (`apps/web/components/listings/detail-page-layout.tsx`):

```typescript
import { ValuationTooltip } from './valuation-tooltip';

export function DetailPageLayout({ listing }: DetailPageLayoutProps) {
  const [showBreakdownModal, setShowBreakdownModal] = useState(false);

  return (
    <div>
      {/* Hero section */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <span className="text-sm text-muted-foreground">List Price</span>
          <p className="text-2xl font-bold">{formatCurrency(listing.price_usd)}</p>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Adjusted Value</span>
            <ValuationTooltip
              listPrice={listing.price_usd}
              adjustedValue={listing.adjusted_price_usd}
              valuationBreakdown={listing.valuation_breakdown}
              onViewDetails={() => setShowBreakdownModal(true)}
            />
          </div>
          <p className="text-2xl font-bold">{formatCurrency(listing.adjusted_price_usd)}</p>
        </div>
      </div>

      {/* Breakdown modal */}
      <ValuationBreakdownModal
        open={showBreakdownModal}
        onOpenChange={setShowBreakdownModal}
        listing={listing}
      />
    </div>
  );
}
```

**Testing Requirements:**
- [ ] E2E test: Tooltip appears on hover
- [ ] E2E test: Clicking link opens modal
- [ ] Visual test: Styling matches design

---

### Phase 3: CPU Performance Metrics Layout

**Objectives:**
- Pair related CPU metrics (Score with $/Mark)
- Display base and adjusted values side-by-side
- Add color coding based on thresholds
- Add tooltips for adjusted values

**Prerequisites:**
- UX-002 completed (ValuationTooltip component)

**Estimated Duration:** 5-6 days

---

#### METRICS-001: Create CPU Mark Thresholds Setting

**Type:** Backend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Database migration adds default thresholds
- [ ] API endpoint returns thresholds
- [ ] Settings service manages thresholds

**Implementation Steps:**

1. **Create migration** (`apps/api/alembic/versions/xxx_add_cpu_mark_thresholds.py`):

```python
"""Add CPU mark thresholds to application settings

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-31
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.execute("""
        INSERT INTO application_settings (key, value, description, created_at, updated_at)
        VALUES (
            'cpu_mark_thresholds',
            '{"excellent": 20.0, "good": 10.0, "fair": 5.0, "neutral": 0.0, "poor": -10.0, "premium": -20.0}'::jsonb,
            'Thresholds for color-coding CPU performance metrics (percentage improvement)',
            NOW(),
            NOW()
        )
        ON CONFLICT (key) DO NOTHING;
    """)

def downgrade():
    op.execute("""
        DELETE FROM application_settings WHERE key = 'cpu_mark_thresholds';
    """)
```

2. **Add API endpoint** (`apps/api/dealbrain_api/api/settings.py`):

```python
@router.get("/settings/cpu_mark_thresholds", response_model=CpuMarkThresholds)
async def get_cpu_mark_thresholds(
    session: AsyncSession = Depends(get_session),
):
    """Get CPU Mark color-coding thresholds."""
    thresholds = await settings_service.get_cpu_mark_thresholds(session)
    return thresholds
```

3. **Add service method** (`apps/api/dealbrain_api/services/settings.py`):

```python
async def get_cpu_mark_thresholds(self, session: AsyncSession) -> dict:
    """Get CPU Mark thresholds from settings."""
    setting = await self.get_setting(session, "cpu_mark_thresholds")
    if not setting:
        return {
            "excellent": 20.0,
            "good": 10.0,
            "fair": 5.0,
            "neutral": 0.0,
            "poor": -10.0,
            "premium": -20.0,
        }
    return setting
```

4. **Add schema** (`apps/api/dealbrain_api/schemas/settings.py`):

```python
from pydantic import BaseModel

class CpuMarkThresholds(BaseModel):
    excellent: float
    good: float
    fair: float
    neutral: float
    poor: float
    premium: float
```

**Testing Requirements:**
- [ ] Unit test: Migration runs successfully
- [ ] Unit test: Endpoint returns default thresholds
- [ ] Integration test: Thresholds persist in database

---

#### METRICS-002: Create Performance Metric Display Component

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 12 hours
**Dependencies:** METRICS-001, UX-002

**Acceptance Criteria:**
- [ ] Component displays base and adjusted values
- [ ] Color coding based on improvement percentage
- [ ] Tooltip explains calculation
- [ ] Responsive layout

**Implementation Steps:**

1. **Create component** (`apps/web/components/listings/performance-metric-display.tsx`):

```typescript
import { useCpuMarkThresholds } from '@/hooks/use-cpu-mark-thresholds';
import { ValuationTooltip } from './valuation-tooltip';
import { formatCurrency } from '@/lib/utils';

interface PerformanceMetricDisplayProps {
  label: string;
  score?: number;
  baseValue?: number;
  adjustedValue?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  showColorCoding?: boolean;
  listPrice?: number;
  adjustedPrice?: number;
  cpuMark?: number;
}

export function PerformanceMetricDisplay({
  label,
  score,
  baseValue,
  adjustedValue,
  prefix = '$',
  decimals = 3,
  showColorCoding = false,
  listPrice,
  adjustedPrice,
  cpuMark,
}: PerformanceMetricDisplayProps) {
  const { data: thresholds } = useCpuMarkThresholds();

  const improvement = useMemo(() => {
    if (!baseValue || !adjustedValue) return 0;
    return ((baseValue - adjustedValue) / baseValue) * 100;
  }, [baseValue, adjustedValue]);

  const colorStyle = useMemo(() => {
    if (!showColorCoding || !thresholds) return null;
    return getCpuMarkColorStyle(improvement, thresholds);
  }, [improvement, showColorCoding, thresholds]);

  return (
    <div className="space-y-1">
      <dt className="text-sm font-medium text-muted-foreground">{label}</dt>
      <dd className="flex items-baseline gap-2">
        {score !== undefined && (
          <span className="text-lg font-semibold">{score.toLocaleString()}</span>
        )}
        {baseValue !== undefined && adjustedValue !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {prefix}{baseValue.toFixed(decimals)}
            </span>
            <span className="text-muted-foreground">→</span>
            <div className="flex items-center gap-1">
              <span
                className={cn(
                  'text-sm font-semibold',
                  colorStyle && `text-[${colorStyle.fg}] bg-[${colorStyle.bg}] px-2 py-0.5 rounded`
                )}
              >
                {prefix}{adjustedValue.toFixed(decimals)}
              </span>
              {improvement !== 0 && (
                <span className={cn(
                  'text-xs',
                  improvement > 0 ? 'text-green-600' : 'text-red-600'
                )}>
                  ({improvement > 0 ? '↓' : '↑'}{Math.abs(improvement).toFixed(1)}%)
                </span>
              )}
              <ValuationTooltip
                listPrice={listPrice || 0}
                adjustedValue={adjustedPrice || 0}
                valuationBreakdown={{
                  listing_price: listPrice,
                  adjusted_price: adjustedPrice,
                  cpu_mark: cpuMark,
                  base_metric: baseValue,
                  adjusted_metric: adjustedValue,
                }}
              />
            </div>
          </div>
        )}
      </dd>
    </div>
  );
}
```

2. **Add color utility** (`apps/web/lib/cpu-mark-utils.ts`):

```typescript
export function getCpuMarkColorStyle(improvement: number, thresholds: CpuMarkThresholds) {
  if (improvement >= thresholds.excellent) {
    return { bg: 'hsl(var(--cpu-mark-excellent-bg))', fg: 'hsl(var(--cpu-mark-excellent-fg))' };
  } else if (improvement >= thresholds.good) {
    return { bg: 'hsl(var(--cpu-mark-good-bg))', fg: 'hsl(var(--cpu-mark-good-fg))' };
  } else if (improvement >= thresholds.fair) {
    return { bg: 'hsl(var(--cpu-mark-fair-bg))', fg: 'hsl(var(--cpu-mark-fair-fg))' };
  } else if (improvement >= thresholds.neutral) {
    return { bg: 'hsl(var(--cpu-mark-neutral-bg))', fg: 'hsl(var(--cpu-mark-neutral-fg))' };
  } else if (improvement >= thresholds.poor) {
    return { bg: 'hsl(var(--cpu-mark-poor-bg))', fg: 'hsl(var(--cpu-mark-poor-fg))' };
  } else {
    return { bg: 'hsl(var(--cpu-mark-premium-bg))', fg: 'hsl(var(--cpu-mark-premium-fg))' };
  }
}
```

3. **Add CSS variables** (`apps/web/styles/globals.css`):

```css
:root {
  --cpu-mark-excellent-bg: 142 71% 25%;
  --cpu-mark-excellent-fg: 0 0% 100%;
  --cpu-mark-good-bg: 142 71% 45%;
  --cpu-mark-good-fg: 142 71% 15%;
  --cpu-mark-fair-bg: 142 71% 85%;
  --cpu-mark-fair-fg: 142 71% 25%;
  --cpu-mark-neutral-bg: 0 0% 90%;
  --cpu-mark-neutral-fg: 0 0% 20%;
  --cpu-mark-poor-bg: 0 84% 85%;
  --cpu-mark-poor-fg: 0 84% 25%;
  --cpu-mark-premium-bg: 0 84% 40%;
  --cpu-mark-premium-fg: 0 0% 100%;
}
```

**Testing Requirements:**
- [ ] Unit test: Color selection based on improvement
- [ ] Unit test: Percentage calculation
- [ ] Visual test: Color coding matches design
- [ ] A11y test: Contrast ratios meet WCAG AA

---

#### METRICS-003: Update Specifications Tab Layout

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 8 hours
**Dependencies:** METRICS-002

**Acceptance Criteria:**
- [ ] CPU metrics paired (Score next to $/Mark)
- [ ] Both single-thread and multi-thread shown
- [ ] Layout responsive (mobile stacks vertically)

**Implementation Steps:**

1. **Update SpecificationsTab** (`apps/web/components/listings/specifications-tab.tsx`):

```typescript
import { PerformanceMetricDisplay } from './performance-metric-display';

export function SpecificationsTab({ listing }: SpecificationsTabProps) {
  // Calculate base $/CPU Mark values
  const baseSingleThreadMark = listing.price_usd / (listing.cpu?.cpu_mark_single || 1);
  const baseMultiThreadMark = listing.price_usd / (listing.cpu?.cpu_mark_multi || 1);

  const adjustedSingleThreadMark = listing.adjusted_price_usd / (listing.cpu?.cpu_mark_single || 1);
  const adjustedMultiThreadMark = listing.adjusted_price_usd / (listing.cpu?.cpu_mark_multi || 1);

  return (
    <div className="space-y-6">
      {/* Compute Section */}
      <Card>
        <CardHeader>
          <CardTitle>Compute</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* CPU */}
          <dl className="grid grid-cols-1 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">CPU</dt>
              <dd>{listing.cpu?.name || 'Not specified'}</dd>
            </div>
            {listing.gpu && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">GPU</dt>
                <dd>{listing.gpu.name}</dd>
              </div>
            )}
          </dl>

          {/* Performance Metrics - Paired Layout */}
          <div className="border-t pt-4 space-y-3">
            <h4 className="text-sm font-semibold">Performance Metrics</h4>

            {/* Single-Thread */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-muted/50 rounded-lg">
              <PerformanceMetricDisplay
                label="Single-Thread Score"
                score={listing.cpu?.cpu_mark_single}
              />
              <PerformanceMetricDisplay
                label="$/Single-Thread Mark"
                baseValue={baseSingleThreadMark}
                adjustedValue={adjustedSingleThreadMark}
                showColorCoding
                listPrice={listing.price_usd}
                adjustedPrice={listing.adjusted_price_usd}
                cpuMark={listing.cpu?.cpu_mark_single}
              />
            </div>

            {/* Multi-Thread */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-muted/50 rounded-lg">
              <PerformanceMetricDisplay
                label="Multi-Thread Score"
                score={listing.cpu?.cpu_mark_multi}
              />
              <PerformanceMetricDisplay
                label="$/Multi-Thread Mark"
                baseValue={baseMultiThreadMark}
                adjustedValue={adjustedMultiThreadMark}
                showColorCoding
                listPrice={listing.price_usd}
                adjustedPrice={listing.adjusted_price_usd}
                cpuMark={listing.cpu?.cpu_mark_multi}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Other sections... */}
    </div>
  );
}
```

**Testing Requirements:**
- [ ] E2E test: Metrics display correctly
- [ ] E2E test: Responsive layout on mobile
- [ ] Visual test: Pairing is clear and readable

---

### Phase 4: Image Management System

**Objectives:**
- Create JSON configuration for image mappings
- Implement image resolver utility
- Refactor ProductImageDisplay to use config
- Migrate existing images to new structure
- Document workflow for non-technical users

**Prerequisites:**
- None (independent phase)

**Estimated Duration:** 2 weeks

---

#### IMG-001: Design and Create Image Configuration File

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] JSON schema defined
- [ ] TypeScript types generated
- [ ] Configuration file created with existing images
- [ ] Validation logic implemented

**Implementation Steps:**

1. **Create config file** (`apps/web/config/product-images.json`):

```json
{
  "version": "1.0",
  "baseUrl": "/images",
  "manufacturers": {
    "hpe": {
      "logo": "/manufacturers/hpe.svg",
      "fallback": "generic"
    },
    "minisforum": {
      "logo": "/manufacturers/minisforum.svg",
      "series": {
        "elitemini": "/manufacturers/minisforum/elitemini.svg"
      },
      "fallback": "generic"
    }
  },
  "formFactors": {
    "mini_pc": {
      "icon": "/form-factors/mini-pc.svg",
      "generic": "/form-factors/mini-pc-generic.svg"
    },
    "desktop": {
      "icon": "/form-factors/desktop.svg"
    }
  },
  "cpuVendors": {
    "intel": "/cpu-vendors/intel.svg",
    "amd": "/cpu-vendors/amd.svg"
  },
  "fallbacks": {
    "generic": "/fallbacks/generic-pc.svg"
  }
}
```

2. **Generate TypeScript types:**

```typescript
// apps/web/types/product-images.ts

export interface ImageConfig {
  version: string;
  baseUrl: string;
  manufacturers: Record<string, ManufacturerImages>;
  formFactors: Record<string, FormFactorImages>;
  cpuVendors: Record<string, string>;
  fallbacks: {
    generic: string;
  };
}

export interface ManufacturerImages {
  logo: string;
  series?: Record<string, string>;
  fallback?: string;
}

export interface FormFactorImages {
  icon: string;
  generic?: string;
}
```

3. **Add validation:**

```typescript
// apps/web/lib/validate-image-config.ts

import { z } from 'zod';

const ImageConfigSchema = z.object({
  version: z.string(),
  baseUrl: z.string(),
  manufacturers: z.record(z.object({
    logo: z.string(),
    series: z.record(z.string()).optional(),
    fallback: z.string().optional(),
  })),
  formFactors: z.record(z.object({
    icon: z.string(),
    generic: z.string().optional(),
  })),
  cpuVendors: z.record(z.string()),
  fallbacks: z.object({
    generic: z.string(),
  }),
});

export function validateImageConfig(config: unknown) {
  return ImageConfigSchema.parse(config);
}
```

**Testing Requirements:**
- [ ] Unit test: Config validation passes
- [ ] Unit test: Invalid config throws error

---

#### IMG-002: Implement Image Resolver Utility

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 8 hours
**Dependencies:** IMG-001

**Acceptance Criteria:**
- [ ] Resolver follows 7-level fallback hierarchy
- [ ] Returns correct image for all scenarios
- [ ] Handles missing config entries gracefully
- [ ] Performance: <1ms per resolution

**Implementation Steps:**

1. **Create resolver** (`apps/web/lib/image-resolver.ts`):

```typescript
import imageConfig from '@/config/product-images.json';
import type { ListingDetail, ListingRecord } from '@/types/listings';

export function resolveProductImage(
  listing: ListingDetail | ListingRecord
): string {
  // 1. Listing-specific URLs
  if (listing.thumbnail_url) {
    return listing.thumbnail_url;
  }
  if (listing.image_url) {
    return listing.image_url;
  }

  const manufacturer = listing.manufacturer?.toLowerCase();
  const series = listing.series?.toLowerCase().replace(/\s+/g, '_');
  const modelNumber = listing.model_number?.toLowerCase().replace(/\s+/g, '_');
  const formFactor = listing.form_factor?.toLowerCase().replace(/\s+/g, '_');
  const cpuVendor = listing.cpu?.manufacturer?.toLowerCase();

  // 2. Model-specific image
  if (manufacturer && modelNumber && imageConfig.manufacturers[manufacturer]?.series?.[modelNumber]) {
    return `${imageConfig.baseUrl}${imageConfig.manufacturers[manufacturer].series[modelNumber]}`;
  }

  // 3. Series-specific image
  if (manufacturer && series && imageConfig.manufacturers[manufacturer]?.series?.[series]) {
    return `${imageConfig.baseUrl}${imageConfig.manufacturers[manufacturer].series[series]}`;
  }

  // 4. Manufacturer logo
  if (manufacturer && imageConfig.manufacturers[manufacturer]?.logo) {
    return `${imageConfig.baseUrl}${imageConfig.manufacturers[manufacturer].logo}`;
  }

  // 5. CPU vendor logo
  if (cpuVendor && imageConfig.cpuVendors[cpuVendor]) {
    return `${imageConfig.baseUrl}${imageConfig.cpuVendors[cpuVendor]}`;
  }

  // 6. Form factor icon
  if (formFactor && imageConfig.formFactors[formFactor]?.icon) {
    return `${imageConfig.baseUrl}${imageConfig.formFactors[formFactor].icon}`;
  }

  // 7. Generic fallback
  return `${imageConfig.baseUrl}${imageConfig.fallbacks.generic}`;
}

// Helper: Get fallback type for debugging
export function getImageSource(listing: ListingDetail | ListingRecord): string {
  if (listing.thumbnail_url) return 'thumbnail';
  if (listing.image_url) return 'image_url';

  const manufacturer = listing.manufacturer?.toLowerCase();
  const series = listing.series?.toLowerCase().replace(/\s+/g, '_');

  if (manufacturer && series && imageConfig.manufacturers[manufacturer]?.series?.[series]) {
    return 'series';
  }
  if (manufacturer && imageConfig.manufacturers[manufacturer]?.logo) {
    return 'manufacturer';
  }
  if (listing.cpu?.manufacturer && imageConfig.cpuVendors[listing.cpu.manufacturer.toLowerCase()]) {
    return 'cpu_vendor';
  }
  if (listing.form_factor && imageConfig.formFactors[listing.form_factor.toLowerCase()]) {
    return 'form_factor';
  }

  return 'generic';
}
```

**Testing Requirements:**
- [ ] Unit test: All 7 fallback levels
- [ ] Unit test: Handles missing fields gracefully
- [ ] Performance test: <1ms resolution time

---

#### IMG-003: Refactor ProductImageDisplay Component

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 12 hours
**Dependencies:** IMG-002

**Acceptance Criteria:**
- [ ] Uses image resolver for all image sources
- [ ] Maintains backward compatibility
- [ ] Supports all existing variants (card, hero, thumbnail)
- [ ] Error handling unchanged

**Implementation Steps:**

1. **Update component** (`apps/web/components/listings/product-image-display.tsx`):

```typescript
import { resolveProductImage, getImageSource } from '@/lib/image-resolver';
import { useState } from 'react';
import Image from 'next/image';
import { Dialog, DialogContent } from '@/components/ui/dialog';

interface ProductImageDisplayProps {
  listing: ListingDetail | ListingRecord;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'card' | 'hero' | 'thumbnail';
  showLightbox?: boolean;
  className?: string;
}

const SIZE_MAP = {
  sm: { width: 64, height: 64 },
  md: { width: 128, height: 128 },
  lg: { width: 256, height: 256 },
  xl: { width: 512, height: 512 },
};

export function ProductImageDisplay({
  listing,
  size = 'md',
  variant = 'card',
  showLightbox = false,
  className,
}: ProductImageDisplayProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [imgError, setImgError] = useState(false);

  const imageSrc = resolveProductImage(listing);
  const imageSource = getImageSource(listing);
  const dimensions = SIZE_MAP[size];

  // Use padding for fallback images (logos, icons)
  const isFallback = !['thumbnail', 'image_url'].includes(imageSource);
  const padding = isFallback ? 'p-8' : 'p-2';

  const handleImageClick = () => {
    if (showLightbox) {
      setLightboxOpen(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showLightbox && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      setLightboxOpen(true);
    }
  };

  return (
    <>
      <div
        className={cn(
          'relative overflow-hidden rounded-lg border bg-muted',
          padding,
          showLightbox && 'cursor-pointer hover:opacity-80 transition',
          className
        )}
        onClick={handleImageClick}
        onKeyDown={handleKeyDown}
        role={showLightbox ? 'button' : undefined}
        tabIndex={showLightbox ? 0 : undefined}
        aria-label={showLightbox ? 'View full-size image' : undefined}
      >
        <Image
          src={imageSrc}
          alt={listing.title || 'Product image'}
          width={dimensions.width}
          height={dimensions.height}
          className="object-contain"
          loading="lazy"
          quality={85}
          onError={() => setImgError(true)}
        />
      </div>

      {showLightbox && (
        <Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
          <DialogContent className="max-w-4xl">
            <Image
              src={imageSrc}
              alt={listing.title || 'Product image'}
              width={1024}
              height={1024}
              className="object-contain"
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
```

**Testing Requirements:**
- [ ] E2E test: All variants render correctly
- [ ] E2E test: Lightbox works
- [ ] Visual regression test: No UI changes

---

#### IMG-004: Reorganize Image Directory Structure

**Type:** Infra
**Priority:** P1-High
**Effort:** 4 hours
**Dependencies:** IMG-001

**Acceptance Criteria:**
- [ ] Images organized by category
- [ ] Existing images migrated
- [ ] README files in each directory
- [ ] No broken images

**Implementation Steps:**

1. **Create new directory structure:**

```bash
cd apps/web/public/images

mkdir -p manufacturers cpu-vendors form-factors fallbacks

# Move existing files
mv hpe.svg manufacturers/
mv intel.svg cpu-vendors/
mv amd.svg cpu-vendors/
mv mini-pc-icon.svg form-factors/
mv desktop-icon.svg form-factors/
mv generic-pc.svg fallbacks/
```

2. **Create README files:**

```markdown
# Manufacturers

Add manufacturer logos here as SVG files.

Naming convention: `<manufacturer-slug>.svg`
Examples:
- `hpe.svg`
- `dell.svg`
- `minisforum.svg`

## Adding a New Manufacturer Logo

1. Obtain SVG logo (512x512px recommended)
2. Save as `<manufacturer-name>.svg` (lowercase, kebab-case)
3. Add entry to `/apps/web/config/product-images.json`:

```json
"manufacturers": {
  "manufacturer-name": {
    "logo": "/manufacturers/manufacturer-name.svg"
  }
}
```

4. Commit changes (no deployment needed!)
```

3. **Update image config to match new paths**

**Testing Requirements:**
- [ ] Manual test: All images load correctly
- [ ] E2E test: Catalog cards show images

---

#### IMG-005: Documentation for Non-Technical Users

**Type:** Documentation
**Priority:** P2-Medium
**Effort:** 4 hours
**Dependencies:** IMG-004

**Acceptance Criteria:**
- [ ] Step-by-step guide for adding images
- [ ] Screenshots included
- [ ] Video tutorial (optional)
- [ ] Troubleshooting section

**Implementation Steps:**

1. **Create user guide** (`docs/guides/adding-product-images.md`):

```markdown
# Adding Product Images - User Guide

This guide explains how to add manufacturer logos, form factor icons, and series images to the Deal Brain catalog without needing to modify code or deploy.

## Prerequisites

- Access to the `/apps/web/public/images/` directory (file manager, FTP, or Git)
- SVG or PNG image file (512x512px recommended, max 200KB)
- Basic text editing skills

## Step 1: Prepare Your Image

1. Obtain the manufacturer logo or product image
2. Ensure it's in SVG format (preferred) or PNG
3. Resize to 512x512px for best quality
4. Optimize file size (max 200KB)
5. Name using lowercase kebab-case (e.g., `minisforum.svg`)

## Step 2: Upload Image

### Option A: File Manager

1. Navigate to `/apps/web/public/images/manufacturers/`
2. Upload your image file (e.g., `minisforum.svg`)
3. Verify file uploaded successfully

### Option B: Git

```bash
cd apps/web/public/images/manufacturers
cp ~/Downloads/minisforum.svg .
git add minisforum.svg
git commit -m "Add Minisforum manufacturer logo"
git push
```

## Step 3: Update Configuration

1. Open `/apps/web/config/product-images.json` in a text editor
2. Add an entry under `manufacturers`:

```json
{
  "manufacturers": {
    "minisforum": {
      "logo": "/manufacturers/minisforum.svg"
    }
  }
}
```

3. Save the file

## Step 4: Verify

1. Refresh the listings page
2. Find a listing with manufacturer "Minisforum"
3. Verify the logo appears in the catalog card

## Adding Series Images

For series-specific images (e.g., Dell OptiPlex):

1. Upload image to `/manufacturers/<manufacturer>/` (e.g., `/manufacturers/dell/optiplex.svg`)
2. Update config:

```json
{
  "manufacturers": {
    "dell": {
      "logo": "/manufacturers/dell.svg",
      "series": {
        "optiplex": "/manufacturers/dell/optiplex.svg"
      }
    }
  }
}
```

## Troubleshooting

**Image doesn't appear:**
- Check file path in config matches uploaded file location
- Verify file name is lowercase with no spaces
- Clear browser cache (Ctrl+Shift+R)

**Image is blurry:**
- Use SVG format instead of PNG
- Ensure minimum 512x512px resolution

**File too large:**
- Optimize SVG using https://jakearchibald.github.io/svgomg/
- Compress PNG using TinyPNG

## Support

For help, contact the engineering team or file an issue.
```

2. **Create video tutorial (optional):**
   - Record screen capture showing steps
   - Upload to internal documentation site

**Testing Requirements:**
- [ ] User testing: Non-technical user successfully adds image

---

## Database Migrations

### Migration 1: Add CPU Mark Thresholds

**File:** `apps/api/alembic/versions/xxx_add_cpu_mark_thresholds.py`

**Changes:**
- Add `cpu_mark_thresholds` setting to `application_settings` table

**Rollback:**
- Delete setting from `application_settings`

---

## API Changes

### New Endpoints

#### `GET /v1/listings/paginated`

**Description:** Cursor-based pagination for large datasets

**Query Parameters:**
- `limit` (int, default: 50, max: 500)
- `cursor` (string, optional)
- `sort_by` (string, default: "updated_at")
- `sort_order` (string, default: "desc")
- `form_factor` (string, optional)
- `manufacturer` (string, optional)
- `min_price` (float, optional)
- `max_price` (float, optional)

**Response:**
```json
{
  "items": [/* ListingRead objects */],
  "total": 1234,
  "limit": 50,
  "next_cursor": "eyJpZCI6MTIzLCJzb3J0X3ZhbHVlIjoiMjAyNS0xMC0zMSJ9",
  "has_next": true
}
```

---

#### `GET /v1/settings/cpu_mark_thresholds`

**Description:** Get CPU Mark color-coding thresholds

**Response:**
```json
{
  "excellent": 20.0,
  "good": 10.0,
  "fair": 5.0,
  "neutral": 0.0,
  "poor": -10.0,
  "premium": -20.0
}
```

---

## Frontend Component Changes

### New Components

1. **ValuationTooltip** (`apps/web/components/listings/valuation-tooltip.tsx`)
   - Displays adjusted value calculation summary
   - Shows top rules by impact
   - Links to full breakdown modal

2. **PerformanceMetricDisplay** (`apps/web/components/listings/performance-metric-display.tsx`)
   - Displays CPU performance metrics
   - Shows base and adjusted values
   - Color-coded based on improvement

### Modified Components

1. **ListingsTable** (`apps/web/components/listings/listings-table.tsx`)
   - Add row virtualization
   - Update column header to "Adjusted Value"

2. **DetailPageLayout** (`apps/web/components/listings/detail-page-layout.tsx`)
   - Rename "Adjusted Price" to "Adjusted Value"
   - Add ValuationTooltip

3. **SpecificationsTab** (`apps/web/components/listings/specifications-tab.tsx`)
   - Pair CPU metrics (Score next to $/Mark)
   - Use PerformanceMetricDisplay component

4. **ProductImageDisplay** (`apps/web/components/listings/product-image-display.tsx`)
   - Use image resolver utility
   - Remove hardcoded fallback logic

---

## Configuration Changes

### New Configuration Files

1. **`apps/web/config/product-images.json`**
   - Image mappings for manufacturers, series, form factors, CPU vendors
   - Fallback hierarchy configuration

### Environment Variables

No new environment variables required.

### Feature Flags

Add to application settings (optional):

- `ENABLE_VIRTUALIZATION` (default: true)
- `ENABLE_IMAGE_CONFIG` (default: true)
- `ENABLE_CPU_MARK_COLORING` (default: true)

---

## Testing Strategy

### Unit Test Coverage Targets

- **Backend:** 80% coverage
  - Settings service methods
  - Pagination logic
  - Cursor encoding/decoding

- **Frontend:** 75% coverage
  - Component rendering
  - Image resolver logic
  - Threshold calculations

### Integration Test Scenarios

1. **Pagination:**
   - Fetch first page
   - Fetch subsequent pages using cursor
   - Verify total count accuracy

2. **Settings:**
   - Fetch CPU mark thresholds
   - Verify default values when not set

3. **Image Resolution:**
   - Test all 7 fallback levels
   - Verify correct image returned

### E2E Test Scenarios

1. **Data Tab Performance:**
   - Load 1,000 listings
   - Sort column
   - Filter by manufacturer
   - Measure interaction latency (<200ms)

2. **Tooltips:**
   - Hover over "Adjusted Value"
   - Verify tooltip appears
   - Click "View Full Breakdown"
   - Verify modal opens

3. **CPU Metrics:**
   - Navigate to detail page
   - Verify metrics paired
   - Verify color coding applied
   - Hover over adjusted value
   - Verify tooltip appears

4. **Image Display:**
   - Verify manufacturer logo appears
   - Verify fallback to CPU vendor logo
   - Verify fallback to generic image

### Performance Test Benchmarks

| Metric | Target | Test Method |
|--------|--------|-------------|
| Data tab load (1,000 rows) | <300ms | React Profiler |
| Interaction latency (sort) | <150ms | Performance.measure |
| Scroll FPS (virtualized) | 60fps | Chrome DevTools |
| Image resolution time | <1ms | Unit test |

### Accessibility Test Checklist

- [ ] All tooltips keyboard accessible
- [ ] Screen reader announces tooltip content
- [ ] Color contrast ratios meet WCAG AA (4.5:1)
- [ ] Focus indicators visible
- [ ] Tab order logical
- [ ] ARIA labels present

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Performance benchmarks met
- [ ] Accessibility audit passed
- [ ] Database migrations tested in staging
- [ ] Rollback plan validated
- [ ] Monitoring dashboards updated
- [ ] Documentation complete

### Deployment Steps

1. **Backend Deployment:**
   ```bash
   # Run migrations
   poetry run alembic upgrade head

   # Deploy API
   make deploy-api

   # Verify health check
   curl https://api.dealbrain.com/health
   ```

2. **Frontend Deployment:**
   ```bash
   # Build with new changes
   cd apps/web
   pnpm build

   # Deploy to production
   make deploy-web

   # Verify deployment
   curl https://dealbrain.com
   ```

3. **Verify Deployment:**
   - Check /listings page loads
   - Verify "Adjusted Value" terminology
   - Test tooltip functionality
   - Verify CPU metrics layout
   - Check image display

### Feature Flag Rollout

**Phase 1: Internal Testing (Day 1-2)**
- Enable all features for internal users
- Monitor error rates and performance
- Gather feedback

**Phase 2: Beta Users (Day 3-5)**
- Enable for 10% of users
- Monitor engagement metrics
- Collect user feedback

**Phase 3: Full Rollout (Day 6-7)**
- Enable for 50% of users
- Monitor metrics
- Address any issues

**Phase 4: 100% Rollout (Day 8+)**
- Enable for all users
- Remove feature flags (code cleanup)

### Monitoring & Alerting

**Metrics to Monitor:**
- Data tab load time (P95)
- Interaction latency (P95)
- Image load failures
- Tooltip engagement rate
- Error rates

**Alerts:**
- P95 latency > 300ms → Warning
- P95 latency > 500ms → Critical
- Error rate > 1% → Warning
- Error rate > 5% → Critical
- Image load failure rate > 5% → Warning

### Rollback Procedures

**Emergency Rollback (if critical issues):**
1. Flip feature flags to disable new features
2. Redeploy previous version
3. Verify issues resolved
4. Investigate root cause

**Database Rollback:**
```bash
# Rollback migration
poetry run alembic downgrade -1

# Verify rollback
poetry run alembic current
```

**Frontend Rollback:**
```bash
# Revert to previous commit
git revert <commit-hash>

# Rebuild and deploy
pnpm build
make deploy-web
```

---

## Timeline & Resource Allocation

### Gantt Chart (Text-Based)

```
Week 1:
  Mon  ████ PERF-001, PERF-002 (Frontend)
  Tue  ████ PERF-002 (continued)
  Wed  ████ PERF-003 (Backend), PERF-002 (Frontend)
  Thu  ████ PERF-004 (Frontend)
  Fri  ████ PERF-005, Testing

Week 2:
  Mon  ████ UX-001, UX-002 (Frontend)
  Tue  ████ UX-002 (continued), UX-003
  Wed  ████ METRICS-001 (Backend), METRICS-002 (Frontend)
  Thu  ████ METRICS-002 (continued)
  Fri  ████ METRICS-003, Testing

Week 3:
  Mon  ████ IMG-001, IMG-002 (Frontend)
  Tue  ████ IMG-003 (Frontend)
  Wed  ████ IMG-003 (continued), IMG-004 (Infra)
  Thu  ████ IMG-005 (Documentation)
  Fri  ████ Integration Testing

Week 4:
  Mon  ████ Performance Testing, Bug Fixes
  Tue  ████ Accessibility Audit
  Wed  ████ Security Review
  Thu  ████ Staging Deployment
  Fri  ████ Production Deployment

Week 5-6:
  Mon-Fri  ████ Monitoring, Iteration, Documentation
```

### Resource Allocation

| Week | Backend (hours) | Frontend (hours) | QA (hours) | Total |
|------|-----------------|------------------|------------|-------|
| 1 | 8 | 32 | 8 | 48 |
| 2 | 8 | 24 | 8 | 40 |
| 3 | 4 | 28 | 12 | 44 |
| 4 | 0 | 16 | 16 | 32 |
| 5-6 | 8 | 12 | 12 | 32 |
| **Total** | **28h** | **112h** | **56h** | **196h** |

### Critical Path

```
PERF-001 → PERF-002 → PERF-004 → Testing → Deployment
             ↓
           PERF-003

UX-002 → METRICS-002 → METRICS-003 → Testing
  ↓
UX-003

IMG-001 → IMG-002 → IMG-003 → IMG-004 → Testing
```

**Critical tasks:** PERF-002, UX-002, METRICS-002, IMG-003

**Buffer:** 20% buffer (5 days) included for unforeseen issues

---

## Risk Management

### Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Virtualization breaks row selection | Medium | High | Thorough testing, feature flag, fallback mode | Frontend Lead |
| Performance degradation on mobile | Medium | High | Test on low-end devices, monitor RUM metrics | Frontend Lead |
| Image config file grows too large | Low | Medium | Set file size limits, lazy loading, code-splitting | Frontend Lead |
| Backend pagination slower than expected | Low | High | Index frequently sorted columns, optimize queries | Backend Lead |
| Tooltip engagement lower than expected | Medium | Low | A/B test designs, add onboarding tour | Product Owner |
| Users struggle with image uploads | Low | Medium | Detailed documentation, video tutorial, onboarding | Content Manager |

### Dependency Risks

**External Dependencies:**
- `@tanstack/react-virtual` library stability → **Low risk** (stable, widely used)
- Next.js Image component compatibility → **Low risk** (core Next.js feature)

**Internal Dependencies:**
- Completion of UX-002 before METRICS-002 → **Medium risk** (sequential work)
  - **Mitigation:** Start UX-002 early, allocate dedicated frontend resource

### Technical Debt Considerations

**Introduced Debt:**
- Image config file may need database migration if it grows beyond 100KB
- Virtualization adds complexity to table component

**Addressed Debt:**
- Removes hardcoded image fallback logic
- Centralizes threshold configuration
- Improves render performance

### Contingency Plans

**If virtualization performance insufficient:**
- Implement server-side pagination as primary solution
- Use virtualization only for pagination result sets
- Reduce page size to 25 rows

**If tooltip engagement low:**
- Add onboarding tour highlighting tooltips
- Experiment with different trigger mechanisms (click vs. hover)
- A/B test tooltip designs

**If image config becomes unwieldy:**
- Migrate to database-backed configuration
- Implement UI for managing images (admin panel)
- Add image upload directly in UI

---

## Quality Assurance

### Code Review Checklist

**Backend:**
- [ ] Migrations are reversible
- [ ] API endpoints have proper error handling
- [ ] Query performance tested with 1,000+ rows
- [ ] Type hints present
- [ ] Docstrings for public methods

**Frontend:**
- [ ] Components are memoized where appropriate
- [ ] Accessibility attributes present (ARIA labels)
- [ ] TypeScript types defined
- [ ] Error boundaries in place
- [ ] Performance optimizations applied

### Performance Benchmarking Plan

**Tools:**
- React Profiler for component render time
- Chrome DevTools Performance tab for interaction latency
- Lighthouse for overall page performance
- Custom instrumentation for API response time

**Benchmarks:**
1. **Baseline (before changes):**
   - Data tab load time with 500 listings
   - Interaction latency for sort/filter
   - Image load time

2. **Target (after changes):**
   - 50% reduction in load time
   - <200ms interaction latency
   - <500ms image load time

3. **Regression prevention:**
   - Automated performance tests in CI/CD
   - Fail build if performance degrades >10%

### Accessibility Audit Plan

**Manual Testing:**
- [ ] Keyboard-only navigation
- [ ] Screen reader testing (NVDA, JAWS)
- [ ] Color contrast verification
- [ ] Focus management

**Automated Testing:**
- [ ] jest-axe tests for all components
- [ ] Lighthouse accessibility score >90
- [ ] Wave browser extension audit

**Compliance:**
- WCAG 2.1 Level AA compliance required

### Security Review Checklist

**Backend:**
- [ ] Input validation on all API parameters
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting on paginated endpoints
- [ ] Authorization checks

**Frontend:**
- [ ] XSS prevention (React auto-escaping)
- [ ] CSP headers for external images
- [ ] No sensitive data in client-side config
- [ ] Image URL validation (same-origin or trusted domains)

---

## Documentation Requirements

### User-Facing Documentation

1. **Release Notes:**
   - Performance improvements
   - New tooltip feature
   - Adjusted value terminology change
   - Enhanced CPU metrics display

2. **User Guide Updates:**
   - How to use tooltips
   - Understanding CPU performance metrics
   - Color-coding explanation

3. **Image Management Guide:**
   - Adding manufacturer logos
   - Troubleshooting image issues

### Developer Documentation

1. **Architecture Documentation:**
   - Update `architecture.md` with virtualization approach
   - Document image resolution system
   - Explain threshold configuration

2. **Component Documentation:**
   - JSDoc for all new components
   - Storybook stories (optional)
   - Usage examples

3. **API Documentation:**
   - Update OpenAPI spec with new endpoints
   - Document pagination cursor format
   - Add examples

### Deployment Runbooks

1. **Migration Runbook:**
   - Pre-migration checklist
   - Migration commands
   - Rollback procedure
   - Verification steps

2. **Deployment Runbook:**
   - Pre-deployment checklist
   - Deployment commands
   - Health check procedures
   - Rollback steps

3. **Monitoring Runbook:**
   - Metrics to monitor
   - Alert thresholds
   - Incident response procedures

---

## Appendix

### Task Dependencies Graph

```
PERF-001 (Install React Virtual)
    ↓
PERF-002 (Implement Virtualization) ──┐
    ↓                                  │
PERF-004 (Optimize Rendering) ────────┼─→ Phase 1 Testing
    ↓                                  │
PERF-005 (Add Monitoring) ────────────┘

PERF-003 (Backend Pagination) → Phase 1 Testing

UX-001 (Find-Replace) ──┐
    ↓                    │
UX-002 (Tooltip Component) ──┼─→ Phase 2 Testing
    ↓                    │
UX-003 (Integrate Tooltip) ──┘

METRICS-001 (Thresholds Setting) ──┐
    ↓                               │
METRICS-002 (Metric Component) ────┼─→ Phase 3 Testing
    ↓                               │
METRICS-003 (Update Layout) ───────┘

IMG-001 (Config File) ──┐
    ↓                    │
IMG-002 (Image Resolver) ──┼─→ Phase 4 Testing
    ↓                    │
IMG-003 (Refactor Component) ──┼
    ↓                    │
IMG-004 (Reorganize Images) ───┼
    ↓                    │
IMG-005 (Documentation) ───────┘
```

### Estimated Effort Breakdown

```
Phase 1: Performance (72h)
├─ PERF-001: 4h
├─ PERF-002: 16h
├─ PERF-003: 8h
├─ PERF-004: 12h
├─ PERF-005: 8h
└─ Testing: 16h

Phase 2: Adjusted Value (28h)
├─ UX-001: 4h
├─ UX-002: 8h
├─ UX-003: 4h
└─ Testing: 8h

Phase 3: CPU Metrics (44h)
├─ METRICS-001: 4h
├─ METRICS-002: 12h
├─ METRICS-003: 8h
└─ Testing: 12h

Phase 4: Images (52h)
├─ IMG-001: 4h
├─ IMG-002: 8h
├─ IMG-003: 12h
├─ IMG-004: 4h
├─ IMG-005: 4h
└─ Testing: 12h
```

---

**End of Implementation Plan**
