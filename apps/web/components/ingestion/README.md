# Single URL Import Component

Implementation of the Single URL Import component for Deal Brain's URL ingestion feature (Phase 4, Task ID-022).

## Overview

This component provides a user-friendly interface for importing PC listings from marketplace URLs (eBay, Amazon, retailers) with real-time status updates and accessibility support.

## Files Created

1. **types.ts** - TypeScript type definitions
2. **schemas.ts** - Zod validation schemas
3. **error-messages.ts** - Error code to message mapping
4. **import-success-result.tsx** - Success result display component
5. **ingestion-status-display.tsx** - Status polling display component
6. **single-url-import-form.tsx** - Main form component
7. **index.ts** - Barrel export file

### Supporting Files

8. **/lib/api/ingestion.ts** - API client functions
9. **/hooks/use-ingestion-job.ts** - React Query polling hook

## Usage

### Basic Usage

```tsx
import { SingleUrlImportForm } from '@/components/ingestion';

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
import { SingleUrlImportForm } from '@/components/ingestion';
import { useRouter } from 'next/navigation';
import { toast } from '@/hooks/use-toast';

export default function ImportPage() {
  const router = useRouter();

  return (
    <SingleUrlImportForm
      onSuccess={(result) => {
        toast({
          title: 'Success!',
          description: `Listing #${result.listingId} imported successfully`,
        });
        router.push(`/listings/${result.listingId}`);
      }}
      onError={(error) => {
        toast({
          title: 'Import Failed',
          description: error.message,
          variant: 'destructive',
        });
      }}
    />
  );
}
```

### Compact Mode (in Dialog)

```tsx
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import { SingleUrlImportForm } from '@/components/ingestion';

export function ImportDialog() {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Import from URL</Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <SingleUrlImportForm
          compact
          onSuccess={() => {
            setOpen(false);
            // Refresh data
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
```

## Component States

The component implements a finite state machine with the following states:

1. **idle** - Initial state, form ready for input
2. **validating** - URL validation in progress
3. **submitting** - Creating import job
4. **polling** - Job running, polling for status
5. **success** - Listing imported successfully
6. **error** - Import failed with error message

## API Integration

### Endpoints

**Submit Import:**
```
POST /api/v1/ingest/single
Body: { url: string, priority?: 'high' | 'normal' }
Response: { job_id: string, status: 'queued' }
```

**Poll Status:**
```
GET /api/v1/ingest/{job_id}
Response: {
  job_id: string,
  status: 'queued' | 'running' | 'complete' | 'failed',
  result?: { listing_id, title, provenance, quality },
  error?: { code, message, details }
}
```

### Polling Strategy

- Polls every 2 seconds while job is queued or running
- Stops polling when status is 'complete' or 'failed'
- 3 retry attempts with exponential backoff
- Automatic cleanup on component unmount

## Props

### SingleUrlImportFormProps

```typescript
interface SingleUrlImportFormProps {
  onSuccess?: (result: ImportSuccessResult) => void;
  onError?: (error: ImportError) => void;
  onReset?: () => void;
  defaultUrl?: string;
  defaultPriority?: ImportPriority;
  compact?: boolean;
  className?: string;
}
```

## Accessibility

### WCAG 2.1 AA Compliance

- Full keyboard navigation support
- Screen reader announcements via ARIA live regions
- Proper focus management
- Color contrast ratios meet AA standards
- Semantic HTML with appropriate ARIA labels

### Keyboard Navigation

- `Enter` in URL field: Submit form (if valid)
- `Escape`: Clear form / dismiss errors
- `Tab/Shift+Tab`: Navigate through form fields
- Arrow keys: Navigate select options

### ARIA Labels

- Form has `aria-label="Import listing from URL"`
- URL input has `aria-required="true"` and `aria-invalid` when errors
- Status updates announced via `aria-live="polite"` or `aria-live="assertive"` for errors
- All interactive elements have proper labels

## Performance

### Optimizations

- Component memoization for status display
- Debounced URL validation (300ms)
- React Query caching (5 minute GC time)
- Cleanup of polling on unmount
- Conditional rendering based on state

### Bundle Impact

- Core component: ~8KB minified
- Dependencies: react-hook-form, zod, @tanstack/react-query, date-fns
- Tree-shakeable exports

## Error Handling

### Retryable Errors

- TIMEOUT
- RATE_LIMITED
- NETWORK_ERROR
- TEMPORARY_ERROR

### Non-Retryable Errors

- INVALID_SCHEMA
- ADAPTER_DISABLED
- ITEM_NOT_FOUND

### Error Display

- User-friendly error messages
- Technical details in collapsible section
- Retry button for retryable errors
- Screen reader announcements

## Testing

### Unit Tests Location

```
apps/web/components/ingestion/__tests__/
```

### Example Test

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SingleUrlImportForm } from '../single-url-import-form';

test('validates URL format', async () => {
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <SingleUrlImportForm />
    </QueryClientProvider>
  );

  const input = screen.getByLabelText(/Listing URL/i);
  await userEvent.type(input, 'invalid-url');
  await userEvent.tab();

  expect(await screen.findByText(/valid URL/i)).toBeInTheDocument();
});
```

## Design System Compliance

### Components Used

- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Alert, AlertTitle, AlertDescription
- Button (variants: default, outline, ghost)
- Input
- Label
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Badge (variants: default, secondary, outline, destructive)

### Color System

- Primary: Blue for loading/polling states
- Success: Green for successful import
- Destructive: Red for errors
- Muted: Gray for secondary information

### Spacing

- 8px grid system
- Card padding: 24px (p-6)
- Form spacing: 16px (space-y-4)
- Button spacing: 8px (gap-2)

## Known Limitations

1. **date-fns dependency** - Requires date-fns to be installed. Add to package.json:
   ```json
   "date-fns": "^3.0.0"
   ```

2. **API endpoints** - Backend must implement:
   - POST /api/v1/ingest/single
   - GET /api/v1/ingest/{job_id}

3. **Router** - Requires Next.js 13+ App Router for navigation

## Future Enhancements

1. URL auto-detection from clipboard
2. Recent URLs dropdown
3. Batch import mode
4. Duplicate detection warning
5. Preview mode before import
6. Custom field mapping
7. Scheduled imports
8. Webhook integration

## Troubleshooting

### Component not rendering

Check that:
- React Query provider is set up in app layout
- date-fns is installed
- All UI components are available in @/components/ui

### TypeScript errors

Ensure:
- TypeScript version >= 5.0
- strict mode is enabled
- All imports use correct paths

### Polling not working

Verify:
- jobId is correctly passed to useIngestionJob
- Backend returns correct status values
- React Query is not disabled globally

## Support

For issues or questions:
- See design docs: `/mnt/containers/deal-brain/docs/design/single-url-import-*.md`
- Check implementation spec: `single-url-import-technical-spec.md`
- Review component tree: `single-url-import-component-tree.md`
