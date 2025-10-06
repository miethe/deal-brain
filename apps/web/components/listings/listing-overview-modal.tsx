"use client";

import { memo } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Button } from "../ui/button";
import { Separator } from "../ui/separator";
import { ValuationCell } from "./valuation-cell";
import { DualMetricCell } from "./dual-metric-cell";
import { PortsDisplay } from "./ports-display";
import { apiFetch } from "../../lib/utils";
import { useValuationThresholds } from "../../hooks/use-valuation-thresholds";
import { ListingRecord } from "../../types/listings";

interface ListingOverviewModalProps {
  listingId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function ListingOverviewModalComponent({ listingId, open, onOpenChange }: ListingOverviewModalProps) {
  const { data: listing, isLoading } = useQuery<ListingRecord>({
    queryKey: ['listing', listingId],
    queryFn: async () => {
      if (!listingId) throw new Error("No listing ID");
      return apiFetch(`/v1/listings/${listingId}`);
    },
    enabled: open && !!listingId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: thresholds } = useValuationThresholds();

  if (!open || !listingId) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center p-8">
            <div className="flex flex-col items-center gap-2">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              <span className="text-sm text-muted-foreground">Loading listing...</span>
            </div>
          </div>
        ) : listing ? (
          <>
            <DialogHeader>
              <DialogTitle className="text-xl">{listing.title}</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              {listing.thumbnail_url && (
                <img
                  src={listing.thumbnail_url}
                  alt={listing.title}
                  className="w-full max-w-md rounded-lg mx-auto"
                />
              )}

              <Section title="Pricing">
                {thresholds && listing.adjusted_price_usd !== null ? (
                  <ValuationCell
                    listPrice={listing.price_usd}
                    adjustedPrice={listing.adjusted_price_usd}
                    thresholds={thresholds}
                    onDetailsClick={() => {
                      onOpenChange(false);
                      window.location.href = `/listings?highlight=${listing.id}&showValuation=true`;
                    }}
                  />
                ) : (
                  <div className="text-sm">
                    <div className="font-medium">List Price: ${listing.price_usd.toFixed(2)}</div>
                    {listing.adjusted_price_usd !== null && (
                      <div className="text-muted-foreground">Adjusted: ${listing.adjusted_price_usd.toFixed(2)}</div>
                    )}
                  </div>
                )}
              </Section>

              <Separator />

              <Section title="Performance Metrics">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">$/CPU Mark (Single):</span>
                    <DualMetricCell
                      raw={listing.dollar_per_cpu_mark_single}
                      adjusted={listing.dollar_per_cpu_mark_single_adjusted}
                      prefix="$"
                      decimals={3}
                    />
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">$/CPU Mark (Multi):</span>
                    <DualMetricCell
                      raw={listing.dollar_per_cpu_mark_multi}
                      adjusted={listing.dollar_per_cpu_mark_multi_adjusted}
                      prefix="$"
                      decimals={3}
                    />
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Composite Score:</span>
                    <span className="font-medium">{listing.score_composite?.toFixed(2) ?? 'N/A'}</span>
                  </div>
                  {listing.perf_per_watt !== null && listing.perf_per_watt !== undefined && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Perf/Watt:</span>
                      <span className="font-medium">{listing.perf_per_watt.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </Section>

              <Separator />

              <Section title="Hardware">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <SpecRow label="CPU" value={listing.cpu_name} />
                  <SpecRow label="GPU" value={listing.gpu_name} />
                  <SpecRow label="RAM" value={listing.ram_gb ? `${listing.ram_gb} GB` : null} />
                  <SpecRow
                    label="Storage"
                    value={listing.primary_storage_gb ? `${listing.primary_storage_gb} GB ${listing.primary_storage_type || ''}`.trim() : null}
                  />
                  {listing.secondary_storage_gb && (
                    <SpecRow
                      label="Secondary Storage"
                      value={`${listing.secondary_storage_gb} GB ${listing.secondary_storage_type || ''}`.trim()}
                    />
                  )}
                </div>
                {listing.ports_profile?.ports && listing.ports_profile.ports.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium mb-2">Connectivity:</div>
                    <PortsDisplay ports={listing.ports_profile.ports} />
                  </div>
                )}
              </Section>

              <Separator />

              <Section title="Metadata">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <SpecRow label="Condition" value={listing.condition} />
                  <SpecRow label="Status" value={listing.status} />
                  <SpecRow label="Manufacturer" value={listing.manufacturer} />
                  <SpecRow label="Form Factor" value={listing.form_factor} />
                  {listing.series && <SpecRow label="Series" value={listing.series} />}
                  {listing.model_number && <SpecRow label="Model #" value={listing.model_number} />}
                </div>
              </Section>
            </div>

            <div className="flex gap-2 mt-6 pt-4 border-t">
              <Button asChild className="flex-1">
                <Link href={`/listings?highlight=${listing.id}`}>
                  View Full Listing
                </Link>
              </Button>
              {listing.valuation_breakdown && (
                <Button variant="outline" className="flex-1" asChild>
                  <Link href={`/listings?highlight=${listing.id}&showValuation=true`}>
                    View Valuation Breakdown
                  </Link>
                </Button>
              )}
            </div>
          </>
        ) : (
          <div className="p-8 text-center">
            <p className="text-sm text-muted-foreground">Listing not found</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="text-sm font-semibold mb-3">{title}</h4>
      {children}
    </div>
  );
}

function SpecRow({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-medium">{value ?? 'N/A'}</span>
    </div>
  );
}

export const ListingOverviewModal = memo(ListingOverviewModalComponent);
