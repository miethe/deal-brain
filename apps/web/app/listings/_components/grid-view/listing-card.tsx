"use client";

import { memo, useState } from "react";
import { ArrowUpRight, SquarePen, Trash2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { useToast } from "@/hooks/use-toast";
import { ListingRecord } from "@/types/listings";
import { formatRamSummary, formatStorageSummary } from "@/components/listings/listing-formatters";
import { PerformanceBadges } from "./performance-badges";
import { useCatalogStore } from "@/stores/catalog-store";
import { EntityTooltip } from "@/components/listings/entity-tooltip";
import { API_URL } from "@/lib/utils";

interface ListingCardProps {
  listing: ListingRecord;
}

/**
 * Listing Card Component
 *
 * Card layout for grid view with:
 * - Header: Title (truncated), Open button
 * - Badges: CPU, Device type, Tags
 * - Price: List price (large), Adjusted value (with color accent)
 * - Performance badges
 * - Metadata: RAM, Storage, Condition
 * - Footer: Vendor badge, Quick Edit button (hover visible)
 */
export const ListingCard = memo(function ListingCard({ listing }: ListingCardProps) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const openDetailsDialog = useCatalogStore((state) => state.openDetailsDialog);
  const openQuickEditDialog = useCatalogStore((state) => state.openQuickEditDialog);

  // Delete mutation
  const { mutate: deleteListing, isPending: isDeleting } = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`${API_URL}/v1/listings/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to delete listing' }));
        throw new Error(error.detail || 'Failed to delete listing');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] });
      toast({
        title: 'Success',
        description: 'Listing deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: `Delete failed: ${error.message}`,
        variant: 'destructive',
      });
    },
  });

  const handleCardClick = () => {
    openDetailsDialog(listing.id);
  };

  const handleQuickEdit = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    openQuickEditDialog(listing.id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    setDeleteConfirmOpen(true);
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
          <div className="flex gap-1">
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
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={handleDelete}
              aria-label="Delete listing"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      {/* Content */}
      <CardContent className="pb-3 flex-1 space-y-3">
        {/* Badges Row */}
        <div className="flex flex-wrap gap-1.5">
          {/* CPU Badge with Tooltip */}
          {listing.cpu_name && (
            <Badge variant="outline" className="text-xs">
              {listing.cpu?.id ? (
                <EntityTooltip
                  entityType="cpu"
                  entityId={listing.cpu.id}
                  variant="inline"
                  disableLink={true}
                >
                  {listing.cpu_name}
                </EntityTooltip>
              ) : (
                listing.cpu_name
              )}
            </Badge>
          )}

          {/* GPU Badge with Tooltip */}
          {listing.gpu_name && (
            <Badge variant="outline" className="text-xs">
              {listing.gpu?.id ? (
                <EntityTooltip
                  entityType="gpu"
                  entityId={listing.gpu.id}
                  variant="inline"
                  disableLink={true}
                >
                  {listing.gpu_name}
                </EntityTooltip>
              ) : (
                listing.gpu_name
              )}
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

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        open={deleteConfirmOpen}
        onOpenChange={setDeleteConfirmOpen}
        title="Delete Listing?"
        description="This action cannot be undone. The listing and all related data will be permanently deleted."
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
        onConfirm={() => deleteListing(listing.id)}
        isLoading={isDeleting}
      />
    </Card>
  );
});
