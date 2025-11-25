import { z } from 'zod';

/**
 * Zod validation schemas for entity edit forms.
 * These schemas match backend Pydantic Update schemas in packages/core/dealbrain_core/schemas/catalog.py
 *
 * Key differences from backend:
 * - Backend uses `attributes_json`, frontend uses `attributes`
 * - All fields are optional to support PATCH updates
 * - Validation rules match Pydantic Field constraints (ge, le)
 */

// ============================================================================
// CPU Edit Schema
// ============================================================================

export const cpuEditSchema = z.object({
  name: z.string().min(1, 'Name is required').max(200).optional(),
  manufacturer: z.string().max(100).nullable().optional(),
  socket: z.string().max(50).nullable().optional(),
  cores: z.number().int().min(1, 'Cores must be at least 1').max(256, 'Cores cannot exceed 256').nullable().optional(),
  threads: z.number().int().min(1, 'Threads must be at least 1').max(512, 'Threads cannot exceed 512').nullable().optional(),
  tdp_w: z.number().int().min(1, 'TDP must be at least 1W').max(1000, 'TDP cannot exceed 1000W').nullable().optional(),
  igpu_model: z.string().max(100).nullable().optional(),
  cpu_mark_multi: z.number().int().min(0, 'CPU Mark Multi cannot be negative').nullable().optional(),
  cpu_mark_single: z.number().int().min(0, 'CPU Mark Single cannot be negative').nullable().optional(),
  igpu_mark: z.number().int().min(0, 'iGPU Mark cannot be negative').nullable().optional(),
  release_year: z.number().int().min(1970, 'Release year must be after 1970').max(2100, 'Release year cannot exceed 2100').nullable().optional(),
  notes: z.string().nullable().optional(),
  passmark_slug: z.string().max(255).nullable().optional(),
  passmark_category: z.string().max(255).nullable().optional(),
  passmark_id: z.string().max(255).nullable().optional(),
  attributes: z.record(z.any()).optional(), // Custom fields - maps to attributes_json in backend
});

export type CPUEditFormData = z.infer<typeof cpuEditSchema>;

// ============================================================================
// GPU Edit Schema
// ============================================================================

export const gpuEditSchema = z.object({
  name: z.string().min(1, 'Name is required').max(200).optional(),
  manufacturer: z.string().max(100).nullable().optional(),
  gpu_mark: z.number().int().min(0, 'GPU Mark cannot be negative').nullable().optional(),
  metal_score: z.number().int().min(0, 'Metal Score cannot be negative').nullable().optional(),
  notes: z.string().nullable().optional(),
  attributes: z.record(z.any()).optional(), // Custom fields
});

export type GPUEditFormData = z.infer<typeof gpuEditSchema>;

// ============================================================================
// RamSpec Edit Schema
// ============================================================================

// DDR generation enum matching backend RamGeneration enum
export const ddrGenerationEnum = z.enum([
  'ddr3',
  'ddr4',
  'ddr5',
  'lpddr4',
  'lpddr4x',
  'lpddr5',
  'lpddr5x',
  'hbm2',
  'hbm3',
  'unknown',
]);

export const ramSpecEditSchema = z.object({
  label: z.string().min(1, 'Label is required').max(100).nullable().optional(),
  ddr_generation: ddrGenerationEnum.optional(),
  speed_mhz: z.number().int().min(0, 'Speed must be non-negative').max(10000, 'Speed cannot exceed 10000 MHz').nullable().optional(),
  module_count: z.number().int().min(1, 'Module count must be at least 1').max(8, 'Module count cannot exceed 8').nullable().optional(),
  capacity_per_module_gb: z.number().int().min(1, 'Capacity must be at least 1GB').max(256, 'Capacity cannot exceed 256GB per module').nullable().optional(),
  total_capacity_gb: z.number().int().min(1, 'Total capacity must be at least 1GB').max(2048, 'Total capacity cannot exceed 2048GB').nullable().optional(),
  notes: z.string().nullable().optional(),
  attributes: z.record(z.any()).optional(), // Custom fields
});

export type RamSpecEditFormData = z.infer<typeof ramSpecEditSchema>;

// ============================================================================
// StorageProfile Edit Schema
// ============================================================================

// Storage medium enum matching backend StorageMedium enum
export const storageMediumEnum = z.enum([
  'nvme',
  'sata_ssd',
  'hdd',
  'hybrid',
  'emmc',
  'ufs',
  'unknown',
]);

// Storage interface enum (string field in backend, but common values)
export const storageInterfaceEnum = z.enum([
  'sata',
  'nvme',
  'pcie',
  'usb',
  'emmc',
]);

// Storage form factor enum (string field in backend, but common values)
export const storageFormFactorEnum = z.enum([
  'm2',
  '2.5',
  '3.5',
  'pcie_card',
  'emmc_embedded',
]);

// Performance tier enum (string field in backend, but common values)
export const performanceTierEnum = z.enum([
  'budget',
  'mainstream',
  'performance',
  'enthusiast',
]);

export const storageProfileEditSchema = z.object({
  label: z.string().min(1, 'Label is required').max(100).nullable().optional(),
  medium: storageMediumEnum.optional(),
  interface: z.string().max(50).nullable().optional(), // Backend uses string, we provide enum for convenience
  form_factor: z.string().max(50).nullable().optional(), // Backend uses string, we provide enum for convenience
  capacity_gb: z.number().int().min(1, 'Capacity must be at least 1GB').max(100000, 'Capacity cannot exceed 100TB').nullable().optional(),
  performance_tier: z.string().max(50).nullable().optional(), // Backend uses string, we provide enum for convenience
  notes: z.string().nullable().optional(),
  attributes: z.record(z.any()).optional(), // Custom fields
});

export type StorageProfileEditFormData = z.infer<typeof storageProfileEditSchema>;

// ============================================================================
// PortsProfile Edit Schema
// ============================================================================

export const portsProfileEditSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100).optional(),
  description: z.string().nullable().optional(),
  attributes: z.record(z.any()).optional(), // Custom fields
  // Note: ports field is handled separately in the UI (not included in this form)
});

export type PortsProfileEditFormData = z.infer<typeof portsProfileEditSchema>;

// ============================================================================
// Profile Edit Schema
// ============================================================================

export const profileEditSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100).optional(),
  description: z.string().nullable().optional(),
  weights_json: z.record(z.number()).optional(), // Maps metric names to weights
  is_default: z.boolean().optional(),
});

export type ProfileEditFormData = z.infer<typeof profileEditSchema>;

// ============================================================================
// Type Helpers
// ============================================================================

/**
 * Union type of all entity edit form data types
 */
export type EntityEditFormData =
  | CPUEditFormData
  | GPUEditFormData
  | RamSpecEditFormData
  | StorageProfileEditFormData
  | PortsProfileEditFormData
  | ProfileEditFormData;

/**
 * Map entity type to corresponding schema
 */
export const entitySchemaMap = {
  cpu: cpuEditSchema,
  gpu: gpuEditSchema,
  'ram-spec': ramSpecEditSchema,
  'storage-profile': storageProfileEditSchema,
  'ports-profile': portsProfileEditSchema,
  profile: profileEditSchema,
} as const;

export type EntityType = keyof typeof entitySchemaMap;
