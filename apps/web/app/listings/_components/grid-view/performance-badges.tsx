"use client";

import { memo } from "react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface PerformanceBadgesProps {
  dollarPerSingleRaw?: number | null;
  dollarPerMultiRaw?: number | null;
  dollarPerSingleAdjusted?: number | null;
  dollarPerMultiAdjusted?: number | null;
}

/**
 * Performance Badges Component
 *
 * Displays 4 performance metric badges:
 * - $/ST (raw) - Dollar per single-thread CPU mark
 * - $/MT (raw) - Dollar per multi-thread CPU mark
 * - adj $/ST - Adjusted dollar per single-thread
 * - adj $/MT - Adjusted dollar per multi-thread
 *
 * Color accent: emerald for adjusted values that are better than raw
 */
export const PerformanceBadges = memo(function PerformanceBadges({
  dollarPerSingleRaw,
  dollarPerMultiRaw,
  dollarPerSingleAdjusted,
  dollarPerMultiAdjusted,
}: PerformanceBadgesProps) {
  const formatMetric = (value?: number | null): string => {
    if (value === null || value === undefined) return "—";
    return `$${value.toFixed(3)}`;
  };

  const isAdjustedBetter = (adjusted?: number | null, raw?: number | null): boolean => {
    if (!adjusted || !raw) return false;
    return adjusted < raw; // Lower is better for price efficiency
  };

  const getBadgeVariant = (isAdjusted: boolean, isBetter: boolean) => {
    if (!isAdjusted) return "secondary";
    return isBetter ? "default" : "secondary";
  };

  const getBadgeClassName = (isAdjusted: boolean, isBetter: boolean) => {
    if (!isAdjusted) return "";
    if (isBetter) {
      return "bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border-emerald-300";
    }
    return "";
  };

  return (
    <TooltipProvider>
      <div className="flex flex-wrap gap-1.5">
        {/* Raw $/ST */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="secondary" className="text-xs font-mono">
              {formatMetric(dollarPerSingleRaw)} /ST
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Price per single-thread CPU mark (base price)</p>
          </TooltipContent>
        </Tooltip>

        {/* Raw $/MT */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="secondary" className="text-xs font-mono">
              {formatMetric(dollarPerMultiRaw)} /MT
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Price per multi-thread CPU mark (base price)</p>
          </TooltipContent>
        </Tooltip>

        {/* Adjusted $/ST */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant={getBadgeVariant(true, isAdjustedBetter(dollarPerSingleAdjusted, dollarPerSingleRaw))}
              className={`text-xs font-mono ${getBadgeClassName(
                true,
                isAdjustedBetter(dollarPerSingleAdjusted, dollarPerSingleRaw)
              )}`}
            >
              adj {formatMetric(dollarPerSingleAdjusted)} /ST
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Price per single-thread CPU mark (adjusted value)</p>
            {isAdjustedBetter(dollarPerSingleAdjusted, dollarPerSingleRaw) && (
              <p className="text-emerald-600 font-medium">Better value after adjustments</p>
            )}
          </TooltipContent>
        </Tooltip>

        {/* Adjusted $/MT */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge
              variant={getBadgeVariant(true, isAdjustedBetter(dollarPerMultiAdjusted, dollarPerMultiRaw))}
              className={`text-xs font-mono ${getBadgeClassName(
                true,
                isAdjustedBetter(dollarPerMultiAdjusted, dollarPerMultiRaw)
              )}`}
            >
              adj {formatMetric(dollarPerMultiAdjusted)} /MT
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <p>Price per multi-thread CPU mark (adjusted value)</p>
            {isAdjustedBetter(dollarPerMultiAdjusted, dollarPerMultiRaw) && (
              <p className="text-emerald-600 font-medium">Better value after adjustments</p>
            )}
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
});
