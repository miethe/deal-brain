/**
 * TypeScript type definitions for Catalog API integration
 *
 * Matches backend Pydantic schemas from:
 * - packages/core/dealbrain_core/schemas/catalog.py
 */

/**
 * CPU catalog item
 */
export interface CpuCatalogItem {
  id: number;
  name: string;
  manufacturer: string;
  socket: string | null;
  cores: number | null;
  threads: number | null;
  tdp_w: number | null;
  igpu_model: string | null;
  cpu_mark_multi: number | null;
  cpu_mark_single: number | null;
  igpu_mark: number | null;
  release_year: number | null;
  notes: string | null;
  passmark_slug: string | null;
  passmark_category: string | null;
  passmark_id: string | null;
  attributes_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * GPU catalog item
 */
export interface GpuCatalogItem {
  id: number;
  name: string;
  manufacturer: string;
  gpu_mark: number | null;
  metal_score: number | null;
  notes: string | null;
  attributes_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * RAM specification catalog item
 */
export interface RamSpecCatalogItem {
  id: number;
  label: string | null;
  ddr_generation: string; // "DDR3" | "DDR4" | "DDR5" | "UNKNOWN"
  speed_mhz: number | null;
  module_count: number | null;
  capacity_per_module_gb: number | null;
  total_capacity_gb: number | null;
  attributes_json: Record<string, any>;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Storage profile catalog item
 */
export interface StorageProfileCatalogItem {
  id: number;
  label: string | null;
  medium: string; // "SSD" | "HDD" | "NVME" | "EMMC" | "OPTANE" | "UNKNOWN"
  interface: string | null;
  form_factor: string | null;
  capacity_gb: number | null;
  performance_tier: string | null;
  attributes_json: Record<string, any>;
  notes: string | null;
  created_at: string;
  updated_at: string;
}
