import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { calculateBuild } from "@/lib/api/builder";
import { useBuilder } from "@/components/builder/builder-provider";

/**
 * Custom hook for real-time build calculations with debouncing
 *
 * Features:
 * - Debounces component changes (300ms)
 * - Automatically calls calculateBuild API
 * - Updates BuilderProvider state with results
 * - Handles loading and error states
 * - Only calculates when CPU is selected (required)
 */
export function useBuilderCalculations() {
  const { state, dispatch } = useBuilder();
  const [debouncedComponents, setDebouncedComponents] = useState(state.components);

  // Debounce component changes to avoid excessive API calls
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedComponents(state.components);
    }, 300);

    return () => clearTimeout(timer);
  }, [state.components]);

  // Query for calculations with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ["builder-calculate", debouncedComponents],
    queryFn: async () => {
      // Only call API if CPU is selected (required component)
      if (!debouncedComponents.cpu_id) {
        return null;
      }

      // Filter out null values and build API payload
      const components: any = {
        cpu_id: debouncedComponents.cpu_id,
      };

      // Add optional components if selected
      if (debouncedComponents.gpu_id) components.gpu_id = debouncedComponents.gpu_id;
      if (debouncedComponents.ram_spec_id)
        components.ram_spec_id = debouncedComponents.ram_spec_id;
      if (debouncedComponents.storage_spec_id)
        components.storage_spec_id = debouncedComponents.storage_spec_id;
      if (debouncedComponents.psu_spec_id)
        components.psu_spec_id = debouncedComponents.psu_spec_id;
      if (debouncedComponents.case_spec_id)
        components.case_spec_id = debouncedComponents.case_spec_id;

      return calculateBuild(components);
    },
    enabled: !!debouncedComponents.cpu_id, // Only run query if CPU selected
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1, // Retry once on failure
  });

  // Update context when calculations complete
  useEffect(() => {
    if (data) {
      dispatch({
        type: "SET_CALCULATIONS",
        payload: {
          valuation: data.valuation,
          metrics: data.metrics,
        },
      });
    }
  }, [data, dispatch]);

  // Update loading state
  useEffect(() => {
    dispatch({ type: "SET_CALCULATING", payload: isLoading });
  }, [isLoading, dispatch]);

  // Update error state
  useEffect(() => {
    if (error) {
      dispatch({
        type: "SET_ERROR",
        payload: error instanceof Error ? error.message : "Calculation failed",
      });
    }
  }, [error, dispatch]);

  return {
    valuation: state.valuation,
    metrics: state.metrics,
    isCalculating: state.isCalculating,
    error: state.error,
  };
}
