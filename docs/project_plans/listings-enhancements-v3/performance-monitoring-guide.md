# Performance Monitoring Guide (PERF-005)

## Overview

Lightweight performance instrumentation for validating Phase 1 optimization targets. This implementation provides dev-mode only monitoring with zero production overhead.

## Architecture (ADR-004)

### Design Principles
- **Lightweight**: No external dependencies, native browser APIs only
- **Dev-mode only**: All instrumentation disabled in production (zero overhead)
- **Console warnings**: Alert developers to slow operations (>200ms)
- **React Profiler**: Track component render performance (>50ms threshold)
- **Performance API**: Use browser Performance API for marks and measures

### Performance Thresholds
- **Interaction Latency**: 200ms (warning threshold)
- **Component Render**: 50ms (warning threshold)
- **API Response**: 200ms (warning threshold)

## Implementation

### 1. Performance Utility Library

**Location**: `/apps/web/lib/performance.ts`

**Key Functions**:

#### `measureInteraction(name, fn)`
Measures synchronous user interactions with automatic threshold checking.

```typescript
const handleSort = useCallback((columnId: string) => {
  measureInteraction('column_sort', () => {
    table.setSorting([{ id: columnId, desc: !sorting[0]?.desc }]);
  });
}, [table, sorting]);
```

#### `measureInteractionAsync(name, fn)`
Measures asynchronous operations (API calls, async state updates).

```typescript
const handleBulkSubmit = useCallback(async () => {
  await measureInteractionAsync('bulk_edit_submit', async () => {
    await apiFetch('/v1/listings/bulk-update', { method: 'POST', body: payload });
    queryClient.invalidateQueries({ queryKey: ['listings', 'records'] });
  });
}, []);
```

#### `logRenderPerformance()`
React Profiler callback for logging slow component renders.

```typescript
<Profiler id="ListingsTable" onRender={logRenderPerformance}>
  <ListingsTable />
</Profiler>
```

#### `startMeasure(name)` / `finishMeasure()`
For multi-step operations or complex instrumentation.

```typescript
const finishMeasure = startMeasure('complex_operation');
// ... perform operation
finishMeasure();
```

### 2. ListingsTable Integration

**Location**: `/apps/web/components/listings/listings-table.tsx`

**Instrumented Interactions**:

1. **Column Sorting** (`column_sort`)
   - Wrapped in `measureInteraction()`
   - Triggered via `onSortingChange` handler

2. **Column Filtering** (`column_filter`)
   - Wrapped in `measureInteraction()`
   - Triggered via `onColumnFiltersChange` handler

3. **Quick Search** (`quick_search`)
   - Debounced at 200ms using `useDebouncedCallback`
   - Wrapped in `measureInteraction()`
   - Tracks search execution time after debounce

4. **Inline Cell Save** (`inline_cell_save`)
   - Wrapped in `measureInteraction()`
   - Measures mutation preparation time

5. **Bulk Edit Submit** (`bulk_edit_submit`)
   - Wrapped in `measureInteractionAsync()`
   - Measures entire async operation including API call

**React Profiler**:
- Entire component wrapped in `<Profiler id="ListingsTable">`
- Logs renders exceeding 50ms threshold
- Distinguishes between mount, update, and nested-update phases

## Usage Examples

### Monitoring a New Interaction

```typescript
// 1. Import the utility
import { measureInteraction } from '@/lib/performance';

// 2. Wrap your handler
const handleAction = useCallback(() => {
  measureInteraction('my_action', () => {
    // Your action logic here
    performExpensiveOperation();
  });
}, []);
```

### Monitoring Async Operations

```typescript
import { measureInteractionAsync } from '@/lib/performance';

const handleAsyncAction = useCallback(async () => {
  await measureInteractionAsync('my_async_action', async () => {
    const result = await fetchData();
    await processData(result);
  });
}, []);
```

### Adding Profiler to a Component

```typescript
import { Profiler } from 'react';
import { logRenderPerformance } from '@/lib/performance';

function MyComponent() {
  return (
    <Profiler id="MyComponent" onRender={logRenderPerformance}>
      {/* Component content */}
    </Profiler>
  );
}
```

## Verification

### Dev Mode Console Output

When running in development mode (`NODE_ENV=development`), you'll see:

```
⚠️ Slow interaction: column_sort took 245.32ms (threshold: 200ms)
⚠️ Slow render: ListingsTable (update) took 67.45ms (threshold: 50ms)
⚠️ Slow async interaction: bulk_edit_submit took 512.78ms (threshold: 200ms)
```

### DevTools Performance Tab

1. Open Chrome DevTools > Performance tab
2. Click "Record"
3. Perform interactions in the app
4. Click "Stop"
5. Look for user timing marks:
   - `interaction_column_sort`
   - `interaction_quick_search`
   - `operation_bulk_edit_submit`

### Production Build Verification

Run a production build to verify zero overhead:

```bash
# Build for production
pnpm --filter @dealbrain/web build

# Verify no performance logging in bundle
grep -r "measureInteraction\|logRenderPerformance" .next/static/chunks/
# Should return nothing or only minified/dead code
```

## Performance Targets (Phase 1)

| Metric | Target | Instrumentation |
|--------|--------|-----------------|
| Column Sort | <200ms | `column_sort` |
| Column Filter | <200ms | `column_filter` |
| Quick Search | <200ms | `quick_search` |
| Inline Cell Save | <200ms | `inline_cell_save` |
| Bulk Edit Submit | <200ms (UI) | `bulk_edit_submit` |
| Component Render | <50ms | React Profiler |

## Troubleshooting

### Console Warnings Not Appearing

**Check**:
1. Running in dev mode: `NODE_ENV=development`
2. Browser console is open and warnings are not filtered
3. Interaction actually triggered (check with debugger)

### Performance Marks Not in DevTools

**Check**:
1. DevTools Performance tab is recording
2. "User Timing" track is enabled in settings
3. Interaction occurred during recording period

### False Positives (Warnings in Fast Operations)

**Potential Causes**:
1. Browser busy with other tasks (background tabs, extensions)
2. CPU throttling in DevTools (disable for accurate measurements)
3. First render includes data fetching (expected to be slow)

## Best Practices

### Do's
- ✅ Wrap user interactions that should be <200ms
- ✅ Use `measureInteractionAsync` for async operations
- ✅ Add Profiler to complex components (>100 LOC)
- ✅ Use descriptive names for measurements
- ✅ Check DevTools Performance tab for detailed analysis

### Don'ts
- ❌ Don't instrument trivial operations (simple state updates)
- ❌ Don't use in tight loops (overhead adds up)
- ❌ Don't add instrumentation in production code paths
- ❌ Don't rely on console warnings for automated testing
- ❌ Don't forget to clean up Performance marks in long-running apps

## Future Enhancements

### Phase 2 Considerations
- **Real User Monitoring (RUM)**: Send performance metrics to backend
- **Performance Budgets**: Fail CI if interactions exceed thresholds
- **Automated Performance Tests**: E2E tests with performance assertions
- **Web Vitals Integration**: Track LCP, FID, CLS, INP
- **Custom Metrics Dashboard**: Visualize performance trends over time

## Related Documentation

- **ADR-004**: Performance Monitoring Architecture Decision Record
- **PERF-001**: React Virtual implementation guide
- **Phase 1 Progress**: `/docs/project_plans/listings-enhancements-v3/progress/phase-1-progress.md`

## Files Modified

### Created
- `/apps/web/lib/performance.ts` - Performance utility library
- `/apps/web/components/listings/__tests__/performance-verification.tsx` - Verification demo
- `/docs/project_plans/listings-enhancements-v3/performance-monitoring-guide.md` - This guide

### Modified
- `/apps/web/components/listings/listings-table.tsx` - Added instrumentation and Profiler
  - Imported `measureInteraction`, `measureInteractionAsync`, `logRenderPerformance`
  - Imported `useDebouncedCallback` from `use-debounce`
  - Added `quickSearchInput` state for debounced search
  - Wrapped sorting/filtering handlers with `measureInteraction()`
  - Wrapped bulk submit with `measureInteractionAsync()`
  - Added debounced search with performance tracking
  - Wrapped component in `<Profiler>` with `logRenderPerformance`

## Success Criteria

- [x] Performance utility created (`lib/performance.ts`)
- [x] React Profiler integrated (ListingsTable wrapped)
- [x] Key interactions instrumented:
  - [x] Column sorting
  - [x] Column filtering
  - [x] Quick search (debounced)
  - [x] Bulk edit submission
  - [x] Inline cell save
- [x] Dev-mode only (verified with TypeScript)
- [x] Console warnings for slow ops (>200ms threshold)
- [x] Zero production overhead (no runtime checks in prod build)

## Validation

```bash
# 1. Start dev server
make web

# 2. Open browser console
# Navigate to http://localhost:3020/dashboard/data

# 3. Perform interactions:
#    - Sort a column
#    - Filter a column
#    - Type in quick search
#    - Edit a cell inline
#    - Select rows and bulk edit

# 4. Check console for warnings (if any operations exceed thresholds)

# 5. Open DevTools Performance tab:
#    - Record performance
#    - Perform interactions
#    - Stop recording
#    - Check "User Timing" track for our measurements
```
