# Phase 4 Progress: Frontend - Real-Time UI Updates

**Status**: Not Started
**Last Updated**: 2025-11-08
**Completion**: 0%

## Overview

Phase 4 implements real-time tracking of bulk import progress. Users see live progress bars, per-URL status, toast notifications for key events, and automatic data refresh after completion.

**Duration**: 2-3 days
**Dependencies**: Phase 2 complete (API endpoints), Phase 3 complete (Modal)
**Risk Level**: Low (polling + UI updates)

## Task Breakdown

### Task 4.1: Create useImportPolling Hook
- **File**: `apps/web/hooks/useImportPolling.ts`
- **Duration**: 3-4 hours
- **Status**: Not Started
- [ ] Polls `/api/v1/ingest/bulk/{bulkJobId}/status` every 2 seconds
- [ ] Stops polling when job status is `complete`
- [ ] Emits `onStatusChange` callback on each status update
- [ ] Emits `onPartialFound` callback when partial import detected
- [ ] Emits `onComplete` callback when entire job completes
- [ ] Dispatches `import-partial-found` custom event for modal integration
- [ ] Dispatches `import-job-complete` custom event for notifications
- [ ] Calculates progress percentage correctly (`completed / total_urls * 100`)
- [ ] Handles API errors gracefully (retries or cancels polling)
- [ ] Can be disabled via `enabled` prop
- [ ] React Query integration (refetchInterval, staleTime, gcTime)
- [ ] No memory leaks (cleanup refs on unmount, tracking detected partials)
- [ ] TypeScript types complete (BulkImportStatus, PerRowImportStatus)
- [ ] Unit tests pass (polling behavior, event emission, error handling)
- [ ] Variant: `useImportPollingWithPagination` for large imports (if needed)

### Task 4.2: Create BulkImportProgress Component
- **File**: `apps/web/components/imports/BulkImportProgress.tsx`
- **Duration**: 2-3 hours
- **Status**: Not Started
- [ ] Displays overall progress bar (0-100%)
- [ ] Shows progress percentage text
- [ ] Displays status count grid (Total, Complete, Partial, Running, Failed)
- [ ] Each status card has icon and color-coded background
- [ ] Shows recent URLs with individual status badges
- [ ] Quality badges display (Complete/Needs Data/Pending)
- [ ] Updates in real-time as status prop changes
- [ ] Performance optimized (memoization to prevent re-renders)
- [ ] Responsive design (2-col on mobile, 5-col on desktop)
- [ ] Color accessibility (WCAG AA contrast ratios)
- [ ] Completion message shown when job completes
- [ ] Max height on URL list with overflow scroll
- [ ] Unit tests pass (rendering, status counts, quality badges)

### Task 4.3: Create ImportNotifications Component
- **File**: `apps/web/components/imports/ImportNotifications.tsx`
- **Duration**: 2-3 hours
- **Status**: Not Started
- [ ] Listens for `import-partial-found` custom event
- [ ] Shows toast: "Data Needed - Please provide missing data for one listing"
- [ ] Listens for `import-job-complete` custom event
- [ ] Shows toast with summary (success count, partial count, fail count)
- [ ] Toast messages are clear and actionable
- [ ] Multiple toasts don't overlap
- [ ] Toast auto-dismisses after 5 seconds
- [ ] Accessible to screen readers (role=alert, aria-live)
- [ ] Integrates with existing toast system (`use-toast` hook)
- [ ] Unit tests pass (event listeners, toast triggers)

## Completed Tasks

(None yet)

## In Progress

(None yet)

## Blocked

(None yet)

## Next Actions

1. Create `useImportPolling` hook with polling logic and event emission
2. Add comprehensive unit tests for hook (polling, events, errors)
3. Create `BulkImportProgress` component with real-time status display
4. Create `ImportNotifications` component with custom event listeners
5. Integrate polling hook + progress component into import page
6. Test real-time updates with mock API responses
7. Verify polling stops when job completes
8. Performance testing (no lag on rapid updates)

## Context for AI Agents

**Key Files**:
- `apps/web/hooks/useImportPolling.ts` - Polling hook (create)
- `apps/web/hooks/__tests__/useImportPolling.test.ts` - Hook tests (create)
- `apps/web/components/imports/BulkImportProgress.tsx` - Progress component (create)
- `apps/web/components/imports/__tests__/BulkImportProgress.test.tsx` - Component tests (create)
- `apps/web/components/imports/ImportNotifications.tsx` - Notification component (create)
- `apps/web/app/dashboard/import/page.tsx` - Integration point (update Phase 3)

**API Endpoints**:
- `GET /api/v1/ingest/bulk/{bulkJobId}/status?offset=0&limit=100` - Polling endpoint
- Response: `BulkImportStatus` with total counts and per-row status array

**Custom Events**:
- `import-partial-found` - Dispatched when partial import completed
- `import-job-complete` - Dispatched when entire job completes

**Component Stack**:
- React Query for polling (`useQuery` with `refetchInterval`)
- Toast system via `use-toast` hook (Radix UI based)
- Progress bar from `@/components/ui/progress`
- Badge component from `@/components/ui/badge`
- Lucide icons for status indicators
- Card component for layout

**Integration Pattern**:
- useImportPolling hook called in import page component
- Hook emits events that trigger modal and notifications
- BulkImportProgress subscribed to status changes
- ImportNotifications listens for custom events
- All components manage their own side effects

**Testing Strategy**:
- Mock fetch for API responses
- Mock timing with `vi.useFakeTimers()` for polling
- Track ref mutations for partial detection
- Verify custom events dispatched and received
- Test error scenarios (API failure, malformed response)

**Performance Considerations**:
- Polling interval: 2 seconds (configurable)
- Stale time: 1 second (keep data fresh)
- GC time: 60 seconds (keep cached)
- Prevent duplicate notifications via ref tracking
- Memoize components to prevent unnecessary re-renders

**Phase Dependencies Satisfied**:
- Phase 1 complete: Database schema supports partial/full imports
- Phase 2 complete: API endpoints for status and completion
- Phase 3 complete: Modal component for data entry

**Success Criteria for Phase Completion**:
- All tasks checked off
- All unit tests passing
- All integration tests passing
- Polling starts and stops correctly
- Events dispatched and received by components
- Real-time updates visible in UI
- No memory leaks or continuous polling after completion
- Code review approved
- Ready for Phase 5 (Integration Testing)
