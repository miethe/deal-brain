"use client";

import { memo } from "react";
import { ArrowUpRight, SquarePen } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ListingRecord } from "@/types/listings";
import { formatRamSummary, formatStorageSummary } from "@/components/listings/listing-formatters";
import { PerformanceBadges } from "./performance-badges";
import { useCatalogStore } from "@/stores/catalog-store";

interface ListingCardProps {
  listing: ListingRecord;
}

/**
 * Listing Card Component
 *
 * Card layout for grid view with:
 * - Header: Title (truncated), Open button
 * - Badges: CPU, Device type, Tags
 * - Price: List price (large), Adjusted price (with color accent)
 * - Performance badges
 * - Metadata: RAM, Storage, Condition
 * - Footer: Vendor badge, Quick Edit button (hover visible)
 */
export const ListingCard = memo(function ListingCard({ listing }: ListingCardProps) {
  const openDetailsDialog = useCatalogStore((state) => state.openDetailsDialog);
  const openQuickEditDialog = useCatalogStore((state) => state.openQuickEditDialog);

  const handleCardClick = () => {
    openDetailsDialog(listing.id);
  };

  const handleQuickEdit = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    openQuickEditDialog(listing.id);
  };

  const handleOpenExternal = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    if (listing.listing_url) {
      window.open(listing.listing_url, "_blank", "noopener,noreferrer");
    }
  };

  const getValuationAccent = (): string => {
    if (!listing.adjusted_price_usd || !listing.price_usd) return "";

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

  // Format tags for display (max 2)
  const tags = listing.attributes?.tags as string[] | undefined;
  const displayTags = tags?.slice(0, 2) || [];

  const ramSummary = formatRamSummary(listing);
  const primaryStorageSummary = formatStorageSummary(
    listing.primary_storage_profile ?? null,
    listing.primary_storage_gb ?? null,
    listing.primary_storage_type ?? null,
  );
  const secondaryStorageSummary = formatStorageSummary(
    listing.secondary_storage_profile ?? null,
    listing.secondary_storage_gb ?? null,
    listing.secondary_storage_type ?? null,
  );

  return (
    <Card
      className="group cursor-pointer hover:shadow-lg transition-shadow duration-200 flex flex-col h-full"
      onClick={handleCardClick}
    >
      {/* Header */}
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-base line-clamp-2 flex-1">
            {listing.title}
          </h3>
          {listing.listing_url && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={handleOpenExternal}
              aria-label="Open listing in new tab"
            >
              <ArrowUpRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      {/* Content */}
      <CardContent className="pb-3 flex-1 space-y-3">
        {/* Badges Row */}
        <div className="flex flex-wrap gap-1.5">
          {listing.cpu_name && (
            <Badge variant="outline" className="text-xs">
              {listing.cpu_name}
            </Badge>
          )}
          {listing.cpu?.cpu_mark_single && listing.cpu?.cpu_mark_multi && (
            <Badge variant="secondary" className="text-xs font-mono">
              ST {listing.cpu.cpu_mark_single.toLocaleString()} / MT {listing.cpu.cpu_mark_multi.toLocaleString()}
            </Badge>
          )}
          {listing.form_factor && (
            <Badge variant="secondary" className="text-xs">
              {listing.form_factor}
            </Badge>
          )}
          {displayTags.map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>

        {/* Price Section */}
        <div className="space-y-1">
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold">
              ${listing.price_usd.toLocaleString()}
            </span>
            {listing.adjusted_price_usd && (
              <span className={`text-sm font-medium ${getValuationAccent()}`}>
                adj ${listing.adjusted_price_usd.toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Performance Badges */}
        <PerformanceBadges
          dollarPerSingleRaw={listing.dollar_per_cpu_mark_single}
          dollarPerMultiRaw={listing.dollar_per_cpu_mark_multi}
          dollarPerSingleAdjusted={listing.dollar_per_cpu_mark_single_adjusted}
          dollarPerMultiAdjusted={listing.dollar_per_cpu_mark_multi_adjusted}
        />

        {/* Metadata Row */}
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
          {ramSummary && <span>{ramSummary}</span>}
          {primaryStorageSummary && <span>{primaryStorageSummary}</span>}
          {secondaryStorageSummary && <span>{secondaryStorageSummary}</span>}
          {listing.condition && (
            <span className="capitalize">{listing.condition}</span>
          )}
        </div>
      </CardContent>

      {/* Footer */}
      <CardFooter className="pt-3 border-t flex items-center justify-between">
        {listing.manufacturer && (
          <Badge variant="outline" className="text-xs">
            {listing.manufacturer}
          </Badge>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="h-8 opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
          onClick={handleQuickEdit}
        >
          <SquarePen className="h-4 w-4 mr-1" />
          Quick Edit
        </Button>
      </CardFooter>
    </Card>
  );
});
