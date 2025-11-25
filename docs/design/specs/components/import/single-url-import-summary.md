# Single URL Import Component - Design Summary
**Task ID-022: Frontend Import Component**
**Created**: 2025-10-19
**Status**: Design Complete - Ready for Implementation

---

## Executive Summary

This design package provides comprehensive specifications for implementing the Single URL Import component for Deal Brain's URL ingestion feature (Phase 4). The component enables users to import PC listings from marketplace URLs with minimal friction, clear status visibility, and full accessibility compliance.

**Key Achievement**: User can paste URL and import in <3 clicks with real-time status updates.

---

## Design Deliverables

### 1. Component Architecture Design
**File**: `/mnt/containers/deal-brain/docs/design/single-url-import-design.md`

**Contents**:
- Component hierarchy and composition strategy
- State management approach (React Query + local state)
- 6 distinct component states (idle, validating, submitting, polling, success, error)
- Accessibility considerations (WCAG 2.1 AA compliance)
- Error handling strategy with retry logic
- Performance optimizations (memoization, debouncing)
- Integration points (API endpoints, React Query)
- Testing strategy (unit, integration, accessibility)

**Key Decisions**:
- Card-based layout for visual consistency
- Polling-based status updates (2s interval)
- Inline status display (progressive disclosure)
- Debounced URL validation (300ms)
- Separate success result component (reusability)

### 2. Visual Design Mockups
**File**: `/mnt/containers/deal-brain/docs/design/single-url-import-mockups.md`

**Contents**:
- 10 detailed ASCII mockups covering all states
- Mobile responsive layouts (<640px breakpoints)
- Dark mode variant specifications
- Animation specifications (timing, easing, keyframes)
- Typography scale (font sizes, weights, line heights)
- Spacing system (8px grid)
- Color system (semantic tokens)
- Micro-interactions (hover, focus, active states)
- Accessibility checklist

**Highlights**:
- Progress bar with shimmer animation
- Provenance badges (eBay API, JSON-LD, Scraper)
- Quality indicators (Full, Partial data)
- Error states with retry options
- Success card with listing preview

### 3. Technical Specification
**File**: `/mnt/containers/deal-brain/docs/design/single-url-import-technical-spec.md`

**Contents**:
- Complete TypeScript type definitions
- Zod validation schema
- API client functions (submit, poll, cancel)
- React Query polling hook implementation
- Full component implementations (3 components)
- Error message mapping
- Testing requirements (unit, accessibility, integration)
- Performance considerations (code splitting, memoization)
- Integration examples

**Code Structure**:
```
apps/web/components/ingestion/
├── single-url-import-form.tsx    (Main component - 250 lines)
├── ingestion-status-display.tsx  (Status UI - 180 lines)
├── import-success-result.tsx     (Success card - 120 lines)
├── types.ts                      (TypeScript definitions - 80 lines)
├── schemas.ts                    (Zod validation - 20 lines)
├── error-messages.ts             (Error mapping - 30 lines)
└── __tests__/                    (Test files)
```

---

## Component States Flow

```
                    ┌─────────┐
                    │  Idle   │
                    └────┬────┘
                         │ User submits URL
                         ↓
                  ┌──────────────┐
                  │ Validating   │ (300ms debounce)
                  └──────┬───────┘
                         │ Valid
                         ↓
                  ┌──────────────┐
                  │ Submitting   │ (POST /ingest/single)
                  └──────┬───────┘
                         │ Job created
                         ↓
                  ┌──────────────┐
                  │   Polling    │ (GET /ingest/{job_id} every 2s)
                  └──────┬───────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         ┌────↓────┐          ┌────↓────┐
         │ Success │          │  Error  │
         └─────────┘          └─────────┘
              │                     │
              │                     ↓
              │              ┌──────────────┐
              │              │ Retry Option │
              │              └──────┬───────┘
              │                     │
              └─────────────────────┘
                         ↓
                  Back to Idle (reset)
```

---

## Key Design Principles

### 1. Speed & Efficiency
- Form submission in 1-2 clicks
- Real-time validation (debounced)
- Optimistic UI updates
- Efficient polling (stops when complete)

### 2. Clarity & Feedback
- Clear status messages at each step
- Progress indicator with elapsed time
- Detailed error messages with retry options
- Success preview with metadata

### 3. Accessibility First
- Full keyboard navigation support
- Screen reader announcements (ARIA live regions)
- WCAG 2.1 AA color contrast
- Focus management (predictable flow)

### 4. Consistency
- Uses existing shadcn/ui components
- Follows Deal Brain design tokens
- Matches listings page patterns
- Responsive across all breakpoints

### 5. Extensibility
- Modular component structure
- Reusable success/error components
- Configurable via props
- Easy to add bulk import UI later

---

## State Management Strategy

### Local State (useState)
```typescript
const [importState, setImportState] = useState<ImportState>({ status: 'idle' });
```
**Used for**: Component-level state machine (idle → polling → success/error)

### React Hook Form
```typescript
const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(urlImportSchema),
});
```
**Used for**: Form validation, field management

### React Query (TanStack Query)
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['ingestion-job', jobId],
  queryFn: () => getIngestionJobStatus(jobId),
  refetchInterval: 2000,
});
```
**Used for**: API calls, polling, caching, retry logic

---

## API Integration

### Endpoints Used

**1. Submit Single URL Import**
```
POST /api/v1/ingest/single
Request: { url: string, priority?: 'high' | 'standard' | 'low' }
Response: { job_id: string, status: 'queued' }
```

**2. Poll Job Status**
```
GET /api/v1/ingest/{job_id}
Response: {
  job_id: string,
  status: 'queued' | 'running' | 'complete' | 'failed',
  result?: { listing_id, provenance, quality, ... },
  error?: { code, message, details }
}
```

**3. Cancel Job (Optional)**
```
DELETE /api/v1/ingest/{job_id}
Response: 204 No Content
```

---

## Accessibility Features

### Keyboard Navigation
- **Tab**: Move between fields and buttons
- **Enter**: Submit form (when in URL field)
- **Escape**: Clear form / dismiss errors
- **Arrow keys**: Navigate select options

### Screen Reader Support
- All form fields have proper labels
- Error messages linked via `aria-describedby`
- Status updates announced via `aria-live="polite"`
- Success/error alerts use `role="status"` and `role="alert"`

### Visual Accessibility
- 4.5:1 contrast ratio for all text
- Focus indicators on all interactive elements
- No color-only indicators (icons + text)
- Consistent focus ring (2px primary color)

### Cognitive Accessibility
- Clear, simple language
- Predictable interactions
- Helpful error messages
- Visual progress indicators

---

## Error Handling

### Error Categories

**1. Validation Errors** (Client-side)
- Empty URL
- Invalid URL format
- URL too long (>2048 chars)

**2. Submission Errors** (Network)
- Failed to create job
- Network timeout
- Server unavailable

**3. Processing Errors** (Adapter)
- `TIMEOUT`: Marketplace slow to respond
- `INVALID_SCHEMA`: Cannot extract data
- `ITEM_NOT_FOUND`: Listing doesn't exist
- `RATE_LIMITED`: Too many requests
- `ADAPTER_DISABLED`: Integration disabled

### Retry Strategy

**Retryable Errors**:
- TIMEOUT
- RATE_LIMITED
- NETWORK_ERROR
- TEMPORARY_ERROR

**Non-retryable Errors**:
- INVALID_SCHEMA
- ITEM_NOT_FOUND
- ADAPTER_DISABLED
- VALIDATION_ERROR

---

## Performance Optimizations

### 1. Code Splitting
```typescript
const SingleUrlImportForm = dynamic(
  () => import('./single-url-import-form'),
  { loading: () => <Skeleton /> }
);
```

### 2. Component Memoization
```typescript
export const StatusDisplay = memo(StatusDisplay, (prev, next) => {
  return prev.state.status === next.state.status;
});
```

### 3. Debounced Validation
```typescript
const debouncedValidate = useMemo(
  () => debounce((url) => validateUrl(url), 300),
  []
);
```

### 4. Optimized Polling
- Starts at 2s interval
- Stops when job complete
- Exponential backoff on errors
- Automatic cleanup on unmount

---

## Testing Coverage

### Unit Tests (12 tests)
- Form field rendering
- URL validation (valid, invalid, empty)
- Form submission
- State transitions
- Error display
- Success display

### Accessibility Tests (6 tests)
- No axe violations
- Keyboard navigation works
- Screen reader announcements
- Focus management
- ARIA labels correct
- Color contrast meets AA

### Integration Tests (4 tests)
- Full import flow (submit → poll → success)
- Error handling with retry
- Cancel import (if supported)
- Redirect to listing on success

**Total**: 22 tests, targeting 90%+ coverage

---

## Implementation Phases

### Phase 1: Core Component (8 hours)
**Deliverables**:
- Type definitions and schemas
- API client functions
- Main form component
- Basic validation

**Acceptance Criteria**:
- Form renders correctly
- URL validation works
- Can submit to API
- Basic error handling

### Phase 2: Status Polling (6 hours)
**Deliverables**:
- Polling hook with React Query
- Status display component
- Progress indicator
- Elapsed timer

**Acceptance Criteria**:
- Polling starts on submit
- Progress bar animates
- Stops when complete
- Shows correct messages

### Phase 3: Success & Error States (4 hours)
**Deliverables**:
- Success result component
- Provenance/quality badges
- Error display with retry
- Error message mapping

**Acceptance Criteria**:
- Success card displays correctly
- Badges show right colors/icons
- Errors are user-friendly
- Retry button works

### Phase 4: Accessibility & Polish (2 hours)
**Deliverables**:
- ARIA labels and roles
- Focus management
- Keyboard navigation
- Screen reader testing

**Acceptance Criteria**:
- Passes axe audit (0 violations)
- Keyboard-only navigation works
- Screen reader announces changes
- Meets WCAG 2.1 AA

---

## Design Decisions & Rationale

### Why Polling Instead of WebSockets?
- Simpler implementation (no WebSocket infrastructure)
- Matches existing backend job tracking pattern
- More resilient to network interruptions
- Easier to test and debug
- Adequate for <10s job latency

### Why Inline Status Display?
- Keeps user focused in one place
- Reduces cognitive load (no modal switching)
- Follows progressive disclosure pattern
- Easier to implement accessible focus management
- Better mobile experience

### Why Card Container?
- Provides visual boundary and structure
- Consistent with existing Deal Brain UI
- Works well in both standalone and embedded contexts
- Easy to make responsive
- Supports compact mode for dialogs

### Why Separate Success Component?
- Reusable in bulk import UI
- Easier to test in isolation
- Cleaner code organization
- Allows future enhancements (share, edit)
- Can be used in other contexts (notifications, etc.)

---

## Integration Points

### Listings Page
Add import dialog or inline form:
```tsx
<Dialog>
  <DialogTrigger>Import from URL</DialogTrigger>
  <DialogContent>
    <SingleUrlImportForm
      compact
      onSuccess={(result) => {
        router.push(`/listings/${result.listingId}`);
        router.refresh();
      }}
    />
  </DialogContent>
</Dialog>
```

### Dedicated Import Page
Standalone page for URL import:
```tsx
// app/import/page.tsx
export default function ImportPage() {
  return (
    <div className="container max-w-2xl py-8">
      <SingleUrlImportForm />
    </div>
  );
}
```

### Bulk Import UI (Future)
Reuse success component:
```tsx
<BulkImportTable>
  {results.map(result => (
    <ImportSuccessResult
      key={result.jobId}
      result={result}
      {...handlers}
    />
  ))}
</BulkImportTable>
```

---

## Future Enhancements

### Phase 5+ (Post-MVP)
1. **URL Auto-detection**: Detect URL in clipboard on focus
2. **Recent URLs**: Show dropdown of recently imported URLs
3. **Batch Mode**: Allow multiple URLs (one per line)
4. **Duplicate Detection**: Warn if URL already imported
5. **Preview Mode**: Show scraped data before confirming
6. **Custom Fields**: Map scraped data to custom fields
7. **Schedule Import**: Set future import time
8. **Webhook Integration**: Trigger webhook on completion

---

## Dependencies

### NPM Packages (Existing)
- `react` ^18.x
- `react-hook-form` ^7.x
- `@hookform/resolvers` ^3.x
- `zod` ^3.x
- `@tanstack/react-query` ^5.x
- `lucide-react` (icons)
- `class-variance-authority` (button variants)
- `date-fns` (date formatting)

### shadcn/ui Components (Existing)
- Card
- Button
- Input
- Select
- Label
- Alert
- Badge

### Backend APIs (Phase 3 Complete)
- POST `/api/v1/ingest/single`
- GET `/api/v1/ingest/{job_id}`

---

## Success Metrics

### User Experience
- Time to import: <10 seconds for eBay URLs
- Error rate: <5% (excluding invalid URLs)
- User satisfaction: Measured via feedback

### Technical Performance
- First render: <100ms
- Form submission: <500ms (network excluded)
- Polling overhead: <50ms per request
- Bundle size: <30KB (component + deps)

### Accessibility
- 0 axe violations
- 100% keyboard navigable
- All states announced to screen readers
- 4.5:1+ contrast ratio on all text

### Code Quality
- 90%+ test coverage
- 0 TypeScript errors
- 0 ESLint errors
- Passes all accessibility tests

---

## Documentation

### For Developers
- Type definitions with JSDoc comments
- README with usage examples
- Storybook stories (future)
- API integration guide

### For Users
- Help tooltip on URL input
- Error messages with actionable guidance
- Success message with next steps
- FAQ page (future)

---

## File Locations (Absolute Paths)

### Design Documents
- Main Design: `/mnt/containers/deal-brain/docs/design/single-url-import-design.md`
- Visual Mockups: `/mnt/containers/deal-brain/docs/design/single-url-import-mockups.md`
- Technical Spec: `/mnt/containers/deal-brain/docs/design/single-url-import-technical-spec.md`
- This Summary: `/mnt/containers/deal-brain/docs/design/single-url-import-summary.md`

### Implementation Files (To Be Created)
- Main Component: `/mnt/containers/deal-brain/apps/web/components/ingestion/single-url-import-form.tsx`
- Status Display: `/mnt/containers/deal-brain/apps/web/components/ingestion/ingestion-status-display.tsx`
- Success Result: `/mnt/containers/deal-brain/apps/web/components/ingestion/import-success-result.tsx`
- Types: `/mnt/containers/deal-brain/apps/web/components/ingestion/types.ts`
- Schemas: `/mnt/containers/deal-brain/apps/web/components/ingestion/schemas.ts`
- Error Messages: `/mnt/containers/deal-brain/apps/web/components/ingestion/error-messages.ts`
- API Client: `/mnt/containers/deal-brain/apps/web/lib/api/ingestion.ts`
- Polling Hook: `/mnt/containers/deal-brain/apps/web/hooks/use-ingestion-job.ts`
- Tests: `/mnt/containers/deal-brain/apps/web/components/ingestion/__tests__/`

---

## Next Steps

### For Implementation Team

1. **Review Design Package**
   - Read all three design documents
   - Ask questions if anything unclear
   - Confirm technical approach

2. **Set Up Development Environment**
   - Ensure backend Phase 3 is running
   - Test API endpoints with Postman/curl
   - Verify React Query is configured

3. **Start Phase 1 Implementation**
   - Create type definitions
   - Set up API client
   - Build main form component
   - Add validation

4. **Incremental Development**
   - Complete one phase at a time
   - Test thoroughly after each phase
   - Update progress tracker
   - Commit with clear messages

5. **Final Testing & Polish**
   - Run full test suite
   - Accessibility audit
   - Cross-browser testing
   - Mobile responsive check

### Estimated Timeline
- **Phase 1**: 2 work sessions (8 hours)
- **Phase 2**: 1.5 work sessions (6 hours)
- **Phase 3**: 1 work session (4 hours)
- **Phase 4**: 0.5 work session (2 hours)

**Total**: ~5 focused work sessions over 1-2 weeks

---

## Support & Questions

If you have questions during implementation:

1. Check the three design documents for details
2. Review existing shadcn/ui components for patterns
3. Test API endpoints directly to understand behavior
4. Refer to Phase 3 backend code for expected responses
5. Look at existing Deal Brain components for consistency

---

**Design Status**: Complete and Ready for Implementation
**Confidence Level**: High - All requirements addressed with detailed specs
**Risk Level**: Low - Well-defined scope, proven patterns, existing backend

---

**Design Team**: UI Designer (Claude Code)
**Review Date**: 2025-10-19
**Approved By**: Ready for development team review
