/**
 * Performance Monitoring Verification
 *
 * This file demonstrates how to verify that performance monitoring is working correctly.
 * Run this in dev mode and check the browser console for performance warnings.
 *
 * Expected Console Output (in development mode):
 * - "⚠️ Slow render: SlowComponent (mount) took XXms" (if render > 50ms)
 * - "⚠️ Slow interaction: test_interaction took XXms" (if interaction > 200ms)
 * - Performance marks/measures visible in DevTools Performance tab
 *
 * In production mode:
 * - No console warnings
 * - No performance overhead
 */

import React, { Profiler, useState } from 'react';
import { measureInteraction, logRenderPerformance } from '../../../lib/performance';

// Simulate a slow component (intentionally slow for testing)
function SlowComponent() {
  const [count, setCount] = useState(0);

  // Simulate expensive computation
  const startTime = performance.now();
  while (performance.now() - startTime < 60) {
    // Busy wait to simulate slow render (>50ms threshold)
  }

  return (
    <div>
      <p>Slow Component Render Count: {count}</p>
      <button
        onClick={() => {
          measureInteraction('test_interaction', () => {
            // Simulate slow interaction
            const start = performance.now();
            while (performance.now() - start < 220) {
              // Busy wait to exceed 200ms threshold
            }
            setCount(count + 1);
          });
        }}
      >
        Trigger Slow Interaction
      </button>
    </div>
  );
}

// Wrapper with Profiler
export function PerformanceVerificationDemo() {
  return (
    <div style={{ padding: '20px' }}>
      <h2>Performance Monitoring Verification</h2>
      <p>
        <strong>Instructions:</strong> Open browser DevTools console and click the button below.
      </p>
      <p>
        <strong>Expected in Dev Mode:</strong> You should see console warnings for slow render
        (component mount > 50ms) and slow interaction (button click > 200ms).
      </p>
      <p>
        <strong>Expected in Production:</strong> No warnings, zero overhead.
      </p>
      <hr style={{ margin: '20px 0' }} />
      <Profiler id="SlowComponent" onRender={logRenderPerformance}>
        <SlowComponent />
      </Profiler>
      <hr style={{ margin: '20px 0' }} />
      <p>
        <strong>Dev Mode:</strong> {process.env.NODE_ENV === 'development' ? 'YES' : 'NO'}
      </p>
    </div>
  );
}

/**
 * Verification Checklist:
 *
 * 1. Performance Utility (lib/performance.ts)
 *    - ✅ measureInteraction() wrapper for user actions
 *    - ✅ Performance.mark/measure for timing
 *    - ✅ Dev-mode only execution (zero production overhead)
 *    - ✅ Console warnings for slow operations (>200ms)
 *
 * 2. React Profiler Integration
 *    - ✅ Wrap ListingsTable in <Profiler> component
 *    - ✅ Log slow renders (>50ms)
 *    - ✅ Track mount vs update performance
 *
 * 3. Instrumented Interactions
 *    - ✅ Column sorting
 *    - ✅ Filtering
 *    - ✅ Quick search (debounced at 200ms)
 *    - ✅ Bulk edit submission
 *    - ✅ Inline cell save
 *
 * 4. Zero Production Overhead
 *    - ✅ All instrumentation wrapped in process.env.NODE_ENV === 'development' checks
 *    - ✅ No external dependencies
 *    - ✅ Uses native browser APIs only
 */
