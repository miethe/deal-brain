import { apiFetch } from "../utils";

export interface AdapterConfig {
  enabled: boolean;
  timeout_s: number;
  retries: number;
  api_key?: string | null;
}

export interface AdapterMetrics {
  adapter: string;
  success_rate: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  field_completeness_pct: number;
  last_24h_requests: number;
  measured_at: string;
}

export interface AdapterWithMetrics {
  adapter_id: string;
  name: string;
  description: string;
  config: AdapterConfig;
  metrics: AdapterMetrics | null;
  supported_domains: string[];
}

export interface AdapterConfigUpdate {
  enabled?: boolean;
  timeout_s?: number;
  retries?: number;
}

export async function fetchAllAdapters(): Promise<AdapterWithMetrics[]> {
  return apiFetch<AdapterWithMetrics[]>("/v1/admin/adapters");
}

export async function updateAdapterConfig(
  adapterId: string,
  update: AdapterConfigUpdate
): Promise<AdapterConfig> {
  return apiFetch<AdapterConfig>(`/v1/admin/adapters/${adapterId}`, {
    method: "PATCH",
    body: JSON.stringify(update),
  });
}

export async function fetchAdapterMetrics(adapterId: string): Promise<AdapterMetrics> {
  return apiFetch<AdapterMetrics>(`/v1/admin/adapters/${adapterId}/metrics`);
}
