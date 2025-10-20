'use client';

import { useState } from 'react';
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
import type { ImportState, SingleUrlImportFormProps, ImportSuccessResult, ImportPriority } from './types';
import { cn } from '@/lib/utils';

// Helper function to determine if an error is retryable
function isRetryableError(code: string): boolean {
  const retryableCodes = ['TIMEOUT', 'RATE_LIMITED', 'NETWORK_ERROR', 'TEMPORARY_ERROR'];
  return retryableCodes.includes(code);
}

export function SingleUrlImportForm({
  onSuccess,
  onError,
  onReset,
  defaultUrl,
  defaultPriority = 'normal',
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
      setImportState({
        status: 'submitting',
        url: watch('url'),
        priority: watch('priority') as ImportPriority
      });
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
  const pollingEnabled = importState.status === 'polling';

  // Use effect to handle polling results
  const { data: jobData } = useIngestionJob({
    jobId,
    enabled: pollingEnabled,
  });

  // Handle job status updates
  if (jobData && importState.status === 'polling') {
    if (jobData.status === 'complete' && jobData.result) {
      const successResult: ImportSuccessResult = {
        jobId: jobData.job_id,
        listingId: jobData.result.listing_id,
        title: jobData.result.title || 'Untitled Listing',
        provenance: jobData.result.provenance,
        quality: jobData.result.quality,
        createdAt: jobData.result.created_at,
      };
      // Only update state once
      if (importState.status === 'polling') {
        setImportState({ status: 'success', result: successResult });
        onSuccess?.(successResult);
      }
    } else if (jobData.status === 'failed' && jobData.error) {
      const importError = {
        code: jobData.error.code,
        message: jobData.error.message,
        details: jobData.error.details,
        retryable: isRetryableError(jobData.error.code),
      };
      // Only update state once
      if (importState.status === 'polling') {
        setImportState({ status: 'error', error: importError });
        onError?.(importError);
      }
    }
  }

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
      const priority = watch('priority') as ImportPriority;
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
              onValueChange={(value) => setValue('priority', value as ImportPriority)}
              disabled={importState.status !== 'idle'}
            >
              <SelectTrigger id="priority" aria-label="Import priority">
                <SelectValue placeholder="Select priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="high">High - Process immediately</SelectItem>
                <SelectItem value="normal">Normal - Standard queue</SelectItem>
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
