"use client";

import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PerformanceBadgeProps {
  label: string; // "ST", "MT", "iGPU"
  value: number;
  variant?: 'excellent' | 'good' | 'fair' | 'poor' | 'igpu' | null;
}

/**
 * Performance Badge Component
 *
 * Displays PassMark benchmark scores with color coding based on performance rating.
 * Includes tooltip with explanation of the metric.
 *
 * Variants:
 * - excellent: Green (0-25th percentile - top 25% value)
 * - good: Blue (25-50th percentile)
 * - fair: Orange (50-75th percentile)
 * - poor: Gray (75-100th percentile - bottom 25% value)
 * - igpu: Purple (integrated GPU metric)
 */
export function PerformanceBadge({ label, value, variant }: PerformanceBadgeProps) {
  // Get badge color classes based on variant
  const getBadgeClasses = () => {
    switch (variant) {
      case 'excellent':
        return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800';
      case 'good':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-950/30 dark:text-blue-400 border-blue-300 dark:border-blue-800';
      case 'fair':
        return 'bg-amber-100 text-amber-800 dark:bg-amber-950/30 dark:text-amber-400 border-amber-300 dark:border-amber-800';
      case 'poor':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-950/30 dark:text-gray-400 border-gray-300 dark:border-gray-800';
      case 'igpu':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-950/30 dark:text-purple-400 border-purple-300 dark:border-purple-800';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-950/30 dark:text-gray-400 border-gray-300 dark:border-gray-800';
    }
  };

  // Get tooltip content based on label
  const getTooltipContent = () => {
    switch (label) {
      case 'ST':
        return 'PassMark Single-Thread Score: Measures single-core performance';
      case 'MT':
        return 'PassMark Multi-Thread Score: Measures multi-core performance';
      case 'iGPU':
        return 'Integrated GPU PassMark Score: Measures graphics performance';
      default:
        return 'PassMark Benchmark Score';
    }
  };

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className={`text-xs font-mono cursor-help ${getBadgeClasses()}`}
          >
            {label}: {value.toLocaleString()}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <p className="text-sm">{getTooltipContent()}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
