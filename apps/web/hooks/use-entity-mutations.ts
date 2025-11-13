"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch, ApiError } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import type {
  CPUEditFormData,
  GPUEditFormData,
  RamSpecEditFormData,
  StorageProfileEditFormData,
  PortsProfileEditFormData,
  ProfileEditFormData,
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

export function useDeleteCpu(cpuId: number, options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      return apiFetch(`/v1/catalog/cpus/${cpuId}`, {
        method: "DELETE",
      });
    },
    onError: (err) => {
      let errorMessage = "Failed to delete CPU";

      if (err instanceof ApiError) {
        if (err.status === 404) {
          errorMessage = "CPU not found";
        } else if (err.status === 409) {
          // Extract usage count from error message like "Cannot delete CPU: used in 5 listing(s)"
          errorMessage = err.message;
        } else {
          errorMessage = err.message;
        }
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      // Invalidate both detail and list caches
      queryClient.invalidateQueries({ queryKey: ["cpu", cpuId] });
      queryClient.invalidateQueries({ queryKey: ["cpus"] });

      toast({
        title: "Success",
        description: "CPU deleted successfully",
      });

      // Call optional success callback for redirects
      options?.onSuccess?.();
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

export function useDeleteGpu(gpuId: number, options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      return apiFetch(`/v1/catalog/gpus/${gpuId}`, {
        method: "DELETE",
      });
    },
    onError: (err) => {
      let errorMessage = "Failed to delete GPU";

      if (err instanceof ApiError) {
        if (err.status === 404) {
          errorMessage = "GPU not found";
        } else if (err.status === 409) {
          errorMessage = err.message;
        } else {
          errorMessage = err.message;
        }
      }

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
        description: "GPU deleted successfully",
      });

      options?.onSuccess?.();
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

export function useDeleteRamSpec(ramSpecId: number, options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      return apiFetch(`/v1/catalog/ram-specs/${ramSpecId}`, {
        method: "DELETE",
      });
    },
    onError: (err) => {
      let errorMessage = "Failed to delete RAM Specification";

      if (err instanceof ApiError) {
        if (err.status === 404) {
          errorMessage = "RAM Specification not found";
        } else if (err.status === 409) {
          errorMessage = err.message;
        } else {
          errorMessage = err.message;
        }
      }

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
        description: "RAM Specification deleted successfully",
      });

      options?.onSuccess?.();
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

export function useDeleteStorageProfile(storageProfileId: number, options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      return apiFetch(`/v1/catalog/storage-profiles/${storageProfileId}`, {
        method: "DELETE",
      });
    },
    onError: (err) => {
      let errorMessage = "Failed to delete Storage Profile";

      if (err instanceof ApiError) {
        if (err.status === 404) {
          errorMessage = "Storage Profile not found";
        } else if (err.status === 409) {
          errorMessage = err.message;
        } else {
          errorMessage = err.message;
        }
      }

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
        description: "Storage Profile deleted successfully",
      });

      options?.onSuccess?.();
    },
  });
}

// ============================================================================
// PortsProfile Mutations
// ============================================================================

export function useUpdatePortsProfile(portsProfileId: number) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: PortsProfileEditFormData) => {
      return apiFetch(`/v1/catalog/ports-profiles/${portsProfileId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ["ports-profile", portsProfileId] });
      const previousPortsProfile = queryClient.getQueryData(["ports-profile", portsProfileId]);

      queryClient.setQueryData(["ports-profile", portsProfileId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          ...newData,
        };
      });

      return { previousPortsProfile };
    },
    onError: (err, newData, context) => {
      if (context?.previousPortsProfile) {
        queryClient.setQueryData(["ports-profile", portsProfileId], context.previousPortsProfile);
      }

      const errorMessage = err instanceof ApiError ? err.message : "Failed to update Ports Profile";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ports-profile", portsProfileId] });
      queryClient.invalidateQueries({ queryKey: ["ports-profiles"] });

      toast({
        title: "Success",
        description: "Ports Profile updated successfully",
      });
    },
  });
}

export function useDeletePortsProfile(portsProfileId: number, options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      return apiFetch(`/v1/catalog/ports-profiles/${portsProfileId}`, {
        method: "DELETE",
      });
    },
    onError: (err) => {
      let errorMessage = "Failed to delete Ports Profile";

      if (err instanceof ApiError) {
        if (err.status === 404) {
          errorMessage = "Ports Profile not found";
        } else if (err.status === 409) {
          errorMessage = err.message;
        } else {
          errorMessage = err.message;
        }
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ports-profile", portsProfileId] });
      queryClient.invalidateQueries({ queryKey: ["ports-profiles"] });

      toast({
        title: "Success",
        description: "Ports Profile deleted successfully",
      });

      options?.onSuccess?.();
    },
  });
}

// ============================================================================
// Profile Mutations (Scoring Profiles)
// ============================================================================

export function useUpdateProfile(profileId: number) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: ProfileEditFormData) => {
      return apiFetch(`/v1/catalog/profiles/${profileId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ["profile", profileId] });
      const previousProfile = queryClient.getQueryData(["profile", profileId]);

      queryClient.setQueryData(["profile", profileId], (old: any) => {
        if (!old) return old;
        return {
          ...old,
          ...newData,
        };
      });

      return { previousProfile };
    },
    onError: (err, newData, context) => {
      if (context?.previousProfile) {
        queryClient.setQueryData(["profile", profileId], context.previousProfile);
      }

      const errorMessage = err instanceof ApiError ? err.message : "Failed to update Profile";

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile", profileId] });
      queryClient.invalidateQueries({ queryKey: ["profiles"] });

      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
    },
  });
}

export function useDeleteProfile(profileId: number, options?: { onSuccess?: () => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async () => {
      return apiFetch(`/v1/catalog/profiles/${profileId}`, {
        method: "DELETE",
      });
    },
    onError: (err) => {
      let errorMessage = "Failed to delete Profile";

      if (err instanceof ApiError) {
        if (err.status === 404) {
          errorMessage = "Profile not found";
        } else if (err.status === 409) {
          errorMessage = err.message;
        } else {
          errorMessage = err.message;
        }
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile", profileId] });
      queryClient.invalidateQueries({ queryKey: ["profiles"] });

      toast({
        title: "Success",
        description: "Profile deleted successfully",
      });

      options?.onSuccess?.();
    },
  });
}
