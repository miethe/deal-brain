import { apiFetch } from '../utils';
import type {
  BulkIngestionResponse,
  BulkIngestionStatusResponse,
} from '@/components/ingestion/bulk-import-types';

/**
 * Submit a bulk URL import job from file upload
 */
export async function submitBulkUrlImportFile(
  file: File
): Promise<BulkIngestionResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return apiFetch<BulkIngestionResponse>('/api/v1/ingest/bulk', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Submit a bulk URL import job from pasted URLs
 * Creates a CSV in-memory and uploads it
 */
export async function submitBulkUrlImportUrls(
  urls: string[]
): Promise<BulkIngestionResponse> {
  // Create CSV content from URLs
  const csvContent = ['url', ...urls].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const file = new File([blob], 'pasted_urls.csv', { type: 'text/csv' });

  const formData = new FormData();
  formData.append('file', file);

  return apiFetch<BulkIngestionResponse>('/api/v1/ingest/bulk', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Get status of a bulk ingestion job with pagination
 */
export async function getBulkIngestionStatus(
  bulkJobId: string,
  offset: number = 0,
  limit: number = 50
): Promise<BulkIngestionStatusResponse> {
  return apiFetch<BulkIngestionStatusResponse>(
    `/api/v1/ingest/bulk/${bulkJobId}?offset=${offset}&limit=${limit}`
  );
}

/**
 * Download bulk import results as CSV
 */
export function downloadBulkResultsCSV(
  data: BulkIngestionStatusResponse,
  filename: string = 'bulk-import-results.csv'
): void {
  // Build CSV content
  const headers = ['URL', 'Status', 'Listing ID', 'Error'];
  const rows = data.per_row_status.map((row) => [
    row.url,
    row.status,
    row.listing_id?.toString() || '',
    row.error || '',
  ]);

  const csvContent = [
    headers.join(','),
    ...rows.map((row) =>
      row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(',')
    ),
  ].join('\n');

  // Create blob and trigger download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
