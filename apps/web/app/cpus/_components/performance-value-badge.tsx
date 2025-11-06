"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ArrowDownIcon, ArrowUpIcon, MinusIcon } from "lucide-react";

interface PerformanceValueBadgeProps {
  rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
  dollarPerMark: number | null;  // $/PassMark ratio
  percentile?: number | null;     // 0-100 where 0 is best value
  metricType?: 'single' | 'multi'; // ST or MT metric
}

/**
 * Performance Value Badge Component
 *
 * Displays $/PassMark rating with color-coded badge and directional arrow indicator.
 * Lower $/mark ratio = better value (cheaper per unit of performance).
 *
 * Rating Tiers (based on percentile):
 * - excellent: 0-25th percentile (top 25% value) - Dark green with down arrow
 * - good: 25-50th percentile - Medium green with down arrow
 * - fair: 50-75th percentile - Yellow with minus icon
 * - poor: 75-100th percentile (bottom 25% value) - Red with up arrow
 *
 * Tooltip displays:
 * - Rating label (e.g., "Excellent Value")
 * - Percentile rank if provided (e.g., "Better than 85% of CPUs")
 * - Description of what the rating means
 *
 * Accessibility:
 * - ARIA labels for screen readers
 * - Keyboard navigation via Tooltip
 * - Semantic color coding with text labels
 */
export const PerformanceValueBadge = React.memo(function PerformanceValueBadge({
  rating,
  dollarPerMark,
  percentile,
  metricType = 'multi',
}: PerformanceValueBadgeProps) {
  // Handle null/missing data
  if (dollarPerMark === null || rating === null) {
    return (
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant="outline"
              className="text-xs font-mono cursor-help bg-gray-100 text-gray-500 dark:bg-gray-950/30 dark:text-gray-400"
              aria-label="No performance value data available"
            >
              <MinusIcon className="mr-1 h-3 w-3" aria-hidden="true" />
              No data
            </Badge>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <p className="text-sm">Performance value data not available</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Get badge color classes and icon based on rating
  const getBadgeConfig = () => {
    switch (rating) {
      case 'excellent':
        return {
          className: 'bg-emerald-600 text-white border-emerald-700',
          icon: ArrowDownIcon,
          label: 'Excellent Value',
          description: 'Top 25% value - significantly lower cost per performance mark',
        };
      case 'good':
        return {
          className: 'bg-emerald-500 text-white border-emerald-600',
          icon: ArrowDownIcon,
          label: 'Good Value',
          description: 'Above average value - lower than typical cost per performance mark',
        };
      case 'fair':
        return {
          className: 'bg-amber-500 text-black border-amber-600',
          icon: MinusIcon,
          label: 'Fair Value',
          description: 'Average value - typical cost per performance mark',
        };
      case 'poor':
        return {
          className: 'bg-red-500 text-white border-red-600',
          icon: ArrowUpIcon,
          label: 'Poor Value',
          description: 'Bottom 25% value - higher cost per performance mark',
        };
      default:
        return {
          className: 'bg-gray-100 text-gray-800 dark:bg-gray-950/30 dark:text-gray-400',
          icon: MinusIcon,
          label: 'Unknown',
          description: 'Value rating not available',
        };
    }
  };

  const config = getBadgeConfig();
  const Icon = config.icon;
  const metricLabel = metricType === 'single' ? 'ST' : 'MT';

  // Format dollar per mark value (4 decimal places)
  const formattedValue = `$${dollarPerMark.toFixed(4)}/mark`;

  // Build tooltip content
  const tooltipContent = (
    <div className="space-y-1">
      <p className="font-semibold">{config.label}</p>
      {percentile !== null && percentile !== undefined && (
        <p className="text-xs">
          Better than {(100 - percentile).toFixed(0)}% of CPUs
        </p>
      )}
      <p className="text-xs text-muted-foreground">{config.description}</p>
      <p className="text-xs font-mono mt-2">
        {metricLabel} Metric: {formattedValue}
      </p>
    </div>
  );

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className={`text-xs font-mono cursor-help ${config.className}`}
            aria-label={`${config.label}: ${formattedValue} for ${metricLabel} performance`}
          >
            <Icon className="mr-1 h-3 w-3" aria-hidden="true" />
            {formattedValue}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          {tooltipContent}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
});
