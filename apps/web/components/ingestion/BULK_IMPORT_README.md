# Bulk URL Import UI Components

This directory contains the complete UI implementation for Deal Brain's bulk URL ingestion feature (Phase 4, Task ID-023).

## Overview

The bulk import feature allows users to upload CSV/JSON files or paste multiple URLs for batch import. It provides real-time progress tracking, per-URL status monitoring, and results export functionality.

## Architecture

### Component Hierarchy

```
BulkImportDialog (Main orchestrator)
├── BulkUploadForm (File upload or paste URLs)
├── BulkProgressDisplay (Real-time progress tracking)
└── BulkStatusTable (Per-URL status with pagination)
```

### Data Flow

1. User uploads file or pastes URLs → `BulkUploadForm`
2. Form validates and submits → API client (`submitBulkUrlImportFile` or `submitBulkUrlImportUrls`)
3. API returns `bulk_job_id` → Start polling
4. React Query hook polls status → `useBulkIngestionJob`
5. Progress updates displayed → `BulkProgressDisplay` + `BulkStatusTable`
6. On completion → Download results as CSV

## Files

### Core Components

- **`bulk-import-dialog.tsx`** - Main modal component with state management
- **`bulk-upload-form.tsx`** - File upload (drag & drop) or paste URLs form
- **`bulk-progress-display.tsx`** - Progress bar and statistics
- **`bulk-status-table.tsx`** - Paginated table of per-URL status

### Supporting Files

- **`bulk-import-types.ts`** - TypeScript type definitions
- **`bulk-import-example.tsx`** - Usage example component
- **`lib/api/bulk-ingestion.ts`** - API client functions
- **`hooks/use-bulk-ingestion-job.ts`** - React Query polling hook

## Component API

### BulkImportDialog

Main dialog component that orchestrates the entire bulk import workflow.

```tsx
import { BulkImportDialog } from '@/components/ingestion/bulk-import-dialog';

<BulkImportDialog
  open={boolean}
  onOpenChange={(open: boolean) => void}
  onSuccess={(result: BulkIngestionStatusResponse) => void}
  onError={(error: BulkImportError) => void}
/>
```

**Props:**
- `open` - Controls dialog visibility
- `onOpenChange` - Callback when dialog open state changes
- `onSuccess` - Optional callback when import completes successfully
- `onError` - Optional callback when import fails

### BulkUploadForm

Form component for file upload or URL paste input.

```tsx
import { BulkUploadForm } from '@/components/ingestion/bulk-upload-form';

<BulkUploadForm
  onSubmit={(data: FormData | string[]) => void}
  disabled={boolean}
  error={BulkImportError | undefined}
/>
```

**Features:**
- Toggle between file upload and paste modes
- Drag & drop file upload (CSV or JSON)
- Real-time URL validation
- Max 1000 URLs per batch
- Max 1MB file size

### BulkProgressDisplay

Progress tracking component with statistics.

```tsx
import { BulkProgressDisplay } from '@/components/ingestion/bulk-progress-display';

<BulkProgressDisplay
  data={BulkIngestionStatusResponse}
  elapsed={number}
/>
```

**Features:**
- Animated progress bar
- Color-coded status (green=complete, yellow=partial, red=failed)
- Statistics grid: Total, Success, Failed, Running, Queued
- Elapsed time display

### BulkStatusTable

Paginated table showing per-URL status.

```tsx
import { BulkStatusTable } from '@/components/ingestion/bulk-status-table';

<BulkStatusTable
  bulkJobId={string}
  data={BulkIngestionStatusResponse}
  onRefresh={() => void}
/>
```

**Features:**
- 50 rows per page
- Status badges (queued, running, complete, failed)
- Clickable listing IDs
- External link to source URL
- Pagination controls

## API Integration

### Endpoints

The components integrate with these backend endpoints:

```
POST /api/v1/ingest/bulk
- Accepts: multipart/form-data (CSV or JSON file)
- Returns: { bulk_job_id: string, total_urls: number }

GET /api/v1/ingest/bulk/{bulk_job_id}?offset=0&limit=50
- Returns: BulkIngestionStatusResponse
```

### Polling Strategy

- Poll interval: **2 seconds** while status is `queued` or `running`
- Stop polling when status is `complete`, `partial`, or `failed`
- Auto-retry: 3 attempts with exponential backoff

### API Client Functions

```ts
// Submit file upload
submitBulkUrlImportFile(file: File): Promise<BulkIngestionResponse>

// Submit pasted URLs (creates CSV in-memory)
submitBulkUrlImportUrls(urls: string[]): Promise<BulkIngestionResponse>

// Get job status with pagination
getBulkIngestionStatus(
  bulkJobId: string,
  offset?: number,
  limit?: number
): Promise<BulkIngestionStatusResponse>

// Download results as CSV
downloadBulkResultsCSV(
  data: BulkIngestionStatusResponse,
  filename?: string
): void
```

## State Management

### Component States

The `BulkImportDialog` manages these states:

1. **`idle`** - Ready for input
2. **`uploading`** - Submitting file/URLs to API
3. **`polling`** - Job running, polling for updates
4. **`complete`** - All URLs processed
5. **`error`** - Upload or processing error

### React Query Hook

The `useBulkIngestionJob` hook handles:
- Automatic polling with configurable interval
- Pagination support
- Cache management (5-minute TTL)
- Retry logic with exponential backoff
- Cancel polling on unmount

## File Formats

### CSV Format

```csv
url
https://www.ebay.com/itm/123456789
https://www.amazon.com/dp/B08N5WRWNW
```

**Requirements:**
- Header row with `url` column
- One URL per row
- UTF-8 encoding
- Max 1MB file size

### JSON Format

```json
[
  { "url": "https://www.ebay.com/itm/123456789" },
  { "url": "https://www.amazon.com/dp/B08N5WRWNW" }
]
```

**Requirements:**
- Array of objects
- Each object must have `url` field
- UTF-8 encoding
- Max 1MB file size

### Paste Format

```
https://www.ebay.com/itm/123456789
https://www.amazon.com/dp/B08N5WRWNW
```

**Requirements:**
- One URL per line
- Each line must start with `http://` or `https://`
- Max 1000 URLs

## Validation

### Client-Side Validation

- **URL format**: Must start with `http://` or `https://`
- **URL count**: 1-1000 URLs per batch
- **File size**: Max 1MB
- **File type**: Must be `.csv` or `.json`
- **Duplicate detection**: Automatically deduplicated (case-sensitive)

### Backend Validation

- Pydantic `HttpUrl` validation
- CSV/JSON parsing with detailed error messages
- 413 status for >1000 URLs
- 422 status for invalid URL formats

## Accessibility

All components follow WCAG 2.1 AA standards:

### Keyboard Navigation
- Tab navigation through all interactive elements
- Arrow keys for pagination
- Escape to close dialog
- Enter/Space to activate buttons

### Screen Reader Support
- ARIA labels on all form controls
- Live regions for progress updates (`aria-live="polite"`)
- Error announcements (`aria-live="assertive"`)
- Descriptive button labels

### Visual Accessibility
- High contrast color-coded status badges
- Focus indicators on all interactive elements
- Clear visual hierarchy
- Responsive design for all screen sizes

## Usage Example

### Basic Usage

```tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { BulkImportDialog } from '@/components/ingestion/bulk-import-dialog';
import { Upload } from 'lucide-react';

export function ImportPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div>
      <Button onClick={() => setDialogOpen(true)}>
        <Upload className="h-4 w-4 mr-2" />
        Bulk Import
      </Button>

      <BulkImportDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={(result) => {
          console.log('Import complete:', result);
        }}
        onError={(error) => {
          console.error('Import failed:', error);
        }}
      />
    </div>
  );
}
```

### With Toast Notifications

```tsx
import { toast } from 'sonner';
import { BulkImportDialog } from '@/components/ingestion/bulk-import-dialog';

<BulkImportDialog
  open={dialogOpen}
  onOpenChange={setDialogOpen}
  onSuccess={(result) => {
    toast.success(
      `Import complete! ${result.success} succeeded, ${result.failed} failed`
    );
  }}
  onError={(error) => {
    toast.error(`Import failed: ${error.message}`);
  }}
/>
```

## Testing Considerations

### Unit Tests

Test each component in isolation:
- Form validation logic
- URL parsing
- Progress calculation
- Status badge selection
- CSV export functionality

### Integration Tests

Test component interactions:
- File upload flow
- URL paste flow
- Polling and state updates
- Pagination
- Error handling

### E2E Tests

Test complete user workflows:
1. Upload CSV → Wait for completion → Download results
2. Paste URLs → Monitor progress → View listing
3. Invalid file → See error → Try again
4. Cancel during polling

## Performance Optimizations

- **Debounced URL validation** - Only validate after user stops typing
- **Memoized components** - Prevent unnecessary re-renders
- **Pagination** - Load only 50 rows at a time
- **React Query caching** - Avoid redundant API calls
- **CSV streaming** - Handle large result files efficiently

## Future Enhancements

Potential improvements for future phases:

1. **WebSocket support** - Real-time updates instead of polling
2. **Pause/Resume** - Allow users to pause long-running jobs
3. **Batch prioritization** - Let users set priority per batch
4. **History view** - Show previous bulk import jobs
5. **Filter/Sort table** - Advanced filtering of results
6. **Partial retry** - Retry only failed URLs
7. **Import templates** - Save/load URL lists
8. **Scheduled imports** - Queue imports for later

## Troubleshooting

### Common Issues

**Problem**: File upload fails with "Invalid file type"
**Solution**: Ensure file has `.csv` or `.json` extension and correct MIME type

**Problem**: URLs not parsing from paste
**Solution**: Ensure each URL is on its own line and starts with `http://` or `https://`

**Problem**: Polling stops but status still shows "running"
**Solution**: Check browser console for API errors; may need to refresh manually

**Problem**: Download CSV button disabled
**Solution**: Wait for all URLs to complete processing (status must be `complete`)

## Dependencies

- **React Hook Form** - Form validation and state
- **React Query** - Server state and polling
- **Radix UI Dialog** - Accessible modal
- **Radix UI Table** - Accessible table
- **Lucide Icons** - UI icons
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety

## Related Documentation

- [Phase 4 Implementation Plan](../../../../docs/project_plans/url-ingest/implementation-plan.md)
- [API Endpoints Documentation](../../../../apps/api/dealbrain_api/api/ingestion.py)
- [Backend Schemas](../../../../packages/core/dealbrain_core/schemas/ingestion.py)
- [Single URL Import](./single-url-import-form.tsx)

## Changelog

### v1.0.0 (2025-10-19)
- Initial implementation
- File upload and paste URL modes
- Real-time progress tracking
- Paginated status table
- CSV export functionality
- Full accessibility support
