# Bulk Import UI - Quick Start Guide

Get started with the bulk URL import feature in 5 minutes.

## Installation

All dependencies are already included in the Deal Brain monorepo. No additional installation needed.

## Basic Usage

### 1. Import the Component

```tsx
import { BulkImportDialog } from '@/components/ingestion/bulk-import-dialog';
```

### 2. Add State Management

```tsx
'use client';

import { useState } from 'react';

export function MyPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  // ... rest of component
}
```

### 3. Render the Component

```tsx
<BulkImportDialog
  open={dialogOpen}
  onOpenChange={setDialogOpen}
/>
```

### 4. Add a Trigger Button

```tsx
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';

<Button onClick={() => setDialogOpen(true)}>
  <Upload className="h-4 w-4 mr-2" />
  Bulk Import URLs
</Button>
```

## Complete Example

```tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { BulkImportDialog } from '@/components/ingestion/bulk-import-dialog';
import { Upload } from 'lucide-react';

export default function ImportPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Import Listings</h1>

      <Button onClick={() => setDialogOpen(true)}>
        <Upload className="h-4 w-4 mr-2" />
        Bulk Import URLs
      </Button>

      <BulkImportDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={(result) => {
          console.log(`Import complete: ${result.success} succeeded`);
        }}
        onError={(error) => {
          console.error('Import failed:', error.message);
        }}
      />
    </div>
  );
}
```

## With Toast Notifications

```tsx
import { toast } from 'sonner'; // or your toast library

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

## File Format Examples

### CSV File (urls.csv)

```csv
url
https://www.ebay.com/itm/123456789012
https://www.amazon.com/dp/B08N5WRWNW
https://www.example.com/product/xyz
```

### JSON File (urls.json)

```json
[
  { "url": "https://www.ebay.com/itm/123456789012" },
  { "url": "https://www.amazon.com/dp/B08N5WRWNW" },
  { "url": "https://www.example.com/product/xyz" }
]
```

### Paste Format

Simply paste URLs into the textarea, one per line:

```
https://www.ebay.com/itm/123456789012
https://www.amazon.com/dp/B08N5WRWNW
https://www.example.com/product/xyz
```

## Features

### File Upload
- Drag & drop or click to browse
- Supports CSV and JSON formats
- Max file size: 1MB
- Max URLs: 1000 per batch

### Paste URLs
- One URL per line
- Real-time validation
- URL count display
- Max: 1000 URLs

### Progress Tracking
- Real-time updates every 2 seconds
- Progress bar with percentage
- Statistics: Total, Success, Failed, Running, Queued
- Elapsed time display

### Status Table
- Per-URL status display
- Pagination (50 rows per page)
- Clickable listing IDs
- Error details

### Results Export
- Download as CSV
- Includes URL, Status, Listing ID, Error
- Auto-generated filename

## Keyboard Shortcuts

- **Tab** - Navigate between elements
- **Enter/Space** - Activate buttons
- **Escape** - Close dialog
- **Arrow keys** - Navigate table pagination

## Accessibility

All components are fully accessible:
- Keyboard navigation
- Screen reader support
- ARIA labels
- High contrast colors
- Focus indicators

## Troubleshooting

### File upload fails
**Problem**: "Invalid file type" error
**Solution**: Ensure file has `.csv` or `.json` extension

### URLs not parsing
**Problem**: No URLs detected from paste
**Solution**: Ensure each URL starts with `http://` or `https://` and is on its own line

### Polling stops
**Problem**: Status stuck at "running"
**Solution**: Check browser console for API errors; try refreshing the page

### Download disabled
**Problem**: "Download CSV" button is disabled
**Solution**: Wait for all URLs to finish processing (status must be "complete")

## API Requirements

Ensure these backend endpoints are available:

```
POST /api/v1/ingest/bulk
GET /api/v1/ingest/bulk/{bulk_job_id}
```

Configure the API URL in your `.env`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Advanced Usage

### Custom Success Handler

```tsx
const handleSuccess = (result) => {
  // Log to analytics
  analytics.track('bulk_import_complete', {
    total: result.total_urls,
    success: result.success,
    failed: result.failed,
  });

  // Redirect to results page
  router.push(`/imports/${result.bulk_job_id}`);

  // Show notification
  toast.success('Import complete!');
};

<BulkImportDialog onSuccess={handleSuccess} />
```

### Custom Error Handler

```tsx
const handleError = (error) => {
  // Log to error tracking
  errorTracker.captureException(error);

  // Show user-friendly message
  if (error.code === 'UPLOAD_ERROR') {
    toast.error('Failed to upload file. Please try again.');
  } else if (error.code === 'VALIDATION_ERROR') {
    toast.error('Invalid file format. Please check your file.');
  } else {
    toast.error('An unexpected error occurred.');
  }
};

<BulkImportDialog onError={handleError} />
```

### Auto-close on Success

```tsx
const handleSuccess = (result) => {
  toast.success('Import complete!');
  setDialogOpen(false); // Close dialog
};

<BulkImportDialog
  open={dialogOpen}
  onOpenChange={setDialogOpen}
  onSuccess={handleSuccess}
/>
```

## Next Steps

- Read the [full documentation](./BULK_IMPORT_README.md)
- Review the [component structure](./COMPONENT_STRUCTURE.md)
- Check out the [implementation details](../../../BULK_IMPORT_UI_IMPLEMENTATION.md)
- See the [example component](./bulk-import-example.tsx)

## Support

For questions or issues:
1. Check the troubleshooting section
2. Review the full documentation
3. Check browser console for errors
4. Verify API endpoints are available

## License

Part of Deal Brain project. See main LICENSE file for details.
