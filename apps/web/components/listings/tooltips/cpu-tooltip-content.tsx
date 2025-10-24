import type { CpuRecordDetail } from "@/types/listing-detail";
import { Separator } from "@/components/ui/separator";
import { Cpu, Gauge, Zap, Calendar } from "lucide-react";

export interface CpuTooltipContentProps {
  cpu: CpuRecordDetail;
}

/**
 * CPU tooltip content component
 *
 * Displays rich CPU information in EntityTooltip hover card:
 * - CPU name and manufacturer
 * - Core/thread count
 * - TDP and clock speeds
 * - Performance metrics (CPU Mark, Single-Thread, iGPU)
 * - Release year
 *
 * @example
 * ```tsx
 * <EntityTooltip
 *   entityType="cpu"
 *   entityId={cpu.id}
 *   tooltipContent={(data) => <CpuTooltipContent cpu={data} />}
 * >
 *   Intel Core i5-12400
 * </EntityTooltip>
 * ```
 */
export function CpuTooltipContent({ cpu }: CpuTooltipContentProps) {
  const formatNumber = (value: number | null | undefined) =>
    value != null ? value.toLocaleString() : "—";

  const formatClock = (ghz: number | null | undefined) =>
    ghz != null ? `${ghz.toFixed(2)} GHz` : "—";

  return (
    <div className="space-y-3">
      {/* Header: CPU Name */}
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Cpu className="h-4 w-4 text-primary" />
          <span>{cpu.name}</span>
        </div>
        {cpu.manufacturer && (
          <div className="mt-1 text-xs text-muted-foreground">{cpu.manufacturer}</div>
        )}
      </div>

      <Separator />

      {/* Core Specifications */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Cores / Threads</span>
          <span className="font-medium">
            {cpu.cores && cpu.threads ? `${cpu.cores}C / ${cpu.threads}T` : "—"}
          </span>
        </div>

        {(cpu.base_clock_ghz || cpu.boost_clock_ghz) && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Clock Speed</span>
            <span className="font-medium text-xs">
              {cpu.base_clock_ghz && formatClock(cpu.base_clock_ghz)}
              {cpu.base_clock_ghz && cpu.boost_clock_ghz && " - "}
              {cpu.boost_clock_ghz && formatClock(cpu.boost_clock_ghz)}
            </span>
          </span>
        )}

        {cpu.tdp_w && (
          <div className="flex justify-between">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Zap className="h-3 w-3" />
              TDP
            </span>
            <span className="font-medium">{cpu.tdp_w}W</span>
          </div>
        )}

        {cpu.socket && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Socket</span>
            <span className="font-medium text-xs">{cpu.socket}</span>
          </div>
        )}

        {cpu.release_year && (
          <div className="flex justify-between">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Calendar className="h-3 w-3" />
              Released
            </span>
            <span className="font-medium">{cpu.release_year}</span>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      {(cpu.cpu_mark_multi || cpu.cpu_mark_single || cpu.igpu_mark) && (
        <>
          <Separator />
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <Gauge className="h-3 w-3" />
              Performance
            </div>

            {cpu.cpu_mark_multi && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Multi-Core</span>
                <span className="font-medium">{formatNumber(cpu.cpu_mark_multi)}</span>
              </div>
            )}

            {cpu.cpu_mark_single && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Single-Core</span>
                <span className="font-medium">{formatNumber(cpu.cpu_mark_single)}</span>
              </div>
            )}

            {cpu.igpu_mark && cpu.igpu_model && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">iGPU</span>
                <span className="font-medium text-xs">
                  {formatNumber(cpu.igpu_mark)} ({cpu.igpu_model})
                </span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
