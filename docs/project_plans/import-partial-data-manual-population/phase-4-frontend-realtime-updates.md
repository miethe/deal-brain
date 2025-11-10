---
title: "Phase 4: Frontend - Real-Time UI Updates"
description: "Implement real-time bulk import status polling, progress tracking, and notifications"
audience: [ai-agents, developers]
tags:
  - implementation
  - frontend
  - ui
  - real-time
created: 2025-11-08
updated: 2025-11-08
category: product-planning
status: pending
related:
  - /docs/project_plans/import-partial-data-manual-population/implementation-plan.md
  - /docs/project_plans/import-partial-data-manual-population/phase-3-frontend-manual-population.md
---

# Phase 4: Frontend - Real-Time UI Updates

**Duration**: 2-3 days
**Dependencies**: Phase 2 complete (API endpoints), Phase 3 complete (Modal)
**Risk Level**: Low (polling + UI updates)

## Phase Overview

Phase 4 implements real-time tracking of bulk import progress. Users see:
- Live progress bar as imports complete
- Per-URL status (queued, running, complete, partial, failed)
- Toast notifications for key events
- Automatic refresh of data after completion

**Key Outcomes**:
- useImportPolling hook polls status every 2 seconds
- BulkImportProgress component displays real-time updates
- Toast notifications for key milestones
- List of completed imports with quality indicators

---

## Task 4.1: Create useImportPolling Hook

**Agent**: `ui-engineer`
**File**: `apps/web/hooks/useImportPolling.ts`
**Duration**: 3-4 hours

### Objective
Implement React hook that polls bulk import status and emits events.

### Implementation

```typescript
import { useEffect, useState, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';

export interface PerRowImportStatus {
  url: string;
  status: 'queued' | 'running' | 'complete' | 'failed';
  listing_id: number | null;
  quality: 'full' | 'partial' | null;
  error: string | null;
}

export interface BulkImportStatus {
  bulk_job_id: string;
  status: 'running' | 'complete' | 'partial' | 'failed' | 'queued';
  total_urls: number;
  completed: number;
  success: number;
  partial: number;
  failed: number;
  running: number;
  queued: number;
  per_row_status: PerRowImportStatus[];
  offset: number;
  limit: number;
  has_more: boolean;
}

interface UseImportPollingOptions {
  bulkJobId: string;
  interval?: number;  // Default 2000ms
  onStatusChange?: (status: BulkImportStatus) => void;
  onComplete?: (status: BulkImportStatus) => void;
  onPartialFound?: (listing: PerRowImportStatus) => void;
  enabled?: boolean;
}

export function useImportPolling({
  bulkJobId,
  interval = 2000,
  onStatusChange,
  onComplete,
  onPartialFound,
  enabled = true,
}: UseImportPollingOptions) {
  const [previousStatus, setPreviousStatus] = useState<BulkImportStatus | null>(null);
  const hasNotifiedCompleteRef = useRef(false);
  const detectedPartialsRef = useRef<Set<number>>(new Set());

  // Query for bulk status with polling
  const { data: status, isLoading, isError, error } = useQuery({
    queryKey: ['bulkImportStatus', bulkJobId],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/ingest/bulk/${bulkJobId}/status?limit=100`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch import status: ${response.statusText}`);
      }

      return (await response.json()) as BulkImportStatus;
    },
    refetchInterval: enabled && 2000 < interval ? interval : 2000,
    enabled: enabled,
    staleTime: 1000,  // Keep data fresh
    gcTime: 60000,    // Keep cached for 60s
  });

  // Track state changes and emit events
  useEffect(() => {
    if (!status) return;

    // Call onStatusChange callback
    onStatusChange?.(status);

    // Detect newly completed imports
    if (status.per_row_status && previousStatus?.per_row_status) {
      status.per_row_status.forEach((current) => {
        const previous = previousStatus.per_row_status.find(
          (p) => p.url === current.url
        );

        // If transitioned to complete and is partial, emit event
        if (
          previous?.status !== 'complete' &&
          current.status === 'complete' &&
          current.quality === 'partial' &&
          current.listing_id &&
          !detectedPartialsRef.current.has(current.listing_id)
        ) {
          detectedPartialsRef.current.add(current.listing_id);
          onPartialFound?.(current);

          // Dispatch custom event for other components to listen
          window.dispatchEvent(
            new CustomEvent('import-partial-found', {
              detail: current,
            })
          );
        }
      });
    }

    // Detect when entire import job completes
    if (
      status.status === 'complete' &&
      !hasNotifiedCompleteRef.current &&
      status.total_urls > 0
    ) {
      hasNotifiedCompleteRef.current = true;
      onComplete?.(status);

      window.dispatchEvent(
        new CustomEvent('import-job-complete', {
          detail: status,
        })
      );
    }

    // Update previous status for next comparison
    setPreviousStatus(status);
  }, [status, previousStatus, onStatusChange, onComplete, onPartialFound]);

  // Calculate progress percentage
  const progressPercent = status
    ? Math.round((status.completed / (status.total_urls || 1)) * 100)
    : 0;

  return {
    status,
    isLoading,
    isError,
    error,
    progressPercent,
  };
}

// Variant: useImportPollingWithPagination for handling large imports
export function useImportPollingWithPagination({
  bulkJobId,
  pageSize = 20,
  interval = 2000,
  onStatusChange,
  onComplete,
  enabled = true,
}: Omit<UseImportPollingOptions, 'onPartialFound'> & {
  pageSize?: number;
}) {
  const [currentPage, setCurrentPage] = useState(0);
  const [allRowStatus, setAllRowStatus] = useState<PerRowImportStatus[]>([]);

  const { data: status, isLoading, isError, error } = useQuery({
    queryKey: ['bulkImportStatus', bulkJobId, currentPage],
    queryFn: async () => {
      const offset = currentPage * pageSize;
      const response = await fetch(
        `/api/v1/ingest/bulk/${bulkJobId}/status?offset=${offset}&limit=${pageSize}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch import status`);
      }

      return (await response.json()) as BulkImportStatus;
    },
    refetchInterval: enabled ? interval : false,
    enabled: enabled,
  });

  // Accumulate all row statuses
  useEffect(() => {
    if (status?.per_row_status) {
      setAllRowStatus((prev) => [
        ...prev.filter(
          (p) =>
            !status.per_row_status.some((curr) => curr.url === p.url)
        ),
        ...status.per_row_status,
      ]);
    }
  }, [status?.per_row_status]);

  // Trigger callbacks
  useEffect(() => {
    if (!status) return;
    onStatusChange?.(status);

    if (status.status === 'complete') {
      onComplete?.(status);
    }
  }, [status, onStatusChange, onComplete]);

  return {
    status,
    isLoading,
    isError,
    error,
    allRowStatus,
    currentPage,
    setCurrentPage,
    hasMore: status?.has_more ?? false,
    progressPercent: status
      ? Math.round((status.completed / (status.total_urls || 1)) * 100)
      : 0,
  };
}
```

### Acceptance Criteria

- [ ] Polls bulk status endpoint every 2 seconds
- [ ] Stops polling when job completes
- [ ] Emits onStatusChange callback on each update
- [ ] Detects partial imports and calls onPartialFound
- [ ] Detects job completion and calls onComplete
- [ ] Dispatches custom window events for modal integration
- [ ] Calculates progress percentage correctly
- [ ] Handles API errors gracefully
- [ ] Can be disabled via enabled prop
- [ ] Works with React Query (refetchInterval, staleTime)
- [ ] No memory leaks (cleanup refs properly)
- [ ] TypeScript types complete

### Testing

```typescript
// apps/web/hooks/__tests__/useImportPolling.test.ts
import { renderHook, waitFor, act } from '@testing-library/react';
import { useImportPolling } from '../useImportPolling';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

describe('useImportPolling', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const renderWithProviders = (hook: () => any) => {
    return renderHook(hook, {
      wrapper: ({ children }) =>
        React.createElement(QueryClientProvider, { client: queryClient }, children),
    });
  };

  it('polls status endpoint', async () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            bulk_job_id: 'test-123',
            status: 'running',
            total_urls: 10,
            completed: 5,
            success: 5,
            partial: 0,
            failed: 0,
            running: 5,
            queued: 0,
            per_row_status: [],
            offset: 0,
            limit: 20,
            has_more: false,
          }),
      })
    );

    global.fetch = mockFetch;

    const { result } = renderWithProviders(() =>
      useImportPolling({ bulkJobId: 'test-123' })
    );

    await waitFor(() => {
      expect(result.current.status).toBeDefined();
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/ingest/bulk/test-123/status')
    );
  });

  it('emits onStatusChange callback', async () => {
    const onStatusChange = vi.fn();

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            bulk_job_id: 'test-123',
            status: 'running',
            total_urls: 10,
            completed: 5,
            success: 5,
            partial: 0,
            failed: 0,
            running: 5,
            queued: 0,
            per_row_status: [],
            offset: 0,
            limit: 20,
            has_more: false,
          }),
      })
    );

    const { result } = renderWithProviders(() =>
      useImportPolling({
        bulkJobId: 'test-123',
        onStatusChange,
      })
    );

    await waitFor(() => {
      expect(onStatusChange).toHaveBeenCalled();
    });
  });

  it('calculates progress percentage', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            bulk_job_id: 'test-123',
            status: 'running',
            total_urls: 10,
            completed: 5,
            success: 5,
            partial: 0,
            failed: 0,
            running: 5,
            queued: 0,
            per_row_status: [],
            offset: 0,
            limit: 20,
            has_more: false,
          }),
      })
    );

    const { result } = renderWithProviders(() =>
      useImportPolling({ bulkJobId: 'test-123' })
    );

    await waitFor(() => {
      expect(result.current.progressPercent).toBe(50);
    });
  });

  it('detects partial imports', async () => {
    const onPartialFound = vi.fn();

    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            bulk_job_id: 'test-123',
            status: 'running',
            total_urls: 1,
            completed: 0,
            success: 0,
            partial: 0,
            failed: 0,
            running: 1,
            queued: 0,
            per_row_status: [
              {
                url: 'https://example.com',
                status: 'running',
                listing_id: null,
                quality: null,
                error: null,
              },
            ],
            offset: 0,
            limit: 20,
            has_more: false,
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            bulk_job_id: 'test-123',
            status: 'complete',
            total_urls: 1,
            completed: 1,
            success: 0,
            partial: 1,
            failed: 0,
            running: 0,
            queued: 0,
            per_row_status: [
              {
                url: 'https://example.com',
                status: 'complete',
                listing_id: 1,
                quality: 'partial',
                error: null,
              },
            ],
            offset: 0,
            limit: 20,
            has_more: false,
          }),
      });

    const { result } = renderWithProviders(() =>
      useImportPolling({
        bulkJobId: 'test-123',
        onPartialFound,
        interval: 100,
      })
    );

    await waitFor(() => {
      expect(onPartialFound).toHaveBeenCalledWith(
        expect.objectContaining({
          listing_id: 1,
          quality: 'partial',
        })
      );
    });
  });

  it('detects job completion', async () => {
    const onComplete = vi.fn();

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            bulk_job_id: 'test-123',
            status: 'complete',
            total_urls: 1,
            completed: 1,
            success: 1,
            partial: 0,
            failed: 0,
            running: 0,
            queued: 0,
            per_row_status: [],
            offset: 0,
            limit: 20,
            has_more: false,
          }),
      })
    );

    const { result } = renderWithProviders(() =>
      useImportPolling({
        bulkJobId: 'test-123',
        onComplete,
      })
    );

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    });
  });
});
```

---

## Task 4.2: Create BulkImportProgress Component

**Agent**: `ui-engineer`
**File**: `apps/web/components/imports/BulkImportProgress.tsx`
**Duration**: 2-3 hours

### Objective
Display real-time bulk import progress with live metrics.

### Implementation

```typescript
import React from 'react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  XCircle,
} from 'lucide-react';
import { BulkImportStatus, PerRowImportStatus } from '@/hooks/useImportPolling';
import { cn } from '@/lib/utils';

interface BulkImportProgressProps {
  status: BulkImportStatus;
  isLoading?: boolean;
}

export function BulkImportProgress({
  status,
  isLoading = false,
}: BulkImportProgressProps) {
  const progressPercent = Math.round(
    (status.completed / (status.total_urls || 1)) * 100
  );

  const getStatusColor = (
    importStatus: 'queued' | 'running' | 'complete' | 'failed'
  ) => {
    switch (importStatus) {
      case 'complete':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'queued':
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getQualityBadge = (quality: 'full' | 'partial' | null) => {
    switch (quality) {
      case 'full':
        return <Badge variant="default">Complete</Badge>;
      case 'partial':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            Needs Data
          </Badge>
        );
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Bulk Import Progress</CardTitle>
        <CardDescription>
          {status.total_urls} URLs - {status.completed} completed
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex justify-between items-baseline">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm text-gray-600">{progressPercent}%</span>
          </div>
          <Progress value={progressPercent} className="h-3" />
        </div>

        {/* Status Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <StatusCard
            label="Total"
            value={status.total_urls}
            icon={<Clock className="w-4 h-4" />}
            className="bg-blue-50"
          />

          <StatusCard
            label="Complete"
            value={status.success}
            icon={<CheckCircle className="w-4 h-4 text-green-600" />}
            className="bg-green-50"
          />

          <StatusCard
            label="Partial"
            value={status.partial}
            icon={<AlertCircle className="w-4 h-4 text-yellow-600" />}
            className="bg-yellow-50"
          />

          <StatusCard
            label="Running"
            value={status.running}
            icon={<Zap className="w-4 h-4 text-blue-600 animate-pulse" />}
            className="bg-blue-50"
          />

          <StatusCard
            label="Failed"
            value={status.failed}
            icon={<XCircle className="w-4 h-4 text-red-600" />}
            className="bg-red-50"
          />
        </div>

        {/* Per-URL Status (if showing details) */}
        {status.per_row_status.length > 0 && (
          <div className="space-y-2 mt-6">
            <h4 className="text-sm font-semibold">Recent Imports</h4>

            <div className="space-y-2 max-h-48 overflow-y-auto">
              {status.per_row_status.slice(0, 5).map((row) => (
                <PerRowStatusItem key={row.url} row={row} />
              ))}

              {status.per_row_status.length > 5 && (
                <p className="text-xs text-gray-500 text-center py-2">
                  ... and {status.per_row_status.length - 5} more
                </p>
              )}
            </div>
          </div>
        )}

        {/* Completion Message */}
        {status.status === 'complete' && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800 font-medium">
              Import completed! {status.partial} listing(s) need data completion.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface StatusCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  className?: string;
}

function StatusCard({ label, value, icon, className }: StatusCardProps) {
  return (
    <div
      className={cn(
        'p-3 rounded-lg text-center',
        className || 'bg-gray-50'
      )}
    >
      <div className="flex justify-center mb-2">{icon}</div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs text-gray-600">{label}</div>
    </div>
  );
}

interface PerRowStatusItemProps {
  row: PerRowImportStatus;
}

function PerRowStatusItem({ row }: PerRowStatusItemProps) {
  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
      <div className="flex-1 truncate">
        <p className="text-gray-700 truncate" title={row.url}>
          {row.url}
        </p>
      </div>

      <div className="flex items-center gap-2 ml-2">
        <span
          className={cn(
            'px-2 py-1 rounded text-xs font-medium',
            getStatusColor(row.status)
          )}
        >
          {row.status}
        </span>

        {row.listing_id && getQualityBadge(row.quality)}
      </div>
    </div>
  );
}

function getStatusColor(
  status: 'queued' | 'running' | 'complete' | 'failed'
) {
  switch (status) {
    case 'complete':
      return 'bg-green-100 text-green-800';
    case 'running':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'queued':
      return 'bg-gray-100 text-gray-800';
  }
}
```

### Acceptance Criteria

- [ ] Displays overall progress percentage
- [ ] Shows count grid (total, complete, partial, running, failed)
- [ ] Updates in real-time as status changes
- [ ] Shows recent URLs with status
- [ ] Quality badges displayed correctly
- [ ] Performance acceptable (no re-renders on every poll)
- [ ] Responsive design works on mobile
- [ ] Colors accessible (WCAG AA)
- [ ] Unit tests pass

### Testing

```typescript
// apps/web/components/imports/__tests__/BulkImportProgress.test.tsx
import { render, screen } from '@testing-library/react';
import { BulkImportProgress } from '../BulkImportProgress';
import { describe, it, expect } from 'vitest';
import { BulkImportStatus } from '@/hooks/useImportPolling';

describe('BulkImportProgress', () => {
  const mockStatus: BulkImportStatus = {
    bulk_job_id: 'test-123',
    status: 'running',
    total_urls: 10,
    completed: 5,
    success: 3,
    partial: 2,
    failed: 0,
    running: 5,
    queued: 0,
    per_row_status: [
      {
        url: 'https://example.com/1',
        status: 'complete',
        listing_id: 1,
        quality: 'full',
        error: null,
      },
      {
        url: 'https://example.com/2',
        status: 'complete',
        listing_id: 2,
        quality: 'partial',
        error: null,
      },
    ],
    offset: 0,
    limit: 20,
    has_more: false,
  };

  it('displays progress percentage', () => {
    render(<BulkImportProgress status={mockStatus} />);

    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('displays status counts', () => {
    render(<BulkImportProgress status={mockStatus} />);

    expect(screen.getByText('Total')).toBeInTheDocument();
    screen.getByText('10');
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('Partial')).toBeInTheDocument();
  });

  it('shows per-row status', () => {
    render(<BulkImportProgress status={mockStatus} />);

    expect(screen.getByText(/example.com/)).toBeInTheDocument();
  });
});
```

---

## Task 4.3: Create ImportNotifications Component

**Agent**: `ui-engineer`
**File**: `apps/web/components/imports/ImportNotifications.tsx`
**Duration**: 2-3 hours

### Objective
Display toast notifications for key import events.

### Implementation

```typescript
import { useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { BulkImportStatus, PerRowImportStatus } from '@/hooks/useImportPolling';

interface ImportNotificationsProps {
  bulkJobId: string;
}

export function ImportNotifications({ bulkJobId }: ImportNotificationsProps) {
  const { toast } = useToast();

  useEffect(() => {
    const handlePartialFound = (event: Event) => {
      const customEvent = event as CustomEvent<PerRowImportStatus>;
      toast({
        title: 'Data Needed',
        description: `Please provide missing data for one listing (e.g., price).`,
        variant: 'default',
      });
    };

    const handleJobComplete = (event: Event) => {
      const customEvent = event as CustomEvent<BulkImportStatus>;
      const { status } = customEvent.detail;

      if (status.partial > 0) {
        toast({
          title: 'Import Complete',
          description: `${status.success} listings ready, ${status.partial} need data.`,
          variant: 'default',
        });
      } else {
        toast({
          title: 'Import Complete',
          description: `All ${status.completed} listings successfully imported!`,
          variant: 'default',
        });
      }
    };

    window.addEventListener('import-partial-found', handlePartialFound);
    window.addEventListener('import-job-complete', handleJobComplete);

    return () => {
      window.removeEventListener('import-partial-found', handlePartialFound);
      window.removeEventListener('import-job-complete', handleJobComplete);
    };
  }, [toast]);

  return null;  // Notifications rendered via toast system
}
```

### Acceptance Criteria

- [ ] Toast shows when partial import detected
- [ ] Toast shows when job completes
- [ ] Toast messages are clear and actionable
- [ ] Multiple toasts can appear without overlapping
- [ ] Auto-dismiss after 5 seconds
- [ ] Accessible (screen readers announce toasts)

---

## Integration Testing for Phase 4

### Polling + Notifications Integration

```typescript
// tests/test_phase4_integration.test.tsx
async function test_e2e_bulk_import_with_realtime_updates() {
  /**
   * Tests:
   * 1. Start bulk import
   * 2. Polling begins
   * 3. Status updates in real-time
   * 4. Partial import detected → modal shows
   * 5. User completes import
   * 6. Polling detects completion
   * 7. Toast shown
   */
}
```

---

## Success Criteria

All of the following must be true to consider Phase 4 complete:

- [ ] useImportPolling hook polls correctly every 2 seconds
- [ ] Stops polling when job completes
- [ ] Detects partial imports and emits events
- [ ] BulkImportProgress displays real-time updates
- [ ] Progress percentage calculated correctly
- [ ] Per-row status displayed with quality badges
- [ ] Toast notifications work for key events
- [ ] Custom window events emitted and received
- [ ] All tests pass (unit + integration)
- [ ] Performance acceptable (no lag on updates)
- [ ] Memory leaks prevented
- [ ] Ready to proceed to Phase 5 (Integration & Testing)
