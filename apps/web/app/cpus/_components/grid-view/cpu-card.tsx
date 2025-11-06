"use client";

import { memo } from "react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CPURecord } from "@/types/cpus";
import { PerformanceBadge } from "./performance-badge";
import { useCPUCatalogStore } from "@/stores/cpu-catalog-store";
import { Cpu } from "lucide-react";

interface CPUCardProps {
  cpu: CPURecord;
}

/**
 * CPU Card Component
 *
 * Card layout for grid view with:
 * - Header: CPU name with manufacturer badge
 * - Specs: Socket, cores/threads, clock speeds, TDP
 * - Performance badges: CPU Mark Single/Multi with color coding
 * - Price targets: Good/Great/Fair prices (if available)
 * - Footer: iGPU info, release year, listings count
 * - Hover state with shadow and cursor pointer
 * - Click to open detail modal (Phase 3)
 */
export const CPUCard = memo(function CPUCard({ cpu }: CPUCardProps) {
  const openDetailsDialog = useCPUCatalogStore((state) => state.openDetailsDialog);

  const handleCardClick = () => {
    // Open CPU detail modal (to be implemented in Phase 3)
    openDetailsDialog(cpu.id);
  };

  // Format clock speed for display
  const formatClockSpeed = (ghz: number | null): string => {
    if (!ghz) return "N/A";
    return `${ghz.toFixed(2)} GHz`;
  };

  // Get performance badge variant based on rating
  const getPerformanceVariant = (): 'excellent' | 'good' | 'fair' | 'poor' | null => {
    return cpu.performance_value_rating as 'excellent' | 'good' | 'fair' | 'poor' | null;
  };

  // Get confidence badge color
  const getConfidenceBadgeVariant = () => {
    switch (cpu.price_target_confidence) {
      case 'high':
        return 'default';
      case 'medium':
        return 'secondary';
      case 'low':
        return 'outline';
      default:
        return 'outline';
    }
  };

  return (
    <Card
      className="group cursor-pointer hover:shadow-lg transition-shadow duration-200 flex flex-col h-full"
      onClick={handleCardClick}
    >
      {/* Header */}
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 space-y-1">
            <h3 className="font-semibold text-base line-clamp-2">
              {cpu.name}
            </h3>
            <div className="flex gap-1.5">
              <Badge variant="secondary" className="text-xs">
                {cpu.manufacturer}
              </Badge>
            </div>
          </div>
          <Cpu className="h-5 w-5 text-muted-foreground flex-shrink-0" />
        </div>
      </CardHeader>

      {/* Content */}
      <CardContent className="pb-3 flex-1 space-y-3">
        {/* Specs Grid */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Socket:</span>
            <div className="font-medium">{cpu.socket || "N/A"}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Cores/Threads:</span>
            <div className="font-medium">
              {cpu.cores && cpu.threads
                ? `${cpu.cores}C/${cpu.threads}T`
                : "N/A"}
            </div>
          </div>
          <div>
            <span className="text-muted-foreground">TDP:</span>
            <div className="font-medium">
              {cpu.tdp_w ? `${cpu.tdp_w}W` : "N/A"}
            </div>
          </div>
          <div>
            <span className="text-muted-foreground">Release:</span>
            <div className="font-medium">
              {cpu.release_year || "N/A"}
            </div>
          </div>
        </div>

        {/* Performance Badges */}
        {(cpu.cpu_mark_single || cpu.cpu_mark_multi) && (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1.5">
              {cpu.cpu_mark_single && (
                <PerformanceBadge
                  label="ST"
                  value={cpu.cpu_mark_single}
                  variant={getPerformanceVariant()}
                />
              )}
              {cpu.cpu_mark_multi && (
                <PerformanceBadge
                  label="MT"
                  value={cpu.cpu_mark_multi}
                  variant={getPerformanceVariant()}
                />
              )}
              {cpu.igpu_mark && (
                <PerformanceBadge
                  label="iGPU"
                  value={cpu.igpu_mark}
                  variant="igpu"
                />
              )}
            </div>
          </div>
        )}

        {/* Price Targets */}
        {cpu.price_target_good && (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Price Targets</span>
              <Badge variant={getConfidenceBadgeVariant()} className="text-xs">
                {cpu.price_target_confidence}
              </Badge>
            </div>
            <div className="grid grid-cols-3 gap-1.5 text-xs">
              {cpu.price_target_great && (
                <div className="rounded bg-emerald-50 dark:bg-emerald-950/30 p-1.5 text-center">
                  <div className="text-emerald-700 dark:text-emerald-400 font-medium">
                    ${cpu.price_target_great.toLocaleString()}
                  </div>
                  <div className="text-muted-foreground">Great</div>
                </div>
              )}
              <div className="rounded bg-blue-50 dark:bg-blue-950/30 p-1.5 text-center">
                <div className="text-blue-700 dark:text-blue-400 font-medium">
                  ${cpu.price_target_good.toLocaleString()}
                </div>
                <div className="text-muted-foreground">Good</div>
              </div>
              {cpu.price_target_fair && (
                <div className="rounded bg-amber-50 dark:bg-amber-950/30 p-1.5 text-center">
                  <div className="text-amber-700 dark:text-amber-400 font-medium">
                    ${cpu.price_target_fair.toLocaleString()}
                  </div>
                  <div className="text-muted-foreground">Fair</div>
                </div>
              )}
            </div>
            {cpu.price_target_sample_size > 0 && (
              <div className="text-xs text-muted-foreground text-center">
                Based on {cpu.price_target_sample_size} listing{cpu.price_target_sample_size !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        )}

        {/* Performance Value Metrics */}
        {(cpu.dollar_per_mark_single || cpu.dollar_per_mark_multi) && (
          <div className="space-y-1 text-xs">
            <div className="text-muted-foreground">Value Metrics:</div>
            <div className="space-y-0.5">
              {cpu.dollar_per_mark_single && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">$/ST Mark:</span>
                  <span className="font-mono font-medium">
                    ${cpu.dollar_per_mark_single.toFixed(4)}
                  </span>
                </div>
              )}
              {cpu.dollar_per_mark_multi && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">$/MT Mark:</span>
                  <span className="font-mono font-medium">
                    ${cpu.dollar_per_mark_multi.toFixed(4)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>

      {/* Footer */}
      <CardFooter className="pt-3 border-t flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex gap-2">
          {cpu.igpu_model && (
            <span title={cpu.igpu_model}>iGPU: {cpu.igpu_model}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {cpu.listings_count > 0 && (
            <Badge variant="outline" className="text-xs">
              {cpu.listings_count} listing{cpu.listings_count !== 1 ? 's' : ''}
            </Badge>
          )}
        </div>
      </CardFooter>
    </Card>
  );
});
