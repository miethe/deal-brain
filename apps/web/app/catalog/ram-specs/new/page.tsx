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
import { useCreateRamSpec, type RamSpecCreatePayload } from "@/hooks/use-catalog";
import Link from "next/link";

const ramSpecCreateSchema = z.object({
  label: z.string().max(100).optional().or(z.literal("")),
  ddr_generation: z.enum([
    "ddr3",
    "ddr4",
    "ddr5",
    "lpddr4",
    "lpddr4x",
    "lpddr5",
    "lpddr5x",
    "hbm2",
    "hbm3",
    "unknown",
  ]),
  speed_mhz: z.coerce.number().int().min(0).max(10000).optional().or(z.literal("")),
  module_count: z.coerce.number().int().min(1).max(8).optional().or(z.literal("")),
  capacity_per_module_gb: z.coerce.number().int().min(1).max(256).optional().or(z.literal("")),
  total_capacity_gb: z.coerce.number().int().min(1).max(2048).optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
});

type RamSpecCreateFormData = z.infer<typeof ramSpecCreateSchema>;

const DDR_GENERATION_OPTIONS = [
  { value: "ddr3", label: "DDR3" },
  { value: "ddr4", label: "DDR4" },
  { value: "ddr5", label: "DDR5" },
  { value: "lpddr4", label: "LPDDR4" },
  { value: "lpddr4x", label: "LPDDR4X" },
  { value: "lpddr5", label: "LPDDR5" },
  { value: "lpddr5x", label: "LPDDR5X" },
  { value: "hbm2", label: "HBM2" },
  { value: "hbm3", label: "HBM3" },
  { value: "unknown", label: "Unknown" },
];

export default function NewRamSpecPage() {
  const router = useRouter();
  const createRamSpec = useCreateRamSpec({
    onSuccess: (ramSpec) => {
      router.push(`/catalog/ram-specs/${ramSpec.id}`);
    },
  });

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RamSpecCreateFormData>({
    resolver: zodResolver(ramSpecCreateSchema),
    defaultValues: {
      ddr_generation: "unknown",
    },
  });

  const ddrGeneration = watch("ddr_generation");

  const onSubmit = async (data: RamSpecCreateFormData) => {
    const payload: RamSpecCreatePayload = {
      label: data.label || null,
      ddr_generation: data.ddr_generation,
      speed_mhz: data.speed_mhz || null,
      module_count: data.module_count || null,
      capacity_per_module_gb: data.capacity_per_module_gb || null,
      total_capacity_gb: data.total_capacity_gb || null,
      notes: data.notes || null,
    };

    createRamSpec.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Create RAM Specification</h1>
        <p className="text-sm text-muted-foreground">Add a new RAM specification to the catalog</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>RAM Specification Details</CardTitle>
          <CardDescription>
            Enter the specifications for the new RAM configuration. Required fields are marked with an asterisk.
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
                  placeholder="e.g., 32GB DDR5-5600"
                  {...register("label")}
                  aria-invalid={errors.label ? "true" : "false"}
                />
                {errors.label && (
                  <p className="text-sm text-destructive">{errors.label.message}</p>
                )}
              </div>

              {/* DDR Generation */}
              <div className="space-y-2">
                <Label htmlFor="ddr_generation">
                  DDR Generation <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={ddrGeneration}
                  onValueChange={(value) => setValue("ddr_generation", value as any)}
                >
                  <SelectTrigger id="ddr_generation">
                    <SelectValue placeholder="Select DDR generation" />
                  </SelectTrigger>
                  <SelectContent>
                    {DDR_GENERATION_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.ddr_generation && (
                  <p className="text-sm text-destructive">{errors.ddr_generation.message}</p>
                )}
              </div>

              {/* Speed and Module Count */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="speed_mhz">Speed (MHz)</Label>
                  <Input
                    id="speed_mhz"
                    type="number"
                    placeholder="e.g., 5600"
                    {...register("speed_mhz")}
                    aria-invalid={errors.speed_mhz ? "true" : "false"}
                  />
                  {errors.speed_mhz && (
                    <p className="text-sm text-destructive">{errors.speed_mhz.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="module_count">Module Count</Label>
                  <Input
                    id="module_count"
                    type="number"
                    placeholder="e.g., 2"
                    {...register("module_count")}
                    aria-invalid={errors.module_count ? "true" : "false"}
                  />
                  {errors.module_count && (
                    <p className="text-sm text-destructive">{errors.module_count.message}</p>
                  )}
                </div>
              </div>

              {/* Capacity */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="capacity_per_module_gb">Capacity per Module (GB)</Label>
                  <Input
                    id="capacity_per_module_gb"
                    type="number"
                    placeholder="e.g., 16"
                    {...register("capacity_per_module_gb")}
                    aria-invalid={errors.capacity_per_module_gb ? "true" : "false"}
                  />
                  {errors.capacity_per_module_gb && (
                    <p className="text-sm text-destructive">
                      {errors.capacity_per_module_gb.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="total_capacity_gb">Total Capacity (GB)</Label>
                  <Input
                    id="total_capacity_gb"
                    type="number"
                    placeholder="e.g., 32"
                    {...register("total_capacity_gb")}
                    aria-invalid={errors.total_capacity_gb ? "true" : "false"}
                  />
                  {errors.total_capacity_gb && (
                    <p className="text-sm text-destructive">{errors.total_capacity_gb.message}</p>
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
                {isSubmitting ? "Creating..." : "Create RAM Specification"}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/catalog/ram-specs">Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
