# Phase 3-4 Context: Frontend - Manual Population & Real-Time Updates

## Implementation Architecture

### Component Hierarchy

```
ImportPage (import flow coordinator)
├── BulkImportProgress (real-time status display)
│   └── StatusCard (individual count display)
│   └── PerRowStatusItem (URL status)
├── ImportNotifications (toast event listener)
└── PartialImportModal (manual data entry)
```

### Data Flow

**Phase 3: Modal Completion**:
1. API completes partial import → emits custom event `import-complete`
2. ImportPage listens for event → detects `quality === 'partial'`
3. PartialImportModal opens with listing data
4. User enters price → API `PATCH /listings/{id}/complete`
5. Modal closes → calls `onComplete()` → invalidates cache

**Phase 4: Real-Time Tracking**:
1. Bulk import initiated → receives `bulk_job_id`
2. useImportPolling hook starts polling status every 2 seconds
3. Hook detects status changes → emits callbacks + custom events
4. BulkImportProgress updates real-time display
5. ImportNotifications displays toast on key events
6. On partial detection → hook dispatches `import-partial-found` event
7. On completion → hook dispatches `import-job-complete` event
8. ImportPage listens to events → opens modal or shows completion toast

## Key Design Patterns

### Event-Driven Integration (Loose Coupling)

**Why**: Prevents tight coupling between polling hook, modal, notifications, and page.

**Pattern**:
```typescript
// useImportPolling emits events
window.dispatchEvent(new CustomEvent('import-partial-found', { detail: row }));
window.dispatchEvent(new CustomEvent('import-job-complete', { detail: status }));

// Components listen independently
window.addEventListener('import-partial-found', handlePartialFound);
window.addEventListener('import-job-complete', handleJobComplete);
```

**Advantage**: Polling, modal, notifications work independently. If notifications are removed, polling + modal still work.

### React Query Integration

**Pattern**:
```typescript
useQuery({
  queryKey: ['bulkImportStatus', bulkJobId],
  queryFn: async () => { /* fetch status */ },
  refetchInterval: enabled ? 2000 : false,  // Polling via refetch
  staleTime: 1000,   // Keep fresh
  gcTime: 60000,     // Cached for 60s after last use
});
```

**Advantage**: React Query manages polling lifecycle, prevents duplicate requests, handles cache cleanup.

### State Change Detection via Ref Tracking

**Problem**: How to detect "new partial" vs "already seen partial"?

**Solution**:
```typescript
const detectedPartialsRef = useRef<Set<number>>(new Set());

// In effect
if (current.quality === 'partial' && !detectedPartialsRef.current.has(listing_id)) {
  detectedPartialsRef.current.add(listing_id);
  onPartialFound?.(current);  // Emit only once
}
```

**Advantage**: Prevents duplicate notifications for same partial. Survives re-renders.

## Technical Decisions

### Polling Interval: 2 Seconds

**Why Not Longer?**
- User perceives lag > 2s as stale
- Could miss rapid completions
- Server load minimal with 2s interval

**Why Not Shorter?**
- UI updates too fast, distracting
- Server load increases
- Battery drain on mobile
- Diminishing returns below 2s

### Custom Events vs Callbacks

**Why Custom Events?**:
- Components don't need prop drilling
- Notifications can be enabled/disabled independently
- Modal doesn't know about notifications
- Polling hook doesn't know about UI components

**Example**:
```typescript
// Without events (tight coupling)
<ImportPage
  onPartialFound={(listing) => setModal(listing)}
  onJobComplete={(status) => showToast(status)}
  onStatusChange={(status) => updateProgress(status)}
/>

// With events (loose coupling)
<ImportPage />
<ImportNotifications bulkJobId={jobId} />
```

### Read-Only vs Editable Fields

**Design**:
- **Read-Only**: Title, CPU, RAM, Storage, Condition, GPU (extracted from source)
- **Editable**: Price (user provides, price extraction often fails)

**Why**:
- Most data extracted reliably from URLs/sources
- Price extraction prone to errors (discounts, currency conversion, seasonal prices)
- User can verify in a few seconds
- Preserves data accuracy

## API Integration Points

### Status Polling Endpoint

**Endpoint**: `GET /api/v1/ingest/bulk/{bulkJobId}/status?offset=0&limit=100`

**Response Structure**:
```json
{
  "bulk_job_id": "abc123",
  "status": "running|complete|partial|failed|queued",
  "total_urls": 100,
  "completed": 45,
  "success": 35,
  "partial": 10,
  "failed": 0,
  "running": 55,
  "queued": 0,
  "per_row_status": [
    {
      "url": "https://...",
      "status": "complete",
      "listing_id": 123,
      "quality": "full|partial",
      "error": null
    }
  ],
  "offset": 0,
  "limit": 100,
  "has_more": false
}
```

**Polling Logic**:
- Stop when `status !== 'running'`
- Stop when `completed === total_urls`
- Page large results with `offset`/`limit`

### Completion Endpoint

**Endpoint**: `PATCH /api/v1/listings/{listing_id}/complete`

**Request**:
```json
{
  "price": 299.99
}
```

**Response**:
```json
{
  "id": 123,
  "title": "Dell...",
  "price_usd": 299.99,
  "adjusted_price_usd": 279.99,
  "quality": "full",
  "valuation_breakdown": {...}
}
```

**Validation**:
- Price required, must be positive
- API validates and returns 400 if invalid
- Modal shows error message from API

## Accessibility Implementation

### ARIA Requirements

**Modal**:
- `dialog` role (Radix Dialog handles automatically)
- `aria-labelledby="dialog-title"`
- `aria-describedby="dialog-description"`
- Close button accessible

**Form**:
- Input labels via `<label htmlFor>`
- Required indicator (`*`)
- Error messages with `role="alert"`
- `aria-invalid="true"` on error
- `aria-required="true"` on required fields

**Progress**:
- `aria-label="Progress: 50%"` on progress bar
- Clear heading hierarchy (h4 for "Recent Imports")

### Keyboard Navigation

**Modal**:
- Tab cycles through inputs and buttons
- Shift+Tab reverses
- Enter submits form (if valid)
- Escape closes modal
- Auto-focus on price input

**Component Requirements**:
- All interactive elements focusable
- Focus outline visible
- No keyboard traps
- Logical tab order

## Component Testing Strategy

### Unit Tests

**Modal**:
- Render extracted data read-only
- Validate price input (required, positive)
- Validate error messages (display/clear)
- API call format
- Loading state
- Keyboard handling

**useImportPolling**:
- Polling starts/stops correctly
- Event emission on status change
- Partial detection logic
- Job completion detection
- Error handling

**BulkImportProgress**:
- Progress percentage calculation
- Status count display
- Per-row status items
- Quality badges
- Responsive grid layout

**ImportNotifications**:
- Toast triggered on partial
- Toast triggered on completion
- Event listeners attached/removed
- Auto-dismiss timing

### Integration Tests

**Phase 3**:
- Modal + API endpoint
- Modal + page event listener
- Multiple modals sequential

**Phase 4**:
- Polling + modal interaction
- Polling + notifications
- Polling + progress display
- Status updates flow through components

## Performance Considerations

### Re-Render Optimization

**Problem**: BulkImportProgress re-renders on every poll (2s interval) → can cause lag.

**Solution**: Memoize component
```typescript
export const BulkImportProgress = React.memo(function BulkImportProgress({
  status,
  isLoading,
}: BulkImportProgressProps) {
  // Component only re-renders if status prop changes
});
```

### Query Invalidation

**Pattern**:
```typescript
// After modal completion
queryClient.invalidateQueries({ queryKey: ['listings'] });
// Triggers refetch of listing list, shows updated data
```

### Polling Cleanup

**Pattern**:
```typescript
return () => {
  window.removeEventListener('import-partial-found', handler);
};
// Cleanup prevents memory leak and duplicate listeners
```

## Pagination for Large Imports

**Use Case**: 10,000+ URLs in single import

**Solution**: `useImportPollingWithPagination` variant
```typescript
const { allRowStatus, currentPage, hasMore } = useImportPollingWithPagination({
  bulkJobId,
  pageSize: 20,
});
```

**Why**: Avoids loading all 10,000 URLs into memory at once.

## Testing Data

### Mock Status Responses

**Running**:
```json
{
  "status": "running",
  "total_urls": 10,
  "completed": 5,
  "success": 3,
  "partial": 2,
  "failed": 0,
  "running": 5,
  "queued": 0
}
```

**Complete with Partials**:
```json
{
  "status": "complete",
  "total_urls": 10,
  "completed": 10,
  "success": 8,
  "partial": 2,
  "failed": 0,
  "running": 0,
  "queued": 0
}
```

### Mock Listing Data

```typescript
const mockListing: Listing = {
  id: 1,
  title: 'Dell OptiPlex 7090',
  cpu: { name: 'Intel Core i5-10500' },
  ram_gb: 8,
  primary_storage_gb: 256,
  primary_storage_type: 'SSD',
  condition: 'refurbished',
  quality: 'partial',
  price_usd: null,
  adjusted_price_usd: null,
};
```

## Error Handling

### Network Errors

**Polling**:
- Catch and log, continue polling
- Don't crash UI
- Show error toast after N retries
- Fallback: show last known status

**Modal**:
- Show error message in alert
- Don't close modal on error
- User can retry or skip
- Log error for debugging

### API Response Errors

**Polling**:
- Response not ok → throw error
- React Query retries automatically
- Show error in toast after failures

**Modal**:
- API returns 400 → show error from `detail` field
- API returns 500 → show generic error
- User can correct and retry

## Related Phase Context

**Phase 1 (Complete)**: Schema supports `quality`, partial price handling, provisioning for completion fields.

**Phase 2 (Complete)**: API endpoints ready for polling and completion.

**Phase 3 (In Progress)**: Modal component for manual price entry.

**Phase 4 (In Progress)**: Real-time polling, progress display, notifications.

**Phase 5 (Not Started)**: End-to-end integration testing, full import workflow validation.

## Type Definitions

Ensure these types are defined in `apps/web/types/listings.ts`:

```typescript
interface Listing {
  id: number;
  title: string;
  cpu?: { name: string };
  gpu?: { name: string };
  ram_gb?: number;
  primary_storage_gb?: number;
  primary_storage_type?: string;
  condition?: string;
  quality: 'full' | 'partial';
  price_usd: number | null;
  adjusted_price_usd: number | null;
  valuation_breakdown?: Record<string, unknown>;
}
```

Ensure hook types are exported from `apps/web/hooks/useImportPolling.ts`:

```typescript
export interface PerRowImportStatus { /* ... */ }
export interface BulkImportStatus { /* ... */ }
export function useImportPolling(options: UseImportPollingOptions) { /* ... */ }
```
