/**
 * Hook for fetching valuation thresholds from settings API
 */
import { useQuery } from '@tanstack/react-query';
import { ValuationThresholds, DEFAULT_THRESHOLDS } from '@/lib/valuation-utils';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useValuationThresholds() {
  return useQuery<ValuationThresholds>({
    queryKey: ['settings', 'valuation_thresholds'],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/settings/valuation_thresholds`);
      if (!response.ok) {
        // Return defaults if settings not found
        return DEFAULT_THRESHOLDS;
      }
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    placeholderData: DEFAULT_THRESHOLDS,
  });
}
