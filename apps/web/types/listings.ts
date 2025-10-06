export type ListingFieldOrigin = "core" | "custom";

export interface ListingFieldSchema {
  key: string;
  label: string;
  data_type: string;
  required: boolean;
  editable: boolean;
  description?: string | null;
  options?: string[] | null;
  validation?: Record<string, unknown> | null;
  origin: ListingFieldOrigin;
}

export interface CustomFieldDefinition {
  id: number;
  entity: string;
  key: string;
  label: string;
  data_type: string;
  description?: string | null;
  required: boolean;
  default_value?: unknown;
  options?: string[] | null;
  is_active: boolean;
  visibility: string;
  created_by?: string | null;
  validation?: Record<string, unknown> | null;
  display_order: number;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface ListingSchemaResponse {
  core_fields: ListingFieldSchema[];
  custom_fields: CustomFieldDefinition[];
}

export interface CpuRecord {
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
}

export interface ListingRecord {
  id: number;
  title: string;
  url: string | null;
  seller: string | null;
  price_usd: number;
  adjusted_price_usd: number | null;
  score_composite: number | null;
  score_cpu_multi: number | null;
  score_cpu_single: number | null;
  score_gpu: number | null;
  dollar_per_cpu_mark: number | null;
  condition: string;
  status: string;
  cpu?: CpuRecord | null;
  gpu?: { id?: number | null; name?: string | null } | null;
  ports_profile?: { id?: number | null; name?: string | null } | null;
  attributes: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
