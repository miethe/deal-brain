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
import { useCreateGpu, type GpuCreatePayload } from "@/hooks/use-catalog";
import Link from "next/link";

const gpuCreateSchema = z.object({
  name: z.string().min(1, "Name is required").max(200),
  manufacturer: z.string().min(1, "Manufacturer is required").max(100),
  gpu_mark: z.coerce.number().int().min(0).optional().or(z.literal("")),
  metal_score: z.coerce.number().int().min(0).optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
});

type GpuCreateFormData = z.infer<typeof gpuCreateSchema>;

export default function NewGPUPage() {
  const router = useRouter();
  const createGpu = useCreateGpu({
    onSuccess: (gpu) => {
      router.push(`/catalog/gpus/${gpu.id}`);
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<GpuCreateFormData>({
    resolver: zodResolver(gpuCreateSchema),
  });

  const onSubmit = async (data: GpuCreateFormData) => {
    const payload: GpuCreatePayload = {
      name: data.name,
      manufacturer: data.manufacturer,
      gpu_mark: data.gpu_mark || null,
      metal_score: data.metal_score || null,
      notes: data.notes || null,
    };

    createGpu.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Create GPU</h1>
        <p className="text-sm text-muted-foreground">Add a new GPU to the catalog</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>GPU Details</CardTitle>
          <CardDescription>
            Enter the specifications for the new GPU. Required fields are marked with an asterisk.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4">
              {/* Name */}
              <div className="space-y-2">
                <Label htmlFor="name">
                  Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="name"
                  placeholder="e.g., NVIDIA GeForce RTX 4090"
                  {...register("name")}
                  aria-invalid={errors.name ? "true" : "false"}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name.message}</p>
                )}
              </div>

              {/* Manufacturer */}
              <div className="space-y-2">
                <Label htmlFor="manufacturer">
                  Manufacturer <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="manufacturer"
                  placeholder="e.g., NVIDIA"
                  {...register("manufacturer")}
                  aria-invalid={errors.manufacturer ? "true" : "false"}
                />
                {errors.manufacturer && (
                  <p className="text-sm text-destructive">{errors.manufacturer.message}</p>
                )}
              </div>

              {/* Benchmark Scores */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="gpu_mark">GPU Mark</Label>
                  <Input
                    id="gpu_mark"
                    type="number"
                    placeholder="e.g., 35000"
                    {...register("gpu_mark")}
                    aria-invalid={errors.gpu_mark ? "true" : "false"}
                  />
                  {errors.gpu_mark && (
                    <p className="text-sm text-destructive">{errors.gpu_mark.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="metal_score">Metal Score</Label>
                  <Input
                    id="metal_score"
                    type="number"
                    placeholder="e.g., 250000"
                    {...register("metal_score")}
                    aria-invalid={errors.metal_score ? "true" : "false"}
                  />
                  {errors.metal_score && (
                    <p className="text-sm text-destructive">{errors.metal_score.message}</p>
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
                {isSubmitting ? "Creating..." : "Create GPU"}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/catalog/gpus">Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
