"use client";

import { useQuery } from "@tanstack/react-query";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Separator } from "../ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { apiFetch } from "../../lib/utils";
import { ValuationCell } from "./valuation-cell";
import { useValuationThresholds } from "@/hooks/use-valuation-thresholds";
import type { LegacyValuationLine, ValuationAdjustment } from "../../types/listings";

interface ValuationBreakdown {
  listing_id: number;
  listing_title: string;
  base_price_usd: number;
  adjusted_price_usd: number;
  total_adjustment: number;
  total_deductions?: number | null;
  matched_rules_count: number;
  ruleset_id?: number | null;
  ruleset_name?: string | null;
  adjustments: ValuationAdjustment[];
  legacy_lines: LegacyValuationLine[];
}

interface ValuationBreakdownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  listingId: number;
  listingTitle: string;
  thumbnailUrl?: string | null;
}

const formatCurrency = (value: number | null | undefined): string =>
  value == null ?
    "—" :
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);

export function ValuationBreakdownModal({
  open,
  onOpenChange,
  listingId,
  listingTitle,
  thumbnailUrl,
}: ValuationBreakdownModalProps) {
  const { data: thresholds } = useValuationThresholds();

  const { data: breakdown, isLoading } = useQuery<ValuationBreakdown>({
    queryKey: ["valuation-breakdown", listingId],
    queryFn: () => apiFetch<ValuationBreakdown>(`/v1/listings/${listingId}/valuation-breakdown`),
    enabled: open,
  });

  const adjustments = breakdown?.adjustments ?? [];
  const legacyLines = breakdown?.legacy_lines ?? [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Valuation Breakdown</DialogTitle>
          {breakdown?.ruleset_name && (
            <DialogDescription>
              Calculated using ruleset <span className="font-medium">{breakdown.ruleset_name}</span>
            </DialogDescription>
          )}
        </DialogHeader>

        {isLoading ? (
          <div className="py-12 text-center text-muted-foreground">Loading breakdown...</div>
        ) : breakdown ? (
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              {thumbnailUrl && (
                <img
                  src={thumbnailUrl}
                  alt={listingTitle}
                  className="w-24 h-24 rounded-lg border object-cover"
                />
              )}
              <div className="flex-1 space-y-3">
                <div>
                  <h3 className="font-semibold text-lg">{listingTitle}</h3>
                  <p className="text-xs text-muted-foreground">
                    Listing ID #{breakdown.listing_id}
                  </p>
                </div>
                {thresholds && (
                  <ValuationCell
                    adjustedPrice={breakdown.adjusted_price_usd}
                    listPrice={breakdown.base_price_usd}
                    thresholds={thresholds}
                    onDetailsClick={() => {}}
                  />
                )}
                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline" className="capitalize">
                    Ruleset: {breakdown.ruleset_name ?? "Auto"}
                  </Badge>
                  <Badge variant="outline">
                    Matched rules: {breakdown.matched_rules_count ?? adjustments.length}
                  </Badge>
                </div>
              </div>
            </div>

            <Separator />

            <div className="grid gap-3 sm:grid-cols-3">
              <SummaryStat label="Base price" value={breakdown.base_price_usd} />
              <SummaryStat label="Adjusted price" value={breakdown.adjusted_price_usd} />
              <SummaryStat
                label="Total adjustment"
                value={breakdown.total_adjustment}
                tone={
                  breakdown.total_adjustment < 0 ? "positive" :
                  breakdown.total_adjustment > 0 ? "negative" :
                  "neutral"
                }
              />
            </div>
            {breakdown.total_deductions != null && (
              <p className="text-xs text-muted-foreground">
                Total deductions: {formatCurrency(breakdown.total_deductions)}
              </p>
            )}

            <div className="space-y-3">
              <h4 className="font-medium text-sm text-muted-foreground">Applied rules</h4>
              {adjustments.length === 0 ? (
                <div className="rounded-md border p-6 text-sm text-muted-foreground">
                  No rule-based adjustments were applied.
                </div>
              ) : (
                <div className="space-y-3">
                  {adjustments.map((adjustment, index) => (
                    <Card key={`${adjustment.rule_id ?? adjustment.rule_name}-${index}`}>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                        <CardTitle className="text-base font-semibold">
                          {adjustment.rule_name}
                        </CardTitle>
                        <span
                          className={
                            adjustment.adjustment_amount < 0 ? "text-emerald-600 font-semibold" :
                            adjustment.adjustment_amount > 0 ? "text-red-600 font-semibold" :
                            "text-muted-foreground font-medium"
                          }
                        >
                          {adjustment.adjustment_amount > 0 ? "+" : ""}
                          {formatCurrency(adjustment.adjustment_amount)}
                        </span>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {adjustment.actions.length === 0 ? (
                          <p className="text-xs text-muted-foreground">
                            No action details available for this rule.
                          </p>
                        ) : (
                          <ul className="space-y-2 text-xs text-muted-foreground">
                            {adjustment.actions.map((action, actionIndex) => (
                              <li key={actionIndex} className="flex items-start justify-between gap-3">
                                <div>
                                  <span className="font-medium text-foreground">
                                    {action.action_type ?? "Action"}
                                  </span>
                                  {action.metric && <span className="ml-1">· {action.metric}</span>}
                                </div>
                                <div className="text-right">
                                  <span
                                    className={
                                      action.value < 0 ? "text-emerald-600" :
                                      action.value > 0 ? "text-red-600" :
                                      "text-muted-foreground"
                                    }
                                  >
                                    {action.value > 0 ? "+" : ""}
                                    {formatCurrency(action.value)}
                                  </span>
                                  {action.error && (
                                    <div className="text-red-600 mt-0.5">Error: {action.error}</div>
                                  )}
                                </div>
                              </li>
                            ))}
                          </ul>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {legacyLines.length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h4 className="font-medium text-sm text-muted-foreground">Component deductions</h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Component</TableHead>
                        <TableHead>Quantity</TableHead>
                        <TableHead>Unit value</TableHead>
                        <TableHead>Condition</TableHead>
                        <TableHead className="text-right">Deduction</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {legacyLines.map((line, lineIndex) => (
                        <TableRow key={`${line.label}-${line.component_type}-${lineIndex}`}>
                          <TableCell>{line.label}</TableCell>
                          <TableCell>{line.quantity}</TableCell>
                          <TableCell>{formatCurrency(line.unit_value)}</TableCell>
                          <TableCell>{line.condition_multiplier.toFixed(2)}</TableCell>
                          <TableCell className="text-right">
                            -{formatCurrency(line.deduction_usd)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </>
            )}

            <Separator />

            <div className="flex items-center justify-between rounded-lg bg-muted/40 p-4">
              <div>
                <div className="text-xs uppercase tracking-wide text-muted-foreground">Adjusted price</div>
                <div className="text-lg font-semibold">
                  {formatCurrency(breakdown.adjusted_price_usd)}
                </div>
              </div>
              <div className="text-right text-xs text-muted-foreground">
                Original price {formatCurrency(breakdown.base_price_usd)}
              </div>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center text-muted-foreground">
            No valuation data available for this listing.
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function SummaryStat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number;
  tone?: "neutral" | "positive" | "negative";
}) {
  const toneClass =
    tone === "positive" ? "text-emerald-600" :
    tone === "negative" ? "text-red-600" :
    "text-foreground";

  return (
    <div className="rounded-lg border p-3">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={`text-lg font-semibold ${toneClass}`}>
        {formatCurrency(value)}
      </div>
    </div>
  );
}
