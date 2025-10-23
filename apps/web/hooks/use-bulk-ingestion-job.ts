'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getBulkIngestionStatus } from '@/lib/api/bulk-ingestion';
import type { BulkIngestionStatusResponse } from '@/components/ingestion/bulk-import-types';

interface UseBulkIngestionJobOptions {
  bulkJobId: string | null;
  offset?: number;
  limit?: number;
  enabled?: boolean;
  onSuccess?: (data: BulkIngestionStatusResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * React Query hook for polling bulk ingestion job status
 *
 * This hook automatically polls the bulk ingestion status endpoint
 * every 2 seconds while the job is running, and stops when complete.
 *
 * It supports pagination for per-URL status data.
 */
export function useBulkIngestionJob({
  bulkJobId,
  offset = 0,
  limit = 50,
  enabled = true,
  onSuccess,
  onError,
}: UseBulkIngestionJobOptions) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['bulk-ingestion-job', bulkJobId, offset, limit],
    queryFn: () => {
      if (!bulkJobId) throw new Error('Bulk Job ID is required');
      return getBulkIngestionStatus(bulkJobId, offset, limit);
    },
    enabled: !!bulkJobId && enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling when job is complete, partial, or failed
      if (!data) return false;
      if (data.status === 'complete' || data.status === 'partial' || data.status === 'failed') {
        return false;
      }
      // Poll every 2 seconds while queued or running
      return 2000;
    },
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    staleTime: 0, // Always fetch fresh data
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
  });

  // Handle success/error callbacks
  const data = query.data;
  const error = query.error;

  if (data && onSuccess) {
    onSuccess(data);
  }

  if (error && onError) {
    onError(error as Error);
  }

  const cancelPolling = () => {
    if (bulkJobId) {
      queryClient.cancelQueries({ queryKey: ['bulk-ingestion-job', bulkJobId] });
    }
  };

  const refetch = () => {
    return query.refetch();
  };

  return {
    ...query,
    cancelPolling,
    refetch,
  };
}
