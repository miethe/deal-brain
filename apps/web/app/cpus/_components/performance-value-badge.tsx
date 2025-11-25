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
 * Displays CPU performance value ($/PassMark ratio) with color-coded rating badges.
 * Lower $/mark values indicate better performance per dollar spent.
 *
 * This component is memoized for performance optimization and is typically used in
 * CPU grid cards, detail panels, and analytics displays.
 *
 * @component
 *
 * @param {PerformanceValueBadgeProps} props - Component props
 * @param {'excellent' | 'good' | 'fair' | 'poor' | null} props.rating - Performance rating based on percentile
 * @param {number | null} props.dollarPerMark - The $/PassMark ratio (e.g., 0.0623 = $0.0623 per PassMark point)
 * @param {number | null} [props.percentile] - Percentile ranking (0-100, where 0 is best value)
 * @param {'single' | 'multi'} [props.metricType='multi'] - Type of metric (ST=single-thread, MT=multi-thread)
 *
 * @returns {React.ReactElement} Badge element with tooltip
 *
 * @example
 * // Excellent value CPU with single-thread metric
 * <PerformanceValueBadge
 *   rating="excellent"
 *   dollarPerMark={0.0623}
 *   percentile={22.5}
 *   metricType="single"
 * />
 *
 * @example
 * // Good multi-thread value
 * <PerformanceValueBadge
 *   rating="good"
 *   dollarPerMark={0.0894}
 *   percentile={45.2}
 *   metricType="multi"
 * />
 *
 * @example
 * // Insufficient data
 * <PerformanceValueBadge
 *   rating={null}
 *   dollarPerMark={null}
 * />
 *
 * Rating Colors & Meanings:
 * - Excellent (Dark Green): Top 25% value - significantly lower cost per performance mark
 * - Good (Medium Green): 25-50th percentile - above average value
 * - Fair (Yellow): 50-75th percentile - average cost per performance mark
 * - Poor (Red): Bottom 25% value - higher cost per performance mark
 * - No Data (Gray): Insufficient benchmark or price data
 *
 * Tooltip Content:
 * - Rating label with description
 * - Percentile rank showing how many CPUs offer better value
 * - Formatted $/mark metric
 * - Single-thread (ST) or Multi-thread (MT) indicator
 *
 * Accessibility:
 * - ARIA labels describing rating and metric
 * - Icons marked as decorative with aria-hidden="true"
 * - Keyboard accessible via Tooltip component (arrow key, Enter navigation)
 * - Sufficient color contrast (WCAG 2.1 AA compliant)
 * - Works with screen readers (tooltip content announced)
 *
 * Performance:
 * - Memoized with React.memo to prevent unnecessary re-renders
 * - No expensive calculations in render path
 * - Tooltip delay set to 300ms to reduce unnecessary DOM operations
 *
 * @see PerformanceValueBadgeProps for prop type definitions
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
