"use client";

import { DealMeter } from "./deal-meter";
import { PerformanceMetrics } from "./performance-metrics";
import { ValuationBreakdown } from "./valuation-breakdown";
import { useBuilderCalculations } from "@/hooks/use-builder-calculations";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

/**
 * Main valuation panel displaying pricing, metrics, and deal quality
 *
 * Features:
 * - Real-time calculations with debouncing
 * - Color-coded deal quality indicator
 * - Performance metrics display
 * - Expandable breakdown of applied rules
 * - Loading and error states
 * - Sticky positioning on desktop (lg:sticky lg:top-6)
 */
export function ValuationPanel() {
  const { valuation, metrics, isCalculating, error } = useBuilderCalculations();

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Valuation Error</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Empty state - no CPU selected yet
  if (!valuation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Build Valuation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-sm text-muted-foreground">
              Select a CPU to begin calculating pricing and performance metrics
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Active state with valuation data
  return (
    <div className="space-y-4 lg:sticky lg:top-6">
      {/* Main Valuation Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Build Valuation</CardTitle>
            {isCalculating && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-xs">Calculating...</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Pricing Summary */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Base Price</span>
              <span className="font-semibold tabular-nums">
                ${valuation.base_price.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Adjusted Value</span>
              <span className="font-semibold text-lg tabular-nums">
                ${valuation.adjusted_price.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center border-t pt-2">
              <span className="text-sm font-medium">Your Savings</span>
              <span
                className={`font-semibold tabular-nums ${
                  valuation.delta_amount >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {valuation.delta_amount > 0 ? "+" : ""}$
                {valuation.delta_amount.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Deal Meter - Color-coded quality indicator */}
          <DealMeter deltaPercentage={valuation.delta_percentage} />
        </CardContent>
      </Card>

      {/* Performance Metrics Card */}
      <PerformanceMetrics metrics={metrics} />

      {/* Valuation Breakdown - Expandable details */}
      <ValuationBreakdown breakdown={valuation} />
    </div>
  );
}
