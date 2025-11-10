/**
 * ValuationTooltip Demo Component
 *
 * Visual demonstration of the ValuationTooltip component with various scenarios.
 * Use this page for manual testing and visual verification.
 *
 * To view: Create a page at app/test-valuation-tooltip/page.tsx that imports this component
 */

"use client";

import { useState } from "react";
import { ValuationTooltip } from "../valuation-tooltip";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ValuationBreakdown } from "@/types/listings";

// Mock scenarios
const scenarios = [
  {
    name: "Good Deal (15% Savings)",
    listPrice: 999,
    adjustedValue: 849,
    breakdown: {
      listing_price: 999,
      adjusted_price: 849,
      total_adjustment: 150,
      matched_rules_count: 3,
      adjustments: [
        {
          rule_id: 1,
          rule_name: "RAM Deduction (8GB DDR4)",
          adjustment_amount: -80,
          actions: [],
        },
        {
          rule_id: 2,
          rule_name: "Storage Deduction (256GB SSD)",
          adjustment_amount: -50,
          actions: [],
        },
        {
          rule_id: 3,
          rule_name: "Condition Adjustment (Good)",
          adjustment_amount: -20,
          actions: [],
        },
      ],
    } as ValuationBreakdown,
  },
  {
    name: "Premium Listing (10% Above Market)",
    listPrice: 1000,
    adjustedValue: 1100,
    breakdown: {
      listing_price: 1000,
      adjusted_price: 1100,
      total_adjustment: -100,
      matched_rules_count: 2,
      adjustments: [
        {
          rule_id: 4,
          rule_name: "Premium CPU Upgrade (i7 → i9)",
          adjustment_amount: 150,
          actions: [],
        },
        {
          rule_id: 5,
          rule_name: "Excellent Condition Bonus",
          adjustment_amount: -50,
          actions: [],
        },
      ],
    } as ValuationBreakdown,
  },
  {
    name: "Many Rules (10 Applied)",
    listPrice: 1200,
    adjustedValue: 950,
    breakdown: {
      listing_price: 1200,
      adjusted_price: 950,
      total_adjustment: 250,
      matched_rules_count: 10,
      adjustments: Array.from({ length: 10 }, (_, i) => ({
        rule_id: i + 1,
        rule_name: `Rule ${i + 1}: ${["RAM", "Storage", "GPU", "CPU", "Condition", "Warranty", "Shipping", "Accessories", "Form Factor", "Brand"][i]} Adjustment`,
        adjustment_amount: -(10 + i * 15),
        actions: [],
      })),
    } as ValuationBreakdown,
  },
  {
    name: "No Breakdown Data",
    listPrice: 899,
    adjustedValue: 799,
    breakdown: null,
  },
];

export function ValuationTooltipDemo() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">ValuationTooltip Component Demo</h1>
        <p className="text-muted-foreground">
          Hover over the info icons or tab to focus them to see the tooltip.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {scenarios.map((scenario, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{scenario.name}</CardTitle>
                <Badge variant={scenario.adjustedValue < scenario.listPrice ? "default" : "secondary"}>
                  {scenario.adjustedValue < scenario.listPrice ? "Savings" : "Premium"}
                </Badge>
              </div>
              <CardDescription>
                List: ${scenario.listPrice} | Adjusted: ${scenario.adjustedValue}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Price Display with Tooltip */}
              <div className="flex items-center gap-2">
                <div className="flex-1">
                  <div className="text-sm text-muted-foreground">Adjusted Value</div>
                  <div className="text-2xl font-bold">
                    ${scenario.adjustedValue}
                  </div>
                </div>
                <ValuationTooltip
                  listPrice={scenario.listPrice}
                  adjustedValue={scenario.adjustedValue}
                  valuationBreakdown={scenario.breakdown}
                  onViewDetails={() => {
                    setModalOpen(true);
                    alert(`Opening modal for: ${scenario.name}`);
                  }}
                />
              </div>

              {/* Breakdown Summary */}
              {scenario.breakdown && (
                <div className="text-xs text-muted-foreground space-y-1 pt-2 border-t">
                  <div>Rules Applied: {scenario.breakdown.matched_rules_count || 0}</div>
                  <div>
                    Total Adjustment: ${Math.abs(scenario.listPrice - scenario.adjustedValue)}{" "}
                    {scenario.adjustedValue < scenario.listPrice ? "savings" : "premium"}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Custom Trigger Example */}
      <Card>
        <CardHeader>
          <CardTitle>Custom Trigger Example</CardTitle>
          <CardDescription>
            The tooltip can use any custom trigger element
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Adjusted Value</div>
              <div className="text-2xl font-bold">$849</div>
            </div>
            <ValuationTooltip
              listPrice={999}
              adjustedValue={849}
              valuationBreakdown={scenarios[0].breakdown}
              onViewDetails={() => alert("View details clicked!")}
            >
              <button className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                Show Breakdown
              </button>
            </ValuationTooltip>
          </div>
        </CardContent>
      </Card>

      {/* Accessibility Testing Card */}
      <Card>
        <CardHeader>
          <CardTitle>Accessibility Testing</CardTitle>
          <CardDescription>
            Test keyboard navigation and screen reader compatibility
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Keyboard Navigation:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Press Tab to focus the info icon</li>
              <li>• Tooltip appears on focus</li>
              <li>• Press Tab again to focus "View Full Breakdown" link</li>
              <li>• Press Escape to dismiss tooltip</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Screen Reader:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Button has aria-label "View valuation details"</li>
              <li>• Tooltip content has aria-label "Valuation calculation summary"</li>
              <li>• All interactive elements are properly labeled</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Modal State Display */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-md">
            <CardHeader>
              <CardTitle>Modal Opened</CardTitle>
              <CardDescription>
                In production, this would show the ValuationBreakdownModal
              </CardDescription>
            </CardHeader>
            <CardContent>
              <button
                onClick={() => setModalOpen(false)}
                className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                Close
              </button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
