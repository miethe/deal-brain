"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { apiFetch, cn } from "../../lib/utils";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";

interface ListingResponse {
  id: number;
  title: string;
  price_usd: number;
  adjusted_price_usd: number | null;
  score_composite: number | null;
  score_cpu_multi: number | null;
  score_cpu_single: number | null;
  dollar_per_cpu_mark: number | null;
  cpu?: { name?: string } | null;
  gpu?: { name?: string } | null;
  condition: string;
}

export function ListingsTable() {
  const { data, isLoading, error, refetch } = useQuery<ListingResponse[]>({
    queryKey: ["listings"],
    queryFn: () => apiFetch<ListingResponse[]>("/v1/listings")
  });

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading listings…</p>;
  }

  if (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return (
      <Card>
        <CardHeader>
          <CardTitle>Listings</CardTitle>
          <CardDescription>Unable to load listings from the API</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{message}</p>
          <Button onClick={() => refetch()} className="mt-2" size="sm">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle>Listings</CardTitle>
            <CardDescription>Your curated catalog with live scoring.</CardDescription>
          </div>
          <Button asChild>
            <Link href="/listings/new">Add listing</Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>CPU</TableHead>
              <TableHead>Condition</TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead className="text-right">Adjusted</TableHead>
              <TableHead className="text-right">$/CPU Mark</TableHead>
              <TableHead className="text-right">Composite</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.map((listing) => (
              <TableRow key={listing.id}>
                <TableCell className="max-w-xs truncate">
                  <div className="flex flex-col">
                    <span className="font-medium text-foreground">{listing.title}</span>
                    <span className="text-xs text-muted-foreground">{listing.gpu?.name ?? "No dedicated GPU"}</span>
                  </div>
                </TableCell>
                <TableCell>{listing.cpu?.name ?? "—"}</TableCell>
                <TableCell>
                  <span className={cn("rounded-full px-2 py-0.5 text-xs capitalize", statusTone(listing.condition))}>
                    {listing.condition}
                  </span>
                </TableCell>
                <TableCell className="text-right">{formatCurrency(listing.price_usd)}</TableCell>
                <TableCell className="text-right">{formatCurrency(listing.adjusted_price_usd)}</TableCell>
                <TableCell className="text-right">{formatNumber(listing.dollar_per_cpu_mark)}</TableCell>
                <TableCell className="text-right">{formatNumber(listing.score_composite)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function formatCurrency(value: number | null | undefined) {
  if (!value) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function formatNumber(value: number | null | undefined) {
  if (!value) return "—";
  return Number(value).toFixed(2);
}

function statusTone(condition: string) {
  switch (condition) {
    case "new":
      return "bg-emerald-100 text-emerald-700";
    case "refurb":
      return "bg-amber-100 text-amber-700";
    default:
      return "bg-slate-200 text-slate-700";
  }
}
