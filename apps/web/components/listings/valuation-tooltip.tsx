"use client";

import { useMemo } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info } from "lucide-react";
import type { ValuationBreakdown } from "@/types/listings";

interface ValuationTooltipProps {
  /** List price in USD */
  listPrice: number;
  /** Adjusted value in USD */
  adjustedValue: number;
  /** Full valuation breakdown with rules and adjustments */
  valuationBreakdown?: ValuationBreakdown | null;
  /** Callback to open the full breakdown modal */
  onViewDetails?: () => void;
  /** Custom trigger element (defaults to info icon) */
  children?: React.ReactNode;
  /** Delay before showing tooltip in milliseconds */
  delayDuration?: number;
}

/**
 * ValuationTooltip Component
 *
 * Displays a hover tooltip with a quick summary of valuation calculation:
 * - List price and adjusted value
 * - Total adjustment (savings or premium)
 * - Top 3-5 rules by impact
 * - Link to full breakdown modal
 *
 * Accessibility:
 * - Keyboard accessible (Tab to focus, Escape to dismiss)
 * - Screen reader compatible with ARIA labels
 * - WCAG 2.1 AA compliant
 *
 * Usage:
 * ```tsx
 * <ValuationTooltip
 *   listPrice={999}
 *   adjustedValue={849}
 *   valuationBreakdown={breakdown}
 *   onViewDetails={() => setModalOpen(true)}
 * />
 * ```
 */
export function ValuationTooltip({
  listPrice,
  adjustedValue,
  valuationBreakdown,
  onViewDetails,
  children,
  delayDuration = 100,
}: ValuationTooltipProps) {
  // Calculate adjustment delta
  const delta = listPrice - adjustedValue;
  const deltaPercent = listPrice > 0 ? (delta / listPrice) * 100 : 0;
  const isSavings = delta > 0;

  // Extract top rules by absolute impact (top 5)
  const topRules = useMemo(() => {
    if (!valuationBreakdown?.adjustments) return [];

    return [...valuationBreakdown.adjustments]
      .sort((a, b) => Math.abs(b.adjustment_amount) - Math.abs(a.adjustment_amount))
      .slice(0, 5);
  }, [valuationBreakdown]);

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <TooltipProvider delayDuration={delayDuration}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children || (
            <button
              type="button"
              className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-sm"
              aria-label="View valuation details"
            >
              <Info className="h-4 w-4" />
            </button>
          )}
        </TooltipTrigger>
        <TooltipContent
          side="top"
          align="start"
          className="max-w-[320px] p-4"
          aria-label="Valuation calculation summary"
        >
          <div className="space-y-3">
            {/* Title */}
            <h4 className="font-semibold text-sm">Adjusted Value Calculation</h4>

            {/* Price Summary */}
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between items-baseline gap-4">
                <span className="text-muted-foreground">List Price:</span>
                <span className="font-medium tabular-nums">{formatCurrency(listPrice)}</span>
              </div>
              <div className="flex justify-between items-baseline gap-4">
                <span className="text-muted-foreground">Adjustments:</span>
                <span
                  className={`font-medium tabular-nums ${
                    isSavings ? "text-green-600 dark:text-green-500" : "text-red-600 dark:text-red-500"
                  }`}
                >
                  {isSavings ? "-" : "+"}
                  {formatCurrency(Math.abs(delta))}
                </span>
              </div>
              <div className="flex justify-between items-baseline gap-4 border-t pt-1.5">
                <span className="font-medium">Adjusted Value:</span>
                <span className="font-semibold text-base tabular-nums">
                  {formatCurrency(adjustedValue)}
                </span>
              </div>
              <div className="text-xs text-muted-foreground text-right">
                {deltaPercent > 0 ? "" : "+"}
                {Math.abs(deltaPercent).toFixed(1)}%{" "}
                {isSavings ? "savings" : "premium"}
              </div>
            </div>

            {/* Top Rules */}
            {topRules.length > 0 && (
              <div className="space-y-1.5 border-t pt-2">
                <p className="text-xs text-muted-foreground">
                  Applied {valuationBreakdown?.matched_rules_count || topRules.length} valuation{" "}
                  {(valuationBreakdown?.matched_rules_count || topRules.length) === 1
                    ? "rule"
                    : "rules"}
                  :
                </p>
                <ul className="space-y-1 text-xs">
                  {topRules.map((rule, index) => (
                    <li key={`${rule.rule_id}-${index}`} className="flex justify-between gap-2">
                      <span className="truncate" title={rule.rule_name}>
                        • {rule.rule_name}
                      </span>
                      <span
                        className={`font-mono whitespace-nowrap ${
                          rule.adjustment_amount < 0
                            ? "text-green-600 dark:text-green-500"
                            : "text-red-600 dark:text-red-500"
                        }`}
                      >
                        {rule.adjustment_amount < 0 ? "" : "+"}
                        {formatCurrency(rule.adjustment_amount)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* View Details Link */}
            {onViewDetails && (
              <button
                type="button"
                onClick={onViewDetails}
                className="w-full mt-2 pt-2 border-t text-xs text-primary hover:text-primary/80 hover:underline flex items-center justify-center gap-1 transition-colors focus:outline-none focus:ring-2 focus:ring-ring rounded-sm"
                aria-label="Open full valuation breakdown modal"
              >
                View Full Breakdown →
              </button>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
