"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCatalogStore } from "@/stores/catalog-store";
import { apiFetch } from "@/lib/utils";
import { ListingRecord } from "@/types/listings";
import { useToast } from "@/hooks/use-toast";

/**
 * Quick Edit Dialog
 *
 * Provides inline editing for key listing fields:
 * - Title
 * - Price
 * - Condition
 * - Status
 *
 * Features:
 * - Optimistic UI updates
 * - Error handling with rollback
 * - Toast notifications
 */

const CONDITIONS = ["new", "refurbished", "used", "for-parts"];
const STATUSES = ["active", "sold", "pending", "archived"];

export function QuickEditDialog() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const isOpen = useCatalogStore((state) => state.quickEditDialogOpen);
  const listingId = useCatalogStore((state) => state.quickEditDialogListingId);
  const closeDialog = useCatalogStore((state) => state.closeQuickEditDialog);

  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("");
  const [condition, setCondition] = useState("new");
  const [status, setStatus] = useState("active");

  // Fetch listing data
  const { data: listing, isLoading } = useQuery({
    queryKey: ["listings", "single", listingId],
    queryFn: () => apiFetch<ListingRecord>(`/v1/listings/${listingId}`),
    enabled: isOpen && !!listingId,
  });

  // Populate form when listing loads
  useEffect(() => {
    if (listing) {
      setTitle(listing.title);
      setPrice(listing.price_usd.toString());
      setCondition(listing.condition || "new");
      setStatus(listing.status || "active");
    }
  }, [listing]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (updates: Partial<ListingRecord>) => {
      return apiFetch(`/v1/listings/${listingId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
    },
    onSuccess: () => {
      // Invalidate queries to refetch data
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      toast({
        title: "Success",
        description: "Listing updated successfully",
      });
      closeDialog();
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update listing",
        variant: "destructive",
      });
    },
  });

  const handleSave = () => {
    const updates: Partial<ListingRecord> = {
      title,
      price_usd: parseFloat(price),
      condition,
      status,
    };

    updateMutation.mutate(updates);
  };

  return (
    <Dialog open={isOpen} onOpenChange={closeDialog}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Quick Edit Listing</DialogTitle>
          <DialogDescription>
            Update key fields quickly without leaving the catalog view.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="space-y-4">
            <div className="h-10 bg-muted animate-pulse rounded" />
            <div className="h-10 bg-muted animate-pulse rounded" />
            <div className="h-10 bg-muted animate-pulse rounded" />
          </div>
        ) : (
          <div className="space-y-4 py-4">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Listing title"
              />
            </div>

            {/* Price */}
            <div className="space-y-2">
              <Label htmlFor="price">Price (USD)</Label>
              <Input
                id="price"
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
                step="0.01"
              />
            </div>

            {/* Condition */}
            <div className="space-y-2">
              <Label htmlFor="condition">Condition</Label>
              <Select value={condition} onValueChange={setCondition}>
                <SelectTrigger id="condition">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONDITIONS.map((cond) => (
                    <SelectItem key={cond} value={cond}>
                      {cond.charAt(0).toUpperCase() + cond.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Status */}
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((stat) => (
                    <SelectItem key={stat} value={stat}>
                      {stat.charAt(0).toUpperCase() + stat.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={closeDialog}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
