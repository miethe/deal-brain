"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import type {
  CPUEditFormData,
  GPUEditFormData,
  RamSpecEditFormData,
  StorageProfileEditFormData,
} from "@/lib/schemas/entity-schemas";

// ============================================================================
// CPU Mutations
// ============================================================================

export function useUpdateCpu(cpuId: number) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: CPUEditFormData) => {
      return apiFetch(`/v1/catalog/cpus/${cpuId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onMutate: async (newData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["cpu", cpuId] });

      // Snapshot previous value
      const previousCpu = queryClient.getQueryData(["cpu", cpuId]);

      // Optimistically update to new value
      queryClient.setQueryData(["cpu", cpuId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          ...newData,
        };
      });

      return { previousCpu };
    },
    onError: (err, newData, context) => {
      // Rollback on error
      if (context?.previousCpu) {
        queryClient.setQueryData(["cpu", cpuId], context.previousCpu);
      }

      // Extract error message
      const errorMessage = err instanceof ApiError ? err.message : "Failed to update CPU";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      // Refetch to sync with server
      queryClient.invalidateQueries({ queryKey: ["cpu", cpuId] });
      queryClient.invalidateQueries({ queryKey: ["cpus"] });

      toast({
        title: "Success",
        description: "CPU updated successfully",
      });
    },
  });
}

// ============================================================================
// GPU Mutations
// ============================================================================

export function useUpdateGpu(gpuId: number) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: GPUEditFormData) => {
      return apiFetch(`/v1/catalog/gpus/${gpuId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ["gpu", gpuId] });
      const previousGpu = queryClient.getQueryData(["gpu", gpuId]);

      queryClient.setQueryData(["gpu", gpuId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          ...newData,
        };
      });

      return { previousGpu };
    },
    onError: (err, newData, context) => {
      if (context?.previousGpu) {
        queryClient.setQueryData(["gpu", gpuId], context.previousGpu);
      }

      const errorMessage = err instanceof ApiError ? err.message : "Failed to update GPU";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gpu", gpuId] });
      queryClient.invalidateQueries({ queryKey: ["gpus"] });

      toast({
        title: "Success",
        description: "GPU updated successfully",
      });
    },
  });
}

// ============================================================================
// RamSpec Mutations
// ============================================================================

export function useUpdateRamSpec(ramSpecId: number) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: RamSpecEditFormData) => {
      return apiFetch(`/v1/catalog/ram-specs/${ramSpecId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ["ram-spec", ramSpecId] });
      const previousRamSpec = queryClient.getQueryData(["ram-spec", ramSpecId]);

      queryClient.setQueryData(["ram-spec", ramSpecId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          ...newData,
        };
      });

      return { previousRamSpec };
    },
    onError: (err, newData, context) => {
      if (context?.previousRamSpec) {
        queryClient.setQueryData(["ram-spec", ramSpecId], context.previousRamSpec);
      }

      const errorMessage = err instanceof ApiError ? err.message : "Failed to update RAM Specification";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ram-spec", ramSpecId] });
      queryClient.invalidateQueries({ queryKey: ["ram-specs"] });

      toast({
        title: "Success",
        description: "RAM Specification updated successfully",
      });
    },
  });
}

// ============================================================================
// StorageProfile Mutations
// ============================================================================

export function useUpdateStorageProfile(storageProfileId: number) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: StorageProfileEditFormData) => {
      return apiFetch(`/v1/catalog/storage-profiles/${storageProfileId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ["storage-profile", storageProfileId] });
      const previousStorageProfile = queryClient.getQueryData(["storage-profile", storageProfileId]);

      queryClient.setQueryData(["storage-profile", storageProfileId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          ...newData,
        };
      });

      return { previousStorageProfile };
    },
    onError: (err, newData, context) => {
      if (context?.previousStorageProfile) {
        queryClient.setQueryData(["storage-profile", storageProfileId], context.previousStorageProfile);
      }

      const errorMessage = err instanceof ApiError ? err.message : "Failed to update Storage Profile";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["storage-profile", storageProfileId] });
      queryClient.invalidateQueries({ queryKey: ["storage-profiles"] });

      toast({
        title: "Success",
        description: "Storage Profile updated successfully",
      });
    },
  });
}
