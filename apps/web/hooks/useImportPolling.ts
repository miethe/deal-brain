'use client';

import { useEffect, useState, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { API_URL } from '@/lib/utils';

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
  interval?: number; // Default 2000ms
  onStatusChange?: (status: BulkImportStatus) => void;
  onComplete?: (status: BulkImportStatus) => void;
  onPartialFound?: (listing: PerRowImportStatus) => void;
  enabled?: boolean;
}

/**
 * React Query hook for polling bulk import status with event emission
 *
 * This hook polls the bulk import status endpoint every 2 seconds (configurable)
 * and emits callbacks when status changes, partials are found, or job completes.
 *
 * Features:
 * - Automatic polling with React Query
 * - Stops polling when job completes
 * - Detects partial imports and emits onPartialFound callback
 * - Detects job completion and emits onComplete callback
 * - Dispatches custom window events for loose coupling
 * - Calculates progress percentage
 * - Prevents memory leaks with proper cleanup
 *
 * Custom Events:
 * - 'import-partial-found': Emitted when a partial import is detected
 * - 'import-job-complete': Emitted when the entire job completes
 */
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
        `${API_URL}/api/v1/ingest/bulk/${bulkJobId}/status?limit=100`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch import status: ${response.statusText}`);
      }

      return (await response.json()) as BulkImportStatus;
    },
    refetchInterval: (query) => {
      if (!enabled) return false;
      const data = query.state.data;
      // Stop polling when job is complete, partial, or failed
      if (!data) return interval;
      if (data.status === 'complete' || data.status === 'partial' || data.status === 'failed') {
        return false;
      }
      // Poll every {interval} seconds while queued or running
      return interval;
    },
    enabled: enabled,
    staleTime: 1000, // Keep data fresh
    gcTime: 60000, // Keep cached for 60s
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
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
      (status.status === 'complete' || status.status === 'partial') &&
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

/**
 * Variant: useImportPollingWithPagination for handling large imports
 *
 * This variant supports pagination for bulk imports with many URLs.
 * It accumulates row status across pages and provides pagination controls.
 */
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
  const hasNotifiedCompleteRef = useRef(false);

  const { data: status, isLoading, isError, error } = useQuery({
    queryKey: ['bulkImportStatus', bulkJobId, currentPage],
    queryFn: async () => {
      const offset = currentPage * pageSize;
      const response = await fetch(
        `${API_URL}/api/v1/ingest/bulk/${bulkJobId}/status?offset=${offset}&limit=${pageSize}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch import status`);
      }

      return (await response.json()) as BulkImportStatus;
    },
    refetchInterval: (query) => {
      if (!enabled) return false;
      const data = query.state.data;
      // Stop polling when job is complete, partial, or failed
      if (!data) return interval;
      if (data.status === 'complete' || data.status === 'partial' || data.status === 'failed') {
        return false;
      }
      // Poll every {interval} seconds while queued or running
      return interval;
    },
    enabled: enabled,
    staleTime: 1000,
    gcTime: 60000,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
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

    if (
      (status.status === 'complete' || status.status === 'partial') &&
      !hasNotifiedCompleteRef.current
    ) {
      hasNotifiedCompleteRef.current = true;
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
