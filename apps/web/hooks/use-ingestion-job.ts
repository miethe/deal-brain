'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getIngestionJobStatus } from '@/lib/api/ingestion';
import type { IngestionJobResponse } from '@/components/ingestion/types';

interface UseIngestionJobOptions {
  jobId: string | null;
  enabled?: boolean;
  onSuccess?: (data: IngestionJobResponse) => void;
  onError?: (error: Error) => void;
}

export function useIngestionJob({
  jobId,
  enabled = true,
  onSuccess,
  onError,
}: UseIngestionJobOptions) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['ingestion-job', jobId],
    queryFn: () => {
      if (!jobId) throw new Error('Job ID is required');
      return getIngestionJobStatus(jobId);
    },
    enabled: !!jobId && enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling when job is complete or failed
      if (!data) return false;
      if (data.status === 'complete' || data.status === 'failed' || data.status === 'partial') {
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
    if (jobId) {
      queryClient.cancelQueries({ queryKey: ['ingestion-job', jobId] });
    }
  };

  return {
    ...query,
    cancelPolling,
  };
}
