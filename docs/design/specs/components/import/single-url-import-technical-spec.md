# Single URL Import Component - Technical Specification
**Task ID-022: Frontend Import Component**
**Created**: 2025-10-19
**Status**: Ready for Implementation

---

## Implementation Overview

This document provides the detailed technical specifications for implementing the Single URL Import component, including code structure, type definitions, API integration, and testing requirements.

---

## 1. TypeScript Type Definitions

### File: `/mnt/containers/deal-brain/apps/web/components/ingestion/types.ts`

```typescript
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
  onCancel?: () => void;
  onRetry?: () => void;
}

// Success result display props
export interface ImportSuccessResultProps {
  result: ImportSuccessResult;
  onViewListing: () => void;
  onImportAnother: () => void;
}
```

---

## 2. Form Validation Schema

### Using Zod for Runtime Validation

```typescript
import { z } from 'zod';

export const urlImportSchema = z.object({
  url: z
    .string()
    .min(1, 'Please enter a listing URL')
    .url('Please enter a valid URL starting with http:// or https://')
    .max(2048, 'URL is too long (max 2048 characters)')
    .refine(
      (url) => {
        // Ensure URL uses http or https
        return url.startsWith('http://') || url.startsWith('https://');
      },
      { message: 'URL must start with http:// or https://' }
    ),
  priority: z.enum(['high', 'standard', 'low']).optional().default('standard'),
});

export type UrlImportFormData = z.infer<typeof urlImportSchema>;
```

---

## 3. API Client Functions

### File: `/mnt/containers/deal-brain/apps/web/lib/api/ingestion.ts`

```typescript
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
  return apiFetch<SingleUrlImportResponse>('/v1/ingest/single', {
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
  return apiFetch<IngestionJobResponse>(`/v1/ingest/${jobId}`);
}

/**
 * Cancel a running ingestion job (if supported)
 */
export async function cancelIngestionJob(jobId: string): Promise<void> {
  return apiFetch<void>(`/v1/ingest/${jobId}`, {
    method: 'DELETE',
  });
}
```

---

## 4. React Query Hook for Job Polling

### File: `/mnt/containers/deal-brain/apps/web/hooks/use-ingestion-job.ts`

```typescript
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
    refetchInterval: (data) => {
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
    onSuccess,
    onError,
  });

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
```

---

## 5. Main Component Implementation

### File: `/mnt/containers/deal-brain/apps/web/components/ingestion/single-url-import-form.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { IngestionStatusDisplay } from './ingestion-status-display';
import { submitSingleUrlImport } from '@/lib/api/ingestion';
import { useIngestionJob } from '@/hooks/use-ingestion-job';
import { urlImportSchema, type UrlImportFormData } from './schemas';
import type { ImportState, SingleUrlImportFormProps, ImportSuccessResult } from './types';
import { cn } from '@/lib/utils';

export function SingleUrlImportForm({
  onSuccess,
  onError,
  onReset,
  defaultUrl,
  defaultPriority = 'standard',
  compact = false,
  className,
}: SingleUrlImportFormProps) {
  const router = useRouter();
  const [importState, setImportState] = useState<ImportState>({ status: 'idle' });

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset: resetForm,
    watch,
    setValue,
  } = useForm<UrlImportFormData>({
    resolver: zodResolver(urlImportSchema),
    defaultValues: {
      url: defaultUrl || '',
      priority: defaultPriority,
    },
    mode: 'onBlur',
  });

  const submitMutation = useMutation({
    mutationFn: submitSingleUrlImport,
    onMutate: () => {
      setImportState({ status: 'submitting', url: watch('url'), priority: watch('priority') });
    },
    onSuccess: (data) => {
      setImportState({
        status: 'polling',
        jobId: data.job_id,
        startTime: Date.now(),
      });
    },
    onError: (error: Error) => {
      const importError = {
        code: 'SUBMIT_ERROR',
        message: error.message || 'Failed to create import job',
        retryable: true,
      };
      setImportState({ status: 'error', error: importError });
      onError?.(importError);
    },
  });

  // Poll job status when in polling state
  const jobId = importState.status === 'polling' ? importState.jobId : null;

  useIngestionJob({
    jobId,
    enabled: importState.status === 'polling',
    onSuccess: (data) => {
      if (data.status === 'complete' && data.result) {
        const successResult: ImportSuccessResult = {
          jobId: data.job_id,
          listingId: data.result.listing_id,
          title: data.result.title || 'Untitled Listing',
          provenance: data.result.provenance,
          quality: data.result.quality,
          createdAt: data.result.created_at,
        };
        setImportState({ status: 'success', result: successResult });
        onSuccess?.(successResult);
      } else if (data.status === 'failed' && data.error) {
        const importError = {
          code: data.error.code,
          message: data.error.message,
          details: data.error.details,
          retryable: isRetryableError(data.error.code),
        };
        setImportState({ status: 'error', error: importError });
        onError?.(importError);
      }
    },
    onError: (error) => {
      const importError = {
        code: 'POLLING_ERROR',
        message: 'Failed to check import status',
        retryable: true,
      };
      setImportState({ status: 'error', error: importError });
      onError?.(importError);
    },
  });

  const onSubmit = (data: UrlImportFormData) => {
    submitMutation.mutate({
      url: data.url,
      priority: data.priority,
    });
  };

  const handleReset = () => {
    resetForm();
    setImportState({ status: 'idle' });
    onReset?.();
  };

  const handleRetry = () => {
    if (importState.status === 'error') {
      const url = watch('url');
      const priority = watch('priority');
      submitMutation.mutate({ url, priority });
    }
  };

  const handleViewListing = () => {
    if (importState.status === 'success') {
      router.push(`/listings/${importState.result.listingId}`);
    }
  };

  const content = (
    <>
      <CardHeader>
        <CardTitle>Import from URL</CardTitle>
        <CardDescription>
          Paste a listing URL from eBay, Amazon, or any retailer
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* URL Input Field */}
          <div className="space-y-2">
            <Label htmlFor="url">
              Listing URL <span className="text-destructive">*</span>
            </Label>
            <Input
              id="url"
              type="url"
              placeholder="https://www.ebay.com/itm/..."
              {...register('url')}
              aria-invalid={!!errors.url}
              aria-describedby={errors.url ? 'url-error' : 'url-help'}
              disabled={importState.status !== 'idle'}
              className={cn(errors.url && 'border-destructive')}
            />
            {errors.url && (
              <p id="url-error" className="text-sm text-destructive">
                {errors.url.message}
              </p>
            )}
            <p id="url-help" className="text-xs text-muted-foreground">
              Supports eBay, Amazon, and most retail websites
            </p>
          </div>

          {/* Priority Select */}
          <div className="space-y-2">
            <Label htmlFor="priority">Priority (optional)</Label>
            <Select
              defaultValue={defaultPriority}
              onValueChange={(value) => setValue('priority', value as any)}
              disabled={importState.status !== 'idle'}
            >
              <SelectTrigger id="priority" aria-label="Import priority">
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="high">High - Process immediately</SelectItem>
                <SelectItem value="standard">Standard - Normal queue</SelectItem>
                <SelectItem value="low">Low - Background processing</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Status Display */}
          {importState.status !== 'idle' && (
            <IngestionStatusDisplay
              state={importState}
              onRetry={handleRetry}
              onViewListing={handleViewListing}
              onImportAnother={handleReset}
            />
          )}
        </form>
      </CardContent>

      {importState.status === 'idle' && (
        <CardFooter className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleReset}
            disabled={!watch('url')}
          >
            Reset
          </Button>
          <Button
            type="submit"
            onClick={handleSubmit(onSubmit)}
            disabled={!isValid || submitMutation.isPending}
          >
            Import Listing
          </Button>
        </CardFooter>
      )}
    </>
  );

  if (compact) {
    return <div className={cn('space-y-4', className)}>{content}</div>;
  }

  return <Card className={className}>{content}</Card>;
}

// Helper function to determine if an error is retryable
function isRetryableError(code: string): boolean {
  const retryableCodes = ['TIMEOUT', 'RATE_LIMITED', 'NETWORK_ERROR', 'TEMPORARY_ERROR'];
  return retryableCodes.includes(code);
}
```

---

## 6. Status Display Component

### File: `/mnt/containers/deal-brain/apps/web/components/ingestion/ingestion-status-display.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, CheckCircle2, RotateCcw, ExternalLink, XCircle } from 'lucide-react';
import { ImportSuccessResult } from './import-success-result';
import type { ImportState } from './types';
import { cn } from '@/lib/utils';

interface IngestionStatusDisplayProps {
  state: ImportState;
  onRetry?: () => void;
  onViewListing?: () => void;
  onImportAnother?: () => void;
}

export function IngestionStatusDisplay({
  state,
  onRetry,
  onViewListing,
  onImportAnother,
}: IngestionStatusDisplayProps) {
  const [elapsed, setElapsed] = useState(0);

  // Track elapsed time for polling state
  useEffect(() => {
    if (state.status === 'polling') {
      const interval = setInterval(() => {
        setElapsed(Math.floor((Date.now() - state.startTime) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setElapsed(0);
    }
  }, [state]);

  // Validating state
  if (state.status === 'validating') {
    return (
      <Alert>
        <Loader2 className="h-4 w-4 animate-spin" />
        <AlertTitle>Validating URL...</AlertTitle>
      </Alert>
    );
  }

  // Submitting state
  if (state.status === 'submitting') {
    return (
      <Alert>
        <Loader2 className="h-4 w-4 animate-spin" />
        <AlertTitle>Creating import job...</AlertTitle>
        <AlertDescription className="text-xs text-muted-foreground">
          This usually takes a few seconds
        </AlertDescription>
      </Alert>
    );
  }

  // Polling state
  if (state.status === 'polling') {
    const progress = calculateProgress(elapsed);
    const message = getPollingMessage(elapsed);

    return (
      <Alert className="border-primary/50 bg-primary/5">
        <div className="flex items-start gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-primary mt-0.5" />
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <AlertTitle className="text-sm font-semibold">
                Importing listing...
              </AlertTitle>
              <Badge variant="outline" className="text-xs tabular-nums">
                {elapsed}s elapsed
              </Badge>
            </div>
            <AlertDescription className="text-xs space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <span className="text-muted-foreground tabular-nums w-10 text-right">
                  {progress}%
                </span>
              </div>
              <p className="text-muted-foreground">{message}</p>
            </AlertDescription>
          </div>
        </div>
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          Importing listing, {elapsed} seconds elapsed, {message}
        </div>
      </Alert>
    );
  }

  // Success state
  if (state.status === 'success') {
    return (
      <ImportSuccessResult
        result={state.result}
        onViewListing={onViewListing || (() => {})}
        onImportAnother={onImportAnother || (() => {})}
      />
    );
  }

  // Error state
  if (state.status === 'error') {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <div className="flex-1">
          <AlertTitle>Import failed</AlertTitle>
          <AlertDescription className="mt-2 space-y-2">
            <p className="text-sm">{state.error.message}</p>

            {state.error.details && (
              <details className="text-xs">
                <summary className="cursor-pointer hover:underline">
                  Show technical details
                </summary>
                <pre className="mt-2 p-2 bg-destructive/10 rounded text-xs overflow-auto max-h-32">
                  {JSON.stringify(state.error.details, null, 2)}
                </pre>
              </details>
            )}

            {state.error.retryable && onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="mt-2"
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
                Try Again
              </Button>
            )}
          </AlertDescription>
        </div>
        <div
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
          className="sr-only"
        >
          Import failed: {state.error.message}
        </div>
      </Alert>
    );
  }

  return null;
}

// Calculate progress percentage based on elapsed time
function calculateProgress(elapsed: number): number {
  if (elapsed < 5) {
    // 0-5s: 15-50% (linear)
    return 15 + (elapsed / 5) * 35;
  } else if (elapsed < 15) {
    // 5-15s: 50-85% (slower)
    return 50 + ((elapsed - 5) / 10) * 35;
  } else {
    // >15s: 85-95% (very slow, asymptotic)
    return Math.min(95, 85 + ((elapsed - 15) / 30) * 10);
  }
}

// Get status message based on elapsed time
function getPollingMessage(elapsed: number): string {
  if (elapsed < 2) {
    return 'Job queued, waiting for worker...';
  } else if (elapsed < 5) {
    return 'Extracting data from marketplace...';
  } else if (elapsed < 10) {
    return 'Processing product details...';
  } else {
    return 'Enriching with component data...';
  }
}
```

---

## 7. Success Result Component

### File: `/mnt/containers/deal-brain/apps/web/components/ingestion/import-success-result.tsx`

```typescript
'use client';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, ExternalLink, Database, AlertCircle } from 'lucide-react';
import type { ImportSuccessResult as ImportSuccessResultType } from './types';
import { formatDistanceToNow } from 'date-fns';

interface ImportSuccessResultProps {
  result: ImportSuccessResultType;
  onViewListing: () => void;
  onImportAnother: () => void;
}

export function ImportSuccessResult({
  result,
  onViewListing,
  onImportAnother,
}: ImportSuccessResultProps) {
  const provenanceBadgeConfig = {
    ebay_api: {
      label: 'eBay API',
      className: 'bg-blue-100 text-blue-700 border-blue-200',
    },
    jsonld: {
      label: 'JSON-LD',
      className: 'bg-purple-100 text-purple-700 border-purple-200',
    },
    scraper: {
      label: 'Scraper',
      className: 'bg-gray-100 text-gray-700 border-gray-200',
    },
  };

  const qualityBadgeConfig = {
    full: {
      label: 'Full data',
      icon: CheckCircle2,
      className: 'bg-green-100 text-green-700 border-green-200',
    },
    partial: {
      label: 'Partial data',
      icon: AlertCircle,
      className: 'bg-amber-100 text-amber-700 border-amber-200',
    },
  };

  const provenance = provenanceBadgeConfig[result.provenance];
  const quality = qualityBadgeConfig[result.quality];
  const QualityIcon = quality.icon;

  const timeAgo = formatDistanceToNow(new Date(result.createdAt), { addSuffix: true });

  return (
    <Alert variant="default" className="border-success/50 bg-success/5">
      <CheckCircle2 className="h-5 w-5 text-success" />
      <div className="flex-1">
        <AlertTitle className="text-success">
          Listing imported successfully!
        </AlertTitle>
        <AlertDescription className="mt-3 space-y-3">
          {/* Listing Preview Card */}
          <div className="rounded-lg border bg-card p-3 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <h4 className="font-medium text-sm line-clamp-2">
                {result.title}
              </h4>
              <Badge variant="secondary" className="text-xs shrink-0">
                #{result.listingId}
              </Badge>
            </div>

            {/* Metadata Row */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
              <Badge
                variant="outline"
                className={`gap-1 ${provenance.className}`}
              >
                <Database className="h-3 w-3" />
                {provenance.label}
              </Badge>

              <Badge
                variant="outline"
                className={`gap-1 ${quality.className}`}
              >
                <QualityIcon className="h-3 w-3" />
                {quality.label}
              </Badge>

              <span className="ml-auto">
                {timeAgo}
              </span>
            </div>
          </div>

          {/* Partial Data Warning */}
          {result.quality === 'partial' && (
            <Alert variant="default" className="bg-blue-50 border-blue-200">
              <AlertCircle className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-xs text-blue-700">
                Some details may be missing. You can edit the listing to add
                CPU, RAM, or storage info.
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onViewListing}
              className="flex-1"
            >
              <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
              View Listing
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={onImportAnother}
              className="flex-1"
            >
              Import Another
            </Button>
          </div>
        </AlertDescription>
      </div>
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        Listing imported successfully. Listing number {result.listingId}.
      </div>
    </Alert>
  );
}
```

---

## 8. Error Message Mapping

```typescript
// File: apps/web/components/ingestion/error-messages.ts

export const ERROR_MESSAGES: Record<string, string> = {
  TIMEOUT: 'Import timed out. The marketplace may be slow to respond.',
  INVALID_SCHEMA: 'Could not extract listing data. The page format may not be supported.',
  ADAPTER_DISABLED: 'This marketplace integration is currently disabled.',
  ITEM_NOT_FOUND: 'Listing not found. The URL may be invalid or the item may have been removed.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  SUBMIT_ERROR: 'Failed to create import job. Please try again.',
  POLLING_ERROR: 'Failed to check import status. The job may still be running.',
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
};

export function getErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] || ERROR_MESSAGES.UNKNOWN_ERROR;
}
```

---

## 9. Testing Requirements

### Unit Tests

```typescript
// File: apps/web/components/ingestion/__tests__/single-url-import-form.test.tsx

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SingleUrlImportForm } from '../single-url-import-form';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

describe('SingleUrlImportForm', () => {
  it('renders form fields correctly', () => {
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <SingleUrlImportForm />
      </QueryClientProvider>
    );

    expect(screen.getByLabelText(/Listing URL/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Priority/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Import Listing/i })).toBeInTheDocument();
  });

  it('validates URL format', async () => {
    const queryClient = createTestQueryClient();
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <SingleUrlImportForm />
      </QueryClientProvider>
    );

    const input = screen.getByLabelText(/Listing URL/i);
    await user.type(input, 'invalid-url');
    await user.tab(); // Trigger blur

    expect(await screen.findByText(/valid URL/i)).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    const queryClient = createTestQueryClient();
    const user = userEvent.setup();
    const onSuccess = jest.fn();

    // Mock API
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ job_id: 'job-123', status: 'queued' }),
      })
    ) as jest.Mock;

    render(
      <QueryClientProvider client={queryClient}>
        <SingleUrlImportForm onSuccess={onSuccess} />
      </QueryClientProvider>
    );

    const input = screen.getByLabelText(/Listing URL/i);
    await user.type(input, 'https://ebay.com/itm/12345');

    const submitButton = screen.getByRole('button', { name: /Import Listing/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/ingest/single'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});
```

### Accessibility Tests

```typescript
// File: apps/web/components/ingestion/__tests__/accessibility.test.tsx

import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import { SingleUrlImportForm } from '../single-url-import-form';

describe('SingleUrlImportForm Accessibility', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(<SingleUrlImportForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('announces status changes to screen readers', async () => {
    const { container } = render(<SingleUrlImportForm />);
    const liveRegion = container.querySelector('[role="status"]');

    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
  });
});
```

---

## 10. Integration with Listings Page

### Example Usage in Listings Page

```typescript
// File: apps/web/app/listings/page.tsx (additions)

import { SingleUrlImportForm } from '@/components/ingestion/single-url-import-form';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export default function ListingsPage() {
  const [importDialogOpen, setImportDialogOpen] = useState(false);

  return (
    <div className="space-y-6">
      {/* Existing listings page content */}

      {/* Add import dialog */}
      <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline">
            Import from URL
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <SingleUrlImportForm
            compact
            onSuccess={(result) => {
              setImportDialogOpen(false);
              // Refresh listings table
              router.refresh();
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

---

## 11. Performance Considerations

### Code Splitting

```typescript
// Lazy load the component to reduce initial bundle size
import dynamic from 'next/dynamic';

const SingleUrlImportForm = dynamic(
  () => import('@/components/ingestion/single-url-import-form').then(mod => mod.SingleUrlImportForm),
  { loading: () => <p>Loading...</p> }
);
```

### Memoization

```typescript
import { memo } from 'react';

export const IngestionStatusDisplay = memo(function IngestionStatusDisplay(props) {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison function
  return prevProps.state.status === nextProps.state.status;
});
```

---

## 12. Implementation Checklist

### Phase 1: Core Component (8 hours)
- [ ] Create type definitions (`types.ts`)
- [ ] Create validation schema (`schemas.ts`)
- [ ] Implement API client functions (`lib/api/ingestion.ts`)
- [ ] Create main form component (`single-url-import-form.tsx`)
- [ ] Add form validation and error handling
- [ ] Test basic form submission

### Phase 2: Status Polling (6 hours)
- [ ] Create polling hook (`hooks/use-ingestion-job.ts`)
- [ ] Implement status display component (`ingestion-status-display.tsx`)
- [ ] Add progress indicator and elapsed timer
- [ ] Implement polling termination logic
- [ ] Test polling edge cases

### Phase 3: Success & Error States (4 hours)
- [ ] Create success result component (`import-success-result.tsx`)
- [ ] Add provenance and quality badges
- [ ] Implement error display with retry
- [ ] Create error message mapping
- [ ] Test all state transitions

### Phase 4: Accessibility & Polish (2 hours)
- [ ] Add ARIA labels and roles
- [ ] Implement focus management
- [ ] Add keyboard navigation
- [ ] Test with screen reader (NVDA/JAWS)
- [ ] Run axe accessibility audit
- [ ] Fix any violations

---

## 13. File Locations (Absolute Paths)

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

**Status**: Ready for Implementation
**Estimated Time**: 20 hours across 4 phases
**Dependencies**: Phase 3 backend complete (API endpoints functional)
