/**
 * Hook for fetching CPU mark thresholds from settings API
 *
 * Provides threshold configuration for CPU performance metric color coding
 * with automatic fallback to defaults and 5-minute cache.
 */
import { useQuery } from '@tanstack/react-query';
import { CpuMarkThresholds, DEFAULT_CPU_MARK_THRESHOLDS } from '@/lib/cpu-mark-utils';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch CPU mark thresholds from settings API with graceful fallback.
 *
 * Features:
 * - 5-minute stale time for reduced API calls
 * - Automatic fallback to defaults on error
 * - Always returns valid threshold data via placeholderData
 * - Type-safe with CpuMarkThresholds interface
 *
 * @returns React Query result with thresholds data
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { data: thresholds, isLoading } = useCpuMarkThresholds();
 *
 *   const style = getCpuMarkStyle(improvement, thresholds);
 *   // ...
 * }
 * ```
 */
export function useCpuMarkThresholds() {
  return useQuery<CpuMarkThresholds>({
    queryKey: ['settings', 'cpu_mark_thresholds'],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_URL}/settings/cpu_mark_thresholds`);
        if (!response.ok) {
          // Return defaults if settings not found (404) or other errors
          return DEFAULT_CPU_MARK_THRESHOLDS;
        }
        const data = await response.json();
        return data as CpuMarkThresholds;
      } catch (error) {
        // Network error or parse error - return defaults
        console.warn('Failed to fetch CPU mark thresholds, using defaults:', error);
        return DEFAULT_CPU_MARK_THRESHOLDS;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    placeholderData: DEFAULT_CPU_MARK_THRESHOLDS, // Always available immediately
    retry: 1, // Only retry once on failure
  });
}
