/**
 * React Query hooks for Catalog API integration
 *
 * Provides hooks for fetching catalog data:
 * - CPUs
 * - GPUs
 * - RAM specifications
 * - Storage profiles
 *
 * Uses React Query for caching, background updates, and error handling.
 */

import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/lib/utils';
import type {
  CpuCatalogItem,
  GpuCatalogItem,
  RamSpecCatalogItem,
  StorageProfileCatalogItem,
} from '@/types/catalog';

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
