import { Separator } from "@/components/ui/separator";
import { HardDrive, Gauge, Box } from "lucide-react";

export interface StorageProfileTooltipContentProps {
  storageProfile: {
    id: number;
    label?: string | null;
    capacity_gb?: number | null;
    medium?: string | null; // "SSD" | "HDD" | "NVMe"
    interface?: string | null; // "SATA" | "NVMe" | "PCIe"
    form_factor?: string | null; // "M.2" | "2.5\"" | "3.5\""
    read_speed_mbps?: number | null;
    write_speed_mbps?: number | null;
  };
}

/**
 * Storage profile tooltip content component
 *
 * Displays rich storage profile information in EntityTooltip hover card:
 * - Capacity and medium (SSD/HDD/NVMe)
 * - Interface and form factor
 * - Read/write speeds (if available)
 *
 * @example
 * ```tsx
 * <EntityTooltip
 *   entityType="storage-profile"
 *   entityId={storageProfile.id}
 *   tooltipContent={(data) => <StorageProfileTooltipContent storageProfile={data} />}
 * >
 *   1TB NVMe SSD
 * </EntityTooltip>
 * ```
 */
export function StorageProfileTooltipContent({
  storageProfile,
}: StorageProfileTooltipContentProps) {
  const formatCapacity = (gb: number | null | undefined) => {
    if (!gb) return "—";
    return gb >= 1000 ? `${(gb / 1000).toFixed(1)}TB` : `${gb}GB`;
  };

  const formatSpeed = (mbps: number | null | undefined) => {
    if (!mbps) return "—";
    return mbps >= 1000 ? `${(mbps / 1000).toFixed(1)} GB/s` : `${mbps} MB/s`;
  };

  const formatLabel = () => {
    if (storageProfile.label) return storageProfile.label;

    const parts: string[] = [];
    if (storageProfile.capacity_gb) parts.push(formatCapacity(storageProfile.capacity_gb));
    if (storageProfile.medium) parts.push(storageProfile.medium.toUpperCase());

    return parts.length > 0 ? parts.join(" ") : "Storage Profile";
  };

  return (
    <div className="space-y-3">
      {/* Header: Storage Label */}
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold">
          <HardDrive className="h-4 w-4 text-primary" />
          <span>{formatLabel()}</span>
        </div>
      </div>

      <Separator />

      {/* Storage Specifications */}
      <div className="space-y-2 text-sm">
        {storageProfile.capacity_gb && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Capacity</span>
            <span className="font-medium">{formatCapacity(storageProfile.capacity_gb)}</span>
          </div>
        )}

        {storageProfile.medium && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Type</span>
            <span className="font-medium">{storageProfile.medium.toUpperCase()}</span>
          </div>
        )}

        {storageProfile.interface && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Interface</span>
            <span className="font-medium">{storageProfile.interface}</span>
          </div>
        )}

        {storageProfile.form_factor && (
          <div className="flex justify-between">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Box className="h-3 w-3" />
              Form Factor
            </span>
            <span className="font-medium">{storageProfile.form_factor}</span>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      {(storageProfile.read_speed_mbps || storageProfile.write_speed_mbps) && (
        <>
          <Separator />
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <Gauge className="h-3 w-3" />
              Performance
            </div>

            {storageProfile.read_speed_mbps && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Read Speed</span>
                <span className="font-medium">{formatSpeed(storageProfile.read_speed_mbps)}</span>
              </div>
            )}

            {storageProfile.write_speed_mbps && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Write Speed</span>
                <span className="font-medium">{formatSpeed(storageProfile.write_speed_mbps)}</span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
