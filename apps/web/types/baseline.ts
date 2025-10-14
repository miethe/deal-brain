/**
 * TypeScript types for Baseline Valuation System
 */

export type BaselineFieldType = "scalar" | "presence" | "multiplier" | "formula";

export interface BaselineField {
  field_name: string;
  field_type: string;
  proper_name?: string;
  description?: string;
  explanation?: string;
  unit?: string;
  min_value?: number;
  max_value?: number;
  formula?: string;
  dependencies?: string[] | null;
  nullable: boolean;
  notes?: string;
  valuation_buckets?: Array<{
    label: string;
    Formula: string | null;
    max_usd: number;
    min_usd: number;
  }> | null;
}

export interface BaselineEntity {
  entity_key: string;
  fields: BaselineField[];
}

export interface BaselineMetadata {
  version: string;
  entities: BaselineEntity[];
  source_hash: string;
  is_active: boolean;
  schema_version?: string;
  generated_at?: string;
  ruleset_id?: number;
  ruleset_name?: string;
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

export interface BaselineFieldDiff {
  entity_key: string;
  field_name: string;
  proper_name?: string;
  change_type: DiffChangeType;
  old_value?: any;
  new_value?: any;
  value_diff?: any;
}

export interface DiffResponse {
  added: BaselineFieldDiff[];
  changed: BaselineFieldDiff[];
  removed: BaselineFieldDiff[];
  summary: {
    added_count: number;
    changed_count: number;
    removed_count: number;
    total_changes: number;
  };
  current_version?: string;
  candidate_version?: string;
}

export interface AdoptRequest {
  candidate_json: Record<string, any>; // Candidate baseline JSON structure
  selected_changes?: string[]; // List of field IDs to adopt (entity.field format)
  trigger_recalculation?: boolean;
  actor?: string;
}

export interface AdoptResponse {
  new_ruleset_id: number;
  new_version: string;
  changes_applied: number;
  recalculation_job_id?: string;
  adopted_fields: string[];
  skipped_fields: string[];
  previous_ruleset_id?: number;
  audit_log_id?: number;
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

export interface HydrateBaselineRequest {
  actor?: string;
}

export interface HydrationSummaryItem {
  original_rule_id: number;
  field_name: string;
  field_type: string;
  expanded_rule_ids: number[];
}

export interface HydrateBaselineResponse {
  status: string;
  ruleset_id: number;
  hydrated_rule_count: number;
  created_rule_count: number;
  hydration_summary: HydrationSummaryItem[];
}
