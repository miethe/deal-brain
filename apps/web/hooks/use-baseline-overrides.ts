"use client";

import { useState, useCallback, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { FieldOverride } from "@/types/baseline";
import {
  getEntityOverrides,
  upsertFieldOverride,
  deleteFieldOverride,
  deleteEntityOverrides,
} from "@/lib/api/baseline";
import { useToast } from "./use-toast";

export interface UseBaselineOverridesOptions {
  entityKey: string;
  autoSave?: boolean;
}

export function useBaselineOverrides({ entityKey, autoSave = false }: UseBaselineOverridesOptions) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Track local overrides state
  const [localOverrides, setLocalOverrides] = useState<Map<string, FieldOverride>>(new Map());
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Fetch existing overrides from server
  const { data: serverOverrides = [], isLoading } = useQuery({
    queryKey: ["baseline-overrides", entityKey],
    queryFn: () => getEntityOverrides(entityKey),
    staleTime: 30000, // 30 seconds
  });

  // Initialize local state from server data
  useEffect(() => {
    const map = new Map<string, FieldOverride>();
    serverOverrides.forEach((override) => {
      map.set(override.field_name, override);
    });
    setLocalOverrides(map);
    setHasUnsavedChanges(false);
  }, [serverOverrides]);

  // Mutation for upserting override
  const upsertMutation = useMutation({
    mutationFn: upsertFieldOverride,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["baseline-overrides", entityKey] });
      queryClient.invalidateQueries({ queryKey: ["baseline-preview"] });
      if (!autoSave) {
        toast({
          title: "Override saved",
          description: "Field override has been updated successfully.",
        });
      }
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to save override",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Mutation for deleting override
  const deleteMutation = useMutation({
    mutationFn: ({ fieldName }: { fieldName: string }) =>
      deleteFieldOverride(entityKey, fieldName),
    onSuccess: (_, { fieldName }) => {
      queryClient.invalidateQueries({ queryKey: ["baseline-overrides", entityKey] });
      queryClient.invalidateQueries({ queryKey: ["baseline-preview"] });
      toast({
        title: "Override reset",
        description: `${fieldName} has been reset to baseline value.`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to reset override",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Mutation for deleting all entity overrides
  const deleteAllMutation = useMutation({
    mutationFn: () => deleteEntityOverrides(entityKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["baseline-overrides", entityKey] });
      queryClient.invalidateQueries({ queryKey: ["baseline-preview"] });
      toast({
        title: "All overrides reset",
        description: "All field overrides for this entity have been reset.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to reset overrides",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  /**
   * Apply an override for a field
   */
  const applyOverride = useCallback(
    (
      fieldName: string,
      overrideData: Partial<Omit<FieldOverride, "field_name" | "entity_key">>
    ) => {
      const newOverride: FieldOverride = {
        field_name: fieldName,
        entity_key: entityKey,
        is_enabled: true,
        ...overrideData,
      };

      setLocalOverrides((prev) => {
        const next = new Map(prev);
        next.set(fieldName, newOverride);
        return next;
      });
      setHasUnsavedChanges(true);

      if (autoSave) {
        upsertMutation.mutate(newOverride);
      }
    },
    [entityKey, autoSave, upsertMutation]
  );

  /**
   * Reset a field to baseline (delete override)
   */
  const resetField = useCallback(
    (fieldName: string) => {
      setLocalOverrides((prev) => {
        const next = new Map(prev);
        next.delete(fieldName);
        return next;
      });
      setHasUnsavedChanges(true);

      deleteMutation.mutate({ fieldName });
    },
    [deleteMutation]
  );

  /**
   * Reset all fields to baseline
   */
  const resetAllFields = useCallback(() => {
    setLocalOverrides(new Map());
    setHasUnsavedChanges(true);
    deleteAllMutation.mutate();
  }, [deleteAllMutation]);

  /**
   * Save all pending changes
   */
  const saveOverrides = useCallback(async () => {
    const promises: Promise<any>[] = [];

    localOverrides.forEach((override) => {
      promises.push(upsertMutation.mutateAsync(override));
    });

    try {
      await Promise.all(promises);
      setHasUnsavedChanges(false);
      toast({
        title: "Overrides saved",
        description: `${promises.length} field override(s) saved successfully.`,
      });
    } catch (error) {
      toast({
        title: "Failed to save overrides",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    }
  }, [localOverrides, upsertMutation, toast]);

  /**
   * Discard local changes
   */
  const discardChanges = useCallback(() => {
    const map = new Map<string, FieldOverride>();
    serverOverrides.forEach((override) => {
      map.set(override.field_name, override);
    });
    setLocalOverrides(map);
    setHasUnsavedChanges(false);
  }, [serverOverrides]);

  /**
   * Get override for a specific field
   */
  const getOverride = useCallback(
    (fieldName: string): FieldOverride | undefined => {
      return localOverrides.get(fieldName);
    },
    [localOverrides]
  );

  /**
   * Check if a field has an override
   */
  const hasOverride = useCallback(
    (fieldName: string): boolean => {
      return localOverrides.has(fieldName);
    },
    [localOverrides]
  );

  return {
    overrides: localOverrides,
    isLoading,
    hasUnsavedChanges,
    isSaving: upsertMutation.isPending || deleteMutation.isPending || deleteAllMutation.isPending,
    applyOverride,
    resetField,
    resetAllFields,
    saveOverrides,
    discardChanges,
    getOverride,
    hasOverride,
  };
}
