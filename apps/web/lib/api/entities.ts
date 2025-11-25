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

/**
 * Fetch entity data for tooltip display
 *
 * Used by EntityTooltip component to lazy-load entity details on hover.
 *
 * @param entityType - Type of entity (cpu, gpu, ram-spec, storage-profile)
 * @param entityId - ID of the entity to fetch
 * @returns Promise resolving to entity data
 */
export async function fetchEntityData(
  entityType: string,
  entityId: number
): Promise<any> {
  const endpoints: Record<string, string> = {
    cpu: `/v1/catalog/cpus/${entityId}`,
    gpu: `/v1/catalog/gpus/${entityId}`,
    "ram-spec": `/v1/catalog/ram-specs/${entityId}`,
    "storage-profile": `/v1/catalog/storage-profiles/${entityId}`,
  };

  const endpoint = endpoints[entityType];
  if (!endpoint) {
    throw new Error(`Unknown entity type: ${entityType}`);
  }

  const url = `${API_URL}${endpoint}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(
        `Failed to fetch ${entityType}: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  } catch (error) {
    console.error(`fetchEntityData error for ${entityType} ${entityId}:`, error);
    throw error;
  }
}
