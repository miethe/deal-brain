# Phase 1: Data Tab Performance Optimization

**Objectives:**
- Achieve <200ms interaction latency for 1,000 listings
- Implement row virtualization for smooth 60fps scrolling
- Add backend pagination for large datasets
- Optimize React rendering performance

**Prerequisites:**
- None (independent phase)

**Estimated Duration:** 2 weeks

---

## PERF-001: Install and Configure React Virtual

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

## PERF-002: Implement Table Row Virtualization

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

## PERF-003: Add Backend Pagination Endpoint

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

## PERF-004: Optimize React Component Rendering

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

## PERF-005: Add Performance Monitoring

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

**Phase 1 Summary:**

| Task | Type | Effort | Status |
|------|------|--------|--------|
| PERF-001 | Frontend | 4h | Pending |
| PERF-002 | Frontend | 16h | Pending |
| PERF-003 | Backend | 8h | Pending |
| PERF-004 | Frontend | 12h | Pending |
| PERF-005 | Frontend | 8h | Pending |
| Testing | All | 16h | Pending |
| **Total** | | **72h** | |
