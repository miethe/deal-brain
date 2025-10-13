/**
 * API client for Baseline Valuation System
 */

import { apiFetch } from "../utils";
import type {
  BaselineMetadata,
  InstantiateRequest,
  InstantiateResponse,
  DiffResponse,
  AdoptRequest,
  AdoptResponse,
  PreviewImpactResponse,
  FieldOverride,
} from "@/types/baseline";

const BASE_PATH = "/api/v1/baseline";

/**
 * Fetch baseline metadata including all entities and fields
 */
export async function getBaselineMetadata(): Promise<BaselineMetadata> {
  return apiFetch<BaselineMetadata>(`${BASE_PATH}/metadata`);
}

/**
 * Instantiate baseline from a JSON file path
 */
export async function instantiateBaseline(
  request: InstantiateRequest
): Promise<InstantiateResponse> {
  return apiFetch<InstantiateResponse>(`${BASE_PATH}/instantiate`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Compare current baseline with candidate baseline
 */
export async function diffBaseline(candidate: BaselineMetadata | string): Promise<DiffResponse> {
  const payload = typeof candidate === "string"
    ? { candidate_json: JSON.parse(candidate) }
    : { candidate_json: candidate };
  return apiFetch<DiffResponse>(`${BASE_PATH}/diff`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Adopt changes from candidate baseline
 */
export async function adoptBaseline(request: AdoptRequest): Promise<AdoptResponse> {
  return apiFetch<AdoptResponse>(`${BASE_PATH}/adopt`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Get all field overrides for an entity
 */
export async function getEntityOverrides(entityKey: string): Promise<FieldOverride[]> {
  return apiFetch<FieldOverride[]>(`${BASE_PATH}/overrides/${entityKey}`);
}

/**
 * Update or create a field override
 */
export async function upsertFieldOverride(override: Omit<FieldOverride, "created_at" | "updated_at">): Promise<FieldOverride> {
  return apiFetch<FieldOverride>(`${BASE_PATH}/overrides`, {
    method: "POST",
    body: JSON.stringify(override),
  });
}

/**
 * Delete a field override (reset to baseline)
 */
export async function deleteFieldOverride(
  entityKey: string,
  fieldName: string
): Promise<void> {
  return apiFetch<void>(
    `${BASE_PATH}/overrides/${entityKey}/${fieldName}`,
    {
      method: "DELETE",
    }
  );
}

/**
 * Bulk delete all overrides for an entity
 */
export async function deleteEntityOverrides(entityKey: string): Promise<void> {
  return apiFetch<void>(`${BASE_PATH}/overrides/${entityKey}`, {
    method: "DELETE",
  });
}

/**
 * Preview impact of current overrides on listings
 */
export async function previewImpact(
  entityKey?: string,
  sampleSize: number = 100
): Promise<PreviewImpactResponse> {
  const params = new URLSearchParams();
  if (entityKey) params.set("entity_key", entityKey);
  params.set("sample_size", sampleSize.toString());

  return apiFetch<PreviewImpactResponse>(`${BASE_PATH}/preview?${params}`);
}

/**
 * Export current baseline configuration to JSON
 */
export async function exportBaseline(): Promise<BaselineMetadata> {
  return apiFetch<BaselineMetadata>(`${BASE_PATH}/export`);
}

/**
 * Validate a baseline JSON structure
 */
export async function validateBaseline(baseline: BaselineMetadata | string): Promise<{
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}> {
  const payload = typeof baseline === "string"
    ? { baseline_json: JSON.parse(baseline) }
    : { baseline_json: baseline };
  return apiFetch<{
    valid: boolean;
    errors?: string[];
    warnings?: string[];
  }>(`${BASE_PATH}/validate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
