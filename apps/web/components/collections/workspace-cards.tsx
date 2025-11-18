"use client";

import { Expand, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { useConfirmation } from "@/components/ui/confirmation-dialog";
import { useRemoveCollectionItem } from "@/hooks/use-collections";
import type { CollectionItem, CollectionItemStatus } from "@/types/collections";

interface WorkspaceCardsProps {
  collectionId: number | string;
  items: CollectionItem[];
  onItemExpand: (item: CollectionItem) => void;
}

const STATUS_COLORS: Record<
  CollectionItemStatus,
  { variant: "default" | "secondary" | "destructive" | "outline"; label: string }
> = {
  undecided: { variant: "default", label: "Undecided" },
  shortlisted: { variant: "secondary", label: "Shortlisted" },
  rejected: { variant: "outline", label: "Rejected" },
  bought: { variant: "default", label: "Bought" },
};

/**
 * Workspace Cards View
 *
 * Mobile-friendly card layout with:
 * - Listing image and name
 * - Price and adjusted price
 * - Key specs (CPU, RAM, storage)
 * - Status badge
 * - Expand button for notes
 * - Remove action
 */
export function WorkspaceCards({
  collectionId,
  items,
  onItemExpand,
}: WorkspaceCardsProps) {
  const { confirm, dialog } = useConfirmation();
  const removeItemMutation = useRemoveCollectionItem({ collectionId });

  const handleRemoveItem = async (itemId: number, listingTitle: string) => {
    const confirmed = await confirm({
      title: "Remove item?",
      description: `Remove "${listingTitle}" from this collection?`,
      confirmText: "Remove",
      variant: "destructive",
    });

    if (confirmed) {
      removeItemMutation.mutate(itemId);
    }
  };

  if (items.length === 0) {
    return (
      <div className="border rounded-lg p-12 text-center">
        <p className="text-muted-foreground">No items in this collection yet.</p>
        <p className="text-sm text-muted-foreground mt-2">
          Add listings from the main listings view.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item) => {
          const listing = item.listing;
          const statusConfig = STATUS_COLORS[item.status];

          return (
            <Card key={item.id} className="flex flex-col">
              {/* Header with Image */}
              <CardHeader className="pb-3">
                <div className="flex items-start gap-3">
                  {/* Image */}
                  <div className="w-20 h-20 bg-muted rounded flex-shrink-0 overflow-hidden">
                    {listing.thumbnail_url ? (
                      <img
                        src={listing.thumbnail_url}
                        alt={listing.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-xs text-muted-foreground">
                          No image
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Title and Status */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-base line-clamp-2 mb-2">
                      {listing.title}
                    </h3>
                    <Badge variant={statusConfig.variant} className="text-xs">
                      {statusConfig.label}
                    </Badge>
                  </div>
                </div>
              </CardHeader>

              {/* Content */}
              <CardContent className="pb-3 flex-1 space-y-3">
                {/* Price */}
                <div className="space-y-1">
                  <div className="text-2xl font-bold">
                    ${listing.price_usd.toLocaleString()}
                  </div>
                  {listing.adjusted_price_usd && (
                    <div className="text-sm text-muted-foreground">
                      Adjusted: ${listing.adjusted_price_usd.toLocaleString()}
                    </div>
                  )}
                </div>

                {/* Specs */}
                <div className="space-y-1 text-sm text-muted-foreground">
                  {listing.cpu_name && (
                    <div>
                      <span className="font-medium">CPU:</span> {listing.cpu_name}
                      {listing.cpu?.cpu_mark_multi && (
                        <span className="ml-2 text-xs">
                          ({listing.cpu.cpu_mark_multi.toLocaleString()})
                        </span>
                      )}
                    </div>
                  )}
                  {listing.gpu_name && (
                    <div>
                      <span className="font-medium">GPU:</span> {listing.gpu_name}
                    </div>
                  )}
                  {listing.ram_gb && (
                    <div>
                      <span className="font-medium">RAM:</span> {listing.ram_gb}GB
                    </div>
                  )}
                  {listing.primary_storage_gb && (
                    <div>
                      <span className="font-medium">Storage:</span>{" "}
                      {listing.primary_storage_gb}GB{" "}
                      {listing.primary_storage_type}
                    </div>
                  )}
                  {listing.form_factor && (
                    <div>
                      <span className="font-medium">Form:</span>{" "}
                      {listing.form_factor}
                    </div>
                  )}
                </div>

                {/* Score Badge */}
                {listing.score_composite && (
                  <div>
                    <Badge variant="outline" className="text-xs">
                      Score: {listing.score_composite.toFixed(2)}
                    </Badge>
                  </div>
                )}

                {/* Price Efficiency */}
                {listing.dollar_per_cpu_mark_multi && (
                  <div className="text-xs text-muted-foreground">
                    ${listing.dollar_per_cpu_mark_multi.toFixed(3)} per CPU Mark
                  </div>
                )}
              </CardContent>

              {/* Footer with Actions */}
              <CardFooter className="pt-3 border-t flex items-center justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onItemExpand(item)}
                >
                  <Expand className="h-4 w-4 mr-1" />
                  Notes
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveItem(item.id, listing.title)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </div>

      {/* Confirmation Dialog */}
      {dialog}
    </>
  );
}
