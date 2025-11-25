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

interface QuickAddConnectivityDialogProps {
  listingId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ConnectivityFormData {
  ports_profile_id: string;
}

/**
 * Quick-Add Connectivity Dialog
 *
 * Allows rapid addition of ports profile data to a listing.
 * Currently supports ports_profile_id input.
 * Future enhancement: port builder UI for creating custom port profiles.
 *
 * @example
 * ```tsx
 * <QuickAddConnectivityDialog
 *   listingId={123}
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 * />
 * ```
 */
export function QuickAddConnectivityDialog({
  listingId,
  open,
  onOpenChange,
}: QuickAddConnectivityDialogProps) {
  const { register, handleSubmit, reset } = useForm<ConnectivityFormData>();
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
        description: "Connectivity data updated successfully",
      });
      reset();
      onOpenChange(false);
    },
    onError: (error: unknown) => {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update connectivity data",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: ConnectivityFormData) => {
    const processedData = {
      ports_profile_id: data.ports_profile_id ? parseInt(data.ports_profile_id, 10) : null,
    };
    updateListing.mutate(processedData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Connectivity Data</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="ports_profile_id">Ports Profile ID</Label>
            <Input
              id="ports_profile_id"
              type="number"
              {...register("ports_profile_id")}
              placeholder="Enter ports profile ID"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Enter the ID of an existing ports profile. Leave empty to clear.
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
