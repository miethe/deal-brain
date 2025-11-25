"use client";

import { useEffect, useState } from "react";
import { useDebouncedCallback } from "use-debounce";
import { Loader2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useUpdateCollectionItem } from "@/hooks/use-collections";
import type { CollectionItem, CollectionItemStatus } from "@/types/collections";

interface ItemDetailsPanelProps {
  collectionId: number | string;
  item: CollectionItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const STATUS_OPTIONS: { value: CollectionItemStatus; label: string; variant: "default" | "secondary" | "destructive" | "outline" }[] = [
  { value: "undecided", label: "Undecided", variant: "default" },
  { value: "shortlisted", label: "Shortlisted", variant: "secondary" },
  { value: "rejected", label: "Rejected", variant: "outline" },
  { value: "bought", label: "Bought", variant: "default" },
];

/**
 * Item Details Panel
 *
 * Side sheet for editing collection item status and notes.
 * Features:
 * - Status dropdown with immediate save
 * - Notes textarea with auto-save (500ms debounce)
 * - Saving indicator
 * - Listing preview (name, price)
 */
export function ItemDetailsPanel({
  collectionId,
  item,
  open,
  onOpenChange,
}: ItemDetailsPanelProps) {
  const [notes, setNotes] = useState(item?.notes || "");
  const [isSaving, setIsSaving] = useState(false);

  const updateItemMutation = useUpdateCollectionItem({
    collectionId,
    onSuccess: () => {
      setIsSaving(false);
    },
  });

  // Sync local notes state when item changes
  useEffect(() => {
    setNotes(item?.notes || "");
  }, [item]);

  // Debounced auto-save for notes (500ms)
  // Pass itemId as parameter to avoid stale closure
  const debouncedSaveNotes = useDebouncedCallback((itemId: number, value: string) => {
    setIsSaving(true);
    updateItemMutation.mutate({
      itemId,
      data: { notes: value },
    });
  }, 500);

  const handleNotesChange = (value: string) => {
    if (!item) return;
    
    setNotes(value);
    setIsSaving(true);
    debouncedSaveNotes(item.id, value);
  };

  const handleStatusChange = (status: CollectionItemStatus) => {
    if (!item) return;

    updateItemMutation.mutate({
      itemId: item.id,
      data: { status },
    });
  };

  if (!item) {
    return null;
  }

  const currentStatusOption = STATUS_OPTIONS.find(
    (opt) => opt.value === item.status
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle className="flex items-center justify-between">
            <span className="truncate">{item.listing.title}</span>
            {isSaving && (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </SheetTitle>
          <SheetDescription>
            ${item.listing.price_usd.toLocaleString()}
            {item.listing.adjusted_price_usd && (
              <span className="text-xs ml-2">
                (adj: ${item.listing.adjusted_price_usd.toLocaleString()})
              </span>
            )}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Status */}
          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select
              value={item.status}
              onValueChange={handleStatusChange}
              disabled={updateItemMutation.isPending}
            >
              <SelectTrigger id="status">
                <SelectValue>
                  {currentStatusOption && (
                    <Badge variant={currentStatusOption.variant} className="text-xs">
                      {currentStatusOption.label}
                    </Badge>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <Badge variant={option.variant} className="text-xs">
                      {option.label}
                    </Badge>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => handleNotesChange(e.target.value)}
              placeholder="Add notes about this listing..."
              rows={10}
              className="resize-none"
              disabled={updateItemMutation.isPending}
            />
            <p className="text-xs text-muted-foreground">
              {isSaving ? "Saving..." : "Auto-saved"}
            </p>
          </div>

          {/* Listing Details Preview */}
          <div className="space-y-2 pt-4 border-t">
            <h4 className="text-sm font-medium">Listing Details</h4>
            <div className="space-y-1 text-sm text-muted-foreground">
              {item.listing.cpu_name && (
                <div>
                  <span className="font-medium">CPU:</span> {item.listing.cpu_name}
                </div>
              )}
              {item.listing.gpu_name && (
                <div>
                  <span className="font-medium">GPU:</span> {item.listing.gpu_name}
                </div>
              )}
              {item.listing.ram_gb && (
                <div>
                  <span className="font-medium">RAM:</span> {item.listing.ram_gb}GB
                </div>
              )}
              {item.listing.form_factor && (
                <div>
                  <span className="font-medium">Form Factor:</span>{" "}
                  {item.listing.form_factor}
                </div>
              )}
              {item.listing.score_composite && (
                <div>
                  <span className="font-medium">Score:</span>{" "}
                  {item.listing.score_composite.toFixed(2)}
                </div>
              )}
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
