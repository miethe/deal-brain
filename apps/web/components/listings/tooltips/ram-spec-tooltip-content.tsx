import { Separator } from "@/components/ui/separator";
import { MemoryStick, Gauge } from "lucide-react";

export interface RamSpecTooltipContentProps {
  ramSpec: {
    id: number;
    label?: string | null;
    total_capacity_gb?: number | null;
    speed_mhz?: number | null;
    ddr_generation?: string | null;
    module_count?: number | null;
    latency_cl?: number | null;
  };
}

/**
 * RAM specification tooltip content component
 *
 * Displays rich RAM specification information in EntityTooltip hover card:
 * - Capacity and generation (DDR4/DDR5)
 * - Speed (MHz)
 * - Module configuration
 * - Latency (CL)
 *
 * @example
 * ```tsx
 * <EntityTooltip
 *   entityType="ram-spec"
 *   entityId={ramSpec.id}
 *   tooltipContent={(data) => <RamSpecTooltipContent ramSpec={data} />}
 * >
 *   32GB DDR4 3600MHz
 * </EntityTooltip>
 * ```
 */
export function RamSpecTooltipContent({ ramSpec }: RamSpecTooltipContentProps) {
  const formatLabel = () => {
    if (ramSpec.label) return ramSpec.label;

    const parts: string[] = [];
    if (ramSpec.total_capacity_gb) parts.push(`${ramSpec.total_capacity_gb}GB`);
    if (ramSpec.ddr_generation) parts.push(ramSpec.ddr_generation.toUpperCase());
    if (ramSpec.speed_mhz) parts.push(`${ramSpec.speed_mhz}MHz`);

    return parts.length > 0 ? parts.join(" ") : "RAM Specification";
  };

  return (
    <div className="space-y-3">
      {/* Header: RAM Label */}
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold">
          <MemoryStick className="h-4 w-4 text-primary" />
          <span>{formatLabel()}</span>
        </div>
      </div>

      <Separator />

      {/* RAM Specifications */}
      <div className="space-y-2 text-sm">
        {ramSpec.total_capacity_gb && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Capacity</span>
            <span className="font-medium">{ramSpec.total_capacity_gb}GB</span>
          </div>
        )}

        {ramSpec.ddr_generation && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Generation</span>
            <span className="font-medium">{ramSpec.ddr_generation.toUpperCase()}</span>
          </div>
        )}

        {ramSpec.speed_mhz && (
          <div className="flex justify-between">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Gauge className="h-3 w-3" />
              Speed
            </span>
            <span className="font-medium">{ramSpec.speed_mhz} MHz</span>
          </div>
        )}

        {ramSpec.module_count && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Modules</span>
            <span className="font-medium">{ramSpec.module_count}x</span>
          </div>
        )}

        {ramSpec.latency_cl && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Latency</span>
            <span className="font-medium">CL{ramSpec.latency_cl}</span>
          </div>
        )}
      </div>
    </div>
  );
}
