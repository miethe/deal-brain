'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Download, RotateCcw } from 'lucide-react';
import { BulkUploadForm } from './bulk-upload-form';
import { BulkProgressDisplay } from './bulk-progress-display';
import { BulkStatusTable } from './bulk-status-table';
import { submitBulkUrlImportFile, submitBulkUrlImportUrls, downloadBulkResultsCSV } from '@/lib/api/bulk-ingestion';
import { useBulkIngestionJob } from '@/hooks/use-bulk-ingestion-job';
import type {
  BulkImportDialogProps,
  BulkImportState,
  BulkImportError,
} from './bulk-import-types';

export function BulkImportDialog({
  open,
  onOpenChange,
  onSuccess,
  onError,
}: BulkImportDialogProps) {
  const [importState, setImportState] = useState<BulkImportState>({ status: 'idle' });
  const [elapsed, setElapsed] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const rowsPerPage = 50;

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async (data: FormData | string[]) => {
      if (data instanceof FormData) {
        return submitBulkUrlImportFile(data.get('file') as File);
      } else {
        return submitBulkUrlImportUrls(data);
      }
    },
    onMutate: (data) => {
      const mode = data instanceof FormData ? 'file' : 'paste';
      const count = data instanceof FormData ? 0 : data.length;
      setImportState({ status: 'uploading', mode, count });
    },
    onSuccess: (response) => {
      setImportState({
        status: 'polling',
        bulkJobId: response.bulk_job_id,
        startTime: Date.now(),
      });
    },
    onError: (error: Error) => {
      const importError: BulkImportError = {
        code: 'UPLOAD_ERROR',
        message: error.message || 'Failed to submit bulk import',
      };
      setImportState({ status: 'error', error: importError });
      onError?.(importError);
    },
  });

  // Polling for job status
  const bulkJobId = importState.status === 'polling' || importState.status === 'complete'
    ? importState.bulkJobId
    : null;
  const pollingEnabled = importState.status === 'polling';

  const { data: jobData, refetch } = useBulkIngestionJob({
    bulkJobId,
    offset: currentPage * rowsPerPage,
    limit: rowsPerPage,
    enabled: pollingEnabled,
  });

  // Track elapsed time during polling
  useEffect(() => {
    if (importState.status === 'polling') {
      const interval = setInterval(() => {
        setElapsed(Math.floor((Date.now() - importState.startTime) / 1000));
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setElapsed(0);
    }
  }, [importState]);

  // Handle job status updates
  useEffect(() => {
    if (jobData && importState.status === 'polling') {
      if (jobData.status === 'complete' || jobData.status === 'partial' || jobData.status === 'failed') {
        // Job finished
        setImportState({
          status: 'complete',
          bulkJobId: jobData.bulk_job_id,
          data: jobData,
        });
        onSuccess?.(jobData);
      }
    }
  }, [jobData, importState.status, onSuccess]);

  const handleSubmit = (data: FormData | string[]) => {
    submitMutation.mutate(data);
  };

  const handleReset = () => {
    setImportState({ status: 'idle' });
    setElapsed(0);
    setCurrentPage(0);
    submitMutation.reset();
  };

  const handleDownload = () => {
    if (importState.status === 'complete' && importState.data) {
      const timestamp = new Date().toISOString().split('T')[0];
      downloadBulkResultsCSV(
        importState.data,
        `bulk-import-${importState.bulkJobId.substring(0, 8)}-${timestamp}.csv`
      );
    }
  };

  const handleRefresh = () => {
    refetch();
  };

  const isComplete = importState.status === 'complete';
  const canDownload = isComplete && importState.data;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Bulk URL Import</DialogTitle>
          <DialogDescription>
            Upload a CSV or JSON file, or paste up to 1000 URLs for batch import
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Idle State: Show Upload Form */}
          {importState.status === 'idle' && (
            <BulkUploadForm
              onSubmit={handleSubmit}
              disabled={false}
              error={importState.status === 'error' ? importState.error : undefined}
            />
          )}

          {/* Uploading State */}
          {importState.status === 'uploading' && (
            <div className="text-center py-8">
              <div className="inline-flex items-center gap-2 text-muted-foreground">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                <span>Uploading and validating...</span>
              </div>
            </div>
          )}

          {/* Polling State: Show Progress */}
          {importState.status === 'polling' && jobData && (
            <div className="space-y-6">
              <BulkProgressDisplay data={jobData} elapsed={elapsed} />
              <BulkStatusTable
                bulkJobId={importState.bulkJobId}
                data={jobData}
                onRefresh={handleRefresh}
              />
            </div>
          )}

          {/* Complete State: Show Final Results */}
          {importState.status === 'complete' && importState.data && (
            <div className="space-y-6">
              <BulkProgressDisplay data={importState.data} elapsed={elapsed} />
              <BulkStatusTable
                bulkJobId={importState.bulkJobId}
                data={importState.data}
                onRefresh={handleRefresh}
              />

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={handleReset}
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Import Another Batch
                </Button>
                <Button
                  variant="default"
                  onClick={handleDownload}
                  disabled={!canDownload}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Results CSV
                </Button>
              </div>
            </div>
          )}

          {/* Error State */}
          {importState.status === 'error' && (
            <div className="space-y-4">
              <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
                <h4 className="font-medium text-destructive mb-2">Import Failed</h4>
                <p className="text-sm text-destructive/90">{importState.error.message}</p>
                {importState.error.details && (
                  <details className="mt-3 text-xs">
                    <summary className="cursor-pointer hover:underline">
                      Show technical details
                    </summary>
                    <pre className="mt-2 p-2 bg-muted rounded overflow-auto max-h-32">
                      {JSON.stringify(importState.error.details, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
              <div className="flex justify-end">
                <Button variant="outline" onClick={handleReset}>
                  Try Again
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Screen reader live region for status updates */}
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {importState.status === 'idle' && 'Ready to upload'}
          {importState.status === 'uploading' && 'Uploading file'}
          {importState.status === 'polling' && jobData &&
            `Processing: ${jobData.completed} of ${jobData.total_urls} complete`}
          {importState.status === 'complete' && 'Import complete'}
          {importState.status === 'error' && `Error: ${importState.error.message}`}
        </div>
      </DialogContent>
    </Dialog>
  );
}
