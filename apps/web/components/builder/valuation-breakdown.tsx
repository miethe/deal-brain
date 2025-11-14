import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ValuationBreakdown as ValuationBreakdownType } from "@/lib/api/builder";

interface ValuationBreakdownProps {
  breakdown: ValuationBreakdownType | null;
}

/**
 * Expandable valuation breakdown showing applied rules and adjustments
 *
 * Displays:
 * - Base price calculation
 * - Applied valuation rules (deductions/premiums)
 * - Final adjusted price
 */
export function ValuationBreakdown({ breakdown }: ValuationBreakdownProps) {
  const [expanded, setExpanded] = useState(false);

  if (!breakdown) return null;

  const hasRules = breakdown.rules_applied && breakdown.rules_applied.length > 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Valuation Breakdown</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="h-8 w-8 p-0"
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-4 pt-0">
          {/* Base Price */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground mb-2">
              Base Configuration
            </h4>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Component Total</span>
              <span className="font-semibold tabular-nums">
                ${breakdown.base_price.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Applied Rules */}
          {hasRules && (
            <div className="border-t pt-4">
              <h4 className="text-xs font-semibold text-muted-foreground mb-2">
                Valuation Adjustments
              </h4>
              <div className="space-y-2">
                {breakdown.rules_applied.map((rule, index) => (
                  <div key={index} className="flex justify-between text-sm">
                    <div className="flex-1">
                      <span className="text-muted-foreground">{rule.rule_name}</span>
                      <span className="text-xs text-muted-foreground/70 ml-1">
                        ({rule.component_type})
                      </span>
                    </div>
                    <span
                      className={`font-semibold tabular-nums ml-2 ${
                        rule.adjustment < 0 ? "text-red-600" : "text-green-600"
                      }`}
                    >
                      {rule.adjustment > 0 ? "+" : ""}$
                      {Math.abs(rule.adjustment).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Final Adjusted Price */}
          <div className="border-t pt-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-semibold">Adjusted Value</span>
              <span className="text-lg font-bold tabular-nums">
                ${breakdown.adjusted_price.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center mt-2">
              <span className="text-xs text-muted-foreground">Total Adjustment</span>
              <span
                className={`text-sm font-semibold tabular-nums ${
                  breakdown.delta_amount >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {breakdown.delta_amount > 0 ? "+" : ""}$
                {breakdown.delta_amount.toFixed(2)}
              </span>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
