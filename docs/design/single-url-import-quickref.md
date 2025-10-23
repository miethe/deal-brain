# Single URL Import Component - Quick Reference
**Task ID-022 Implementation Guide**
**Created**: 2025-10-19

---

## Quick Start

### Step 1: Read Design Documents (30 min)
1. `/mnt/containers/deal-brain/docs/design/single-url-import-summary.md` - Overview
2. `/mnt/containers/deal-brain/docs/design/single-url-import-technical-spec.md` - Code specs
3. `/mnt/containers/deal-brain/docs/design/single-url-import-mockups.md` - Visual reference

### Step 2: Verify Backend Ready (5 min)
```bash
# Start backend
make up

# Test single URL import endpoint
curl -X POST http://localhost:8020/api/v1/ingest/single \
  -H "Content-Type: application/json" \
  -d '{"url": "https://ebay.com/itm/12345"}'

# Expected: { "job_id": "...", "status": "queued" }
```

### Step 3: Create Files (Phase 1 - 8 hours)
```bash
cd /mnt/containers/deal-brain/apps/web

# 1. Types
touch components/ingestion/types.ts
touch components/ingestion/schemas.ts
touch components/ingestion/error-messages.ts

# 2. API Client
touch lib/api/ingestion.ts

# 3. Hook
touch hooks/use-ingestion-job.ts

# 4. Components
touch components/ingestion/single-url-import-form.tsx
touch components/ingestion/ingestion-status-display.tsx
touch components/ingestion/import-success-result.tsx

# 5. Tests
mkdir -p components/ingestion/__tests__
touch components/ingestion/__tests__/single-url-import-form.test.tsx
```

---

## Component Structure Cheat Sheet

### State Machine
```
idle → validating → submitting → polling → success/error
```

### Key State Type
```typescript
type ImportState =
  | { status: 'idle' }
  | { status: 'validating'; url: string }
  | { status: 'submitting'; url: string; priority: ImportPriority }
  | { status: 'polling'; jobId: string; startTime: number }
  | { status: 'success'; result: ImportSuccessResult }
  | { status: 'error'; error: ImportError };
```

### API Endpoints
```typescript
POST /api/v1/ingest/single   → { job_id, status }
GET  /api/v1/ingest/{job_id} → { job_id, status, result?, error? }
```

### Polling Logic
```typescript
refetchInterval: (data) => {
  if (data?.status === 'complete' || data?.status === 'failed') {
    return false; // Stop
  }
  return 2000; // Poll every 2s
}
```

---

## Component Props Quick Reference

### SingleUrlImportForm
```typescript
interface SingleUrlImportFormProps {
  onSuccess?: (result: ImportSuccessResult) => void;
  onError?: (error: ImportError) => void;
  onReset?: () => void;
  defaultUrl?: string;
  defaultPriority?: 'high' | 'standard' | 'low';
  compact?: boolean;  // No card wrapper
  className?: string;
}
```

### IngestionStatusDisplay
```typescript
interface IngestionStatusDisplayProps {
  state: ImportState;
  onCancel?: () => void;
  onRetry?: () => void;
}
```

### ImportSuccessResult
```typescript
interface ImportSuccessResultProps {
  result: ImportSuccessResult;
  onViewListing: () => void;
  onImportAnother: () => void;
}
```

---

## Styling Cheat Sheet

### Colors (Tailwind Classes)
```
Primary:     bg-primary text-primary-foreground
Success:     bg-success text-success-foreground
Error:       bg-destructive text-destructive-foreground
Muted:       bg-muted text-muted-foreground
Card:        bg-card text-card-foreground

Provenance Badges:
- eBay:      bg-blue-100 text-blue-700 border-blue-200
- JSON-LD:   bg-purple-100 text-purple-700 border-purple-200
- Scraper:   bg-gray-100 text-gray-700 border-gray-200

Quality Badges:
- Full:      bg-green-100 text-green-700 border-green-200
- Partial:   bg-amber-100 text-amber-700 border-amber-200
```

### Spacing (8px Grid)
```
Card padding:      p-6    (24px)
Section gap:       space-y-4 (16px)
Field gap:         space-y-2 (8px)
Button gap:        gap-2 (8px)
```

### Typography
```
Card title:        text-2xl font-semibold
Card description:  text-sm text-muted-foreground
Form label:        text-sm font-medium
Input:             text-base (16px)
Error:             text-sm text-destructive
Badge:             text-xs font-medium
```

---

## Testing Checklist

### Unit Tests
- [ ] Form renders correctly
- [ ] URL validation (empty, invalid, valid)
- [ ] Form submission
- [ ] State transitions
- [ ] Error display
- [ ] Success display
- [ ] Progress bar updates
- [ ] Elapsed timer increments

### Accessibility Tests
- [ ] No axe violations
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Screen reader announcements
- [ ] Focus management
- [ ] ARIA labels present
- [ ] Color contrast meets AA (4.5:1)

### Integration Tests
- [ ] Submit → Poll → Success flow
- [ ] Submit → Poll → Error flow
- [ ] Retry on error
- [ ] Cancel polling on unmount
- [ ] Router navigation on success

---

## Common Gotchas

### 1. Polling Cleanup
```typescript
useEffect(() => {
  return () => {
    queryClient.cancelQueries(['ingestion-job', jobId]);
  };
}, [jobId]);
```

### 2. Form Disabled During Submission
```typescript
disabled={importState.status !== 'idle'}
```

### 3. Progress Calculation
```typescript
// Don't use linear progress - use asymptotic
if (elapsed < 5) return 15 + (elapsed / 5) * 35;
else if (elapsed < 15) return 50 + ((elapsed - 5) / 10) * 35;
else return Math.min(95, 85 + ((elapsed - 15) / 30) * 10);
```

### 4. Error Retryability
```typescript
const retryableCodes = ['TIMEOUT', 'RATE_LIMITED', 'NETWORK_ERROR'];
const isRetryable = retryableCodes.includes(error.code);
```

### 5. ARIA Live Regions
```typescript
// Hidden but announced to screen readers
<div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
  {statusMessage}
</div>
```

---

## Code Snippets

### API Client
```typescript
export async function submitSingleUrlImport(
  data: SingleUrlImportRequest
): Promise<SingleUrlImportResponse> {
  return apiFetch<SingleUrlImportResponse>('/v1/ingest/single', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

### Polling Hook
```typescript
export function useIngestionJob({ jobId, enabled, onSuccess, onError }) {
  return useQuery({
    queryKey: ['ingestion-job', jobId],
    queryFn: () => getIngestionJobStatus(jobId),
    enabled: !!jobId && enabled,
    refetchInterval: (data) =>
      (data?.status === 'complete' || data?.status === 'failed') ? false : 2000,
    retry: 3,
    onSuccess,
    onError,
  });
}
```

### Form Validation
```typescript
const urlImportSchema = z.object({
  url: z.string()
    .min(1, 'Please enter a listing URL')
    .url('Please enter a valid URL')
    .max(2048, 'URL is too long'),
  priority: z.enum(['high', 'standard', 'low']).optional().default('standard'),
});
```

### Progress Bar
```typescript
<div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
  <div
    className="h-full bg-primary transition-all duration-300 ease-out"
    style={{ width: `${progress}%` }}
  />
</div>
```

---

## Implementation Order

### Day 1 (4 hours) - Foundation
1. Create type definitions (`types.ts`)
2. Create validation schema (`schemas.ts`)
3. Create API client (`lib/api/ingestion.ts`)
4. Test API calls directly

### Day 2 (4 hours) - Core Component
1. Create main form component skeleton
2. Add URL input with validation
3. Add priority select
4. Wire up form submission
5. Test basic flow

### Day 3 (3 hours) - Polling
1. Create polling hook
2. Add to main component
3. Test polling starts/stops correctly

### Day 4 (3 hours) - Status Display
1. Create status display component
2. Add all state handlers (validating, submitting, polling)
3. Add progress bar
4. Add elapsed timer

### Day 5 (3 hours) - Success & Error
1. Create success result component
2. Add provenance/quality badges
3. Create error display with retry
4. Test all states

### Day 6 (3 hours) - Accessibility & Testing
1. Add ARIA labels
2. Implement focus management
3. Write unit tests
4. Write accessibility tests
5. Run axe audit

---

## Testing Commands

```bash
# Run all tests
pnpm test

# Run specific test file
pnpm test components/ingestion/__tests__/single-url-import-form.test.tsx

# Run with coverage
pnpm test --coverage

# Run accessibility tests
pnpm test:a11y

# Watch mode (during development)
pnpm test:watch
```

---

## Verification Checklist

### Before Submitting PR
- [ ] All tests pass
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Accessibility audit passes (0 violations)
- [ ] Works on mobile (< 640px)
- [ ] Works in dark mode
- [ ] Keyboard navigation works
- [ ] Screen reader tested (basic)
- [ ] Error states work
- [ ] Success state works
- [ ] Retry button works
- [ ] Navigation to listing works
- [ ] Form resets properly
- [ ] Code formatted (Prettier)
- [ ] No console errors

### Performance Checks
- [ ] Bundle size reasonable (<30KB)
- [ ] No unnecessary re-renders
- [ ] Debouncing works (validation)
- [ ] Polling stops when complete
- [ ] Cleanup on unmount

---

## Useful Links

- Design Summary: `/mnt/containers/deal-brain/docs/design/single-url-import-summary.md`
- Technical Spec: `/mnt/containers/deal-brain/docs/design/single-url-import-technical-spec.md`
- Visual Mockups: `/mnt/containers/deal-brain/docs/design/single-url-import-mockups.md`
- Backend API Docs: `/mnt/containers/deal-brain/docs/project_plans/url-ingest/implementation-plan.md`
- shadcn/ui Docs: https://ui.shadcn.com
- React Query Docs: https://tanstack.com/query/latest

---

## Getting Help

If stuck:
1. Check technical spec for detailed implementation
2. Look at existing Deal Brain components for patterns
3. Test API endpoints with curl/Postman
4. Review shadcn/ui component examples
5. Check React Query polling examples

---

**Quick Reference Version**: 1.0
**Last Updated**: 2025-10-19
