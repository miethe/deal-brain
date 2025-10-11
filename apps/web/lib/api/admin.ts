import { apiFetch } from "../utils";

export interface AdminTaskSubmission {
  task_id: string;
  action: string;
  status: string;
  message?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface AdminTaskStatus {
  task_id: string;
  action: string | null;
  status: string;
  state: string;
  result?: unknown;
  error?: string | null;
}

export interface ValuationRecalcPayload {
  listing_ids?: number[];
  ruleset_id?: number | null;
  batch_size?: number;
  include_inactive?: boolean;
  reason?: string | null;
}

export interface MetricsRecalcPayload {
  listing_ids?: number[];
}

export async function triggerValuationRecalc(
  payload: ValuationRecalcPayload
): Promise<AdminTaskSubmission> {
  return apiFetch<AdminTaskSubmission>("/v1/admin/tasks/recalculate-valuations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function triggerMetricsRecalc(
  payload: MetricsRecalcPayload
): Promise<AdminTaskSubmission> {
  return apiFetch<AdminTaskSubmission>("/v1/admin/tasks/recalculate-metrics", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function triggerCpuMarkRecalc(
  payload: MetricsRecalcPayload
): Promise<AdminTaskSubmission> {
  return apiFetch<AdminTaskSubmission>("/v1/admin/tasks/recalculate-cpu-marks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function triggerPassmarkImport(file: File): Promise<AdminTaskSubmission> {
  const formData = new FormData();
  formData.append("upload", file);
  return apiFetch<AdminTaskSubmission>("/v1/admin/tasks/import-passmark", {
    method: "POST",
    body: formData,
  });
}

export async function triggerEntityImport(
  entity: string,
  file: File,
  dryRun: boolean
): Promise<AdminTaskSubmission> {
  const formData = new FormData();
  formData.append("entity", entity);
  formData.append("dry_run", dryRun ? "true" : "false");
  formData.append("upload", file);
  return apiFetch<AdminTaskSubmission>("/v1/admin/tasks/import-entities", {
    method: "POST",
    body: formData,
  });
}

export async function fetchTaskStatus(taskId: string): Promise<AdminTaskStatus> {
  return apiFetch<AdminTaskStatus>(`/v1/admin/tasks/${taskId}`);
}
