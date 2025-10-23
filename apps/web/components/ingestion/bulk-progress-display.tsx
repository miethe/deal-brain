'use client';

import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Loader2, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { BulkProgressDisplayProps } from './bulk-import-types';

/**
 * Calculate progress percentage from bulk job data
 */
function calculateProgress(completed: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
}

/**
 * Get status message based on job status and counts
 */
function getStatusMessage(
  status: string,
  total: number,
  completed: number,
  success: number,
  failed: number
): string {
  if (status === 'queued') {
    return 'Queued, waiting to start...';
  } else if (status === 'running') {
    return `Processing ${total - completed} remaining URL${total - completed !== 1 ? 's' : ''}...`;
  } else if (status === 'complete') {
    return success === total
      ? 'All URLs imported successfully!'
      : `Completed with ${failed} error${failed !== 1 ? 's' : ''}`;
  } else if (status === 'partial') {
    return `Completed: ${success} successful, ${failed} failed`;
  } else if (status === 'failed') {
    return 'All imports failed';
  }
  return 'Unknown status';
}

export function BulkProgressDisplay({ data, elapsed }: BulkProgressDisplayProps) {
  const progress = calculateProgress(data.completed, data.total_urls);
  const message = getStatusMessage(
    data.status,
    data.total_urls,
    data.completed,
    data.success,
    data.failed
  );
  const isComplete = data.status === 'complete' || data.status === 'partial' || data.status === 'failed';

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {data.status === 'running' && (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            )}
            {data.status === 'complete' && (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            )}
            {data.status === 'partial' && (
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
            )}
            {data.status === 'failed' && (
              <XCircle className="h-4 w-4 text-destructive" />
            )}
            <span className="text-sm font-medium">{message}</span>
          </div>
          <Badge variant="outline" className="text-xs tabular-nums">
            {elapsed}s
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full transition-all duration-300 ease-out',
                data.status === 'complete' && 'bg-green-600',
                data.status === 'partial' && 'bg-yellow-600',
                data.status === 'failed' && 'bg-destructive',
                data.status === 'running' && 'bg-primary',
                data.status === 'queued' && 'bg-muted-foreground'
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-sm text-muted-foreground tabular-nums w-12 text-right">
            {progress}%
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {/* Total */}
        <div className="bg-muted/50 rounded-lg p-3">
          <div className="text-2xl font-bold tabular-nums">{data.total_urls}</div>
          <div className="text-xs text-muted-foreground">Total</div>
        </div>

        {/* Success */}
        <div className="bg-green-50 dark:bg-green-950/20 rounded-lg p-3">
          <div className="text-2xl font-bold text-green-700 dark:text-green-400 tabular-nums">
            {data.success}
          </div>
          <div className="text-xs text-green-600 dark:text-green-500">Success</div>
        </div>

        {/* Failed */}
        <div className="bg-red-50 dark:bg-red-950/20 rounded-lg p-3">
          <div className="text-2xl font-bold text-red-700 dark:text-red-400 tabular-nums">
            {data.failed}
          </div>
          <div className="text-xs text-red-600 dark:text-red-500">Failed</div>
        </div>

        {/* Running */}
        <div className="bg-blue-50 dark:bg-blue-950/20 rounded-lg p-3">
          <div className="text-2xl font-bold text-blue-700 dark:text-blue-400 tabular-nums">
            {data.running}
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-500">Running</div>
        </div>

        {/* Queued */}
        <div className="bg-gray-50 dark:bg-gray-950/20 rounded-lg p-3">
          <div className="text-2xl font-bold text-gray-700 dark:text-gray-400 tabular-nums">
            {data.queued}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-500">Queued</div>
        </div>
      </div>

      {/* Screen reader announcement */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        Bulk import progress: {progress}% complete, {message}
      </div>
    </div>
  );
}
