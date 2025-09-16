import { notFound } from "next/navigation";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../../components/ui/table";
import { Badge } from "../../../components/ui/badge";
import { apiFetch } from "../../../lib/utils";

interface ListingDetail {
  id: number;
  title: string;
  price_usd: number;
  adjusted_price_usd: number | null;
  valuation_breakdown?: {
    adjusted_price: number;
    listing_price: number;
    total_deductions: number;
    lines: Array<{
      label: string;
      component_type: string;
      quantity: number;
      unit_value: number;
      condition_multiplier: number;
      deduction_usd: number;
    }>;
  };
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
            <CardDescription>Deductions applied to normalize the listing.</CardDescription>
          </CardHeader>
          <CardContent>
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
                {breakdown.lines.map((line) => (
                  <TableRow key={`${line.label}-${line.component_type}`}>
                    <TableCell>{line.label}</TableCell>
                    <TableCell>{line.quantity}</TableCell>
                    <TableCell>${line.unit_value.toFixed(2)}</TableCell>
                    <TableCell>{line.condition_multiplier.toFixed(2)}</TableCell>
                    <TableCell className="text-right">-${line.deduction_usd.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="mt-4 flex justify-end text-sm text-muted-foreground">
              Total deductions: ${breakdown.total_deductions.toFixed(2)} · Adjusted price: ${breakdown.adjusted_price.toFixed(2)}
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
