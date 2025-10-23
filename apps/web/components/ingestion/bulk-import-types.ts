/**
 * TypeScript types for bulk URL import workflow
 */

// ============================================================================
// Backend Response Types (matching Pydantic schemas)
// ============================================================================

export interface PerRowStatus {
  url: string;
  status: 'queued' | 'running' | 'complete' | 'partial' | 'failed';
  listing_id: number | null;
  error: string | null;
}

export interface BulkIngestionResponse {
  bulk_job_id: string;
  total_urls: number;
}

export interface BulkIngestionStatusResponse {
  bulk_job_id: string;
  status: 'queued' | 'running' | 'complete' | 'partial' | 'failed';
  total_urls: number;
  completed: number;
  success: number;
  partial: number;
  failed: number;
  running: number;
  queued: number;
  per_row_status: PerRowStatus[];
  offset: number;
  limit: number;
  has_more: boolean;
}

// ============================================================================
// UI State Types
// ============================================================================

export type BulkImportMode = 'file' | 'paste';

export type BulkImportState =
  | { status: 'idle' }
  | { status: 'validating'; mode: BulkImportMode; count: number }
  | { status: 'uploading'; mode: BulkImportMode; count: number }
  | { status: 'polling'; bulkJobId: string; startTime: number }
  | { status: 'complete'; bulkJobId: string; data: BulkIngestionStatusResponse }
  | { status: 'error'; error: BulkImportError };

export interface BulkImportError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// Component Props
// ============================================================================

export interface BulkImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (result: BulkIngestionStatusResponse) => void;
  onError?: (error: BulkImportError) => void;
}

export interface BulkUploadFormProps {
  onSubmit: (data: FormData | string[]) => void;
  disabled: boolean;
  error?: BulkImportError;
}

export interface BulkProgressDisplayProps {
  data: BulkIngestionStatusResponse;
  elapsed: number;
}

export interface BulkStatusTableProps {
  bulkJobId: string;
  data: BulkIngestionStatusResponse;
  onRefresh?: () => void;
}

// ============================================================================
// Form Validation Types
// ============================================================================

export interface BulkImportFormData {
  mode: BulkImportMode;
  file?: File;
  urls?: string;
}

export interface ParsedUrls {
  urls: string[];
  errors: string[];
  warnings: string[];
}
