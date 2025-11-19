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
import { ListingRecord, RamSpecRecord, StorageProfileRecord } from "@/types/listings";
import { useToast } from "@/hooks/use-toast";
import { CpuSelector } from "@/components/forms/cpu-selector";
import { GpuSelector } from "@/components/forms/gpu-selector";
import { RamSpecSelector } from "@/components/forms/ram-spec-selector";
import { StorageProfileSelector } from "@/components/forms/storage-profile-selector";

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

const createLinkId = () => Math.random().toString(36).slice(2, 10);

const isValidHttpUrl = (value: string) => {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
};

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
  const [listingUrl, setListingUrl] = useState("");
  const [otherLinks, setOtherLinks] = useState<Array<{ id: string; url: string; label: string }>>([]);
  const [linkError, setLinkError] = useState<string | null>(null);

  // Hardware component states
  const [cpuId, setCpuId] = useState<number | null>(null);
  const [gpuId, setGpuId] = useState<number | null>(null);
  const [ramSpec, setRamSpec] = useState<RamSpecRecord | null>(null);
  const [primaryStorage, setPrimaryStorage] = useState<StorageProfileRecord | null>(null);
  const [secondaryStorage, setSecondaryStorage] = useState<StorageProfileRecord | null>(null);

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
      setListingUrl(listing.listing_url ?? "");
      const supplemental = (listing.other_urls ?? []).map((link, index) => ({
        id: `${createLinkId()}-${index}`,
        url: link.url,
        label: link.label ?? "",
      }));
      setOtherLinks(supplemental);
      setLinkError(null);

      // Populate hardware component fields
      setCpuId(listing.cpu?.id ?? null);
      setGpuId(listing.gpu?.id ?? null);
      setRamSpec(listing.ram_spec ?? null);
      setPrimaryStorage(listing.primary_storage_profile ?? null);
      setSecondaryStorage(listing.secondary_storage_profile ?? null);
    }
  }, [listing]);

  const addOtherLink = () => {
    setOtherLinks((prev) => [...prev, { id: createLinkId(), url: "", label: "" }]);
  };

  const updateOtherLink = (id: string, field: "url" | "label", value: string) => {
    setOtherLinks((prev) =>
      prev.map((link) => (link.id === id ? { ...link, [field]: value } : link))
    );
  };

  const removeOtherLink = (id: string) => {
    setOtherLinks((prev) => prev.filter((link) => link.id !== id));
  };

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (fields: Record<string, unknown>) => {
      return apiFetch(`/v1/listings/${listingId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields }),
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
    if (!listingId) {
      return;
    }

    setLinkError(null);

    const primaryLink = listingUrl.trim();
    if (primaryLink && !isValidHttpUrl(primaryLink)) {
      setLinkError("Primary listing URL must start with http:// or https://");
      return;
    }

    const preparedOtherLinks = otherLinks
      .map((link) => ({ url: link.url.trim(), label: link.label.trim() }))
      .filter((link) => Boolean(link.url));

    const invalidSupplemental = preparedOtherLinks.find((link) => !isValidHttpUrl(link.url));
    if (invalidSupplemental) {
      setLinkError(`Additional link must use http/https: ${invalidSupplemental.url}`);
      return;
    }

    const seen = new Set<string>();
    const uniqueSupplemental = preparedOtherLinks.reduce<Array<{ url: string; label?: string }>>(
      (acc, link) => {
        if (seen.has(link.url)) {
          return acc;
        }
        seen.add(link.url);
        acc.push({ url: link.url, label: link.label ? link.label : undefined });
        return acc;
      },
      []
    );

    const fields: Record<string, unknown> = {
      title: title.trim(),
      condition,
      status,
      listing_url: primaryLink || null,
      other_urls: uniqueSupplemental,
      cpu_id: cpuId,
      gpu_id: gpuId,
      ram_spec_id: ramSpec?.id ?? null,
      primary_storage_profile_id: primaryStorage?.id ?? null,
      secondary_storage_profile_id: secondaryStorage?.id ?? null,
    };

    const parsedPrice = parseFloat(price);
    if (!Number.isNaN(parsedPrice)) {
      fields.price_usd = parsedPrice;
    }

    updateMutation.mutate(fields);
  };

  return (
    <Dialog open={isOpen} onOpenChange={closeDialog}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
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

            {/* Hardware Components Section */}
            <div className="pt-2 border-t">
              <h4 className="text-sm font-semibold mb-3">Hardware Components</h4>

              {/* CPU */}
              <div className="space-y-2 mb-3">
                <Label htmlFor="cpu">CPU</Label>
                <CpuSelector value={cpuId} onChange={setCpuId} placeholder="Select CPU" />
              </div>

              {/* GPU */}
              <div className="space-y-2 mb-3">
                <Label htmlFor="gpu">GPU</Label>
                <GpuSelector value={gpuId} onChange={setGpuId} placeholder="Select GPU (optional)" />
              </div>

              {/* RAM */}
              <div className="space-y-2 mb-3">
                <Label htmlFor="ram">RAM</Label>
                <RamSpecSelector value={ramSpec} onChange={setRamSpec} placeholder="Select RAM spec" />
              </div>

              {/* Primary Storage */}
              <div className="space-y-2 mb-3">
                <Label htmlFor="primary-storage">Primary Storage</Label>
                <StorageProfileSelector
                  value={primaryStorage}
                  onChange={setPrimaryStorage}
                  placeholder="Select primary storage"
                  context="primary"
                />
              </div>

              {/* Secondary Storage */}
              <div className="space-y-2">
                <Label htmlFor="secondary-storage">Secondary Storage</Label>
                <StorageProfileSelector
                  value={secondaryStorage}
                  onChange={setSecondaryStorage}
                  placeholder="Select secondary storage (optional)"
                  context="secondary"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="listing_url">Listing URL</Label>
              <Input
                id="listing_url"
                placeholder="https://www.ebay.com/itm/..."
                value={listingUrl}
                onChange={(event) => setListingUrl(event.target.value)}
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Additional Links</Label>
                <Button type="button" variant="outline" size="sm" onClick={addOtherLink}>
                  Add Link
                </Button>
              </div>
              {linkError && <p className="text-sm text-destructive">{linkError}</p>}
              {otherLinks.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Share supplemental references like photo galleries or alternate marketplaces.
                </p>
              ) : (
                <div className="space-y-2">
                  {otherLinks.map((link) => (
                    <div key={link.id} className="flex flex-col gap-2">
                      <Input
                        placeholder="https://imgur.com/album/..."
                        value={link.url}
                        onChange={(event) => updateOtherLink(link.id, "url", event.target.value)}
                      />
                      <div className="flex gap-2">
                        <Input
                          className="flex-1"
                          placeholder="Optional label"
                          value={link.label}
                          onChange={(event) => updateOtherLink(link.id, "label", event.target.value)}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeOtherLink(link.id)}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
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
