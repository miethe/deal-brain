/**
 * React Query hooks for Catalog API integration
 *
 * Provides hooks for fetching and mutating catalog data:
 * - CPUs
 * - GPUs
 * - RAM specifications
 * - Storage profiles
 *
 * Uses React Query for caching, background updates, and error handling.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, ApiError } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import type {
  CpuCatalogItem,
  GpuCatalogItem,
  RamSpecCatalogItem,
  StorageProfileCatalogItem,
} from '@/types/catalog';

// ============================================================================
// Query Hooks (Fetching)
// ============================================================================

/**
 * Fetch all CPUs from catalog
 *
 * @returns Query result with CPU catalog items array
 */
export function useCatalogCPUs() {
  return useQuery({
    queryKey: ['catalog', 'cpus'],
    queryFn: () => apiFetch<CpuCatalogItem[]>('/v1/catalog/cpus'),
    staleTime: 5 * 60 * 1000, // 5 minutes - catalog data changes infrequently
  });
}

/**
 * Fetch all GPUs from catalog
 *
 * @returns Query result with GPU catalog items array
 */
export function useCatalogGPUs() {
  return useQuery({
    queryKey: ['catalog', 'gpus'],
    queryFn: () => apiFetch<GpuCatalogItem[]>('/v1/catalog/gpus'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch all RAM specifications from catalog
 *
 * @returns Query result with RAM spec catalog items array
 */
export function useCatalogRAMSpecs() {
  return useQuery({
    queryKey: ['catalog', 'ram-specs'],
    queryFn: () => apiFetch<RamSpecCatalogItem[]>('/v1/catalog/ram-specs'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Fetch all storage profiles from catalog
 *
 * @returns Query result with storage profile catalog items array
 */
export function useCatalogStorageProfiles() {
  return useQuery({
    queryKey: ['catalog', 'storage-profiles'],
    queryFn: () => apiFetch<StorageProfileCatalogItem[]>('/v1/catalog/storage-profiles'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================================
// Mutation Hooks (Creating)
// ============================================================================

/**
 * Create payload types matching backend schemas
 */
export interface CpuCreatePayload {
  name: string;
  manufacturer: string;
  socket?: string | null;
  cores?: number | null;
  threads?: number | null;
  tdp_w?: number | null;
  igpu_model?: string | null;
  cpu_mark_multi?: number | null;
  cpu_mark_single?: number | null;
  igpu_mark?: number | null;
  release_year?: number | null;
  notes?: string | null;
  passmark_slug?: string | null;
  passmark_category?: string | null;
  passmark_id?: string | null;
  attributes?: Record<string, any>;
}

export interface GpuCreatePayload {
  name: string;
  manufacturer: string;
  gpu_mark?: number | null;
  metal_score?: number | null;
  notes?: string | null;
  attributes?: Record<string, any>;
}

export interface RamSpecCreatePayload {
  label?: string | null;
  ddr_generation: string; // 'ddr3' | 'ddr4' | 'ddr5' | etc.
  speed_mhz?: number | null;
  module_count?: number | null;
  capacity_per_module_gb?: number | null;
  total_capacity_gb?: number | null;
  notes?: string | null;
  attributes?: Record<string, any>;
}

export interface StorageProfileCreatePayload {
  label?: string | null;
  medium: string; // 'nvme' | 'sata_ssd' | 'hdd' | etc.
  interface?: string | null;
  form_factor?: string | null;
  capacity_gb?: number | null;
  performance_tier?: string | null;
  notes?: string | null;
  attributes?: Record<string, any>;
}

/**
 * Create a new CPU in the catalog
 */
export function useCreateCpu(options?: { onSuccess?: (cpu: CpuCatalogItem) => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: CpuCreatePayload) => {
      return apiFetch<CpuCatalogItem>('/v1/catalog/cpus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    },
    onError: (err) => {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to create CPU';
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    },
    onSuccess: (cpu) => {
      queryClient.invalidateQueries({ queryKey: ['catalog', 'cpus'] });
      queryClient.invalidateQueries({ queryKey: ['cpus'] });

      toast({
        title: 'Success',
        description: 'CPU created successfully',
      });

      options?.onSuccess?.(cpu);
    },
  });
}

/**
 * Create a new GPU in the catalog
 */
export function useCreateGpu(options?: { onSuccess?: (gpu: GpuCatalogItem) => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: GpuCreatePayload) => {
      return apiFetch<GpuCatalogItem>('/v1/catalog/gpus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    },
    onError: (err) => {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to create GPU';
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    },
    onSuccess: (gpu) => {
      queryClient.invalidateQueries({ queryKey: ['catalog', 'gpus'] });
      queryClient.invalidateQueries({ queryKey: ['gpus'] });

      toast({
        title: 'Success',
        description: 'GPU created successfully',
      });

      options?.onSuccess?.(gpu);
    },
  });
}

/**
 * Create a new RAM specification in the catalog
 */
export function useCreateRamSpec(options?: { onSuccess?: (ramSpec: RamSpecCatalogItem) => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: RamSpecCreatePayload) => {
      return apiFetch<RamSpecCatalogItem>('/v1/catalog/ram-specs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    },
    onError: (err) => {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to create RAM specification';
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    },
    onSuccess: (ramSpec) => {
      queryClient.invalidateQueries({ queryKey: ['catalog', 'ram-specs'] });
      queryClient.invalidateQueries({ queryKey: ['ram-specs'] });

      toast({
        title: 'Success',
        description: 'RAM specification created successfully',
      });

      options?.onSuccess?.(ramSpec);
    },
  });
}

/**
 * Create a new storage profile in the catalog
 */
export function useCreateStorageProfile(options?: { onSuccess?: (storageProfile: StorageProfileCatalogItem) => void }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: StorageProfileCreatePayload) => {
      return apiFetch<StorageProfileCatalogItem>('/v1/catalog/storage-profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    },
    onError: (err) => {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to create storage profile';
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });
    },
    onSuccess: (storageProfile) => {
      queryClient.invalidateQueries({ queryKey: ['catalog', 'storage-profiles'] });
      queryClient.invalidateQueries({ queryKey: ['storage-profiles'] });

      toast({
        title: 'Success',
        description: 'Storage profile created successfully',
      });

      options?.onSuccess?.(storageProfile);
    },
  });
}
