"use client";

import React, { useMemo } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info } from "lucide-react";
import {
  calculateImprovement,
  getCpuMarkStyle,
  formatCpuMark,
  formatImprovement,
  getImprovementArrow,
} from "@/lib/cpu-mark-utils";
import { useCpuMarkThresholds } from "@/hooks/use-cpu-mark-thresholds";
import { cn } from "@/lib/utils";

export interface PerformanceMetricDisplayProps {
  /** Metric label (e.g., "$/CPU Mark Multi", "$/CPU Mark Single") */
  label: string;
  /** Overall score value (optional, for composite metrics) */
  score?: number;
  /** Base value calculated from list price */
  baseValue?: number;
  /** Adjusted value calculated from adjusted price */
  adjustedValue?: number;
  /** Currency prefix (default: "$") */
  prefix?: string;
  /** Value suffix (optional, e.g., "/mark") */
  suffix?: string;
  /** Number of decimal places (default: 3) */
  decimals?: number;
  /** Enable color coding based on improvement (default: true) */
  showColorCoding?: boolean;
  /** List price for calculation explanation */
  listPrice?: number;
  /** Adjusted price for calculation explanation */
  adjustedPrice?: number;
  /** CPU mark benchmark value for calculation explanation */
  cpuMark?: number;
  /** Delay before showing tooltip in milliseconds (default: 100) */
  delayDuration?: number;
}

/**
 * PerformanceMetricDisplay Component
 *
 * Displays CPU performance metrics with color-coded improvement indicators.
 * Shows base → adjusted value with improvement percentage and visual styling
 * based on configurable thresholds.
 *
 * Features:
 * - Color coding for improvement ranges (excellent, good, fair, neutral, poor, premium)
 * - Accessible design with WCAG 2.1 AA compliance
 * - Interactive tooltip with calculation methodology
 * - Memoized for optimal table performance
 * - Theme-aware CSS variable styling
 *
 * Color Ranges (from ADR-006):
 * - Excellent: ≥20% improvement (dark green)
 * - Good: 10-20% improvement (medium green)
 * - Fair: 5-10% improvement (light green)
 * - Neutral: 0-5% change (gray)
 * - Poor: -10-0% degradation (light red)
 * - Premium: <-10% degradation (dark red)
 *
 * Accessibility:
 * - Keyboard accessible (Tab to focus, Escape to dismiss tooltip)
 * - Screen reader compatible with comprehensive ARIA labels
 * - Color supplemented with text labels and symbols
 * - 4.5:1 contrast ratio on all color combinations
 *
 * @example
 * ```tsx
 * <PerformanceMetricDisplay
 *   label="$/CPU Mark Multi"
 *   baseValue={0.100}
 *   adjustedValue={0.080}
 *   listPrice={1000}
 *   adjustedPrice={800}
 *   cpuMark={10000}
 *   showColorCoding
 * />
 * ```
 */
export const PerformanceMetricDisplay = React.memo<PerformanceMetricDisplayProps>(
  function PerformanceMetricDisplay({
    label,
    score,
    baseValue,
    adjustedValue,
    prefix = "$",
    suffix = "",
    decimals = 3,
    showColorCoding = true,
    listPrice,
    adjustedPrice,
    cpuMark,
    delayDuration = 100,
  }) {
    // Fetch thresholds from settings API
    const { data: thresholds } = useCpuMarkThresholds();

    // Calculate improvement and styling
    const { improvement, colorStyle, arrow } = useMemo(() => {
      if (!baseValue || !adjustedValue || !thresholds) {
        return {
          improvement: 0,
          colorStyle: null,
          arrow: { symbol: '→', ariaLabel: 'no change' },
        };
      }

      const imp = calculateImprovement(baseValue, adjustedValue);
      const style = showColorCoding ? getCpuMarkStyle(imp, thresholds) : null;
      const arr = getImprovementArrow(imp);

      return {
        improvement: imp,
        colorStyle: style,
        arrow: arr,
      };
    }, [baseValue, adjustedValue, thresholds, showColorCoding]);

    // Format values for display
    const formattedBase = baseValue ? formatCpuMark(baseValue, decimals) : null;
    const formattedAdjusted = adjustedValue ? formatCpuMark(adjustedValue, decimals) : null;
    const formattedImprovement = improvement !== 0 ? formatImprovement(improvement) : null;

    // Build accessible aria label
    const ariaLabel = useMemo(() => {
      const parts: string[] = [label];

      if (score !== undefined) {
        parts.push(`score ${score.toFixed(1)}`);
      }

      if (formattedBase && formattedAdjusted) {
        parts.push(
          `efficiency ${prefix}${formattedAdjusted}${suffix} per mark`
        );

        if (colorStyle) {
          parts.push(`rated ${colorStyle.label}`);
        }

        if (improvement !== 0) {
          parts.push(
            `${improvement > 0 ? 'improved' : 'reduced'} by ${Math.abs(improvement).toFixed(1)}%`
          );
        }
      } else if (formattedAdjusted) {
        parts.push(`${prefix}${formattedAdjusted}${suffix}`);
      }

      return parts.join(', ');
    }, [label, score, formattedBase, formattedAdjusted, prefix, suffix, colorStyle, improvement]);

    // Display just adjusted value if no base value
    if (!baseValue || !formattedBase) {
      return (
        <div className="space-y-0.5">
          <div className="text-xs text-muted-foreground">{label}</div>
          {score !== undefined && (
            <div className="font-medium text-sm">{score.toFixed(1)}</div>
          )}
          {formattedAdjusted && (
            <div className="text-sm tabular-nums" aria-label={ariaLabel}>
              {prefix}{formattedAdjusted}{suffix}
            </div>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-0.5">
        {/* Label */}
        <div className="text-xs text-muted-foreground">{label}</div>

        {/* Score (if provided) */}
        {score !== undefined && (
          <div className="font-medium text-sm">{score.toFixed(1)}</div>
        )}

        {/* Base → Adjusted with tooltip */}
        <div className="flex items-center gap-1.5">
          <div className="flex items-baseline gap-1 text-sm tabular-nums">
            {/* Base value (muted) */}
            <span className="text-muted-foreground" aria-label={`Base: ${prefix}${formattedBase}${suffix}`}>
              {prefix}{formattedBase}
            </span>

            {/* Arrow indicator */}
            <span
              className="text-muted-foreground"
              aria-label={arrow.ariaLabel}
              aria-hidden="true"
            >
              {arrow.symbol}
            </span>

            {/* Adjusted value with color coding */}
            <span
              className={cn(
                "font-medium px-1.5 py-0.5 rounded text-xs border",
                colorStyle?.className
              )}
              role="status"
              aria-label={ariaLabel}
            >
              {prefix}{formattedAdjusted}{suffix}
              {/* Screen reader only: improvement label */}
              {colorStyle && (
                <span className="sr-only"> {colorStyle.label} efficiency</span>
              )}
            </span>
          </div>

          {/* Info tooltip */}
          {listPrice && adjustedPrice && cpuMark && (
            <TooltipProvider delayDuration={delayDuration}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="inline-flex items-center text-muted-foreground hover:text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-sm"
                    aria-label="View calculation details"
                  >
                    <Info className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent
                  side="top"
                  align="start"
                  className="max-w-[320px] p-4"
                  aria-label="Performance metric calculation details"
                >
                  <div className="space-y-3">
                    {/* Title */}
                    <h4 className="font-semibold text-sm">{label} Calculation</h4>

                    {/* Calculation breakdown */}
                    <div className="space-y-2 text-sm">
                      <div className="space-y-1">
                        <div className="flex justify-between items-baseline gap-4">
                          <span className="text-muted-foreground">List Price:</span>
                          <span className="font-mono tabular-nums">${listPrice.toFixed(0)}</span>
                        </div>
                        <div className="flex justify-between items-baseline gap-4">
                          <span className="text-muted-foreground">CPU Mark:</span>
                          <span className="font-mono tabular-nums">{cpuMark.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-baseline gap-4 border-t pt-1">
                          <span className="font-medium">Base Efficiency:</span>
                          <span className="font-mono tabular-nums">
                            ${formattedBase}/mark
                          </span>
                        </div>
                      </div>

                      <div className="space-y-1 border-t pt-2">
                        <div className="flex justify-between items-baseline gap-4">
                          <span className="text-muted-foreground">Adjusted Price:</span>
                          <span className="font-mono tabular-nums">${adjustedPrice.toFixed(0)}</span>
                        </div>
                        <div className="flex justify-between items-baseline gap-4">
                          <span className="text-muted-foreground">CPU Mark:</span>
                          <span className="font-mono tabular-nums">{cpuMark.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-baseline gap-4 border-t pt-1">
                          <span className="font-medium">Adjusted Efficiency:</span>
                          <span className="font-mono tabular-nums">
                            ${formattedAdjusted}/mark
                          </span>
                        </div>
                      </div>

                      {/* Improvement summary */}
                      {formattedImprovement && colorStyle && (
                        <div className="border-t pt-2">
                          <div className="flex justify-between items-baseline gap-4">
                            <span className="font-medium">Improvement:</span>
                            <span
                              className={cn(
                                "font-semibold tabular-nums",
                                improvement > 0
                                  ? "text-green-600 dark:text-green-500"
                                  : "text-red-600 dark:text-red-500"
                              )}
                            >
                              {formattedImprovement}
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            Rated: <span className="font-medium">{colorStyle.label}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Formula explanation */}
                    <div className="text-xs text-muted-foreground border-t pt-2">
                      <strong>Formula:</strong> Price ÷ CPU Mark
                      <br />
                      Lower values indicate better price-to-performance efficiency.
                    </div>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {/* Improvement percentage (below values) */}
        {formattedImprovement && colorStyle && (
          <div className="text-xs text-muted-foreground">
            {formattedImprovement} {colorStyle.label.toLowerCase()}
          </div>
        )}
      </div>
    );
  },
  // Custom comparison to prevent unnecessary re-renders
  (prevProps, nextProps) => {
    return (
      prevProps.label === nextProps.label &&
      prevProps.score === nextProps.score &&
      prevProps.baseValue === nextProps.baseValue &&
      prevProps.adjustedValue === nextProps.adjustedValue &&
      prevProps.prefix === nextProps.prefix &&
      prevProps.suffix === nextProps.suffix &&
      prevProps.decimals === nextProps.decimals &&
      prevProps.showColorCoding === nextProps.showColorCoding &&
      prevProps.listPrice === nextProps.listPrice &&
      prevProps.adjustedPrice === nextProps.adjustedPrice &&
      prevProps.cpuMark === nextProps.cpuMark
    );
  }
);
