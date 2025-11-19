/**
 * React Query hooks for CPU API integration
 *
 * Provides hooks for:
 * - Fetching all CPUs with optional analytics data, sorting, and filtering
 * - Fetching detailed CPU information with market data
 * - Fetching CPU statistics for filter options
 *
 * Uses React Query for caching, background updates, and error handling.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/lib/utils';
import type { CPURecord, CPUDetail, CPUStatistics } from '@/types/cpus';

export interface UseCPUsOptions {
  include_analytics?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  only_with_listings?: boolean;
}

/**
 * Fetch all CPUs with optional analytics data, sorting, and filtering
 *
 * Analytics includes:
 * - Price targets (good, great, fair) with confidence levels
 * - Performance value metrics ($/PassMark ratios and percentile rankings)
 * - Active listings count per CPU
 *
 * Sorting support:
 * - Sort by: name, manufacturer, cores, threads, tdp_w, cpu_mark_multi, cpu_mark_single, release_year, listings_count
 * - Sort order: asc (ascending) or desc (descending)
 *
 * Filtering support:
 * - only_with_listings: Show only CPUs with active listings
 *
 * @param include_analytics - Whether to include price targets and performance values (default: true)
 * @param sort_by - Field to sort by (default: "name")
 * @param sort_order - Sort direction "asc" or "desc" (default: "asc")
 * @param only_with_listings - Show only CPUs with active listings (default: false)
 * @returns Query result with CPU records array
 *
 * @example
 * ```tsx
 * // Basic usage
 * const { data: cpus, isLoading, error } = useCPUs();
 *
 * // Legacy boolean signature is still supported
 * const { data: cpusWithAnalytics } = useCPUs(true);
 *
 * // With sorting
 * const { data: cpus } = useCPUs({
 *   sort_by: 'listings_count',
 *   sort_order: 'desc',
 * });
 *
 * // With filters
 * const { data: cpus } = useCPUs({
 *   only_with_listings: true,
 *   sort_by: 'cpu_mark_multi',
 *   sort_order: 'desc',
 * });
 *
 * if (isLoading) return <LoadingSpinner />;
 * if (error) return <ErrorMessage error={error} />;
 *
 * return <CPUTable cpus={cpus} />;
 * ```
 */
export function useCPUs(optionsOrIncludeAnalytics?: boolean | UseCPUsOptions) {
  const normalizedOptions: UseCPUsOptions =
    typeof optionsOrIncludeAnalytics === 'boolean' || optionsOrIncludeAnalytics === undefined
      ? { include_analytics: optionsOrIncludeAnalytics ?? true }
      : optionsOrIncludeAnalytics;

  const {
    include_analytics = true,
    sort_by = 'name',
    sort_order = 'asc',
    only_with_listings = false,
  } = normalizedOptions;

  return useQuery({
    queryKey: ['cpus', { include_analytics, sort_by, sort_order, only_with_listings }],
    queryFn: () => {
      const params = new URLSearchParams();
      if (include_analytics) {
        params.set('include_analytics', 'true');
      }
      if (sort_by) {
        params.set('sort_by', sort_by);
      }
      if (sort_order) {
        params.set('sort_order', sort_order);
      }
      if (only_with_listings) {
        params.set('only_with_listings', 'true');
      }
      return apiFetch<CPURecord[]>(`/v1/cpus?${params}`);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - analytics data updates periodically
  });
}

/**
 * Fetch detailed CPU information with market data
 *
 * Includes:
 * - Full CPU specifications and analytics
 * - Top 10 associated listings (cheapest by adjusted price)
 * - Price distribution for histogram visualization
 *
 * This hook is conditionally enabled - it only fetches when an ID is provided.
 * Useful for detail modals/panels that may be closed.
 *
 * @param id - CPU ID (null to disable query)
 * @returns Query result with CPU detail (includes associated listings and price distribution)
 *
 * @example
 * ```tsx
 * const [selectedCPUId, setSelectedCPUId] = useState<number | null>(null);
 * const { data: cpuDetail, isLoading } = useCPUDetail(selectedCPUId);
 *
 * return (
 *   <>
 *     <CPUList onSelect={setSelectedCPUId} />
 *     {selectedCPUId && (
 *       <CPUDetailModal
 *         cpu={cpuDetail}
 *         isLoading={isLoading}
 *         onClose={() => setSelectedCPUId(null)}
 *       />
 *     )}
 *   </>
 * );
 * ```
 */
export function useCPUDetail(id: number | null) {
  return useQuery({
    queryKey: ['cpus', id, 'detail'],
    queryFn: () => apiFetch<CPUDetail>(`/v1/cpus/${id}`),
    enabled: id !== null, // Only fetch if ID is provided
    staleTime: 3 * 60 * 1000, // 3 minutes - detail data includes market data
  });
}

/**
 * Fetch CPU statistics for filter options
 *
 * Returns global statistics for building filter UI controls:
 * - Available manufacturers and sockets (for dropdowns)
 * - Min/max ranges for cores, TDP, years (for sliders)
 * - Total CPU count (for display)
 *
 * Statistics rarely change, so they're cached for 10 minutes.
 *
 * @returns Query result with global CPU statistics
 *
 * @example
 * ```tsx
 * const { data: stats } = useCPUStatistics();
 *
 * return (
 *   <CPUFilters
 *     manufacturers={stats?.manufacturers ?? []}
 *     sockets={stats?.sockets ?? []}
 *     coreRange={stats?.core_range ?? [2, 64]}
 *     tdpRange={stats?.tdp_range ?? [15, 280]}
 *     yearRange={stats?.year_range ?? [2015, 2025]}
 *   />
 * );
 * ```
 */
export function useCPUStatistics() {
  return useQuery({
    queryKey: ['cpus', 'statistics'],
    queryFn: () => apiFetch<CPUStatistics>('/v1/cpus/statistics/global'),
    staleTime: 10 * 60 * 1000, // 10 minutes - statistics rarely change
  });
}
