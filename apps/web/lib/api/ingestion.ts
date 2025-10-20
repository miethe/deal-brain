import { apiFetch } from '../utils';
import type {
  SingleUrlImportRequest,
  SingleUrlImportResponse,
  IngestionJobResponse,
} from '@/components/ingestion/types';

/**
 * Submit a single URL for import
 */
export async function submitSingleUrlImport(
  data: SingleUrlImportRequest
): Promise<SingleUrlImportResponse> {
  return apiFetch<SingleUrlImportResponse>('/api/v1/ingest/single', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get status of an ingestion job
 */
export async function getIngestionJobStatus(
  jobId: string
): Promise<IngestionJobResponse> {
  return apiFetch<IngestionJobResponse>(`/api/v1/ingest/${jobId}`);
}

/**
 * Cancel a running ingestion job (if supported)
 */
export async function cancelIngestionJob(jobId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/ingest/${jobId}`, {
    method: 'DELETE',
  });
}
