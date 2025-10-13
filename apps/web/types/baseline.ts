/**
 * TypeScript types for Baseline Valuation System
 */

export type BaselineFieldType = "scalar" | "presence" | "multiplier" | "formula";

export interface BaselineField {
  name: string;
  field_type: BaselineFieldType;
  description: string;
  explanation?: string;
  baseline_min?: number;
  baseline_max?: number;
  formula?: string;
  formula_vars?: string[];
  unit?: string;
  constraints?: {
    min?: number;
    max?: number;
    step?: number;
  };
  metadata?: Record<string, any>;
}

export interface BaselineEntity {
  entity_key: string;
  entity_name: string;
  description: string;
  fields: BaselineField[];
  metadata?: Record<string, any>;
}

export interface BaselineMetadata {
  schema_version: string;
  source: string;
  generated_at: string;
  entities: BaselineEntity[];
  metadata?: Record<string, any>;
}

export interface FieldOverride {
  field_name: string;
  entity_key: string;
  override_value?: number;
  override_min?: number;
  override_max?: number;
  override_formula?: string;
  is_enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface OverrideState {
  entity_key: string;
  overrides: Map<string, FieldOverride>;
  hasChanges: boolean;
}

export interface InstantiateRequest {
  path: string;
  dry_run?: boolean;
}

export interface InstantiateResponse {
  success: boolean;
  message: string;
  version?: string;
  entities_created?: number;
  fields_created?: number;
  metadata?: BaselineMetadata;
}

export type DiffChangeType = "added" | "changed" | "removed";

export interface DiffFieldChange {
  field_name: string;
  change_type: DiffChangeType;
  current_value?: any;
  candidate_value?: any;
  current_min?: number;
  candidate_min?: number;
  current_max?: number;
  candidate_max?: number;
  current_formula?: string;
  candidate_formula?: string;
}

export interface DiffEntityChange {
  entity_key: string;
  entity_name: string;
  fields: DiffFieldChange[];
}

export interface DiffResponse {
  has_changes: boolean;
  summary: {
    added_count: number;
    changed_count: number;
    removed_count: number;
  };
  changes: DiffEntityChange[];
  metadata?: {
    current_version?: string;
    candidate_version?: string;
  };
}

export interface AdoptRequest {
  candidate_baseline: BaselineMetadata | string; // JSON string or object
  selected_changes?: {
    entity_key: string;
    field_names: string[];
  }[];
  recalculate_valuations?: boolean;
  backup_current?: boolean;
}

export interface AdoptResponse {
  success: boolean;
  message: string;
  new_version: string;
  changes_applied: number;
  backup_created?: boolean;
  recalculation_job_id?: string;
}

export interface PreviewImpactStats {
  total_listings: number;
  matched_count: number;
  match_percentage: number;
  avg_delta: number;
  min_delta: number;
  max_delta: number;
  median_delta: number;
  std_dev_delta?: number;
}

export interface PreviewListingSample {
  id: number;
  title: string;
  current_price: number;
  baseline_price: number;
  override_price: number;
  delta: number;
  delta_pct: number;
}

export interface PreviewImpactResponse {
  statistics: PreviewImpactStats;
  samples: PreviewListingSample[];
  generated_at: string;
}
