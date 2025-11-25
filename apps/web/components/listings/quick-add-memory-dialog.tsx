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

interface QuickAddMemoryDialogProps {
  listingId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface MemoryFormData {
  ram_gb: string;
  ram_type: string;
  ram_speed_mhz: string;
}

/**
 * Quick-Add Memory Dialog
 *
 * Allows rapid addition of RAM specifications to a listing.
 * Supports capacity, type, and speed configuration.
 *
 * @example
 * ```tsx
 * <QuickAddMemoryDialog
 *   listingId={123}
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 * />
 * ```
 */
export function QuickAddMemoryDialog({
  listingId,
  open,
  onOpenChange,
}: QuickAddMemoryDialogProps) {
  const { register, handleSubmit, reset } = useForm<MemoryFormData>();
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
        description: "Memory data updated successfully",
      });
      reset();
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update memory data",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: MemoryFormData) => {
    const processedData = {
      ram_gb: data.ram_gb ? parseInt(data.ram_gb, 10) : null,
      ram_type: data.ram_type?.trim() || null,
      ram_speed_mhz: data.ram_speed_mhz ? parseInt(data.ram_speed_mhz, 10) : null,
    };
    updateListing.mutate(processedData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Memory Data</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="ram_gb">RAM Capacity (GB)</Label>
            <Input
              id="ram_gb"
              type="number"
              {...register("ram_gb")}
              placeholder="e.g., 16"
            />
          </div>

          <div>
            <Label htmlFor="ram_type">RAM Type</Label>
            <Input
              id="ram_type"
              type="text"
              {...register("ram_type")}
              placeholder="e.g., DDR4, DDR5"
            />
          </div>

          <div>
            <Label htmlFor="ram_speed_mhz">RAM Speed (MHz)</Label>
            <Input
              id="ram_speed_mhz"
              type="number"
              {...register("ram_speed_mhz")}
              placeholder="e.g., 3200"
            />
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
