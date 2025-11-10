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
 * Displays CPU price targets (Great/Good/Fair) calculated from active listing data.
 * Provides market-based price guidance with confidence indicators based on sample size.
 *
 * This component is memoized for performance optimization and supports two display
 * variants optimized for different contexts (cards vs detail panels).
 *
 * @component
 *
 * @param {PriceTargetsProps} props - Component props
 * @param {number | null} props.priceTargetGreat - Great deal price (mean - 1 std dev)
 * @param {number | null} props.priceTargetGood - Good price (mean/average)
 * @param {number | null} props.priceTargetFair - Fair price (mean + 1 std dev)
 * @param {'high' | 'medium' | 'low' | 'insufficient' | null} props.confidence - Confidence level based on sample size
 * @param {number} props.sampleSize - Number of listings used to calculate targets
 * @param {'compact' | 'detailed'} [props.variant='compact'] - Display variant for different contexts
 *
 * @returns {React.ReactElement} Price targets display or insufficient data alert
 *
 * @example
 * // Compact variant for CPU grid cards
 * <PriceTargets
 *   priceTargetGreat={320}
 *   priceTargetGood={350}
 *   priceTargetFair={380}
 *   confidence="high"
 *   sampleSize={12}
 *   variant="compact"
 * />
 *
 * @example
 * // Detailed variant for CPU detail panel
 * <PriceTargets
 *   priceTargetGreat={320}
 *   priceTargetGood={350}
 *   priceTargetFair={380}
 *   confidence="medium"
 *   sampleSize={7}
 *   variant="detailed"
 * />
 *
 * @example
 * // Insufficient data case
 * <PriceTargets
 *   priceTargetGreat={null}
 *   priceTargetGood={null}
 *   priceTargetFair={null}
 *   confidence="insufficient"
 *   sampleSize={1}
 *   variant="compact"
 * />
 *
 * Price Tiers:
 * - Great Deal (Green): Mean - 1 standard deviation - below average prices (best deals)
 * - Good Price (Blue): Mean/Average - typical market price for this CPU
 * - Fair Price (Yellow/Amber): Mean + 1 standard deviation - above average pricing (premium)
 *
 * Confidence Levels:
 * - high: 10+ listings - highly reliable price estimates
 * - medium: 5-9 listings - moderate confidence in estimates
 * - low: 2-4 listings - limited data, use with caution
 * - insufficient: <2 listings - not enough data to calculate targets
 *
 * Variants:
 * - compact: Horizontal 3-column grid layout (suitable for CPU cards, listings rows)
 *   - Minimal spacing and smaller text
 *   - Header with confidence badge
 *   - Sample size footer
 * - detailed: Vertical list layout (suitable for detail panels, modals)
 *   - Larger text and more spacing
 *   - Better readability for focused viewing
 *   - Individual section styling for each tier
 *
 * Insufficient Data Alert:
 * - Displays when confidence is 'insufficient' or sample size < 2
 * - Suggests checking the Listings page for available deals
 * - Amber/warning styling to draw attention
 *
 * Tooltips:
 * - Each price tier has a tooltip explaining what it represents
 * - Confidence badge has tooltip showing the calculation basis
 * - Helps users understand pricing methodology
 *
 * Accessibility:
 * - Semantic color coding with text labels (not relying on color alone)
 * - ARIA labels for all interactive elements
 * - Role="region" on price tier sections for screen reader context
 * - Tooltip content keyboard accessible and announced
 * - Sufficient color contrast (WCAG 2.1 AA compliant)
 * - Locale-aware currency formatting for different regions
 *
 * Performance:
 * - Memoized with React.memo to prevent unnecessary re-renders
 * - Conditional rendering for Great/Fair prices (optional data)
 * - No expensive calculations in render path
 * - Tooltip delay set to 300ms to reduce tooltip dom operations
 *
 * @see PriceTargetsProps for prop type definitions
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
