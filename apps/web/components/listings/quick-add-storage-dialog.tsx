"use client";

import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface QuickAddStorageDialogProps {
  listingId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface StorageFormData {
  primary_storage_gb: string;
  primary_storage_type: string;
  secondary_storage_gb: string;
  secondary_storage_type: string;
}

/**
 * Quick-Add Storage Dialog
 *
 * Allows rapid addition of storage specifications to a listing.
 * Supports both primary and secondary storage configurations.
 *
 * @example
 * ```tsx
 * <QuickAddStorageDialog
 *   listingId={123}
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 * />
 * ```
 */
export function QuickAddStorageDialog({
  listingId,
  open,
  onOpenChange,
}: QuickAddStorageDialogProps) {
  const { register, handleSubmit, reset } = useForm<StorageFormData>();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const updateListing = useMutation({
    mutationFn: (data: Record<string, number | string | null>) =>
      apiFetch(`/v1/listings/${listingId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields: data }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listing", listingId] });
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      toast({
        title: "Success",
        description: "Storage data updated successfully",
      });
      reset();
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update storage data",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: StorageFormData) => {
    const processedData = {
      primary_storage_gb: data.primary_storage_gb ? parseInt(data.primary_storage_gb, 10) : null,
      primary_storage_type: data.primary_storage_type?.trim() || null,
      secondary_storage_gb: data.secondary_storage_gb ? parseInt(data.secondary_storage_gb, 10) : null,
      secondary_storage_type: data.secondary_storage_type?.trim() || null,
    };
    updateListing.mutate(processedData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Storage Data</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Primary Storage */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Primary Storage</h3>
            <div>
              <Label htmlFor="primary_storage_gb">Capacity (GB)</Label>
              <Input
                id="primary_storage_gb"
                type="number"
                {...register("primary_storage_gb")}
                placeholder="e.g., 512"
              />
            </div>
            <div>
              <Label htmlFor="primary_storage_type">Type</Label>
              <Input
                id="primary_storage_type"
                type="text"
                {...register("primary_storage_type")}
                placeholder="e.g., NVMe SSD, SATA SSD"
              />
            </div>
          </div>

          {/* Secondary Storage */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="text-sm font-semibold">Secondary Storage</h3>
            <div>
              <Label htmlFor="secondary_storage_gb">Capacity (GB)</Label>
              <Input
                id="secondary_storage_gb"
                type="number"
                {...register("secondary_storage_gb")}
                placeholder="e.g., 1000"
              />
            </div>
            <div>
              <Label htmlFor="secondary_storage_type">Type</Label>
              <Input
                id="secondary_storage_type"
                type="text"
                {...register("secondary_storage_type")}
                placeholder="e.g., HDD, SATA SSD"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateListing.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateListing.isPending}>
              {updateListing.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
