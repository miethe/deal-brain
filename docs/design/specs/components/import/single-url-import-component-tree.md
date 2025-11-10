# Single URL Import Component - Component Tree
**Visual Reference for Task ID-022**
**Created**: 2025-10-19

---

## Component Hierarchy

```
SingleUrlImportForm (Smart Component)
│
├─ Props:
│  ├─ onSuccess?: (result) => void
│  ├─ onError?: (error) => void
│  ├─ onReset?: () => void
│  ├─ defaultUrl?: string
│  ├─ defaultPriority?: ImportPriority
│  ├─ compact?: boolean
│  └─ className?: string
│
├─ State:
│  ├─ importState: ImportState (idle|validating|submitting|polling|success|error)
│  └─ form: useForm() with react-hook-form
│
├─ Hooks:
│  ├─ useForm() - Form validation
│  ├─ useMutation() - Submit URL import
│  ├─ useIngestionJob() - Poll job status
│  └─ useRouter() - Navigation
│
└─ Children:
   │
   ├─ Card (if !compact) or div (if compact)
   │  │
   │  ├─ CardHeader
   │  │  ├─ CardTitle: "Import from URL"
   │  │  └─ CardDescription: "Paste a listing URL..."
   │  │
   │  ├─ CardContent
   │  │  │
   │  │  └─ form (onSubmit={handleSubmit(onSubmit)})
   │  │     │
   │  │     ├─ URL Input Field
   │  │     │  ├─ Label: "Listing URL *"
   │  │     │  ├─ Input
   │  │     │  │  ├─ type="url"
   │  │     │  │  ├─ placeholder="https://www.ebay.com/itm/..."
   │  │     │  │  ├─ disabled={importState.status !== 'idle'}
   │  │     │  │  └─ aria-invalid={!!errors.url}
   │  │     │  ├─ Error message (if errors.url)
   │  │     │  └─ Help text: "Supports eBay, Amazon..."
   │  │     │
   │  │     ├─ Priority Select
   │  │     │  ├─ Label: "Priority (optional)"
   │  │     │  └─ Select
   │  │     │     ├─ SelectTrigger
   │  │     │     │  └─ SelectValue
   │  │     │     └─ SelectContent
   │  │     │        ├─ SelectItem: "High - Process immediately"
   │  │     │        ├─ SelectItem: "Standard - Normal queue"
   │  │     │        └─ SelectItem: "Low - Background processing"
   │  │     │
   │  │     └─ IngestionStatusDisplay (if state !== 'idle')
   │  │        └─ [See IngestionStatusDisplay tree below]
   │  │
   │  └─ CardFooter (if state === 'idle')
   │     ├─ Button: "Reset" (variant=outline)
   │     └─ Button: "Import Listing" (type=submit)
   │
   └─ ARIA Live Region (hidden)
      └─ role="status", aria-live="polite"
```

---

## IngestionStatusDisplay Component

```
IngestionStatusDisplay (Presentational)
│
├─ Props:
│  ├─ state: ImportState
│  ├─ onRetry?: () => void
│  ├─ onViewListing?: () => void
│  └─ onImportAnother?: () => void
│
├─ Internal State:
│  └─ elapsed: number (seconds, updated every 1s)
│
└─ Conditional Rendering (based on state.status):
   │
   ├─ if status === 'validating':
   │  └─ Alert
   │     ├─ Loader2 icon (spinning)
   │     └─ AlertTitle: "Validating URL..."
   │
   ├─ if status === 'submitting':
   │  └─ Alert
   │     ├─ Loader2 icon (spinning)
   │     ├─ AlertTitle: "Creating import job..."
   │     └─ AlertDescription: "This usually takes a few seconds"
   │
   ├─ if status === 'polling':
   │  └─ Alert (primary themed)
   │     ├─ Loader2 icon (spinning)
   │     ├─ AlertTitle: "Importing listing..."
   │     ├─ Badge: "{elapsed}s elapsed"
   │     ├─ Progress bar
   │     │  ├─ Background: muted
   │     │  ├─ Fill: primary (animated)
   │     │  └─ Percentage text: "{progress}%"
   │     ├─ Status message (changes based on elapsed time)
   │     └─ ARIA live region (screen reader only)
   │
   ├─ if status === 'success':
   │  └─ ImportSuccessResult
   │     └─ [See ImportSuccessResult tree below]
   │
   └─ if status === 'error':
      └─ Alert (destructive variant)
         ├─ AlertCircle icon
         ├─ AlertTitle: "Import failed"
         ├─ AlertDescription
         │  ├─ Error message text
         │  ├─ details element (expandable)
         │  │  ├─ summary: "Show technical details"
         │  │  └─ pre: JSON.stringify(error.details)
         │  └─ Button: "Try Again" (if retryable)
         │     └─ RotateCcw icon
         └─ ARIA alert region (screen reader only)
```

---

## ImportSuccessResult Component

```
ImportSuccessResult (Presentational)
│
├─ Props:
│  ├─ result: ImportSuccessResult
│  ├─ onViewListing: () => void
│  └─ onImportAnother: () => void
│
└─ Children:
   │
   └─ Alert (success themed)
      ├─ CheckCircle2 icon (green)
      ├─ AlertTitle: "Listing imported successfully!"
      └─ AlertDescription
         │
         ├─ Listing Preview Card (bordered, bg-card)
         │  │
         │  ├─ Header Row
         │  │  ├─ h4: {result.title} (line-clamp-2)
         │  │  └─ Badge: "#{result.listingId}"
         │  │
         │  └─ Metadata Row
         │     ├─ Provenance Badge
         │     │  ├─ Database icon
         │     │  └─ "EBAY API" | "JSON-LD" | "SCRAPER"
         │     ├─ Quality Badge
         │     │  ├─ CheckCircle2 | AlertCircle icon
         │     │  └─ "Full data" | "Partial data"
         │     └─ Timestamp: "Just now" | "2 minutes ago"
         │
         ├─ Partial Data Warning Alert (if quality === 'partial')
         │  ├─ AlertCircle icon (blue)
         │  └─ "Some details may be missing..."
         │
         ├─ Action Buttons Row
         │  ├─ Button: "View Listing" (outline, flex-1)
         │  │  └─ ExternalLink icon
         │  └─ Button: "Import Another" (primary, flex-1)
         │
         └─ ARIA status region (screen reader only)
```

---

## Data Flow

### 1. Form Submission Flow
```
User enters URL
    ↓
Validation (Zod schema)
    ↓
User clicks "Import Listing"
    ↓
handleSubmit(onSubmit) triggered
    ↓
submitMutation.mutate({ url, priority })
    ↓
setImportState({ status: 'submitting' })
    ↓
API: POST /v1/ingest/single
    ↓
Response: { job_id, status }
    ↓
setImportState({ status: 'polling', jobId, startTime })
```

### 2. Polling Flow
```
State changes to 'polling'
    ↓
useIngestionJob hook activates (enabled=true)
    ↓
useQuery starts with refetchInterval=2000ms
    ↓
Every 2 seconds:
    API: GET /v1/ingest/{job_id}
    ↓
    Response: { status, result?, error? }
    ↓
    if status === 'complete':
        setImportState({ status: 'success', result })
    else if status === 'failed':
        setImportState({ status: 'error', error })
    else:
        Continue polling
```

### 3. Success Flow
```
State changes to 'success'
    ↓
ImportSuccessResult renders
    ↓
User clicks "View Listing"
    ↓
onViewListing() called
    ↓
router.push(`/listings/${listingId}`)
```

---

## Props Flow Diagram

```
Parent Component (e.g., ListingsPage)
    │
    ├─ onSuccess={(result) => {
    │    toast.success(`Listing #${result.listingId} imported!`);
    │    router.push(`/listings/${result.listingId}`);
    │  }}
    │
    ├─ onError={(error) => {
    │    toast.error(`Import failed: ${error.message}`);
    │  }}
    │
    └─ onReset={() => {
         // Optional cleanup
       }}
         ↓
SingleUrlImportForm
    │
    ├─ Internal: submitMutation → submitSingleUrlImport(data)
    │
    ├─ Internal: useIngestionJob({ jobId, onSuccess, onError })
    │
    └─ Passes to children:
       │
       ├→ IngestionStatusDisplay
       │    ├─ state={importState}
       │    ├─ onRetry={handleRetry}
       │    └─ Conditionally renders:
       │       │
       │       └→ ImportSuccessResult
       │            ├─ result={importState.result}
       │            ├─ onViewListing={handleViewListing}
       │            └─ onImportAnother={handleReset}
       │
       └→ Form Buttons
            ├─ "Reset" → handleReset()
            └─ "Import Listing" → handleSubmit(onSubmit)
```

---

## State Management Layers

### Layer 1: Form State (React Hook Form)
```
useForm({
  resolver: zodResolver(urlImportSchema),
  defaultValues: { url: '', priority: 'standard' },
  mode: 'onBlur',
})
    ↓
Manages:
- URL input value
- Priority select value
- Validation errors
- Form submission
```

### Layer 2: Import State (useState)
```
const [importState, setImportState] = useState<ImportState>({ status: 'idle' });
    ↓
Manages:
- Current step in import flow (idle → validating → submitting → polling → success/error)
- Job ID (when polling)
- Start time (for elapsed timer)
- Result data (on success)
- Error data (on failure)
```

### Layer 3: API State (React Query)
```
useMutation() for submit
    ↓
Manages:
- POST request to create job
- Loading state
- Error handling
- Retry logic

useQuery() for polling
    ↓
Manages:
- GET requests to check status
- Automatic refetching (every 2s)
- Cache management
- Stale data handling
```

---

## Hook Dependencies

```
SingleUrlImportForm
    │
    ├─ useForm() (react-hook-form)
    │  └─ Triggers: zodResolver(urlImportSchema)
    │
    ├─ useMutation() (@tanstack/react-query)
    │  ├─ mutationFn: submitSingleUrlImport
    │  ├─ onMutate: setImportState({ status: 'submitting' })
    │  ├─ onSuccess: setImportState({ status: 'polling', jobId })
    │  └─ onError: setImportState({ status: 'error', error })
    │
    ├─ useIngestionJob() (custom hook)
    │  │
    │  └─ useQuery() (@tanstack/react-query)
    │     ├─ queryKey: ['ingestion-job', jobId]
    │     ├─ queryFn: getIngestionJobStatus(jobId)
    │     ├─ enabled: !!jobId && importState.status === 'polling'
    │     ├─ refetchInterval: 2000ms (or false if complete)
    │     ├─ onSuccess: handle success/error state
    │     └─ onError: setImportState({ status: 'error' })
    │
    ├─ useRouter() (next/navigation)
    │  └─ Used for: router.push(`/listings/${listingId}`)
    │
    └─ useEffect() (IngestionStatusDisplay)
       └─ Updates elapsed timer every 1s when polling
```

---

## Event Handlers

### Main Component Events
```typescript
// Form submission
const onSubmit = (data: UrlImportFormData) => {
  submitMutation.mutate({ url: data.url, priority: data.priority });
};

// Reset form and state
const handleReset = () => {
  resetForm();
  setImportState({ status: 'idle' });
  onReset?.();
};

// Retry after error
const handleRetry = () => {
  const url = watch('url');
  const priority = watch('priority');
  submitMutation.mutate({ url, priority });
};

// Navigate to listing
const handleViewListing = () => {
  if (importState.status === 'success') {
    router.push(`/listings/${importState.result.listingId}`);
  }
};
```

### Status Display Events
```typescript
// Elapsed timer (in IngestionStatusDisplay)
useEffect(() => {
  if (state.status === 'polling') {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - state.startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }
}, [state]);
```

---

## CSS Class Patterns

### Layout Classes
```
Container:      max-w-2xl mx-auto py-8
Card:           rounded-lg border bg-card shadow-sm
Spacing:        space-y-4 (vertical) or gap-2 (flexbox)
Padding:        p-6 (card), p-3 (preview), p-2 (badge)
```

### State-Based Classes
```
Input (normal):   border-input
Input (error):    border-destructive
Input (disabled): opacity-50 cursor-not-allowed
Button (disabled): pointer-events-none opacity-50
```

### Animation Classes
```
Spinner:        animate-spin
Progress:       transition-all duration-300 ease-out
Alert:          animate-in slide-in-from-top-2
Success icon:   animate-in zoom-in-95
```

---

## Accessibility Tree

```
form (role="form", aria-label="Import listing from URL")
│
├─ Input (role="textbox")
│  ├─ aria-label="Listing URL"
│  ├─ aria-required="true"
│  ├─ aria-invalid={!!errors.url}
│  └─ aria-describedby="url-help url-error"
│
├─ Select (role="combobox")
│  ├─ aria-label="Import priority"
│  └─ aria-expanded={open}
│
├─ Alert (role="status" or role="alert")
│  ├─ For informational: aria-live="polite"
│  └─ For errors: aria-live="assertive"
│
└─ Buttons
   ├─ "Reset" (role="button")
   ├─ "Import Listing" (role="button", aria-disabled={!isValid})
   ├─ "Try Again" (role="button")
   ├─ "View Listing" (role="button")
   └─ "Import Another" (role="button")
```

---

## Component Files Summary

### Total Files: 9

1. **types.ts** (~80 lines)
   - All TypeScript interfaces and types
   - No dependencies

2. **schemas.ts** (~20 lines)
   - Zod validation schemas
   - Depends on: zod

3. **error-messages.ts** (~30 lines)
   - Error code to message mapping
   - No dependencies

4. **lib/api/ingestion.ts** (~40 lines)
   - API client functions
   - Depends on: utils.ts (apiFetch)

5. **hooks/use-ingestion-job.ts** (~60 lines)
   - Custom polling hook
   - Depends on: @tanstack/react-query, api/ingestion.ts

6. **single-url-import-form.tsx** (~250 lines)
   - Main smart component
   - Depends on: all above + UI components

7. **ingestion-status-display.tsx** (~180 lines)
   - Status UI component
   - Depends on: types.ts, UI components

8. **import-success-result.tsx** (~120 lines)
   - Success card component
   - Depends on: types.ts, UI components, date-fns

9. **__tests__/single-url-import-form.test.tsx** (~150 lines)
   - Test suite
   - Depends on: @testing-library/react, jest

**Total Lines of Code**: ~930 lines

---

## Dependency Graph

```
┌─────────────────────┐
│   External Deps     │
└─────────────────────┘
    │
    ├─ react
    ├─ react-hook-form
    ├─ @hookform/resolvers
    ├─ zod
    ├─ @tanstack/react-query
    ├─ next/navigation
    ├─ lucide-react
    ├─ date-fns
    └─ class-variance-authority
         │
         ↓
┌─────────────────────┐
│  Shared Utilities   │
└─────────────────────┘
    │
    ├─ lib/utils.ts (cn, apiFetch)
    └─ components/ui/* (shadcn)
         │
         ↓
┌─────────────────────┐
│   Types & Schemas   │
└─────────────────────┘
    │
    ├─ types.ts
    ├─ schemas.ts
    └─ error-messages.ts
         │
         ↓
┌─────────────────────┐
│   API & Hooks       │
└─────────────────────┘
    │
    ├─ lib/api/ingestion.ts
    └─ hooks/use-ingestion-job.ts
         │
         ↓
┌─────────────────────┐
│    Components       │
└─────────────────────┘
    │
    ├─ import-success-result.tsx
    ├─ ingestion-status-display.tsx
    └─ single-url-import-form.tsx
```

---

**Component Tree Version**: 1.0
**Last Updated**: 2025-10-19
**Purpose**: Visual reference for component structure and relationships
