import * as React from "react";
import { cn } from "@/lib/utils";

interface DualMetricCellProps {
  raw: number | null | undefined;
  adjusted: number | null | undefined;
  prefix?: string; // e.g., "$"
  suffix?: string; // e.g., "W"
  decimals?: number; // default 3 for metrics
}

function DualMetricCellComponent({
  raw,
  adjusted,
  prefix = "$",
  suffix = "",
  decimals = 3,
}: DualMetricCellProps) {
  if (!raw && raw !== 0) {
    return <span className="text-muted-foreground text-sm">—</span>;
  }

  const formatValue = (val: number) =>
    `${prefix}${val.toFixed(decimals)}${suffix}`;

  // Calculate improvement percentage
  const improvement =
    adjusted !== null && adjusted !== undefined && raw > adjusted
      ? ((raw - adjusted) / raw * 100).toFixed(0)
      : null;

  const degradation =
    adjusted !== null && adjusted !== undefined && adjusted > raw
      ? ((adjusted - raw) / raw * 100).toFixed(0)
      : null;

  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-sm font-medium">{formatValue(raw)}</span>
      {adjusted !== null && adjusted !== undefined && (
        <span
          className={cn(
            "text-xs",
            improvement && "text-green-600 font-medium",
            degradation && "text-red-600 font-medium",
            !improvement && !degradation && "text-muted-foreground"
          )}
        >
          {formatValue(adjusted)}
          {improvement && (
            <span className="ml-1" title="Improvement after adjustments">
              ↓{improvement}%
            </span>
          )}
          {degradation && (
            <span className="ml-1" title="Higher after adjustments">
              ↑{degradation}%
            </span>
          )}
        </span>
      )}
    </div>
  );
}

export const DualMetricCell = React.memo(DualMetricCellComponent);
