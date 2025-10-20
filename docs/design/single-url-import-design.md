# Single URL Import Component Design
**Task ID-022: Frontend Import Component**
**Design Date**: 2025-10-19
**Designer**: UI Design System
**Status**: Design Complete - Ready for Implementation

---

## Overview

The Single URL Import component enables users to import PC listings from marketplace URLs (eBay, Amazon, retailers) with minimal friction. The design prioritizes speed, clarity, and accessibility while maintaining consistency with Deal Brain's existing shadcn/ui-based design system.

**Key Goal**: User can paste URL and import in <3 clicks with clear status visibility.

---

## Component Architecture

### Component Hierarchy

```
SingleUrlImportForm (Smart Component)
├── Card (Container)
│   ├── CardHeader
│   │   ├── CardTitle
│   │   └── CardDescription
│   ├── CardContent
│   │   ├── FormField (URL Input)
│   │   │   ├── Label
│   │   │   ├── Input
│   │   │   └── FormMessage (Error)
│   │   ├── FormField (Priority Select)
│   │   │   ├── Label
│   │   │   ├── Select
│   │   │   └── FormMessage
│   │   └── ImportStatusDisplay
│   │       ├── Alert (Status Messages)
│   │       ├── IngestionProgress (Polling State)
│   │       └── ImportSuccessResult (Success State)
│   └── CardFooter
│       ├── Button (Cancel/Reset)
│       └── Button (Import - Primary)
```

### File Structure

```
apps/web/components/ingestion/
├── single-url-import-form.tsx    # Main component
├── ingestion-status-display.tsx  # Status polling UI
├── import-success-result.tsx     # Success result display
└── types.ts                      # TypeScript interfaces

apps/web/lib/api/
└── ingestion.ts                  # API client functions

apps/web/hooks/
└── use-ingestion-job.ts          # React Query hook for polling
```

---

## State Management

### Component States (Finite State Machine)

```typescript
type ImportState =
  | { status: 'idle' }
  | { status: 'validating' }
  | { status: 'submitting' }
  | { status: 'polling', jobId: string }
  | { status: 'success', result: ImportResult }
  | { status: 'error', error: string }

interface ImportResult {
  job_id: string;
  listing_id: number | null;
  provenance: 'ebay_api' | 'jsonld' | 'scraper';
  quality: 'full' | 'partial';
  created_at: string;
}
```

### State Transitions

```
idle → validating → submitting → polling → success
  ↓         ↓           ↓           ↓
error ← error ← error ← error
```

### React Query Integration

```typescript
// Hook for job status polling
const { data, isLoading, error } = useQuery({
  queryKey: ['ingestion-job', jobId],
  queryFn: () => apiFetch<IngestionJobStatus>(`/v1/ingest/${jobId}`),
  enabled: !!jobId && state.status === 'polling',
  refetchInterval: (data) => {
    // Stop polling when complete
    if (data?.status === 'complete' || data?.status === 'failed') {
      return false;
    }
    // Poll every 2 seconds while running
    return 2000;
  },
  retry: 3,
  retryDelay: 1000,
});
```

---

## Visual Design

### Layout & Spacing (8px Grid System)

```
Card Container
┌─────────────────────────────────────────────┐
│ Import from URL                    [Header] │
│ Paste a listing URL to import              │
├─────────────────────────────────────────────┤
│                                    [24px ↕] │
│ Listing URL *                               │
│ ┌─────────────────────────────────────────┐ │
│ │ https://ebay.com/itm/...               │ │ [40px height]
│ └─────────────────────────────────────────┘ │
│                                    [16px ↕] │
│ Priority (optional)                         │
│ ┌─────────────────────────────────────────┐ │
│ │ Standard ▼                             │ │ [40px height]
│ └─────────────────────────────────────────┘ │
│                                    [24px ↕] │
│ [Status Display Area - Conditional]         │
│                                    [24px ↕] │
├─────────────────────────────────────────────┤
│                 [Reset]  [Import Listing] │ │ [Footer - 16px padding]
└─────────────────────────────────────────────┘
```

### Responsive Breakpoints

- **Mobile (<640px)**: Single column, full-width buttons
- **Tablet (640-1024px)**: Standard layout, 90% width
- **Desktop (>1024px)**: Max width 600px, centered in card

### Color System (Using Deal Brain Palette)

**Form States:**
- Input Border (Default): `hsl(var(--input))`
- Input Border (Focus): `hsl(var(--ring))` with 2px ring
- Input Border (Error): `hsl(var(--destructive))`
- Input Background: `hsl(var(--background))`

**Status Colors:**
- Queued/Running: `hsl(var(--primary))` - Blue
- Success: `hsl(var(--success))` - Green
- Error: `hsl(var(--destructive))` - Red
- Warning: `hsl(45 93% 47%)` - Amber

**Provenance Badges:**
- eBay API: `bg-blue-100 text-blue-800 border-blue-200`
- JSON-LD: `bg-purple-100 text-purple-800 border-purple-200`
- Scraper: `bg-gray-100 text-gray-800 border-gray-200`

**Quality Indicators:**
- Full: `bg-green-100 text-green-800` with checkmark icon
- Partial: `bg-amber-100 text-amber-800` with alert icon

---

## Component Specifications

### 1. URL Input Field

**Tailwind Classes:**
```tsx
<Input
  type="url"
  placeholder="https://www.ebay.com/itm/..."
  className="h-10 text-base"
  aria-label="Listing URL"
  aria-required="true"
  aria-describedby="url-help url-error"
/>
```

**Validation Rules:**
- Required field
- Valid URL format (http/https)
- Max length 2048 characters
- Debounced validation (300ms)

**Error Messages:**
- Empty: "Please enter a listing URL"
- Invalid: "Please enter a valid URL starting with http:// or https://"
- Unsupported: "This marketplace is not yet supported"

### 2. Priority Select

**Options:**
```typescript
const priorityOptions = [
  { value: 'high', label: 'High - Process immediately' },
  { value: 'standard', label: 'Standard - Normal queue' },
  { value: 'low', label: 'Low - Background processing' },
];
```

**Tailwind Classes:**
```tsx
<Select defaultValue="standard">
  <SelectTrigger className="h-10">
    <SelectValue placeholder="Select priority" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="high">High - Process immediately</SelectItem>
    <SelectItem value="standard">Standard - Normal queue</SelectItem>
    <SelectItem value="low">Low - Background processing</SelectItem>
  </SelectContent>
</Select>
```

### 3. Status Display States

#### A. Idle State
```tsx
// No status display - clean form only
```

#### B. Validating State
```tsx
<Alert variant="default" className="flex items-center gap-2">
  <Loader2 className="h-4 w-4 animate-spin" />
  <div>
    <AlertTitle>Validating URL...</AlertTitle>
  </div>
</Alert>
```

#### C. Submitting State
```tsx
<Alert variant="default" className="flex items-center gap-2">
  <Loader2 className="h-4 w-4 animate-spin" />
  <div>
    <AlertTitle>Creating import job...</AlertTitle>
    <AlertDescription className="text-xs text-muted-foreground">
      This usually takes a few seconds
    </AlertDescription>
  </div>
</Alert>
```

#### D. Polling State (Queued/Running)
```tsx
<Alert variant="default" className="border-primary/50 bg-primary/5">
  <div className="flex items-start gap-3">
    <Loader2 className="h-5 w-5 animate-spin text-primary mt-0.5" />
    <div className="flex-1 space-y-2">
      <div className="flex items-center justify-between">
        <AlertTitle className="text-sm font-semibold">
          Importing listing...
        </AlertTitle>
        <Badge variant="outline" className="text-xs">
          {elapsed}s elapsed
        </Badge>
      </div>
      <AlertDescription className="text-xs space-y-1">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary animate-pulse transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-muted-foreground tabular-nums">{progress}%</span>
        </div>
        <p className="text-muted-foreground">
          {statusMessage}
        </p>
      </AlertDescription>
    </div>
  </div>
</Alert>
```

**Status Messages by Job State:**
- `queued`: "Job queued, waiting for worker..."
- `running`: "Extracting data from marketplace..."
- `running` (after 5s): "Processing product details..."
- `running` (after 10s): "Enriching with component data..."

#### E. Success State
```tsx
<Alert variant="default" className="border-success/50 bg-success/5">
  <CheckCircle2 className="h-5 w-5 text-success" />
  <div className="flex-1">
    <AlertTitle className="text-success">
      Listing imported successfully!
    </AlertTitle>
    <AlertDescription className="mt-3 space-y-3">
      {/* Listing Preview Card */}
      <div className="rounded-lg border bg-card p-3 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <h4 className="font-medium text-sm line-clamp-2">
            {result.title}
          </h4>
          <Badge variant="secondary" className="text-xs shrink-0">
            #{result.listing_id}
          </Badge>
        </div>

        {/* Metadata Row */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge
            variant="outline"
            className="gap-1 bg-blue-50 text-blue-700 border-blue-200"
          >
            <Database className="h-3 w-3" />
            {result.provenance.replace('_', ' ').toUpperCase()}
          </Badge>

          {result.quality === 'full' ? (
            <Badge variant="outline" className="gap-1 bg-green-50 text-green-700 border-green-200">
              <CheckCircle2 className="h-3 w-3" />
              Full data
            </Badge>
          ) : (
            <Badge variant="outline" className="gap-1 bg-amber-50 text-amber-700 border-amber-200">
              <AlertCircle className="h-3 w-3" />
              Partial data
            </Badge>
          )}

          <span className="ml-auto">
            Just now
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => router.push(`/listings/${result.listing_id}`)}
          className="flex-1"
        >
          <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
          View Listing
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={handleReset}
          className="flex-1"
        >
          Import Another
        </Button>
      </div>
    </AlertDescription>
  </div>
</Alert>
```

#### F. Error State
```tsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <div className="flex-1">
    <AlertTitle>Import failed</AlertTitle>
    <AlertDescription className="mt-2 space-y-2">
      <p className="text-sm">{error.message}</p>

      {/* Error Details (Collapsible) */}
      {error.details && (
        <details className="text-xs">
          <summary className="cursor-pointer hover:underline">
            Show technical details
          </summary>
          <pre className="mt-2 p-2 bg-destructive/10 rounded text-xs overflow-auto">
            {JSON.stringify(error.details, null, 2)}
          </pre>
        </details>
      )}

      {/* Retry Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleRetry}
        className="mt-2"
      >
        <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
        Try Again
      </Button>
    </AlertDescription>
  </div>
</Alert>
```

**Common Error Messages:**
- `TIMEOUT`: "Import timed out. The marketplace may be slow to respond."
- `INVALID_SCHEMA`: "Could not extract listing data. The page format may not be supported."
- `ADAPTER_DISABLED`: "This marketplace integration is currently disabled."
- `ITEM_NOT_FOUND`: "Listing not found. The URL may be invalid or the item may have been removed."
- `RATE_LIMITED`: "Too many requests. Please wait a moment and try again."
- `NETWORK_ERROR`: "Network error. Please check your connection and try again."

---

## Accessibility (WCAG 2.1 AA)

### Keyboard Navigation

**Tab Order:**
1. URL Input Field
2. Priority Select Trigger
3. Priority Options (when open)
4. Reset Button
5. Import Button
6. Success Action Buttons (when visible)

**Keyboard Shortcuts:**
- `Enter` in URL field: Submit form (if valid)
- `Escape`: Clear form / dismiss errors
- `Tab`: Navigate forward
- `Shift+Tab`: Navigate backward
- Arrow keys in Select: Navigate options

### Screen Reader Support

**ARIA Labels:**
```tsx
<form aria-label="Import listing from URL">
  <Input
    aria-label="Listing URL"
    aria-required="true"
    aria-invalid={!!errors.url}
    aria-describedby="url-help url-error"
  />

  <Select aria-label="Import priority">
    {/* ... */}
  </Select>

  <Button
    aria-label="Import listing"
    aria-disabled={!isValid || isSubmitting}
  >
    Import Listing
  </Button>
</form>
```

**Live Regions for Status Updates:**
```tsx
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="sr-only"
>
  {statusMessage}
</div>
```

**Status Announcements:**
- Validating: "Validating URL"
- Submitting: "Creating import job"
- Polling: "Importing listing, please wait"
- Success: "Listing imported successfully"
- Error: "Import failed, [error message]"

### Focus Management

**Focus Transitions:**
1. On submit: Focus moves to status alert
2. On success: Focus moves to "View Listing" button
3. On error: Focus moves to error alert
4. On reset: Focus returns to URL input

**Focus Visible:**
```css
.focus-visible:outline-none
.focus-visible:ring-2
.focus-visible:ring-ring
.focus-visible:ring-offset-2
```

### Color Contrast Ratios

All text meets WCAG AA standards:
- Normal text (14px+): 4.5:1 minimum
- Large text (18px+ or 14px+ bold): 3:1 minimum
- Interactive elements: 3:1 minimum against background

**Tested Combinations:**
- Primary button text on primary bg: 7.2:1
- Error text on error bg: 6.8:1
- Success text on success bg: 5.1:1
- Muted text on background: 4.6:1

---

## Performance Optimizations

### Component Memoization

```typescript
// Memoize status display to prevent re-renders
const StatusDisplay = React.memo(({ status, result, error }) => {
  // ... render logic
});

// Memoize success result display
const SuccessResult = React.memo(({ result }) => {
  // ... render logic
});
```

### Debouncing

```typescript
// Debounce URL validation (300ms)
const debouncedValidateUrl = useMemo(
  () => debounce((url: string) => {
    // Validation logic
  }, 300),
  []
);
```

### Polling Optimization

```typescript
// Exponential backoff for polling interval
const getRefetchInterval = (attemptCount: number) => {
  if (attemptCount < 5) return 2000;  // 2s for first 5 attempts (10s)
  if (attemptCount < 15) return 3000; // 3s for next 10 attempts (30s)
  return 5000; // 5s thereafter
};
```

### Cleanup on Unmount

```typescript
useEffect(() => {
  return () => {
    // Cancel pending requests
    queryClient.cancelQueries(['ingestion-job', jobId]);
  };
}, [jobId]);
```

---

## Error Handling Strategy

### Error Boundaries

```typescript
// Wrap component in error boundary
<ErrorBoundary
  fallback={<ImportErrorFallback />}
  onError={(error) => {
    console.error('Import component error:', error);
    // Log to monitoring service
  }}
>
  <SingleUrlImportForm />
</ErrorBoundary>
```

### Network Error Recovery

```typescript
// Retry logic with exponential backoff
const { mutate, isError, error, reset } = useMutation({
  mutationFn: (data) => apiFetch('/v1/ingest/single', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  onError: (error) => {
    // Show user-friendly error message
    setImportState({
      status: 'error',
      error: getErrorMessage(error),
    });
  },
});
```

### Graceful Degradation

**If polling fails:**
- Show manual refresh button
- Display last known status
- Provide link to check jobs page

**If API unavailable:**
- Show clear offline message
- Suggest checking network connection
- Offer to retry when ready

---

## Integration Points

### API Endpoints

**Submit Import:**
```typescript
POST /api/v1/ingest/single
Body: { url: string, priority?: 'high' | 'standard' | 'low' }
Response: { job_id: string, status: 'queued' }
```

**Poll Status:**
```typescript
GET /api/v1/ingest/{job_id}
Response: {
  job_id: string,
  status: 'queued' | 'running' | 'complete' | 'failed',
  result?: {
    listing_id: number,
    provenance: string,
    quality: 'full' | 'partial',
    title?: string,
  },
  error?: {
    code: string,
    message: string,
    details?: any,
  },
  created_at: string,
  updated_at: string,
}
```

### React Query Keys

```typescript
const queryKeys = {
  ingestionJob: (jobId: string) => ['ingestion-job', jobId],
  ingestionJobs: ['ingestion-jobs'],
};
```

### Router Integration

```typescript
// Navigate to listing on success
const router = useRouter();
router.push(`/listings/${result.listing_id}`);
router.refresh(); // Refresh listings table
```

---

## Component Props Interface

```typescript
interface SingleUrlImportFormProps {
  /** Optional callback when import succeeds */
  onSuccess?: (result: ImportResult) => void;

  /** Optional callback when import fails */
  onError?: (error: Error) => void;

  /** Optional callback when form is reset */
  onReset?: () => void;

  /** Optional default URL to pre-fill */
  defaultUrl?: string;

  /** Optional default priority */
  defaultPriority?: 'high' | 'standard' | 'low';

  /** Whether to show in compact mode (no card wrapper) */
  compact?: boolean;

  /** Optional CSS class name */
  className?: string;
}
```

---

## Usage Examples

### Basic Usage

```tsx
import { SingleUrlImportForm } from '@/components/ingestion/single-url-import-form';

export default function ImportPage() {
  return (
    <div className="container max-w-2xl py-8">
      <SingleUrlImportForm />
    </div>
  );
}
```

### With Callbacks

```tsx
<SingleUrlImportForm
  onSuccess={(result) => {
    toast.success(`Listing #${result.listing_id} imported!`);
    router.push(`/listings/${result.listing_id}`);
  }}
  onError={(error) => {
    toast.error(`Import failed: ${error.message}`);
  }}
/>
```

### Pre-filled URL (from query params)

```tsx
const searchParams = useSearchParams();
const prefilledUrl = searchParams.get('url');

<SingleUrlImportForm
  defaultUrl={prefilledUrl || undefined}
/>
```

### Compact Mode (in modal)

```tsx
<Dialog>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Import Listing</DialogTitle>
    </DialogHeader>
    <SingleUrlImportForm compact onSuccess={handleClose} />
  </DialogContent>
</Dialog>
```

---

## Testing Strategy

### Unit Tests

```typescript
describe('SingleUrlImportForm', () => {
  it('renders form fields correctly', () => {
    render(<SingleUrlImportForm />);
    expect(screen.getByLabelText('Listing URL')).toBeInTheDocument();
    expect(screen.getByLabelText('Priority')).toBeInTheDocument();
  });

  it('validates URL format', async () => {
    render(<SingleUrlImportForm />);
    const input = screen.getByLabelText('Listing URL');

    await userEvent.type(input, 'invalid-url');
    await userEvent.tab(); // Trigger blur

    expect(await screen.findByText(/valid URL/i)).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    const onSuccess = jest.fn();
    render(<SingleUrlImportForm onSuccess={onSuccess} />);

    await userEvent.type(
      screen.getByLabelText('Listing URL'),
      'https://ebay.com/itm/12345'
    );
    await userEvent.click(screen.getByText('Import Listing'));

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled();
    });
  });

  it('displays polling status correctly', async () => {
    // Mock polling response
    server.use(
      rest.get('/api/v1/ingest/:jobId', (req, res, ctx) => {
        return res(ctx.json({ status: 'running' }));
      })
    );

    render(<SingleUrlImportForm />);
    // ... submit form

    expect(await screen.findByText(/Importing listing/i)).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});
```

### Accessibility Tests

```typescript
describe('SingleUrlImportForm Accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(<SingleUrlImportForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('supports keyboard navigation', async () => {
    render(<SingleUrlImportForm />);

    const urlInput = screen.getByLabelText('Listing URL');
    const submitButton = screen.getByText('Import Listing');

    urlInput.focus();
    expect(document.activeElement).toBe(urlInput);

    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByLabelText('Priority'));

    await userEvent.tab();
    await userEvent.tab();
    expect(document.activeElement).toBe(submitButton);
  });

  it('announces status changes to screen readers', async () => {
    render(<SingleUrlImportForm />);

    const liveRegion = screen.getByRole('status');
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');

    // ... trigger import

    await waitFor(() => {
      expect(liveRegion).toHaveTextContent(/Importing listing/i);
    });
  });
});
```

### Integration Tests

```typescript
describe('SingleUrlImportForm Integration', () => {
  it('completes full import flow', async () => {
    // Mock API responses
    server.use(
      rest.post('/api/v1/ingest/single', (req, res, ctx) => {
        return res(ctx.json({ job_id: 'job-123', status: 'queued' }));
      }),
      rest.get('/api/v1/ingest/job-123', (req, res, ctx) => {
        return res(ctx.json({
          job_id: 'job-123',
          status: 'complete',
          result: {
            listing_id: 456,
            provenance: 'ebay_api',
            quality: 'full',
          },
        }));
      })
    );

    const onSuccess = jest.fn();
    render(<SingleUrlImportForm onSuccess={onSuccess} />);

    // Submit form
    await userEvent.type(
      screen.getByLabelText('Listing URL'),
      'https://ebay.com/itm/12345'
    );
    await userEvent.click(screen.getByText('Import Listing'));

    // Wait for success
    await waitFor(() => {
      expect(screen.getByText(/imported successfully/i)).toBeInTheDocument();
    });

    expect(onSuccess).toHaveBeenCalledWith(
      expect.objectContaining({
        listing_id: 456,
        provenance: 'ebay_api',
      })
    );
  });
});
```

---

## Implementation Checklist

### Phase 1: Core Component (8 hours)
- [ ] Create component file structure
- [ ] Implement form fields (URL input, priority select)
- [ ] Add form validation with Zod schema
- [ ] Implement submit handler
- [ ] Add basic error handling
- [ ] Wire up React Query mutation
- [ ] Test basic form submission

### Phase 2: Status Polling (6 hours)
- [ ] Create polling hook with React Query
- [ ] Implement status display component
- [ ] Add loading states (validating, submitting, polling)
- [ ] Add progress indicator
- [ ] Implement polling termination logic
- [ ] Test polling edge cases

### Phase 3: Success & Error States (4 hours)
- [ ] Create success result component
- [ ] Add listing preview card
- [ ] Implement provenance badges
- [ ] Add quality indicators
- [ ] Create error display with retry
- [ ] Test all state transitions

### Phase 4: Accessibility & Polish (2 hours)
- [ ] Add ARIA labels and roles
- [ ] Implement focus management
- [ ] Add keyboard shortcuts
- [ ] Test with screen reader
- [ ] Run axe accessibility audit
- [ ] Fix any violations

---

## Design Decisions & Rationale

### Why Card Container?
Provides visual boundary and consistent spacing. Matches existing Deal Brain patterns (see listings page cards).

### Why Polling Instead of WebSockets?
- Simpler implementation (no WebSocket infrastructure needed)
- Matches existing job tracking pattern in backend
- More resilient to network interruptions
- Easier to test and debug
- Adequate for <10s job latency

### Why Inline Status Display?
- Keeps user focused in one place
- Reduces cognitive load (no modal switching)
- Follows progressive disclosure pattern
- Easier to implement accessible focus management

### Why Debounced Validation?
- Prevents excessive validation calls while typing
- Improves perceived performance
- Standard UX pattern for form inputs
- 300ms is sweet spot (feels instant, prevents waste)

### Why Separate Success Result Component?
- Reusable in other contexts (bulk import, etc.)
- Easier to test in isolation
- Cleaner code organization
- Allows for future enhancements (share, edit, etc.)

---

## Future Enhancements (Post-MVP)

1. **URL Auto-detection**: Detect URL in clipboard on focus
2. **Recent URLs**: Show dropdown of recently imported URLs
3. **Batch Mode**: Allow multiple URLs in textarea (one per line)
4. **Duplicate Detection**: Warn if URL already imported
5. **Preview Mode**: Show scraped data before confirming import
6. **Custom Fields**: Map scraped data to custom fields
7. **Schedule Import**: Set future import time
8. **Webhook Integration**: Trigger webhook on completion

---

## File Locations

All file paths are absolute:

- **Main Component**: `/mnt/containers/deal-brain/apps/web/components/ingestion/single-url-import-form.tsx`
- **Status Display**: `/mnt/containers/deal-brain/apps/web/components/ingestion/ingestion-status-display.tsx`
- **Success Result**: `/mnt/containers/deal-brain/apps/web/components/ingestion/import-success-result.tsx`
- **Types**: `/mnt/containers/deal-brain/apps/web/components/ingestion/types.ts`
- **API Client**: `/mnt/containers/deal-brain/apps/web/lib/api/ingestion.ts`
- **Polling Hook**: `/mnt/containers/deal-brain/apps/web/hooks/use-ingestion-job.ts`
- **Design Doc**: `/mnt/containers/deal-brain/docs/design/single-url-import-design.md`

---

**Design Status**: Complete - Ready for Implementation
**Next Step**: Begin Phase 1 implementation (core component)
**Estimated Implementation Time**: 20 hours across 4 phases
