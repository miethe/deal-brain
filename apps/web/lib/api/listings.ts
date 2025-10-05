import { apiFetch } from "../utils";

export interface CpuResponse {
  id: number;
  name: string;
  manufacturer: string;
  cpu_mark_single: number | null;
  cpu_mark_multi: number | null;
  igpu_mark: number | null;
  tdp_w: number | null;
  release_year: number | null;
  igpu_model: string | null;
}

export interface ListingResponse {
  id: number;
  title: string;
  price_usd: number;
  adjusted_price_usd: number | null;
  condition: string;
  // Performance metrics
  dollar_per_cpu_mark_single: number | null;
  dollar_per_cpu_mark_single_adjusted: number | null;
  dollar_per_cpu_mark_multi: number | null;
  dollar_per_cpu_mark_multi_adjusted: number | null;
  // Product metadata
  manufacturer: string | null;
  series: string | null;
  model_number: string | null;
  form_factor: string | null;
  // CPU details
  cpu: CpuResponse | null;
  cpu_id: number | null;
  // Ports data
  ports_profile: {
    id: number;
    ports: Array<{ port_type: string; quantity: number }>;
  } | null;
}

export interface PortEntry {
  port_type: string;
  quantity: number;
}

/**
 * Fetch full CPU details by ID
 */
export async function getCpu(cpuId: number): Promise<CpuResponse> {
  return apiFetch<CpuResponse>(`/v1/catalog/cpus/${cpuId}`);
}

/**
 * Recalculate all performance metrics for a listing
 */
export async function recalculateListingMetrics(
  listingId: number
): Promise<ListingResponse> {
  return apiFetch<ListingResponse>(`/v1/listings/${listingId}/recalculate-metrics`, {
    method: "POST",
  });
}

/**
 * Update ports for a listing
 */
export async function updateListingPorts(
  listingId: number,
  ports: PortEntry[]
): Promise<void> {
  await apiFetch(`/v1/listings/${listingId}/ports`, {
    method: "POST",
    body: JSON.stringify({ ports }),
  });
}

/**
 * Get ports for a listing
 */
export async function getListingPorts(listingId: number): Promise<PortEntry[]> {
  const response = await apiFetch<{ ports: PortEntry[] }>(
    `/v1/listings/${listingId}/ports`
  );
  return response.ports;
}
