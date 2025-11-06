/**
 * Help Text Usage Examples
 *
 * @module usage-examples
 * @description Demonstrates how to use centralized help text in components.
 * These examples show best practices for tooltips, empty states, error messages,
 * and info banners.
 *
 * NOTE: This file is for documentation purposes only. Copy patterns to your
 * components as needed.
 */

import React from "react";
import {
  METRIC_TOOLTIPS,
  FILTER_HELP,
  EMPTY_STATES,
  ERROR_MESSAGES,
  INFO_BANNERS,
  getMetricTooltip,
  getConfidenceTooltip,
  getPerformanceValueTooltip,
} from "./cpu-catalog-help";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { HelpCircle, InfoIcon, AlertTriangleIcon } from "lucide-react";

// ============================================================================
// EXAMPLE 1: Metric Tooltip in a Card
// ============================================================================

export function MetricTooltipExample({ cpuMark }: { cpuMark: number }) {
  const tooltip = getMetricTooltip("cpuMark");

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="cursor-help">
            <span className="text-sm text-muted-foreground">CPU Mark</span>
            <div className="text-xl font-semibold">{cpuMark.toLocaleString()}</div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="space-y-1">
            <p className="font-semibold">{tooltip.title}</p>
            <p className="text-xs text-muted-foreground">{tooltip.content}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ============================================================================
// EXAMPLE 2: Filter Label with Help Icon
// ============================================================================

export function FilterLabelWithHelpExample() {
  const socketHelp = FILTER_HELP.socket;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label htmlFor="socket-filter">{socketHelp.label}</Label>
        <TooltipProvider delayDuration={300}>
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="h-4 w-4 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent side="right" className="max-w-xs">
              <p className="text-sm">{socketHelp.help}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      {/* Filter control would go here */}
    </div>
  );
}

// ============================================================================
// EXAMPLE 3: Empty State with Action Button
// ============================================================================

export function EmptyStateExample({
  onClearFilters,
}: {
  onClearFilters: () => void;
}) {
  const emptyState = EMPTY_STATES.noResults;

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="text-center space-y-4 max-w-md">
        <h3 className="text-lg font-semibold text-foreground">
          {emptyState.title}
        </h3>
        <p className="text-sm text-muted-foreground">{emptyState.message}</p>
        {emptyState.action && (
          <Button onClick={onClearFilters} variant="outline">
            {emptyState.action}
          </Button>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// EXAMPLE 4: Error Alert with Retry Action
// ============================================================================

export function ErrorAlertExample({
  onRetry,
}: {
  onRetry: () => void;
}) {
  const error = ERROR_MESSAGES.loadCPUsFailed;

  return (
    <Alert variant="destructive" className="mb-4">
      <AlertTriangleIcon className="h-4 w-4" />
      <AlertTitle>{error.title}</AlertTitle>
      <AlertDescription className="mt-2">
        <p>{error.message}</p>
        <Button onClick={onRetry} variant="outline" size="sm" className="mt-3">
          {error.action}
        </Button>
      </AlertDescription>
    </Alert>
  );
}

// ============================================================================
// EXAMPLE 5: Info Banner
// ============================================================================

export function InfoBannerExample() {
  const banner = INFO_BANNERS.priceTargetsExplanation;

  // Map banner variant to Alert variant
  // Banner variants: "info", "warning", "tip"
  // Alert variants: "default" | "destructive" | undefined
  const alertVariant: "default" | "destructive" | undefined =
    banner.variant === "warning" ? "destructive" : "default";

  return (
    <Alert variant={alertVariant} className="mb-4">
      <InfoIcon className="h-4 w-4" />
      <AlertTitle>{banner.title}</AlertTitle>
      <AlertDescription>{banner.message}</AlertDescription>
    </Alert>
  );
}

// ============================================================================
// EXAMPLE 6: Dynamic Confidence Tooltip
// ============================================================================

export function ConfidenceBadgeExample({
  confidence,
  sampleSize,
}: {
  confidence: "high" | "medium" | "low" | "insufficient";
  sampleSize: number;
}) {
  const tooltip = getConfidenceTooltip(confidence);

  // Get badge variant based on confidence
  const getBadgeVariant = () => {
    switch (confidence) {
      case "high":
        return "default";
      case "medium":
        return "secondary";
      case "low":
      case "insufficient":
        return "outline";
      default:
        return "outline";
    }
  };

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant={getBadgeVariant()} className="cursor-help">
            {confidence}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="space-y-1">
            <p className="font-semibold">{tooltip.title}</p>
            <p className="text-xs text-muted-foreground">{tooltip.content}</p>
            <p className="text-xs text-muted-foreground mt-2">
              Sample size: {sampleSize} listings
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ============================================================================
// EXAMPLE 7: Dynamic Performance Value Tooltip
// ============================================================================

export function PerformanceValueBadgeExample({
  rating,
  dollarPerMark,
  percentile,
}: {
  rating: "excellent" | "good" | "fair" | "poor";
  dollarPerMark: number;
  percentile?: number;
}) {
  const tooltip = getPerformanceValueTooltip(rating);

  // Get badge color based on rating
  const getBadgeClassName = () => {
    switch (rating) {
      case "excellent":
        return "bg-emerald-600 text-white border-emerald-700";
      case "good":
        return "bg-emerald-500 text-white border-emerald-600";
      case "fair":
        return "bg-amber-500 text-black border-amber-600";
      case "poor":
        return "bg-red-500 text-white border-red-600";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className={`text-xs font-mono cursor-help ${getBadgeClassName()}`}
          >
            ${dollarPerMark.toFixed(4)}/mark
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <div className="space-y-1">
            <p className="font-semibold">{tooltip.title}</p>
            {percentile !== undefined && (
              <p className="text-xs">
                Better than {(100 - percentile).toFixed(0)}% of CPUs
              </p>
            )}
            <p className="text-xs text-muted-foreground">{tooltip.content}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ============================================================================
// EXAMPLE 8: Multiple Tooltips in a Specification Grid
// ============================================================================

export function SpecificationGridExample({
  cpu,
}: {
  cpu: {
    cores: number;
    threads: number;
    tdp_w: number;
    socket: string;
    release_year: number;
  };
}) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Cores */}
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-help">
              <span className="text-sm text-muted-foreground">
                {METRIC_TOOLTIPS.cores.title}
              </span>
              <div className="text-lg font-medium">{cpu.cores}</div>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <p className="text-sm">{METRIC_TOOLTIPS.cores.content}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Threads */}
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-help">
              <span className="text-sm text-muted-foreground">
                {METRIC_TOOLTIPS.threads.title}
              </span>
              <div className="text-lg font-medium">{cpu.threads}</div>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <p className="text-sm">{METRIC_TOOLTIPS.threads.content}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* TDP */}
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-help">
              <span className="text-sm text-muted-foreground">
                {METRIC_TOOLTIPS.tdp.title}
              </span>
              <div className="text-lg font-medium">{cpu.tdp_w}W</div>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <p className="text-sm">{METRIC_TOOLTIPS.tdp.content}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Socket */}
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-help">
              <span className="text-sm text-muted-foreground">
                {METRIC_TOOLTIPS.socket.title}
              </span>
              <div className="text-lg font-medium">{cpu.socket}</div>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <p className="text-sm">{METRIC_TOOLTIPS.socket.content}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}

// ============================================================================
// EXAMPLE 9: Insufficient Data Alert (Price Targets)
// ============================================================================

export function InsufficientDataAlertExample() {
  const emptyState = EMPTY_STATES.noPriceTargets;

  return (
    <Alert variant="default" className="border-amber-200 bg-amber-50 dark:bg-amber-950/30">
      <InfoIcon className="h-4 w-4 text-amber-600" />
      <AlertTitle className="text-amber-800 dark:text-amber-200">
        {emptyState.title}
      </AlertTitle>
      <AlertDescription className="text-xs text-amber-700 dark:text-amber-300">
        {emptyState.message}
      </AlertDescription>
    </Alert>
  );
}

// ============================================================================
// EXAMPLE 10: Combined Tooltip with Multiple Metrics
// ============================================================================

export function CombinedMetricTooltipExample({
  cpuMarkSingle,
  cpuMarkMulti,
}: {
  cpuMarkSingle: number;
  cpuMarkMulti: number;
}) {
  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="cursor-help rounded-lg border p-3">
            <div className="space-y-2">
              <div>
                <span className="text-xs text-muted-foreground">Single-Thread</span>
                <div className="text-lg font-semibold">
                  {cpuMarkSingle.toLocaleString()}
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Multi-Thread</span>
                <div className="text-lg font-semibold">
                  {cpuMarkMulti.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="right" className="max-w-sm">
          <div className="space-y-3">
            <div>
              <p className="font-semibold">
                {METRIC_TOOLTIPS.singleThreadRating.title}
              </p>
              <p className="text-xs text-muted-foreground">
                {METRIC_TOOLTIPS.singleThreadRating.content}
              </p>
            </div>
            <div>
              <p className="font-semibold">{METRIC_TOOLTIPS.cpuMark.title}</p>
              <p className="text-xs text-muted-foreground">
                {METRIC_TOOLTIPS.cpuMark.content}
              </p>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
