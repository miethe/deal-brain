import { API_URL } from "../utils";

export interface FieldMetadata {
  key: string;
  label: string;
  data_type: string;
  description?: string;
  options?: string[];
  is_custom: boolean;
  validation?: Record<string, any>;
}

export interface EntityMetadata {
  key: string;
  label: string;
  fields: FieldMetadata[];
}

export interface OperatorDefinition {
  value: string;
  label: string;
  field_types: string[];
}

export interface EntitiesMetadataResponse {
  entities: EntityMetadata[];
  operators: OperatorDefinition[];
}

export async function fetchEntitiesMetadata(): Promise<EntitiesMetadataResponse> {
  const response = await fetch(`${API_URL}/entities/metadata`);
  if (!response.ok) {
    throw new Error("Failed to fetch entities metadata");
  }
  return response.json();
}
