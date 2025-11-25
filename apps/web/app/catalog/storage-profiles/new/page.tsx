"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateStorageProfile, type StorageProfileCreatePayload } from "@/hooks/use-catalog";
import Link from "next/link";

const storageProfileCreateSchema = z.object({
  label: z.string().max(100).optional().or(z.literal("")),
  medium: z.enum([
    "nvme",
    "sata_ssd",
    "hdd",
    "hybrid",
    "emmc",
    "ufs",
    "unknown",
  ]),
  interface: z.string().max(50).optional().or(z.literal("")),
  form_factor: z.string().max(50).optional().or(z.literal("")),
  capacity_gb: z.coerce.number().int().min(1).max(100000).optional().or(z.literal("")),
  performance_tier: z.string().max(50).optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
});

type StorageProfileCreateFormData = z.infer<typeof storageProfileCreateSchema>;

const STORAGE_MEDIUM_OPTIONS = [
  { value: "nvme", label: "NVMe" },
  { value: "sata_ssd", label: "SATA SSD" },
  { value: "hdd", label: "HDD" },
  { value: "hybrid", label: "Hybrid (SSHD)" },
  { value: "emmc", label: "eMMC" },
  { value: "ufs", label: "UFS" },
  { value: "unknown", label: "Unknown" },
];

const INTERFACE_OPTIONS = [
  { value: "nvme", label: "NVMe" },
  { value: "sata", label: "SATA" },
  { value: "pcie", label: "PCIe" },
  { value: "usb", label: "USB" },
  { value: "emmc", label: "eMMC" },
];

const FORM_FACTOR_OPTIONS = [
  { value: "m2", label: "M.2" },
  { value: "2.5", label: "2.5\"" },
  { value: "3.5", label: "3.5\"" },
  { value: "pcie_card", label: "PCIe Card" },
  { value: "emmc_embedded", label: "eMMC Embedded" },
];

const PERFORMANCE_TIER_OPTIONS = [
  { value: "budget", label: "Budget" },
  { value: "mainstream", label: "Mainstream" },
  { value: "performance", label: "Performance" },
  { value: "enthusiast", label: "Enthusiast" },
];

export default function NewStorageProfilePage() {
  const router = useRouter();
  const createStorageProfile = useCreateStorageProfile({
    onSuccess: (storageProfile) => {
      router.push(`/catalog/storage-profiles/${storageProfile.id}`);
    },
  });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<StorageProfileCreateFormData>({
    resolver: zodResolver(storageProfileCreateSchema),
    defaultValues: {
      medium: "unknown",
    },
  });

  const medium = watch("medium");
  const interfaceValue = watch("interface");
  const formFactor = watch("form_factor");
  const performanceTier = watch("performance_tier");

  const onSubmit = async (data: StorageProfileCreateFormData) => {
    const payload: StorageProfileCreatePayload = {
      label: data.label || null,
      medium: data.medium,
      interface: data.interface || null,
      form_factor: data.form_factor || null,
      capacity_gb: data.capacity_gb || null,
      performance_tier: data.performance_tier || null,
      notes: data.notes || null,
    };

    createStorageProfile.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Create Storage Profile</h1>
        <p className="text-sm text-muted-foreground">Add a new storage profile to the catalog</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Storage Profile Details</CardTitle>
          <CardDescription>
            Enter the specifications for the new storage profile. Required fields are marked with an asterisk.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4">
              {/* Label */}
              <div className="space-y-2">
                <Label htmlFor="label">Label</Label>
                <Input
                  id="label"
                  placeholder="e.g., 1TB NVMe SSD"
                  {...register("label")}
                  aria-invalid={errors.label ? "true" : "false"}
                />
                {errors.label && (
                  <p className="text-sm text-destructive">{errors.label.message}</p>
                )}
              </div>

              {/* Storage Medium */}
              <div className="space-y-2">
                <Label htmlFor="medium">
                  Storage Medium <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={medium}
                  onValueChange={(value) => setValue("medium", value as any)}
                >
                  <SelectTrigger id="medium">
                    <SelectValue placeholder="Select storage medium" />
                  </SelectTrigger>
                  <SelectContent>
                    {STORAGE_MEDIUM_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.medium && (
                  <p className="text-sm text-destructive">{errors.medium.message}</p>
                )}
              </div>

              {/* Interface and Form Factor */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="interface">Interface</Label>
                  <Select
                    value={interfaceValue || ""}
                    onValueChange={(value) => setValue("interface", value)}
                  >
                    <SelectTrigger id="interface">
                      <SelectValue placeholder="Select interface" />
                    </SelectTrigger>
                    <SelectContent>
                      {INTERFACE_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.interface && (
                    <p className="text-sm text-destructive">{errors.interface.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="form_factor">Form Factor</Label>
                  <Select
                    value={formFactor || ""}
                    onValueChange={(value) => setValue("form_factor", value)}
                  >
                    <SelectTrigger id="form_factor">
                      <SelectValue placeholder="Select form factor" />
                    </SelectTrigger>
                    <SelectContent>
                      {FORM_FACTOR_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.form_factor && (
                    <p className="text-sm text-destructive">{errors.form_factor.message}</p>
                  )}
                </div>
              </div>

              {/* Capacity and Performance Tier */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="capacity_gb">Capacity (GB)</Label>
                  <Input
                    id="capacity_gb"
                    type="number"
                    placeholder="e.g., 1024"
                    {...register("capacity_gb")}
                    aria-invalid={errors.capacity_gb ? "true" : "false"}
                  />
                  {errors.capacity_gb && (
                    <p className="text-sm text-destructive">{errors.capacity_gb.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="performance_tier">Performance Tier</Label>
                  <Select
                    value={performanceTier || ""}
                    onValueChange={(value) => setValue("performance_tier", value)}
                  >
                    <SelectTrigger id="performance_tier">
                      <SelectValue placeholder="Select performance tier" />
                    </SelectTrigger>
                    <SelectContent>
                      {PERFORMANCE_TIER_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.performance_tier && (
                    <p className="text-sm text-destructive">{errors.performance_tier.message}</p>
                  )}
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  placeholder="Additional notes or comments..."
                  {...register("notes")}
                  rows={3}
                />
                {errors.notes && (
                  <p className="text-sm text-destructive">{errors.notes.message}</p>
                )}
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create Storage Profile"}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/catalog/storage-profiles">Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
