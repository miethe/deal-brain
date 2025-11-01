"use client";

/**
 * Performance Monitoring Utility
 *
 * Lightweight instrumentation for tracking interaction latency and render performance.
 * - Dev-mode only (zero production overhead)
 * - Console warnings for slow operations (>200ms)
 * - React Profiler integration support
 * - Performance marks/measures in DevTools
 *
 * @see ADR-004: Performance Monitoring Architecture
 */

// Performance thresholds (in milliseconds)
const SLOW_INTERACTION_THRESHOLD = 200;
const SLOW_RENDER_THRESHOLD = 50;

// Check if we're in development mode
const isDev = process.env.NODE_ENV === 'development';

/**
 * Measure the duration of a user interaction
 * Logs a warning if the interaction exceeds the slow threshold
 *
 * @param name - Descriptive name for the interaction (e.g., 'column_sort', 'bulk_edit_submit')
 * @param fn - The function to measure
 * @returns The result of the function execution
 *
 * @example
 * const handleSort = useCallback((columnId: string) => {
 *   measureInteraction('column_sort', () => {
 *     table.setSorting([{ id: columnId, desc: !sorting[0]?.desc }]);
 *   });
 * }, [table, sorting]);
 */
export function measureInteraction<T>(name: string, fn: () => T): T {
  if (!isDev) {
    return fn();
  }

  const markStart = `${name}_start`;
  const markEnd = `${name}_end`;
  const measureName = `interaction_${name}`;

  try {
    performance.mark(markStart);
    const result = fn();
    performance.mark(markEnd);

    const measure = performance.measure(measureName, markStart, markEnd);
    const duration = measure.duration;

    if (duration > SLOW_INTERACTION_THRESHOLD) {
      console.warn(
        `⚠️ Slow interaction: ${name} took ${duration.toFixed(2)}ms (threshold: ${SLOW_INTERACTION_THRESHOLD}ms)`
      );
    }

    // Clean up marks to avoid memory leaks
    performance.clearMarks(markStart);
    performance.clearMarks(markEnd);
    performance.clearMeasures(measureName);

    return result;
  } catch (error) {
    // If performance API fails, just execute the function
    console.error('Performance measurement failed:', error);
    return fn();
  }
}

/**
 * Measure the duration of an async interaction
 * Logs a warning if the interaction exceeds the slow threshold
 *
 * @param name - Descriptive name for the interaction
 * @param fn - The async function to measure
 * @returns A promise with the result of the function execution
 *
 * @example
 * const handleBulkUpdate = useCallback(async () => {
 *   await measureInteractionAsync('bulk_edit_submit', async () => {
 *     await apiFetch('/v1/listings/bulk-update', { method: 'POST', body: payload });
 *   });
 * }, []);
 */
export async function measureInteractionAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
  if (!isDev) {
    return fn();
  }

  const markStart = `${name}_start`;
  const markEnd = `${name}_end`;
  const measureName = `interaction_${name}`;

  try {
    performance.mark(markStart);
    const result = await fn();
    performance.mark(markEnd);

    const measure = performance.measure(measureName, markStart, markEnd);
    const duration = measure.duration;

    if (duration > SLOW_INTERACTION_THRESHOLD) {
      console.warn(
        `⚠️ Slow async interaction: ${name} took ${duration.toFixed(2)}ms (threshold: ${SLOW_INTERACTION_THRESHOLD}ms)`
      );
    }

    // Clean up marks to avoid memory leaks
    performance.clearMarks(markStart);
    performance.clearMarks(markEnd);
    performance.clearMeasures(measureName);

    return result;
  } catch (error) {
    // If performance API fails, just execute the function
    console.error('Performance measurement failed:', error);
    return fn();
  }
}

/**
 * React Profiler callback for logging slow component renders
 *
 * @param id - Component identifier
 * @param phase - 'mount', 'update', or 'nested-update'
 * @param actualDuration - Time spent rendering the committed update
 * @param baseDuration - Estimated time to render the entire subtree without memoization
 * @param startTime - When React began rendering this update
 * @param commitTime - When React committed this update
 * @param interactions - Set of interactions that were being traced (deprecated in React 18+)
 *
 * @example
 * <Profiler id="ListingsTable" onRender={logRenderPerformance}>
 *   <ListingsTable />
 * </Profiler>
 */
export function logRenderPerformance(
  id: string,
  phase: 'mount' | 'update' | 'nested-update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number,
  interactions: Set<any>
): void {
  if (!isDev) {
    return;
  }

  // Only log slow renders
  if (actualDuration > SLOW_RENDER_THRESHOLD) {
    console.warn(
      `⚠️ Slow render: ${id} (${phase}) took ${actualDuration.toFixed(2)}ms (threshold: ${SLOW_RENDER_THRESHOLD}ms)`,
      {
        phase,
        actualDuration: `${actualDuration.toFixed(2)}ms`,
        baseDuration: `${baseDuration.toFixed(2)}ms`,
        startTime,
        commitTime,
      }
    );
  }
}

/**
 * Start a performance measurement for a multi-step operation
 * Returns a function to complete the measurement
 *
 * @param name - Descriptive name for the operation
 * @returns A function to call when the operation completes
 *
 * @example
 * const finishMeasure = startMeasure('debounced_search');
 * // ... perform operation
 * finishMeasure();
 */
export function startMeasure(name: string): () => void {
  if (!isDev) {
    return () => {}; // No-op in production
  }

  const markStart = `${name}_start`;
  performance.mark(markStart);

  return () => {
    const markEnd = `${name}_end`;
    const measureName = `operation_${name}`;

    try {
      performance.mark(markEnd);
      const measure = performance.measure(measureName, markStart, markEnd);
      const duration = measure.duration;

      if (duration > SLOW_INTERACTION_THRESHOLD) {
        console.warn(
          `⚠️ Slow operation: ${name} took ${duration.toFixed(2)}ms (threshold: ${SLOW_INTERACTION_THRESHOLD}ms)`
        );
      }

      // Clean up
      performance.clearMarks(markStart);
      performance.clearMarks(markEnd);
      performance.clearMeasures(measureName);
    } catch (error) {
      console.error('Performance measurement failed:', error);
    }
  };
}

/**
 * Log API response time
 *
 * @param endpoint - API endpoint path
 * @param duration - Response time in milliseconds
 *
 * @example
 * const start = performance.now();
 * const response = await fetch(url);
 * logApiResponse('/v1/listings', performance.now() - start);
 */
export function logApiResponse(endpoint: string, duration: number): void {
  if (!isDev) {
    return;
  }

  if (duration > SLOW_INTERACTION_THRESHOLD) {
    console.warn(
      `⚠️ Slow API response: ${endpoint} took ${duration.toFixed(2)}ms (threshold: ${SLOW_INTERACTION_THRESHOLD}ms)`
    );
  }
}

/**
 * Get performance metrics summary
 * Returns a summary of all performance marks and measures
 *
 * @returns Object containing performance entries
 */
export function getPerformanceMetrics(): {
  marks: PerformanceEntry[];
  measures: PerformanceEntry[];
} {
  if (!isDev) {
    return { marks: [], measures: [] };
  }

  return {
    marks: performance.getEntriesByType('mark'),
    measures: performance.getEntriesByType('measure'),
  };
}

/**
 * Clear all performance marks and measures
 * Useful for cleaning up after batch operations
 */
export function clearPerformanceMetrics(): void {
  if (!isDev) {
    return;
  }

  performance.clearMarks();
  performance.clearMeasures();
}
