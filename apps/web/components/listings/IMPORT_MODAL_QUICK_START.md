# ImportModal - Quick Start Guide

## 🚀 Quick Start (30 seconds)

```tsx
import { useState } from 'react';
import { ImportModal } from '@/components/listings/import-modal';
import { Button } from '@/components/ui/button';

function MyComponent() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setOpen(true)}>Import</Button>
      <ImportModal open={open} onOpenChange={setOpen} />
    </>
  );
}
```

## 📋 Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `open` | boolean | ✅ | Controls modal visibility |
| `onOpenChange` | (open: boolean) => void | ✅ | State change handler |
| `onSuccess` | () => void | ❌ | Callback after successful import |

## 🎯 Common Patterns

### Pattern 1: Refresh Data After Import
```tsx
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();

<ImportModal
  open={open}
  onOpenChange={setOpen}
  onSuccess={() => {
    queryClient.invalidateQueries({ queryKey: ['listings'] });
  }}
/>
```

### Pattern 2: Navigate After Import
```tsx
import { useRouter } from 'next/navigation';

const router = useRouter();

<ImportModal
  open={open}
  onOpenChange={setOpen}
  onSuccess={() => {
    router.push('/listings');
  }}
/>
```

### Pattern 3: Show Custom Toast
```tsx
import { useToast } from '@/hooks/use-toast';

const { toast } = useToast();

<ImportModal
  open={open}
  onOpenChange={setOpen}
  onSuccess={() => {
    toast({
      title: 'Import Started',
      description: 'Processing in background'
    });
  }}
/>
```

## ✨ Features

- **URL Import**: Import from eBay, Amazon, and other marketplace URLs
- **File Upload**: Upload Excel workbooks (.xlsx, .xls, .csv)
- **Tab Interface**: Easy switching between import methods
- **Validation**: Prevents empty submissions
- **Toast Notifications**: Automatic success/error feedback
- **Auto-cleanup**: State resets when modal closes
- **Keyboard Support**: Enter key submits URL import

## 🔗 API Endpoints

### URL Import
```
POST /api/v1/ingest/single
Body: { url, priority }
Response: { job_id }
```

### File Upload
```
POST /v1/imports/sessions
Body: FormData with 'upload' field
Response: { id, filename, status }
```

## 📚 Full Documentation

- **Component**: [import-modal.tsx](./import-modal.tsx)
- **Examples**: [import-modal.example.tsx](./import-modal.example.tsx)
- **Docs**: [import-modal.md](./import-modal.md)
- **Summary**: [IMPORT_MODAL_SUMMARY.md](./IMPORT_MODAL_SUMMARY.md)
- **Architecture**: [import-modal-architecture.txt](./import-modal-architecture.txt)

## 🧪 Testing

```bash
# Start dev server
make web

# Navigate to your page
# Add ImportModal component
# Test both import methods
# Verify toast notifications
# Check onSuccess callback
```

## ⚡ Quick Integration

### Add to Listings Page
```tsx
// In /apps/web/app/listings/page.tsx
import { ImportModal } from '@/components/listings/import-modal';

export default function ListingsPage() {
  const [importOpen, setImportOpen] = useState(false);

  return (
    <div>
      <div className="flex justify-between">
        <h1>Listings</h1>
        <Button onClick={() => setImportOpen(true)}>Import</Button>
      </div>

      <ImportModal
        open={importOpen}
        onOpenChange={setImportOpen}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['listings'] });
        }}
      />

      {/* Existing content */}
    </div>
  );
}
```

### Add to Empty State
```tsx
function EmptyListings() {
  const [importOpen, setImportOpen] = useState(false);

  return (
    <div className="text-center py-12">
      <h3>No listings yet</h3>
      <Button onClick={() => setImportOpen(true)}>
        Import Your First Listing
      </Button>
      <ImportModal open={importOpen} onOpenChange={setImportOpen} />
    </div>
  );
}
```

## 🤔 When to Use

### Use ImportModal ✅
- Quick single imports from anywhere
- Empty state CTAs
- Dashboard quick actions
- Toolbar import buttons

### Use Full Import Page ✅
- Complex batch imports
- File mapping required
- Conflict resolution needed
- Multi-entity imports

## 💡 Tips

1. **Always provide onSuccess**: Refresh data or navigate after import
2. **Use with React Query**: Invalidate queries to refresh data
3. **Keep it accessible**: Button should have clear label
4. **Handle loading states**: Modal handles its own loading
5. **Don't poll manually**: Import processes in background

## 🐛 Common Issues

**Issue**: Modal doesn't close after import
**Solution**: Component auto-closes, check console for errors

**Issue**: Data doesn't refresh
**Solution**: Add onSuccess callback with data refresh logic

**Issue**: Toast doesn't appear
**Solution**: Ensure toast provider is in app layout

## 📞 Need Help?

- See full documentation: [import-modal.md](./import-modal.md)
- Check examples: [import-modal.example.tsx](./import-modal.example.tsx)
- Review architecture: [import-modal-architecture.txt](./import-modal-architecture.txt)
