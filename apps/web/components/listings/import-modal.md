# ImportModal Component

A reusable modal component for importing listings from URLs or file uploads.

## Location

`/apps/web/components/listings/import-modal.tsx`

## Overview

The `ImportModal` component provides a unified interface for importing listings into Deal Brain through two methods:

1. **URL Import**: Import individual listings from marketplace URLs (eBay, Amazon, etc.)
2. **File Upload**: Import listings from Excel workbooks (.xlsx, .xls, .csv)

## Props Interface

```typescript
export interface ImportModalProps {
  open: boolean;                    // Controls modal visibility
  onOpenChange: (open: boolean) => void;  // Callback when modal state changes
  onSuccess?: () => void;          // Optional callback after successful import
}
```

## Features

### URL Import
- Validates URL input before submission
- Submits to `/api/v1/ingest/single` endpoint
- Creates ingestion job for async processing
- Displays job ID on success
- Supports Enter key for quick submission

### File Upload
- Accepts .xlsx, .xls, and .csv files
- Submits to `/v1/imports/sessions` endpoint
- Creates import session for batch processing
- Displays session ID on success
- Shows selected filename

### User Experience
- **Tab Navigation**: Switch between URL and File import modes
- **Loading States**: Disables inputs and shows loading text during import
- **Validation**: Prevents empty submissions with user-friendly error messages
- **Toast Notifications**: Success and error feedback via toast system
- **Auto-cleanup**: Resets form state when modal closes
- **Keyboard Support**: Enter key submits URL import

## API Endpoints

### URL Import
```
POST /api/v1/ingest/single
Content-Type: application/json

Body: {
  "url": "https://www.ebay.com/itm/...",
  "priority": "normal"
}

Response: {
  "job_id": "uuid-string",
  ...
}
```

### File Import
```
POST /v1/imports/sessions
Content-Type: multipart/form-data

Body: FormData with 'upload' field

Response: {
  "id": "session-uuid",
  "filename": "workbook.xlsx",
  "status": "pending",
  ...
}
```

## Usage Examples

### Basic Usage

```tsx
import { useState } from 'react';
import { ImportModal } from '@/components/listings/import-modal';
import { Button } from '@/components/ui/button';

export function MyComponent() {
  const [importOpen, setImportOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setImportOpen(true)}>
        Import Listing
      </Button>

      <ImportModal
        open={importOpen}
        onOpenChange={setImportOpen}
        onSuccess={() => console.log('Import completed!')}
      />
    </>
  );
}
```

### With Data Refresh

```tsx
import { useQueryClient } from '@tanstack/react-query';

export function ListingsPage() {
  const [importOpen, setImportOpen] = useState(false);
  const queryClient = useQueryClient();

  return (
    <>
      <Button onClick={() => setImportOpen(true)}>Import</Button>

      <ImportModal
        open={importOpen}
        onOpenChange={setImportOpen}
        onSuccess={() => {
          // Refresh listings data after import
          queryClient.invalidateQueries(['listings']);
        }}
      />
    </>
  );
}
```

### With Navigation

```tsx
import { useRouter } from 'next/navigation';

export function EmptyState() {
  const [importOpen, setImportOpen] = useState(false);
  const router = useRouter();

  return (
    <>
      <Button onClick={() => setImportOpen(true)}>
        Import Your First Listing
      </Button>

      <ImportModal
        open={importOpen}
        onOpenChange={setImportOpen}
        onSuccess={() => {
          // Navigate to listings page after import
          router.push('/listings');
        }}
      />
    </>
  );
}
```

### With Custom Toast

```tsx
import { useToast } from '@/hooks/use-toast';

export function Dashboard() {
  const [importOpen, setImportOpen] = useState(false);
  const { toast } = useToast();

  return (
    <>
      <Button onClick={() => setImportOpen(true)}>Import</Button>

      <ImportModal
        open={importOpen}
        onOpenChange={setImportOpen}
        onSuccess={() => {
          toast({
            title: 'Import Started',
            description: 'Your import is being processed in the background.',
          });
        }}
      />
    </>
  );
}
```

## Implementation Details

### State Management

The component manages internal state for:
- `isImporting`: Loading state during API calls
- `activeTab`: Current tab ('url' or 'file')
- `importUrl`: URL input value
- `selectedFile`: Selected file for upload

### Error Handling

Errors are handled at multiple levels:

1. **Validation Errors**: Empty inputs show user-friendly messages
2. **API Errors**: Parse JSON error responses with fallback messages
3. **Toast Notifications**: Display errors via toast system
4. **Non-blocking**: Errors don't close the modal, allowing retry

### Accessibility

- Proper label associations with form inputs
- Keyboard navigation support (Enter key for URL submit)
- Focus management within modal
- Disabled states for loading conditions

## Dependencies

- `@/components/ui/dialog` - Modal dialog component
- `@/components/ui/button` - Button component
- `@/components/ui/input` - Input field component
- `@/components/ui/label` - Form label component
- `@/components/ui/tabs` - Tab navigation component
- `@/hooks/use-toast` - Toast notification system
- `@/lib/utils` - API_URL constant
- `lucide-react` - Icons (Upload, Link)

## Notes

### Async Processing

Both import methods return immediately with a job/session ID. The actual import processing happens asynchronously:

- **URL Import**: Creates an ingestion job that polls for completion
- **File Import**: Creates an import session that requires mapping and commit steps

For full import workflow including job polling, see:
- `/components/ingestion/single-url-import-form.tsx` - Full URL import with polling
- `/components/import/importer-workspace.tsx` - Full file import workflow

### Future Enhancements

Potential improvements for this component:

1. **Job Polling**: Add optional polling to track import completion
2. **Progress Indicators**: Show upload progress for large files
3. **Bulk URL Input**: Add textarea for multiple URL imports
4. **Validation**: Add URL pattern validation for supported marketplaces
5. **File Preview**: Show file metadata before upload
6. **Recent Imports**: Display list of recent import jobs

## Testing Checklist

- [ ] Modal opens when `open={true}`
- [ ] Modal closes when Cancel or X clicked
- [ ] URL tab shows URL input field
- [ ] File tab shows file input field
- [ ] Tab switching works correctly
- [ ] URL input disabled when loading
- [ ] File input disabled when loading
- [ ] Import button disabled with empty input
- [ ] Import button disabled during loading
- [ ] Enter key submits URL import
- [ ] Success closes modal
- [ ] Success shows toast notification
- [ ] Success calls onSuccess callback
- [ ] Error shows toast notification
- [ ] Error keeps modal open
- [ ] State resets when modal closes
- [ ] Selected filename displays correctly

## Related Components

- `/app/(dashboard)/import/page.tsx` - Full import page with both methods
- `/components/ingestion/single-url-import-form.tsx` - Advanced URL import with polling
- `/components/import/importer-workspace.tsx` - Advanced file import with mapping
- `/components/ingestion/bulk-import-dialog.tsx` - Bulk URL import dialog
