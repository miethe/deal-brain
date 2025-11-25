/**
 * PERF-004 Rendering Benchmark Script
 *
 * This script helps measure the performance improvements from React rendering optimizations.
 *
 * Usage:
 * 1. Import this component in your test page
 * 2. Wrap ListingsTable with PerformanceMonitor
 * 3. Perform actions (sort, filter, edit)
 * 4. Check console for performance metrics
 */

import { Profiler, ProfilerOnRenderCallback } from 'react';

interface PerformanceMetrics {
  componentId: string;
  phase: 'mount' | 'update';
  actualDuration: number;
  baseDuration: number;
  startTime: number;
  commitTime: number;
  timestamp: number;
}

const metrics: PerformanceMetrics[] = [];

export const onRenderCallback: ProfilerOnRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) => {
  const metric: PerformanceMetrics = {
    componentId: id,
    phase,
    actualDuration,
    baseDuration,
    startTime,
    commitTime,
    timestamp: Date.now()
  };

  metrics.push(metric);

  // Log to console
  console.log('[PERF]', {
    component: id,
    phase,
    renderTime: `${actualDuration.toFixed(2)}ms`,
    baseTime: `${baseDuration.toFixed(2)}ms`,
    optimization: `${((1 - actualDuration / baseDuration) * 100).toFixed(1)}%`
  });

  // Track render count
  const renderCount = metrics.filter(m => m.componentId === id).length;
  if (renderCount % 10 === 0) {
    console.log(`[PERF] ${id} has rendered ${renderCount} times`);
  }
};

export function PerformanceMonitor({
  id,
  children
}: {
  id: string;
  children: React.ReactNode
}) {
  return (
    <Profiler id={id} onRender={onRenderCallback}>
      {children}
    </Profiler>
  );
}

/**
 * Get performance summary
 */
export function getPerformanceSummary(componentId: string) {
  const componentMetrics = metrics.filter(m => m.componentId === componentId);

  if (componentMetrics.length === 0) {
    return { error: 'No metrics found' };
  }

  const mountMetrics = componentMetrics.filter(m => m.phase === 'mount');
  const updateMetrics = componentMetrics.filter(m => m.phase === 'update');

  const avgActualDuration = componentMetrics.reduce((sum, m) => sum + m.actualDuration, 0) / componentMetrics.length;
  const avgBaseDuration = componentMetrics.reduce((sum, m) => sum + m.baseDuration, 0) / componentMetrics.length;

  return {
    totalRenders: componentMetrics.length,
    mountRenders: mountMetrics.length,
    updateRenders: updateMetrics.length,
    avgRenderTime: avgActualDuration.toFixed(2) + 'ms',
    avgBaseTime: avgBaseDuration.toFixed(2) + 'ms',
    optimizationGain: ((1 - avgActualDuration / avgBaseDuration) * 100).toFixed(1) + '%',
    metrics: componentMetrics
  };
}

/**
 * Reset metrics
 */
export function resetMetrics() {
  metrics.length = 0;
  console.log('[PERF] Metrics reset');
}

/**
 * Export metrics to JSON
 */
export function exportMetrics() {
  const blob = new Blob([JSON.stringify(metrics, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `perf-metrics-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  console.log('[PERF] Metrics exported');
}

// Make functions available in browser console
if (typeof window !== 'undefined') {
  (window as any).perfSummary = getPerformanceSummary;
  (window as any).perfReset = resetMetrics;
  (window as any).perfExport = exportMetrics;

  console.log('[PERF] Performance monitoring active. Use:');
  console.log('  perfSummary("ListingsTable") - Get performance summary');
  console.log('  perfReset() - Reset metrics');
  console.log('  perfExport() - Export metrics to JSON');
}
