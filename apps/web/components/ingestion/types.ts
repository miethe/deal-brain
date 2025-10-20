// Ingestion job status from backend
export type IngestionJobStatus = 'queued' | 'running' | 'complete' | 'failed' | 'partial';

// Provenance indicating data source
export type Provenance = 'ebay_api' | 'jsonld' | 'scraper';

// Quality level of extracted data
export type QualityLevel = 'full' | 'partial';

// Priority for job processing
export type ImportPriority = 'high' | 'standard' | 'low';

// Component state machine
export type ImportState =
  | { status: 'idle' }
  | { status: 'validating'; url: string }
  | { status: 'submitting'; url: string; priority: ImportPriority }
  | { status: 'polling'; jobId: string; startTime: number }
  | { status: 'success'; result: ImportSuccessResult }
  | { status: 'error'; error: ImportError };

// API response for single URL import
export interface SingleUrlImportRequest {
  url: string;
  priority?: ImportPriority;
}

export interface SingleUrlImportResponse {
  job_id: string;
  status: IngestionJobStatus;
}

// Job status response
export interface IngestionJobResponse {
  job_id: string;
  status: IngestionJobStatus;
  url: string;
  result?: {
    listing_id: number;
    title?: string;
    provenance: Provenance;
    quality: QualityLevel;
    created_at: string;
  };
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  created_at: string;
  updated_at: string;
}

// Success result for UI display
export interface ImportSuccessResult {
  jobId: string;
  listingId: number;
  title: string;
  provenance: Provenance;
  quality: QualityLevel;
  createdAt: string;
}

// Error information
export interface ImportError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  retryable: boolean;
}

// Component props
export interface SingleUrlImportFormProps {
  onSuccess?: (result: ImportSuccessResult) => void;
  onError?: (error: ImportError) => void;
  onReset?: () => void;
  defaultUrl?: string;
  defaultPriority?: ImportPriority;
  compact?: boolean;
  className?: string;
}

// Status display props
export interface IngestionStatusDisplayProps {
  state: ImportState;
  onRetry?: () => void;
  onViewListing?: () => void;
  onImportAnother?: () => void;
}

// Success result display props
export interface ImportSuccessResultProps {
  result: ImportSuccessResult;
  onViewListing: () => void;
  onImportAnother: () => void;
}
