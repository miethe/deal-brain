'use client';

import { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, RotateCcw } from 'lucide-react';
import { ImportSuccessResult } from './import-success-result';
import type { IngestionStatusDisplayProps } from './types';

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
    return Math.round(15 + (elapsed / 5) * 35);
  } else if (elapsed < 15) {
    // 5-15s: 50-85% (slower)
    return Math.round(50 + ((elapsed - 5) / 10) * 35);
  } else {
    // >15s: 85-95% (very slow, asymptotic)
    return Math.min(95, Math.round(85 + ((elapsed - 15) / 30) * 10));
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
