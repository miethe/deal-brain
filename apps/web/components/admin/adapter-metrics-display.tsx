"use client";

import { Badge } from "../ui/badge";
import type { AdapterMetrics } from "../../lib/api/adapter-settings";

interface AdapterMetricsDisplayProps {
  metrics: AdapterMetrics | null;
  isLoading?: boolean;
}

export function AdapterMetricsDisplay({ metrics, isLoading }: AdapterMetricsDisplayProps) {
  if (isLoading) {
    return (
      <div className="space-y-3" aria-busy="true" aria-label="Loading metrics">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="space-y-1">
              <div className="h-3 w-20 animate-pulse rounded bg-muted" />
              <div className="h-5 w-16 animate-pulse rounded bg-muted" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
        No metrics available yet. Metrics are collected after the first successful ingestion.
      </div>
    );
  }

  const successRateBadgeVariant =
    metrics.success_rate >= 95
      ? "default"
      : metrics.success_rate >= 80
      ? "secondary"
      : "destructive";

  const completenessVariant =
    metrics.field_completeness_pct >= 90
      ? "default"
      : metrics.field_completeness_pct >= 70
      ? "secondary"
      : "outline";

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Success Rate</p>
          <div className="flex items-center gap-2">
            <Badge variant={successRateBadgeVariant} aria-label={`Success rate: ${metrics.success_rate}%`}>
              {metrics.success_rate.toFixed(1)}%
            </Badge>
          </div>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">P50 Latency</p>
          <p className="text-sm font-medium" aria-label={`P50 latency: ${metrics.p50_latency_ms} milliseconds`}>
            {metrics.p50_latency_ms.toFixed(0)}ms
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">P95 Latency</p>
          <p className="text-sm font-medium" aria-label={`P95 latency: ${metrics.p95_latency_ms} milliseconds`}>
            {metrics.p95_latency_ms.toFixed(0)}ms
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Field Completeness</p>
          <div className="flex items-center gap-2">
            <Badge variant={completenessVariant} aria-label={`Field completeness: ${metrics.field_completeness_pct}%`}>
              {metrics.field_completeness_pct.toFixed(1)}%
            </Badge>
          </div>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Last 24h Requests</p>
          <p className="text-sm font-medium" aria-label={`Last 24 hours requests: ${metrics.last_24h_requests}`}>
            {metrics.last_24h_requests.toLocaleString()}
          </p>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Measured At</p>
          <p className="text-sm font-medium" aria-label={`Measured at: ${new Date(metrics.measured_at).toLocaleString()}`}>
            {new Date(metrics.measured_at).toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
}
