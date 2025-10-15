"use client";

import { useQuery } from "@tanstack/react-query";
import { API_URL } from "../lib/utils";

interface FieldValuesResponse {
  field_name: string;
  values: string[];
  count: number;
}

interface UseFieldValuesOptions {
  fieldName: string | null;
  limit?: number;
  search?: string;
  enabled?: boolean;
}

/**
 * Hook to fetch existing values for a field (for autocomplete)
 * @param fieldName - Full field name (e.g., "listing.condition", "cpu.manufacturer")
 * @param limit - Maximum number of values to fetch (default: 100, max: 1000)
 * @param search - Optional search filter
 * @param enabled - Whether the query should run (default: true)
 */
export function useFieldValues({
  fieldName,
  limit = 100,
  search,
  enabled = true,
}: UseFieldValuesOptions) {
  return useQuery({
    queryKey: ["field-values", fieldName, limit, search],
    queryFn: async (): Promise<FieldValuesResponse> => {
      if (!fieldName) {
        throw new Error("fieldName is required");
      }

      const params = new URLSearchParams();
      if (limit) params.append("limit", limit.toString());
      if (search) params.append("search", search);

      const url = `${API_URL}/v1/fields/${fieldName}/values?${params.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch field values: ${response.statusText}`);
      }

      return response.json();
    },
    enabled: enabled && !!fieldName,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1, // Only retry once on failure
  });
}
