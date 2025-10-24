import type { GpuRecordDetail } from "@/types/listing-detail";
import { Separator } from "@/components/ui/separator";
import { Box, MemoryStick, Gauge, Zap } from "lucide-react";

export interface GpuTooltipContentProps {
  gpu: {
    id: number;
    name: string;
    model?: string | null;
    manufacturer?: string | null;
    vram_gb?: number | null;
    vram_type?: string | null;
    tdp_w?: number | null;
    cores?: number | null;
    gpu_mark?: number | null;
  };
}

/**
 * GPU tooltip content component
 *
 * Displays rich GPU information in EntityTooltip hover card:
 * - GPU name and manufacturer
 * - VRAM capacity and type
 * - TDP and core count
 * - Performance metrics (GPU Mark)
 *
 * @example
 * ```tsx
 * <EntityTooltip
 *   entityType="gpu"
 *   entityId={gpu.id}
 *   tooltipContent={(data) => <GpuTooltipContent gpu={data} />}
 * >
 *   NVIDIA RTX 3060
 * </EntityTooltip>
 * ```
 */
export function GpuTooltipContent({ gpu }: GpuTooltipContentProps) {
  const formatNumber = (value: number | null | undefined) =>
    value != null ? value.toLocaleString() : "—";

  return (
    <div className="space-y-3">
      {/* Header: GPU Name */}
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Box className="h-4 w-4 text-primary" />
          <span>{gpu.model || gpu.name}</span>
        </div>
        {gpu.manufacturer && (
          <div className="mt-1 text-xs text-muted-foreground">{gpu.manufacturer}</div>
        )}
      </div>

      <Separator />

      {/* GPU Specifications */}
      <div className="space-y-2 text-sm">
        {gpu.vram_gb && (
          <div className="flex justify-between">
            <span className="flex items-center gap-1 text-muted-foreground">
              <MemoryStick className="h-3 w-3" />
              VRAM
            </span>
            <span className="font-medium">
              {gpu.vram_gb}GB{gpu.vram_type ? ` ${gpu.vram_type}` : ""}
            </span>
          </div>
        )}

        {gpu.cores && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Cores</span>
            <span className="font-medium">{formatNumber(gpu.cores)}</span>
          </div>
        )}

        {gpu.tdp_w && (
          <div className="flex justify-between">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Zap className="h-3 w-3" />
              TDP
            </span>
            <span className="font-medium">{gpu.tdp_w}W</span>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      {gpu.gpu_mark && (
        <>
          <Separator />
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <Gauge className="h-3 w-3" />
              Performance
            </div>

            <div className="flex justify-between">
              <span className="text-muted-foreground">GPU Mark</span>
              <span className="font-medium">{formatNumber(gpu.gpu_mark)}</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
