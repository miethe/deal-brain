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

export interface ListingLink {
  url: string;
  label?: string | null;
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

export interface PortRecord {
  id?: number | null;
  port_type: string;
  quantity: number;
  version?: string | null;
  notes?: string | null;
}

export interface PortsProfileRecord {
  id?: number | null;
  name?: string | null;
  ports?: PortRecord[] | null;
}

export interface ValuationAdjustmentAction {
  action_type?: string | null;
  metric?: string | null;
  value: number;
  details?: Record<string, unknown> | null;
  error?: string | null;
}

export interface ValuationAdjustment {
  rule_id?: number | null;
  rule_name: string;
  adjustment_amount: number;
  actions: ValuationAdjustmentAction[];
}

export interface LegacyValuationLine {
  label: string;
  component_type: string;
  quantity: number;
  unit_value: number;
  condition_multiplier: number;
  deduction_usd: number;
  adjustment_usd?: number | null;
}

export interface ValuationBreakdown {
  listing_price: number;
  adjusted_price: number;
  total_adjustment: number;
  total_deductions?: number | null;
  matched_rules_count?: number;
  ruleset?: {
    id?: number | null;
    name?: string | null;
  };
  ruleset_name?: string | null;
  adjustments: ValuationAdjustment[];
  legacy_lines?: LegacyValuationLine[];
  lines?: LegacyValuationLine[];
}

export interface ListingRecord {
  id: number;
  title: string;
  listing_url: string | null;
  other_urls?: ListingLink[] | null;
  seller: string | null;
  price_usd: number;
  adjusted_price_usd: number | null;
  score_composite: number | null;
  score_cpu_multi: number | null;
  score_cpu_single: number | null;
  score_gpu: number | null;
  dollar_per_cpu_mark: number | null;
  dollar_per_single_mark: number | null;
  dollar_per_cpu_mark_single?: number | null | undefined;
  dollar_per_cpu_mark_single_adjusted?: number | null | undefined;
  dollar_per_cpu_mark_multi?: number | null | undefined;
  dollar_per_cpu_mark_multi_adjusted?: number | null | undefined;
  perf_per_watt?: number | null | undefined;
  condition: string;
  status: string;
  cpu_id?: number | null;
  cpu_name?: string | null;
  gpu_id?: number | null;
  gpu_name?: string | null;
  ram_gb?: number | null;
  primary_storage_gb?: number | null;
  primary_storage_type?: string | null;
  secondary_storage_gb?: number | null;
  secondary_storage_type?: string | null;
  manufacturer?: string | null;
  series?: string | null;
  model_number?: string | null;
  form_factor?: string | null;
  thumbnail_url?: string | null;
  valuation_breakdown?: ValuationBreakdown | null;
  cpu?: CpuRecord | null;
  gpu?: { id?: number | null; name?: string | null } | null;
  ports_profile?: PortsProfileRecord | null;
  attributes: Record<string, unknown>;
  ruleset_id?: number | null;
  created_at: string;
  updated_at: string;
}
