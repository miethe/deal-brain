"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "../../lib/utils";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import Link from "next/link";
import { ListingOverviewModal } from "../listings/listing-overview-modal";

interface DashboardData {
  best_value: ListingSummary | null;
  best_perf_per_watt: ListingSummary | null;
  best_under_budget: ListingSummary[];
}

interface ListingSummary {
  id: number;
  title: string;
  adjusted_price_usd: number | null;
  score_composite: number | null;
  dollar_per_cpu_mark: number | null;
  perf_per_watt: number | null;
}

export function DashboardSummary() {
  const [selectedListingId, setSelectedListingId] = useState<number | null>(null);
  const [overviewOpen, setOverviewOpen] = useState(false);

  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch<DashboardData>("/v1/dashboard"),
    staleTime: 1 * 60 * 1000, // 1 minute
  });

  const handleListingClick = (listingId: number) => {
    setSelectedListingId(listingId);
    setOverviewOpen(true);
  };

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading dashboard metrics…</p>;
  }

  if (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return <p className="text-sm text-destructive">Failed to load dashboard: {message}</p>;
  }

  if (!data) {
    return <p className="text-sm text-muted-foreground">No dashboard data yet. Add a listing to get started.</p>;
  }

  return (
    <>
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard
          title="Best $ / CPU Mark"
          description="Adjusted price normalized by CPU score"
          listing={data.best_value}
          onListingClick={handleListingClick}
        />
        <SummaryCard
          title="Top Perf / Watt"
          description="Efficiency champion for tonight's shortlist"
          listing={data.best_perf_per_watt}
          onListingClick={handleListingClick}
        />
        <Card>
          <CardHeader>
            <CardTitle>Best Under Budget</CardTitle>
            <CardDescription>Top picks within your configured ceiling</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {data.best_under_budget.length === 0 ? (
              <span className="text-sm text-muted-foreground">No listings within budget yet.</span>
            ) : (
              data.best_under_budget.map((listing) => (
                <ListingRow key={listing.id} listing={listing} onClick={() => handleListingClick(listing.id)} />
              ))
            )}
            <Button asChild variant="outline" className="mt-2">
              <Link href="/listings">Open listings table</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <ListingOverviewModal
        listingId={selectedListingId}
        open={overviewOpen}
        onOpenChange={setOverviewOpen}
      />
    </>
  );
}

function SummaryCard({
  title,
  description,
  listing,
  onListingClick,
}: {
  title: string;
  description: string;
  listing: ListingSummary | null;
  onListingClick: (listingId: number) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {listing ? (
          <>
            <button
              onClick={() => onListingClick(listing.id)}
              className="flex flex-col gap-1 text-left rounded-md p-2 -m-2 transition-colors hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              aria-label={`View details for ${listing.title}`}
            >
              <span className="text-base font-semibold leading-tight">{listing.title}</span>
              <span className="text-sm text-muted-foreground">
                Adjusted: {formatCurrency(listing.adjusted_price_usd)} · $/CPU Mark: {formatNumber(listing.dollar_per_cpu_mark)}
              </span>
            </button>
            <Badge className="w-fit">Composite {formatNumber(listing.score_composite)}</Badge>
            <Button asChild size="sm" variant="outline">
              <Link href={`/listings?highlight=${listing.id}`}>View listing</Link>
            </Button>
          </>
        ) : (
          <span className="text-sm text-muted-foreground">No data available yet.</span>
        )}
      </CardContent>
    </Card>
  );
}

function ListingRow({ listing, onClick }: { listing: ListingSummary; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded-md border p-3 text-left transition-colors hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      aria-label={`View details for ${listing.title}`}
    >
      <div className="text-sm font-medium leading-tight">{listing.title}</div>
      <div className="text-xs text-muted-foreground">
        Adjusted {formatCurrency(listing.adjusted_price_usd)} · Composite {formatNumber(listing.score_composite)}
      </div>
    </button>
  );
}

function formatCurrency(value: number | null) {
  if (!value) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function formatNumber(value: number | null) {
  if (!value) return "—";
  return Number(value).toFixed(2);
}
