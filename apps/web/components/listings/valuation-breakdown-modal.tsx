"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, TrendingDown, TrendingUp, ExternalLink } from "lucide-react";
import Link from "next/link";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Separator } from "../ui/separator";
import { apiFetch } from "../../lib/utils";
import { ValuationCell } from "./valuation-cell";
import { useValuationThresholds } from "@/hooks/use-valuation-thresholds";

interface AppliedRuleDetail {
  rule_group_name: string;
  rule_name: string;
  rule_description?: string;
  adjustment_amount: number;
  conditions_met: string[];
  actions_applied: string[];
}

interface ValuationBreakdown {
  listing_id: number;
  listing_title: string;
  base_price_usd: number;
  adjusted_price_usd: number;
  total_adjustment: number;
  active_ruleset: string;
  applied_rules: AppliedRuleDetail[];
}

interface ValuationBreakdownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  listingId: number;
  listingTitle: string;
  thumbnailUrl?: string | null;
}

export function ValuationBreakdownModal({
  open,
  onOpenChange,
  listingId,
  listingTitle,
  thumbnailUrl,
}: ValuationBreakdownModalProps) {
  const [expandedRules, setExpandedRules] = useState<Set<number>>(new Set());
  const { data: thresholds } = useValuationThresholds();

  const { data: breakdown, isLoading } = useQuery<ValuationBreakdown>({
    queryKey: ["valuation-breakdown", listingId],
    queryFn: () => apiFetch<ValuationBreakdown>(`/v1/listings/${listingId}/valuation-breakdown`),
    enabled: open,
  });

  const toggleRuleExpansion = (index: number) => {
    const newExpanded = new Set(expandedRules);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRules(newExpanded);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Valuation Breakdown</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="py-12 text-center text-muted-foreground">Loading breakdown...</div>
        ) : breakdown ? (
          <div className="space-y-6">
            {/* Listing Header with Thumbnail and Valuation */}
            <div className="flex items-start gap-4">
              {thumbnailUrl && (
                <img
                  src={thumbnailUrl}
                  alt={listingTitle}
                  className="w-24 h-24 object-cover rounded-lg border"
                />
              )}
              <div className="flex-1 space-y-2">
                <h3 className="font-semibold text-lg">{listingTitle}</h3>
                {thresholds && (
                  <ValuationCell
                    adjustedPrice={breakdown.adjusted_price_usd}
                    listPrice={breakdown.base_price_usd}
                    thresholds={thresholds}
                    onDetailsClick={() => {}} // Already in details view
                  />
                )}
              </div>
            </div>

            <Separator />

            {/* Base Price */}
            <div>
              <h4 className="font-medium mb-2 text-sm text-muted-foreground">Base Price</h4>
              <p className="text-2xl font-semibold">{formatCurrency(breakdown.base_price_usd)}</p>
            </div>

            {/* Applied Rules */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-sm text-muted-foreground">Applied Rules</h4>
                <Badge variant="outline" className="text-xs">
                  {breakdown.active_ruleset}
                </Badge>
              </div>
              {breakdown.applied_rules.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-8 border rounded-lg">
                  No rules applied to this listing
                </div>
              ) : (
                <div className="space-y-2">
                  {breakdown.applied_rules.map((rule, index) => {
                    const isExpanded = expandedRules.has(index);
                    return (
                      <Card key={index} className="overflow-hidden">
                        <div
                          className="flex items-center justify-between p-4 cursor-pointer hover:bg-accent/50 transition-colors"
                          onClick={() => toggleRuleExpansion(index)}
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <div className="h-6 w-6 flex items-center justify-center">
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm">{rule.rule_name}</span>
                                <Badge variant="secondary" className="text-xs">
                                  {rule.rule_group_name}
                                </Badge>
                              </div>
                              {rule.rule_description && !isExpanded && (
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  {rule.rule_description}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            {rule.adjustment_amount < 0 ? (
                              <span className="font-medium text-green-600">
                                {formatCurrency(rule.adjustment_amount)}
                              </span>
                            ) : rule.adjustment_amount > 0 ? (
                              <span className="font-medium text-red-600">
                                +{formatCurrency(rule.adjustment_amount)}
                              </span>
                            ) : (
                              <span className="font-medium text-muted-foreground">
                                {formatCurrency(0)}
                              </span>
                            )}
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="border-t bg-muted/30 p-4 space-y-3 text-sm">
                            {rule.rule_description && (
                              <div>
                                <p className="text-xs text-muted-foreground mb-1">Description</p>
                                <p className="text-sm">{rule.rule_description}</p>
                              </div>
                            )}

                            {rule.conditions_met.length > 0 && (
                              <div>
                                <p className="text-xs text-muted-foreground mb-1">Conditions Met</p>
                                <ul className="space-y-1">
                                  {rule.conditions_met.map((condition, idx) => (
                                    <li key={idx} className="text-xs">
                                      • {condition}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {rule.actions_applied.length > 0 && (
                              <div>
                                <p className="text-xs text-muted-foreground mb-1">Actions Applied</p>
                                <ul className="space-y-1">
                                  {rule.actions_applied.map((action, idx) => (
                                    <li key={idx} className="text-xs">
                                      • {action}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>

            <Separator />

            {/* Final Summary */}
            <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
              <span className="font-semibold">Adjusted Price</span>
              <span className="text-2xl font-bold">
                {formatCurrency(breakdown.adjusted_price_usd)}
              </span>
            </div>

            {/* Link to full breakdown page */}
            <div className="flex justify-center">
              <Button asChild variant="ghost" size="sm">
                <Link href={`/listings/${listingId}`} className="flex items-center gap-2">
                  View Full Details
                  <ExternalLink className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center text-muted-foreground">
            No valuation data available for this listing
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
