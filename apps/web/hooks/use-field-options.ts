"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_URL } from "../lib/utils";

interface FieldOption {
  label: string;
  value: string;
}

interface CreateOptionParams {
  entity: string;
  fieldKey: string;
  value: string;
}

/**
 * Hook to manage field options (for Global Fields integration)
 * @param entity - The entity type (e.g., "listing", "cpu", "gpu")
 * @param fieldKey - The field key (e.g., "ram_gb", "storage_type")
 */
export function useFieldOptions(entity: string, fieldKey: string) {
  const queryClient = useQueryClient();

  // Fetch options for a field
  const { data: options = [], isLoading } = useQuery<string[]>({
    queryKey: ["field-options", entity, fieldKey],
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/v1/fields-data/${entity}/${fieldKey}/options`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch field options");
      }
      const data = await response.json();
      return data.options || [];
    },
    // Only fetch if we have entity and fieldKey
    enabled: !!entity && !!fieldKey,
  });

  // Create a new option
  const createOption = useMutation({
    mutationFn: async ({ entity, fieldKey, value }: CreateOptionParams) => {
      const response = await fetch(
        `${API_URL}/v1/fields-data/${entity}/${fieldKey}/options`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ value }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create option");
      }

      return response.json();
    },
    onSuccess: (_, variables) => {
      // Invalidate and refetch options
      queryClient.invalidateQueries({
        queryKey: ["field-options", variables.entity, variables.fieldKey],
      });
    },
  });

  // Convert options to ComboBox format
  const comboBoxOptions: FieldOption[] = options.map((opt) => ({
    label: String(opt),
    value: String(opt),
  }));

  return {
    options: comboBoxOptions,
    isLoading,
    createOption: (value: string) =>
      createOption.mutateAsync({ entity, fieldKey, value }),
    isCreating: createOption.isPending,
  };
}
