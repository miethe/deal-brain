export type MappingStatus = "auto" | "manual" | "missing";

export interface MappingSuggestion {
  column: string;
  confidence: number;
  reason?: string | null;
}

export interface FieldMapping {
  field: string;
  label: string;
  required: boolean;
  data_type: string;
  column?: string | null;
  status: MappingStatus;
  confidence: number;
  suggestions: MappingSuggestion[];
}

export interface EntityMapping {
  sheet?: string | null;
  fields: Record<string, FieldMapping>;
}

export interface SheetColumn {
  name: string;
  samples: string[];
}

export interface SheetMeta {
  sheet_name: string;
  row_count: number;
  columns: SheetColumn[];
  entity?: string | null;
  entity_label?: string | null;
  confidence: number;
}

export interface ComponentMatchSuggestion {
  match: string;
  confidence: number;
}

export interface ComponentMatch {
  row_index: number;
  value: string;
  status: "auto" | "review" | "unmatched";
  auto_match?: string | null;
  suggestions: ComponentMatchSuggestion[];
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

export interface EntityPreview {
  rows: Record<string, unknown>[];
  missing_required_fields: string[];
  total_rows: number;
  mapped_field_count: number;
  component_matches?: ComponentMatch[] | null;
}

export interface CpuConflictField {
  field: string;
  existing: unknown;
  incoming: unknown;
}

export interface CpuConflict {
  name: string;
  existing: Record<string, unknown>;
  incoming: Record<string, unknown>;
  fields: CpuConflictField[];
}

export interface ImportSessionSnapshot {
  id: string;
  filename: string;
  content_type: string | null;
  status: string;
  checksum: string | null;
  sheet_meta: SheetMeta[];
  mappings: Record<string, EntityMapping>;
  preview: Record<string, EntityPreview>;
  conflicts: Record<string, unknown>;
  declared_entities: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface ImportSessionList {
  sessions: ImportSessionSnapshot[];
}

export interface ConflictResolutionPayload {
  entity: "cpu";
  identifier: string;
  action: "update" | "skip" | "keep";
}

export interface ComponentOverridePayload {
  entity: "listing";
  row_index: number;
  cpu_match?: string | null;
  gpu_match?: string | null;
}

export interface CommitResponse {
  status: string;
  counts: Record<string, number>;
  session: ImportSessionSnapshot;
  auto_created_cpus: string[];
}

export interface ImporterFieldCreateResponse {
  field: CustomFieldDefinition;
  session: ImportSessionSnapshot;
}
