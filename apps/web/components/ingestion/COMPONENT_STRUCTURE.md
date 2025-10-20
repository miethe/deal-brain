# Bulk Import UI Component Structure

## Visual Component Tree

```
┌─────────────────────────────────────────────────────────┐
│              BulkImportDialog                           │
│  (Main orchestrator - state machine)                    │
│                                                         │
│  States:                                                │
│  • idle → uploading → polling → complete                │
│  • idle → uploading → error                             │
└─────────────────────────────────────────────────────────┘
                      │
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ BulkUpload  │ │  BulkProgress│ │ BulkStatus   │
│ Form        │ │  Display     │ │ Table        │
└─────────────┘ └──────────────┘ └──────────────┘
        │             │             │
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│ File Upload │ │ Progress Bar │ │ Paginated    │
│ + Paste     │ │ + Stats Grid │ │ Table with   │
│ Toggle      │ │ + Status     │ │ Row Details  │
└─────────────┘ └──────────────┘ └──────────────┘
```

## State Flow Diagram

```
┌─────────┐
│  IDLE   │ ◄────────────────────────┐
└────┬────┘                          │
     │ User submits                  │
     │ (file or URLs)               │ Reset
     ▼                               │
┌───────────┐                        │
│ UPLOADING │                        │
└─────┬─────┘                        │
      │ API Success                  │
      ▼                              │
┌──────────┐                         │
│ POLLING  │◄─────┐                  │
└────┬─────┘      │                  │
     │ Poll every │ Status:          │
     │ 2 seconds  │ running          │
     │            │                  │
     ├────────────┘                  │
     │ Status:                       │
     │ complete/partial/failed       │
     ▼                               │
┌───────────┐                        │
│ COMPLETE  │────────────────────────┘
└───────────┘
     │
     │ Download CSV
     ▼
```

## Data Flow

```
User Input
    │
    ▼
┌──────────────────┐
│ BulkUploadForm   │
│ - Validate       │
│ - Parse URLs     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ API Client           │
│ submitBulkUrlImport  │
└─────────┬────────────┘
          │
          ▼
┌────────────────────────┐
│ Backend API            │
│ POST /api/v1/ingest/   │
│      bulk              │
└───────┬────────────────┘
        │
        │ Returns: bulk_job_id
        ▼
┌───────────────────────┐
│ useBulkIngestionJob   │
│ (React Query Hook)    │
│ - Poll every 2s       │
│ - Cache results       │
└──────┬────────────────┘
       │
       │ Update state
       ▼
┌──────────────────────┐
│ BulkProgressDisplay  │
│ - Progress bar       │
│ - Stats              │
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│ BulkStatusTable      │
│ - Per-URL status     │
│ - Pagination         │
└──────────────────────┘
```

## File Dependencies

```
bulk-import-dialog.tsx
├── bulk-import-types.ts
├── bulk-upload-form.tsx
│   ├── bulk-import-types.ts
│   └── @/components/ui/* (Button, Label, Textarea, Alert)
├── bulk-progress-display.tsx
│   ├── bulk-import-types.ts
│   └── @/components/ui/* (Badge)
├── bulk-status-table.tsx
│   ├── bulk-import-types.ts
│   └── @/components/ui/* (Badge, Button, Table)
├── @/lib/api/bulk-ingestion.ts
│   ├── bulk-import-types.ts
│   └── @/lib/utils (apiFetch)
└── @/hooks/use-bulk-ingestion-job.ts
    ├── bulk-import-types.ts
    └── @/lib/api/bulk-ingestion.ts
```

## Component Responsibilities

### BulkImportDialog
**Role**: Orchestrator
**Responsibilities**:
- Manage overall state machine
- Coordinate child components
- Handle API mutations
- Trigger polling
- Provide callbacks (onSuccess, onError)

### BulkUploadForm
**Role**: Input Handler
**Responsibilities**:
- File upload (drag & drop)
- URL paste input
- Client-side validation
- Mode switching (file/paste)
- Error display

### BulkProgressDisplay
**Role**: Progress Tracker
**Responsibilities**:
- Show progress bar
- Display statistics (total, success, failed, etc.)
- Show elapsed time
- Visual status indicators

### BulkStatusTable
**Role**: Results Display
**Responsibilities**:
- Render per-URL status
- Handle pagination (50 rows/page)
- Provide row actions (view listing, etc.)
- Show error details

### useBulkIngestionJob Hook
**Role**: Data Fetcher
**Responsibilities**:
- Poll backend API every 2 seconds
- Manage React Query cache
- Handle retry logic
- Stop polling when complete

### bulk-ingestion.ts API Client
**Role**: Network Interface
**Responsibilities**:
- Submit file uploads
- Submit pasted URLs
- Fetch job status
- Download CSV results

## API Endpoints Used

```
POST /api/v1/ingest/bulk
├── Input: multipart/form-data (file)
└── Output: { bulk_job_id, total_urls }

GET /api/v1/ingest/bulk/{bulk_job_id}
├── Query: ?offset=0&limit=50
└── Output: BulkIngestionStatusResponse {
    bulk_job_id, status, total_urls,
    completed, success, failed, running, queued,
    per_row_status[], offset, limit, has_more
}
```

## Type Definitions

All TypeScript types are defined in `bulk-import-types.ts`:

```typescript
// Backend response types
BulkIngestionResponse
BulkIngestionStatusResponse
PerRowStatus

// UI state types
BulkImportState
BulkImportMode
BulkImportError

// Component props
BulkImportDialogProps
BulkUploadFormProps
BulkProgressDisplayProps
BulkStatusTableProps
```

## UI Layout

### Dialog Structure
```
┌────────────────────────────────────────────┐
│ Bulk URL Import                      [X]   │
├────────────────────────────────────────────┤
│                                            │
│ [File Upload] [Paste URLs]  ◄─── Toggle   │
│                                            │
│ ┌────────────────────────────────────┐    │
│ │  Drag & drop or browse             │    │
│ │  (or textarea for paste mode)      │    │
│ └────────────────────────────────────┘    │
│                                            │
│          [Import 42 URLs] ◄─── Action     │
│                                            │
├────────────────────────────────────────────┤
│ Progress: 75% ████████████░░░░░            │
│                                            │
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│ │100 │ │ 75 │ │ 15 │ │ 10 │ │ 0  │       │
│ │Tot │ │Suc │ │Fai │ │Run │ │Que │       │
│ └────┘ └────┘ └────┘ └────┘ └────┘       │
│                                            │
├────────────────────────────────────────────┤
│ Per-URL Status (1-50 of 100)               │
│ ┌────────────────────────────────────────┐ │
│ │ URL          Status  ID    Result      │ │
│ ├────────────────────────────────────────┤ │
│ │ ebay.com/... ✓ Done  #123  Success     │ │
│ │ amzn.com/... ⏳ Run   -     Processing  │ │
│ │ shop.com/... ✗ Fail  -     Error       │ │
│ └────────────────────────────────────────┘ │
│              [<] Page 1 of 2 [>]           │
│                                            │
├────────────────────────────────────────────┤
│ [Import Another]    [Download CSV]        │
└────────────────────────────────────────────┘
```

## Accessibility Features

- **Keyboard Navigation**: Tab through all controls
- **Screen Reader**: Live regions announce status
- **ARIA Labels**: All buttons and inputs labeled
- **Focus Management**: Dialog traps focus
- **Color Contrast**: WCAG AA compliant
- **Error Announcements**: Assertive alerts for errors

## Performance Considerations

1. **Pagination**: Only render 50 rows at a time
2. **Memoization**: Prevent unnecessary re-renders
3. **Debouncing**: Validate URLs after typing stops
4. **Polling Interval**: 2 seconds (balance freshness vs. load)
5. **Cache TTL**: 5 minutes (React Query)
6. **Retry Strategy**: Exponential backoff

## Integration Points

This component integrates with:
1. **Backend API** (`/api/v1/ingest/bulk`)
2. **React Query** (server state management)
3. **Radix UI** (accessible primitives)
4. **Tailwind CSS** (styling)
5. **shadcn/ui** (UI component library)
6. **Next.js Router** (navigation to listings)
