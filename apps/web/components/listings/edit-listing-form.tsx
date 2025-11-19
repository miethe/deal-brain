"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { apiFetch } from "../../lib/utils";
import { useToast } from "../../hooks/use-toast";
import { CpuSelector } from "../forms/cpu-selector";
import { GpuSelector } from "../forms/gpu-selector";
import { RamSpecSelector } from "../forms/ram-spec-selector";
import { StorageProfileSelector } from "../forms/storage-profile-selector";
import type { ListingDetail } from "../../types/listing-detail";
import type { RamSpecRecord, StorageProfileRecord } from "../../types/listings";

const CONDITIONS = [
  { value: "new", label: "New" },
  { value: "refurb", label: "Refurb" },
  { value: "used", label: "Used" },
  { value: "for-parts", label: "For Parts" },
];

const STATUSES = [
  { value: "active", label: "Active" },
  { value: "sold", label: "Sold" },
  { value: "pending", label: "Pending" },
  { value: "archived", label: "Archived" },
];

const MANUFACTURER_OPTIONS = [
  "Dell",
  "HP",
  "Lenovo",
  "Apple",
  "ASUS",
  "Acer",
  "MSI",
  "Custom Build",
  "Other",
];

const FORM_FACTOR_OPTIONS = [
  "Desktop",
  "Laptop",
  "Server",
  "Mini-PC",
  "All-in-One",
  "Other",
];

interface EditListingFormProps {
  listing: ListingDetail;
}

export function EditListingForm({ listing }: EditListingFormProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Form state
  const [title, setTitle] = useState(listing.title);
  const [price, setPrice] = useState(listing.price_usd.toString());
  const [condition, setCondition] = useState(listing.condition || "used");
  const [status, setStatus] = useState(listing.status || "active");
  const [manufacturer, setManufacturer] = useState(listing.manufacturer || "");
  const [series, setSeries] = useState(listing.series || "");
  const [modelNumber, setModelNumber] = useState(listing.model_number || "");
  const [formFactor, setFormFactor] = useState(listing.form_factor || "");
  const [listingUrl, setListingUrl] = useState(listing.listing_url || "");

  // Hardware component states
  const [cpuId, setCpuId] = useState<number | null>(listing.cpu?.id ?? null);
  const [gpuId, setGpuId] = useState<number | null>(listing.gpu?.id ?? null);
  const [ramSpec, setRamSpec] = useState<RamSpecRecord | null>(listing.ram_spec ?? null);
  const [primaryStorage, setPrimaryStorage] = useState<StorageProfileRecord | null>(
    listing.primary_storage_profile ?? null
  );
  const [secondaryStorage, setSecondaryStorage] = useState<StorageProfileRecord | null>(
    listing.secondary_storage_profile ?? null
  );

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (fields: Record<string, unknown>) => {
      return apiFetch(`/v1/listings/${listing.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fields }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
      queryClient.invalidateQueries({ queryKey: ["listing", listing.id] });
      toast({
        title: "Success",
        description: "Listing updated successfully",
      });
      router.push(`/listings/${listing.id}`);
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update listing",
        variant: "destructive",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const fields: Record<string, unknown> = {
      title: title.trim(),
      price_usd: parseFloat(price) || 0,
      condition,
      status,
      manufacturer: manufacturer.trim() || null,
      series: series.trim() || null,
      model_number: modelNumber.trim() || null,
      form_factor: formFactor || null,
      listing_url: listingUrl.trim() || null,
      cpu_id: cpuId,
      gpu_id: gpuId,
      ram_spec_id: ramSpec?.id ?? null,
      primary_storage_profile_id: primaryStorage?.id ?? null,
      secondary_storage_profile_id: secondaryStorage?.id ?? null,
    };

    updateMutation.mutate(fields);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
          <CardDescription>
            Core listing details like title, price, and condition.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Listing title"
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="price">Price (USD) *</Label>
              <Input
                id="price"
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
                step="0.01"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="condition">Condition</Label>
              <Select value={condition} onValueChange={setCondition}>
                <SelectTrigger id="condition">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONDITIONS.map((cond) => (
                    <SelectItem key={cond.value} value={cond.value}>
                      {cond.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger id="status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUSES.map((stat) => (
                  <SelectItem key={stat.value} value={stat.value}>
                    {stat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Hardware Components */}
      <Card>
        <CardHeader>
          <CardTitle>Hardware Components</CardTitle>
          <CardDescription>
            Select CPU, GPU, RAM, and storage configurations.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="cpu">CPU</Label>
            <CpuSelector value={cpuId} onChange={setCpuId} placeholder="Select CPU" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="gpu">GPU</Label>
            <GpuSelector value={gpuId} onChange={setGpuId} placeholder="Select GPU (optional)" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ram">RAM</Label>
            <RamSpecSelector value={ramSpec} onChange={setRamSpec} placeholder="Select RAM spec" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="primary-storage">Primary Storage</Label>
            <StorageProfileSelector
              value={primaryStorage}
              onChange={setPrimaryStorage}
              placeholder="Select primary storage"
              context="primary"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="secondary-storage">Secondary Storage</Label>
            <StorageProfileSelector
              value={secondaryStorage}
              onChange={setSecondaryStorage}
              placeholder="Select secondary storage (optional)"
              context="secondary"
            />
          </div>
        </CardContent>
      </Card>

      {/* Product Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Product Metadata</CardTitle>
          <CardDescription>
            Additional product details like manufacturer, model, and form factor.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="manufacturer">Manufacturer</Label>
              <Select value={manufacturer} onValueChange={setManufacturer}>
                <SelectTrigger id="manufacturer">
                  <SelectValue placeholder="Select manufacturer" />
                </SelectTrigger>
                <SelectContent>
                  {MANUFACTURER_OPTIONS.map((mfr) => (
                    <SelectItem key={mfr} value={mfr}>
                      {mfr}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="form-factor">Form Factor</Label>
              <Select value={formFactor} onValueChange={setFormFactor}>
                <SelectTrigger id="form-factor">
                  <SelectValue placeholder="Select form factor" />
                </SelectTrigger>
                <SelectContent>
                  {FORM_FACTOR_OPTIONS.map((ff) => (
                    <SelectItem key={ff} value={ff}>
                      {ff}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="series">Series</Label>
              <Input
                id="series"
                value={series}
                onChange={(e) => setSeries(e.target.value)}
                placeholder="e.g., OptiPlex, ThinkCentre"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="model-number">Model Number</Label>
              <Input
                id="model-number"
                value={modelNumber}
                onChange={(e) => setModelNumber(e.target.value)}
                placeholder="e.g., 7050, M720q"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="listing-url">Listing URL</Label>
            <Input
              id="listing-url"
              value={listingUrl}
              onChange={(e) => setListingUrl(e.target.value)}
              placeholder="https://www.ebay.com/itm/..."
              type="url"
            />
          </div>
        </CardContent>
      </Card>

      {/* Form Actions */}
      <div className="flex gap-2 justify-end">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.push(`/listings/${listing.id}`)}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={updateMutation.isPending}>
          {updateMutation.isPending ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </form>
  );
}
