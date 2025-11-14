import { apiFetch } from "../utils";

/**
 * Component identifiers for build configuration
 */
export interface BuildComponents {
  cpu_id: number;
  gpu_id?: number | null;
  ram_spec_id?: number | null;
  storage_spec_id?: number | null;
  psu_spec_id?: number | null;
  case_spec_id?: number | null;
}

/**
 * Valuation breakdown structure from backend
 */
export interface ValuationBreakdown {
  base_price: number;
  adjusted_price: number;
  delta_amount: number;
  delta_percentage: number;
  rules_applied: Array<{
    rule_id: number;
    rule_name: string;
    adjustment: number;
    component_type: string;
  }>;
}

/**
 * Performance metrics for build
 */
export interface BuildMetrics {
  dollar_per_cpu_mark_multi: number | null;
  dollar_per_cpu_mark_single: number | null;
  composite_score: number | null;
}

/**
 * Response from calculate endpoint
 */
export interface CalculateBuildResponse {
  valuation: ValuationBreakdown;
  metrics: BuildMetrics;
}

/**
 * Saved build structure
 */
export interface SavedBuild {
  id: number;
  user_id: string | null;
  build_name: string | null;
  build_snapshot: {
    components: BuildComponents;
    valuation: ValuationBreakdown;
    metrics: BuildMetrics;
  };
  share_token: string | null;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Request payload for saving a build
 */
export interface SaveBuildRequest {
  build_name?: string | null;
  components: BuildComponents;
  valuation: ValuationBreakdown;
  metrics: BuildMetrics;
  is_public?: boolean;
}

/**
 * Paginated response for listing builds
 */
export interface ListBuildsResponse {
  items: SavedBuild[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Calculate pricing and metrics for a build configuration
 */
export async function calculateBuild(
  components: BuildComponents
): Promise<CalculateBuildResponse> {
  return apiFetch<CalculateBuildResponse>("/v1/builder/calculate", {
    method: "POST",
    body: JSON.stringify(components),
  });
}

/**
 * Save a build configuration with valuation and metrics
 */
export async function saveBuild(buildData: SaveBuildRequest): Promise<SavedBuild> {
  return apiFetch<SavedBuild>("/v1/builder/builds", {
    method: "POST",
    body: JSON.stringify(buildData),
  });
}

/**
 * Get paginated list of user's builds
 */
export async function getUserBuilds(
  limit = 10,
  offset = 0
): Promise<ListBuildsResponse> {
  return apiFetch<ListBuildsResponse>(
    `/v1/builder/builds?limit=${limit}&offset=${offset}`
  );
}

/**
 * Get a specific build by ID
 */
export async function getBuildById(buildId: number): Promise<SavedBuild> {
  return apiFetch<SavedBuild>(`/v1/builder/builds/${buildId}`);
}

/**
 * Get a shared build by its public share token
 */
export async function getSharedBuild(shareToken: string): Promise<SavedBuild> {
  return apiFetch<SavedBuild>(`/v1/builder/builds/shared/${shareToken}`);
}

/**
 * Delete a saved build by ID
 */
export async function deleteBuild(buildId: number): Promise<void> {
  return apiFetch<void>(`/v1/builder/builds/${buildId}`, {
    method: "DELETE",
  });
}
