'use client';

import { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, RotateCcw, CheckCircle2 } from 'lucide-react';
import { ImportSuccessResult } from './import-success-result';
import type { IngestionStatusDisplayProps } from './types';

export function IngestionStatusDisplay({
  state,
  jobData,
  onRetry,
  onViewListing,
  onImportAnother,
}: IngestionStatusDisplayProps) {
  const [elapsed, setElapsed] = useState(0);
  const [showCompletion, setShowCompletion] = useState(false);

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

  // Show completion animation when transitioning to success
  useEffect(() => {
    if (state.status === 'success') {
      setShowCompletion(true);
      const timeout = setTimeout(() => setShowCompletion(false), 500);
      return () => clearTimeout(timeout);
    }
  }, [state.status]);

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
    // Use real progress from backend, fallback to time-based if unavailable
    const backendProgress = jobData?.progress_pct;
    const progress = backendProgress ?? calculateProgress(elapsed);

    // Log for debugging during development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Progress] ${progress}% (backend: ${backendProgress ?? 'null'}, elapsed: ${elapsed}s)`);
    }

    const message = getPollingMessage(elapsed, backendProgress);

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
                    className="h-full bg-primary transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                    role="progressbar"
                    aria-valuenow={progress}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label="Import progress"
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
          Importing listing, {elapsed} seconds elapsed, {progress}% complete, {message}
        </div>
      </Alert>
    );
  }

  // Success state - show completion animation first
  if (state.status === 'success') {
    if (showCompletion) {
      return (
        <Alert className="border-green-500/50 bg-green-50/50">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
            <div className="flex-1 space-y-2">
              <div className="flex items-center justify-between">
                <AlertTitle className="text-sm font-semibold text-green-700">
                  Import complete!
                </AlertTitle>
              </div>
              <AlertDescription className="text-xs space-y-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-600 transition-all duration-500 ease-out"
                      style={{ width: '100%' }}
                    />
                  </div>
                  <span className="text-green-700 tabular-nums w-10 text-right font-semibold">
                    100%
                  </span>
                </div>
                <p className="text-green-700">Processing complete</p>
              </AlertDescription>
            </div>
          </div>
        </Alert>
      );
    }

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

/**
 * Calculate cosmetic progress based on elapsed time.
 * Used as fallback when backend doesn't provide progress_pct.
 * @deprecated Use backend progress_pct when available
 */
function calculateProgress(elapsed: number): number {
  if (elapsed < 5) {
    // 0-5s: 15-50% (linear)
    return Math.round(15 + (elapsed / 5) * 35);
  } else if (elapsed < 15) {
    // 5-15s: 50-85% (slower)
    return Math.round(50 + ((elapsed - 5) / 10) * 35);
  } else if (elapsed < 30) {
    // 15-30s: 85-96% (very slow, asymptotic)
    return Math.min(96, Math.round(85 + ((elapsed - 15) / 15) * 11));
  } else {
    // >30s: 96-98% (extremely slow, to avoid looking stuck at 100%)
    return Math.min(98, Math.round(96 + ((elapsed - 30) / 60) * 2));
  }
}

/**
 * Get status message based on progress or elapsed time.
 * Prioritizes backend progress when available, falls back to time-based messages.
 */
function getPollingMessage(elapsed: number, backendProgress: number | null | undefined): string {
  // If we have backend progress, use progress-based messages
  if (backendProgress !== null && backendProgress !== undefined) {
    if (backendProgress < 20) {
      return 'Starting import...';
    } else if (backendProgress < 40) {
      return 'Extracting data from URL...';
    } else if (backendProgress < 70) {
      return 'Normalizing and enriching data...';
    } else if (backendProgress < 90) {
      return 'Saving to database...';
    } else {
      return 'Finalizing import...';
    }
  }

  // Fallback to time-based messages if no backend progress
  if (elapsed < 2) {
    return 'Job queued, waiting for worker...';
  } else if (elapsed < 5) {
    return 'Extracting data from marketplace...';
  } else if (elapsed < 10) {
    return 'Processing product details...';
  } else if (elapsed < 20) {
    return 'Enriching with component data...';
  } else if (elapsed < 30) {
    return 'Finalizing listing data...';
  } else {
    return 'Taking longer than expected...';
  }
}
