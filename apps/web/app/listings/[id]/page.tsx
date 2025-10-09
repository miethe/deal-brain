import { notFound } from "next/navigation";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";
import { Badge } from "../../../components/ui/badge";
import { apiFetch } from "../../../lib/utils";
import type { ValuationBreakdown } from "../../../types/listings";

interface ListingDetail {
  id: number;
  title: string;
  price_usd: number;
  adjusted_price_usd: number | null;
  valuation_breakdown?: ValuationBreakdown | null;
  score_cpu_multi: number | null;
  score_cpu_single: number | null;
  score_composite: number | null;
  perf_per_watt: number | null;
  dollar_per_cpu_mark: number | null;
  cpu?: { name?: string } | null;
  gpu?: { name?: string } | null;
  condition: string;
}

export default async function ListingDetailPage({ params }: { params: { id: string } }) {
  let listing: ListingDetail | null = null;
  try {
    listing = await apiFetch<ListingDetail>(`/v1/listings/${params.id}`);
  } catch (error) {
    listing = null;
  }

  if (!listing) {
    notFound();
  }

  const breakdown = listing.valuation_breakdown;
  const adjustments = breakdown?.adjustments ?? [];
  const legacyLines = breakdown?.legacy_lines ?? breakdown?.lines ?? [];

  const formatCurrency = (value: number | null | undefined) =>
    value == null ?
      "—" :
      new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold tracking-tight">{listing.title}</h1>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span>CPU: {listing.cpu?.name ?? "Unknown"}</span>
          <span>GPU: {listing.gpu?.name ?? "None"}</span>
          <Badge className="capitalize">{listing.condition}</Badge>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Scores</CardTitle>
          <CardDescription>Computed by the backend valuation + scoring engine.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Listing price" value={listing.price_usd} format="currency" />
          <Metric label="Adjusted price" value={listing.adjusted_price_usd} format="currency" />
          <Metric label="$ / CPU Mark" value={listing.dollar_per_cpu_mark} />
          <Metric label="Composite score" value={listing.score_composite} />
          <Metric label="CPU multi" value={listing.score_cpu_multi} />
          <Metric label="CPU single" value={listing.score_cpu_single} />
          <Metric label="Perf / watt" value={listing.perf_per_watt} />
        </CardContent>
      </Card>
      {breakdown && (
        <Card>
          <CardHeader>
            <CardTitle>Valuation breakdown</CardTitle>
            <CardDescription>
              Rule-driven adjustments applied to derive the adjusted price.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="flex flex-col gap-1 text-sm">
                <span className="text-muted-foreground">
                  Ruleset: {breakdown.ruleset?.name ?? "None"} · Matched rules:{" "}
                  {breakdown.matched_rules_count ?? adjustments.length}
                </span>
                <span className="font-medium">
                  Total adjustment: {formatCurrency(breakdown.total_adjustment)}
                  {breakdown.total_deductions != null && (
                    <span className="text-muted-foreground">
                      {" "}
                      · Total deductions: {formatCurrency(breakdown.total_deductions)}
                    </span>
                  )}
                </span>
              </div>

              {adjustments.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rule</TableHead>
                      <TableHead>Adjustment</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {adjustments.map((adjustment, index) => (
                      <TableRow key={`${adjustment.rule_id ?? adjustment.rule_name}-${index}`}>
                        <TableCell className="font-medium">{adjustment.rule_name}</TableCell>
                        <TableCell
                          className={
                            adjustment.adjustment_amount < 0 ? "text-emerald-600 font-medium" :
                            adjustment.adjustment_amount > 0 ? "text-red-600 font-medium" :
                            "text-muted-foreground"
                          }
                        >
                          {adjustment.adjustment_amount > 0 ? "+" : ""}
                          {formatCurrency(adjustment.adjustment_amount)}
                        </TableCell>
                        <TableCell>
                          {adjustment.actions.length === 0 ? (
                            <span className="text-muted-foreground text-xs">No action details</span>
                          ) : (
                            <ul className="space-y-1 text-xs text-muted-foreground">
                              {adjustment.actions.map((action, actionIndex) => (
                                <li key={actionIndex}>
                                  <span className="font-medium text-foreground">
                                    {action.action_type ?? "action"}
                                  </span>
                                  {action.metric && <span> · {action.metric}</span>}
                                  <span>
                                    {" "}
                                    ({action.value >= 0 ? "+" : ""}
                                    {formatCurrency(action.value)})
                                  </span>
                                  {action.error && (
                                    <span className="text-red-600"> – {action.error}</span>
                                  )}
                                </li>
                              ))}
                            </ul>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="rounded-md border p-6 text-sm text-muted-foreground">
                  No rule-based adjustments were applied.
                </div>
              )}

              {legacyLines.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold">Component deductions</h4>
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
                      {legacyLines.map((line) => (
                        <TableRow key={`${line.label}-${line.component_type}`}>
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
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Metric({ label, value, format }: { label: string; value: number | null | undefined; format?: "currency" }) {
  const display =
    value == null ?
      "—" :
      format === "currency" ?
        new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value) :
        Number(value).toFixed(2);
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold text-foreground">{display}</div>
    </div>
  );
}
