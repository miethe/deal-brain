"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCatalogStore } from "@/stores/catalog-store";
import { apiFetch } from "@/lib/utils";
import type { ListingRecord } from "@/types/listings";
import { PerformanceBadges } from "@/app/listings/_components/grid-view/performance-badges";
import { ListingValuationTab } from "./listing-valuation-tab";
import { formatRamSummary, formatStorageSummary } from "./listing-formatters";
import { EntityTooltip } from "./entity-tooltip";

/**
 * Listing Details Dialog
 *
 * Full details modal accessible from all catalog views.
 * Shows:
 * - Header with title, device type, open link
 * - KPI metrics grid (4 tiles)
 * - Performance badges
 * - Specs grid
 * - Link to full page view
 */

export function ListingDetailsDialog() {
  const isOpen = useCatalogStore((state) => state.detailsDialogOpen);
  const listingId = useCatalogStore((state) => state.detailsDialogListingId);
  const closeDialog = useCatalogStore((state) => state.closeDetailsDialog);
  const [activeTab, setActiveTab] = useState<"details" | "valuation">("details");
  const searchParams = useSearchParams();

  const { data: listing, isLoading } = useQuery({
    queryKey: ["listings", "single", listingId],
    queryFn: () => apiFetch<ListingRecord>(`/v1/listings/${listingId}`),
    enabled: isOpen && !!listingId,
  });

  const showValuationParam = searchParams?.get("showValuation");

  useEffect(() => {
    if (!isOpen) return;
    setActiveTab(showValuationParam === "true" ? "valuation" : "details");
  }, [isOpen, listingId, showValuationParam]);

  const getValuationAccent = (): string => {
    if (!listing?.adjusted_price_usd || !listing?.price_usd) return "";

    const delta = listing.price_usd - listing.adjusted_price_usd;
    const deltaPercent = (delta / listing.price_usd) * 100;

    if (deltaPercent >= 15) {
      return "text-emerald-600 dark:text-emerald-400";
    } else if (deltaPercent >= 5) {
      return "text-emerald-700 dark:text-emerald-500";
    } else if (deltaPercent <= -10) {
      return "text-amber-600 dark:text-amber-400";
    }
    return "text-muted-foreground";
  };

  const getLinkLabel = (url: string, label?: string | null) => {
    if (label) return label;
    try {
      const { hostname } = new URL(url);
      return hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  };

  const ramSummary = listing ? formatRamSummary(listing) : null;
  const primaryStorageSummary = listing
    ? formatStorageSummary(
        listing.primary_storage_profile ?? null,
        listing.primary_storage_gb ?? null,
        listing.primary_storage_type ?? null,
      )
    : null;
  const secondaryStorageSummary = listing
    ? formatStorageSummary(
        listing.secondary_storage_profile ?? null,
        listing.secondary_storage_gb ?? null,
        listing.secondary_storage_type ?? null,
      )
    : null;

  return (
    <Dialog open={isOpen} onOpenChange={closeDialog}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <DialogTitle className="text-xl">{listing?.title}</DialogTitle>
              <DialogDescription className="mt-1">
                {listing?.form_factor && (
                  <Badge variant="secondary" className="mt-2">
                    {listing.form_factor}
                  </Badge>
                )}
              </DialogDescription>
            </div>
            {listing?.listing_url && (
              <Button
                variant="ghost"
                size="sm"
                asChild
              >
                <a href={listing.listing_url} target="_blank" rel="noopener noreferrer">
                  <ArrowUpRight className="h-4 w-4" />
                </a>
              </Button>
            )}
          </div>
        </DialogHeader>

        {isLoading ? (
          <div className="space-y-4">
            <div className="h-32 bg-muted animate-pulse rounded" />
            <div className="h-32 bg-muted animate-pulse rounded" />
          </div>
        ) : listing ? (
          <Tabs
            value={activeTab}
            onValueChange={(value) => setActiveTab(value as "details" | "valuation")}
            className="mt-4"
          >
            <TabsList className="grid w-full grid-cols-2 sm:w-auto">
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="valuation">Valuation</TabsTrigger>
            </TabsList>

            <TabsContent value="details" className="mt-4 space-y-6">
              {/* KPI Metrics Grid */}
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Price</p>
                  <p className="text-xl font-bold">${listing.price_usd.toLocaleString()}</p>
                </div>
                {listing.adjusted_price_usd && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Adjusted</p>
                    <p className={`text-xl font-bold ${getValuationAccent()}`}>
                      ${listing.adjusted_price_usd.toLocaleString()}
                    </p>
                  </div>
                )}
                {listing.dollar_per_cpu_mark_single && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">$/ST</p>
                    <p className="text-xl font-bold font-mono">
                      ${listing.dollar_per_cpu_mark_single.toFixed(3)}
                    </p>
                  </div>
                )}
                {listing.dollar_per_cpu_mark_multi && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">$/MT</p>
                    <p className="text-xl font-bold font-mono">
                      ${listing.dollar_per_cpu_mark_multi.toFixed(3)}
                    </p>
                  </div>
                )}
              </div>

              <Separator />

              {/* Performance Badges */}
              <div>
                <h4 className="mb-2 text-sm font-medium">Performance Metrics</h4>
                <PerformanceBadges
                  dollarPerSingleRaw={listing.dollar_per_cpu_mark_single}
                  dollarPerMultiRaw={listing.dollar_per_cpu_mark_multi}
                  dollarPerSingleAdjusted={listing.dollar_per_cpu_mark_single_adjusted}
                  dollarPerMultiAdjusted={listing.dollar_per_cpu_mark_multi_adjusted}
                />
              </div>

              <Separator />

              {/* Specs Grid */}
              <div>
                <h4 className="mb-3 text-sm font-medium">Specifications</h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  {listing.cpu_name && (
                    <>
                      <span className="text-muted-foreground">CPU</span>
                      <span className="font-medium">
                        {listing.cpu?.id ? (
                          <EntityTooltip
                            entityType="cpu"
                            entityId={listing.cpu.id}
                            variant="inline"
                          >
                            {listing.cpu_name}
                          </EntityTooltip>
                        ) : (
                          listing.cpu_name
                        )}
                      </span>
                    </>
                  )}
                  {listing.gpu_name && (
                    <>
                      <span className="text-muted-foreground">GPU</span>
                      <span className="font-medium">
                        {listing.gpu?.id ? (
                          <EntityTooltip
                            entityType="gpu"
                            entityId={listing.gpu.id}
                            variant="inline"
                          >
                            {listing.gpu_name}
                          </EntityTooltip>
                        ) : (
                          listing.gpu_name
                        )}
                      </span>
                    </>
                  )}
                  {listing.cpu?.cpu_mark_single && listing.cpu?.cpu_mark_multi && (
                    <>
                      <span className="text-muted-foreground">CPU Scores</span>
                      <span className="font-medium font-mono">
                        ST {listing.cpu.cpu_mark_single.toLocaleString()} / MT {listing.cpu.cpu_mark_multi.toLocaleString()}
                      </span>
                    </>
                  )}
                  {ramSummary && (
                    <>
                      <span className="text-muted-foreground">RAM</span>
                      <span className="font-medium">
                        {listing.ram_spec?.id ? (
                          <EntityTooltip
                            entityType="ram-spec"
                            entityId={listing.ram_spec.id}
                            variant="inline"
                          >
                            {ramSummary}
                          </EntityTooltip>
                        ) : (
                          ramSummary
                        )}
                      </span>
                    </>
                  )}
                  {primaryStorageSummary && (
                    <>
                      <span className="text-muted-foreground">Primary Storage</span>
                      <span className="font-medium">
                        {listing.primary_storage_profile?.id ? (
                          <EntityTooltip
                            entityType="storage-profile"
                            entityId={listing.primary_storage_profile.id}
                            variant="inline"
                          >
                            {primaryStorageSummary}
                          </EntityTooltip>
                        ) : (
                          primaryStorageSummary
                        )}
                      </span>
                    </>
                  )}
                  {secondaryStorageSummary && (
                    <>
                      <span className="text-muted-foreground">Secondary Storage</span>
                      <span className="font-medium">
                        {listing.secondary_storage_profile?.id ? (
                          <EntityTooltip
                            entityType="storage-profile"
                            entityId={listing.secondary_storage_profile.id}
                            variant="inline"
                          >
                            {secondaryStorageSummary}
                          </EntityTooltip>
                        ) : (
                          secondaryStorageSummary
                        )}
                      </span>
                    </>
                  )}
                  {listing.condition && (
                    <>
                      <span className="text-muted-foreground">Condition</span>
                      <span className="font-medium capitalize">{listing.condition}</span>
                    </>
                  )}
                  {listing.manufacturer && (
                    <>
                      <span className="text-muted-foreground">Manufacturer</span>
                      <span className="font-medium">{listing.manufacturer}</span>
                    </>
                  )}
                  {listing.series && (
                    <>
                      <span className="text-muted-foreground">Series</span>
                      <span className="font-medium">{listing.series}</span>
                    </>
                  )}
                  {listing.model_number && (
                    <>
                      <span className="text-muted-foreground">Model</span>
                      <span className="font-medium">{listing.model_number}</span>
                    </>
                  )}
                </div>
              </div>

              {!!listing.other_urls?.length && (
                <>
                  <Separator />
                  <div>
                    <h4 className="mb-3 text-sm font-medium">Additional Links</h4>
                    <ul className="space-y-2 text-sm">
                      {listing.other_urls.map((link) => (
                        <li key={link.url}>
                          <a
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline"
                          >
                            {getLinkLabel(link.url, link.label)}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}

              <Separator />

              {/* Footer - Link to full page */}
              <div className="flex justify-center">
                <Button variant="outline" asChild>
                  <Link href={`/listings/${listing.id}`}>
                    View Full Page
                    <ArrowUpRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </TabsContent>

            <TabsContent value="valuation" className="mt-4">
              <ListingValuationTab listing={listing} />
            </TabsContent>
          </Tabs>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
