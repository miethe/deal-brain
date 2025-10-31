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

interface QuickAddComputeDialogProps {
  listingId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ComputeFormData {
  cpu_id: string;
  gpu_id: string;
}

/**
 * Quick-Add Compute Dialog
 *
 * Allows rapid addition of CPU and GPU data to a listing.
 * Currently supports direct ID input for both CPU and GPU.
 * Future enhancement: searchable dropdown for component selection.
 *
 * @example
 * ```tsx
 * <QuickAddComputeDialog
 *   listingId={123}
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 * />
 * ```
 */
export function QuickAddComputeDialog({
  listingId,
  open,
  onOpenChange,
}: QuickAddComputeDialogProps) {
  const { register, handleSubmit, reset } = useForm<ComputeFormData>();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const updateListing = useMutation({
    mutationFn: (data: Record<string, number | null>) =>
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
        description: "Compute data updated successfully",
      });
      reset();
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update compute data",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: ComputeFormData) => {
    const processedData = {
      cpu_id: data.cpu_id ? parseInt(data.cpu_id, 10) : null,
      gpu_id: data.gpu_id ? parseInt(data.gpu_id, 10) : null,
    };
    updateListing.mutate(processedData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Compute Data</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="cpu_id">CPU ID</Label>
            <Input
              id="cpu_id"
              type="number"
              {...register("cpu_id")}
              placeholder="Enter CPU ID"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Enter the ID of a CPU from the catalog. Leave empty to clear.
            </p>
          </div>

          <div>
            <Label htmlFor="gpu_id">GPU ID</Label>
            <Input
              id="gpu_id"
              type="number"
              {...register("gpu_id")}
              placeholder="Enter GPU ID"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Enter the ID of a GPU from the catalog. Leave empty to clear.
            </p>
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
