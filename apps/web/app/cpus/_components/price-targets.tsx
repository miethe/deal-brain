"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { InfoIcon } from "lucide-react";

interface PriceTargetsProps {
  priceTargetGreat: number | null;
  priceTargetGood: number | null;
  priceTargetFair: number | null;
  confidence: 'high' | 'medium' | 'low' | 'insufficient' | null;
  sampleSize: number;
  variant?: 'compact' | 'detailed'; // default 'compact'
}

/**
 * Price Targets Component
 *
 * Displays price target tiers (Great/Good/Fair) with confidence badge and sample size.
 * Price targets are calculated from active listing adjusted prices:
 * - Great: One standard deviation below average (better deals)
 * - Good: Average adjusted price (typical market price)
 * - Fair: One standard deviation above average (premium pricing)
 *
 * Confidence levels based on sample size:
 * - high: 10+ listings
 * - medium: 5-9 listings
 * - low: 2-4 listings
 * - insufficient: <2 listings
 *
 * Variants:
 * - compact: Horizontal 3-column grid with minimal spacing (for cards)
 * - detailed: Vertical list with more spacing and larger text (for detail panels)
 *
 * Accessibility:
 * - Semantic color coding with text labels
 * - Tooltips explain what each price tier represents
 * - Alert message for insufficient data cases
 */
export const PriceTargets = React.memo(function PriceTargets({
  priceTargetGreat,
  priceTargetGood,
  priceTargetFair,
  confidence,
  sampleSize,
  variant = 'compact',
}: PriceTargetsProps) {
  // Handle insufficient data case
  if (confidence === 'insufficient' || sampleSize < 2 || !priceTargetGood) {
    return (
      <Alert variant="default" className="border-amber-200 bg-amber-50 dark:bg-amber-950/30">
        <InfoIcon className="h-4 w-4 text-amber-600" />
        <AlertDescription className="text-xs text-amber-800 dark:text-amber-200">
          Insufficient data - check{' '}
          <span className="font-semibold">Listings page</span> for available
          deals
        </AlertDescription>
      </Alert>
    );
  }

  // Get confidence badge variant
  const getConfidenceBadgeVariant = () => {
    switch (confidence) {
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

  // Get confidence tooltip content
  const getConfidenceTooltip = () => {
    switch (confidence) {
      case 'high':
        return 'High confidence: Based on 10+ listings';
      case 'medium':
        return 'Medium confidence: Based on 5-9 listings';
      case 'low':
        return 'Low confidence: Based on 2-4 listings';
      default:
        return 'Confidence level unknown';
    }
  };

  // Compact variant (for cards)
  if (variant === 'compact') {
    return (
      <div className="space-y-1.5">
        {/* Header with confidence badge */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Price Targets</span>
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge
                  variant={getConfidenceBadgeVariant()}
                  className="text-xs cursor-help"
                  aria-label={getConfidenceTooltip()}
                >
                  {confidence}
                </Badge>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="text-sm">{getConfidenceTooltip()}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Price tier grid */}
        <div className="grid grid-cols-3 gap-1.5 text-xs">
          {priceTargetGreat && (
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    className="rounded bg-emerald-50 dark:bg-emerald-950/30 p-1.5 text-center cursor-help"
                    role="region"
                    aria-label="Great deal price target"
                  >
                    <div className="text-emerald-700 dark:text-emerald-400 font-medium">
                      ${priceTargetGreat.toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Great</div>
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p className="text-sm">
                    Great Deal: One standard deviation below average price
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}

          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className="rounded bg-blue-50 dark:bg-blue-950/30 p-1.5 text-center cursor-help"
                  role="region"
                  aria-label="Good price target"
                >
                  <div className="text-blue-700 dark:text-blue-400 font-medium">
                    ${priceTargetGood.toLocaleString()}
                  </div>
                  <div className="text-muted-foreground">Good</div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="text-sm">
                  Good Price: Average market price for this CPU
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {priceTargetFair && (
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div
                    className="rounded bg-amber-50 dark:bg-amber-950/30 p-1.5 text-center cursor-help"
                    role="region"
                    aria-label="Fair price target"
                  >
                    <div className="text-amber-700 dark:text-amber-400 font-medium">
                      ${priceTargetFair.toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Fair</div>
                  </div>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p className="text-sm">
                    Fair Price: One standard deviation above average (premium)
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {/* Sample size footer */}
        {sampleSize > 0 && (
          <div className="text-xs text-muted-foreground text-center">
            Based on {sampleSize} listing{sampleSize !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    );
  }

  // Detailed variant (for detail panels)
  return (
    <div className="space-y-3">
      {/* Header with confidence badge */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Price Targets</h4>
        <TooltipProvider delayDuration={300}>
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge
                variant={getConfidenceBadgeVariant()}
                className="cursor-help"
                aria-label={getConfidenceTooltip()}
              >
                {confidence}
              </Badge>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              <p className="text-sm">{getConfidenceTooltip()}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Price tiers - vertical list */}
      <div className="space-y-2">
        {priceTargetGreat && (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className="rounded-lg bg-emerald-50 dark:bg-emerald-950/30 p-3 cursor-help"
                  role="region"
                  aria-label="Great deal price target"
                >
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm text-muted-foreground">Great Deal</span>
                    <span className="text-lg font-semibold text-emerald-700 dark:text-emerald-400">
                      ${priceTargetGreat.toLocaleString()}
                    </span>
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="text-sm">
                  Great Deal: One standard deviation below average price
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        <TooltipProvider delayDuration={300}>
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className="rounded-lg bg-blue-50 dark:bg-blue-950/30 p-3 cursor-help"
                role="region"
                aria-label="Good price target"
              >
                <div className="flex items-baseline justify-between">
                  <span className="text-sm text-muted-foreground">Good Price</span>
                  <span className="text-lg font-semibold text-blue-700 dark:text-blue-400">
                    ${priceTargetGood.toLocaleString()}
                  </span>
                </div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              <p className="text-sm">
                Good Price: Average market price for this CPU
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {priceTargetFair && (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <div
                  className="rounded-lg bg-amber-50 dark:bg-amber-950/30 p-3 cursor-help"
                  role="region"
                  aria-label="Fair price target"
                >
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm text-muted-foreground">Fair Price</span>
                    <span className="text-lg font-semibold text-amber-700 dark:text-amber-400">
                      ${priceTargetFair.toLocaleString()}
                    </span>
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="text-sm">
                  Fair Price: One standard deviation above average (premium)
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {/* Sample size footer */}
      {sampleSize > 0 && (
        <div className="text-sm text-muted-foreground">
          Based on {sampleSize} active listing{sampleSize !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
});
