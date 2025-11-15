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
import { useCreateCpu, type CpuCreatePayload } from "@/hooks/use-catalog";
import Link from "next/link";

const cpuCreateSchema = z.object({
  name: z.string().min(1, "Name is required").max(200),
  manufacturer: z.string().min(1, "Manufacturer is required").max(100),
  socket: z.string().max(50).optional().or(z.literal("")),
  cores: z.coerce.number().int().min(1).max(256).optional().or(z.literal("")),
  threads: z.coerce.number().int().min(1).max(512).optional().or(z.literal("")),
  tdp_w: z.coerce.number().int().min(1).max(1000).optional().or(z.literal("")),
  igpu_model: z.string().max(100).optional().or(z.literal("")),
  cpu_mark_multi: z.coerce.number().int().min(0).optional().or(z.literal("")),
  cpu_mark_single: z.coerce.number().int().min(0).optional().or(z.literal("")),
  igpu_mark: z.coerce.number().int().min(0).optional().or(z.literal("")),
  release_year: z.coerce.number().int().min(1970).max(2100).optional().or(z.literal("")),
  notes: z.string().optional().or(z.literal("")),
});

type CpuCreateFormData = z.infer<typeof cpuCreateSchema>;

export default function NewCPUPage() {
  const router = useRouter();
  const createCpu = useCreateCpu({
    onSuccess: (cpu) => {
      router.push(`/catalog/cpus/${cpu.id}`);
    },
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CpuCreateFormData>({
    resolver: zodResolver(cpuCreateSchema),
  });

  const onSubmit = async (data: CpuCreateFormData) => {
    const payload: CpuCreatePayload = {
      name: data.name,
      manufacturer: data.manufacturer,
      socket: data.socket || null,
      cores: data.cores || null,
      threads: data.threads || null,
      tdp_w: data.tdp_w || null,
      igpu_model: data.igpu_model || null,
      cpu_mark_multi: data.cpu_mark_multi || null,
      cpu_mark_single: data.cpu_mark_single || null,
      igpu_mark: data.igpu_mark || null,
      release_year: data.release_year || null,
      notes: data.notes || null,
    };

    createCpu.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Create CPU</h1>
        <p className="text-sm text-muted-foreground">Add a new CPU to the catalog</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>CPU Details</CardTitle>
          <CardDescription>
            Enter the specifications for the new CPU. Required fields are marked with an asterisk.
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
                  placeholder="e.g., Intel Core i7-12700K"
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
                  placeholder="e.g., Intel"
                  {...register("manufacturer")}
                  aria-invalid={errors.manufacturer ? "true" : "false"}
                />
                {errors.manufacturer && (
                  <p className="text-sm text-destructive">{errors.manufacturer.message}</p>
                )}
              </div>

              {/* Socket */}
              <div className="space-y-2">
                <Label htmlFor="socket">Socket</Label>
                <Input
                  id="socket"
                  placeholder="e.g., LGA1700"
                  {...register("socket")}
                  aria-invalid={errors.socket ? "true" : "false"}
                />
                {errors.socket && (
                  <p className="text-sm text-destructive">{errors.socket.message}</p>
                )}
              </div>

              {/* Cores and Threads */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="cores">Cores</Label>
                  <Input
                    id="cores"
                    type="number"
                    placeholder="e.g., 12"
                    {...register("cores")}
                    aria-invalid={errors.cores ? "true" : "false"}
                  />
                  {errors.cores && (
                    <p className="text-sm text-destructive">{errors.cores.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="threads">Threads</Label>
                  <Input
                    id="threads"
                    type="number"
                    placeholder="e.g., 20"
                    {...register("threads")}
                    aria-invalid={errors.threads ? "true" : "false"}
                  />
                  {errors.threads && (
                    <p className="text-sm text-destructive">{errors.threads.message}</p>
                  )}
                </div>
              </div>

              {/* TDP and Release Year */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tdp_w">TDP (Watts)</Label>
                  <Input
                    id="tdp_w"
                    type="number"
                    placeholder="e.g., 125"
                    {...register("tdp_w")}
                    aria-invalid={errors.tdp_w ? "true" : "false"}
                  />
                  {errors.tdp_w && (
                    <p className="text-sm text-destructive">{errors.tdp_w.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="release_year">Release Year</Label>
                  <Input
                    id="release_year"
                    type="number"
                    placeholder="e.g., 2023"
                    {...register("release_year")}
                    aria-invalid={errors.release_year ? "true" : "false"}
                  />
                  {errors.release_year && (
                    <p className="text-sm text-destructive">{errors.release_year.message}</p>
                  )}
                </div>
              </div>

              {/* iGPU Model */}
              <div className="space-y-2">
                <Label htmlFor="igpu_model">Integrated GPU Model</Label>
                <Input
                  id="igpu_model"
                  placeholder="e.g., Intel UHD Graphics 770"
                  {...register("igpu_model")}
                  aria-invalid={errors.igpu_model ? "true" : "false"}
                />
                {errors.igpu_model && (
                  <p className="text-sm text-destructive">{errors.igpu_model.message}</p>
                )}
              </div>

              {/* Benchmark Scores */}
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="cpu_mark_multi">CPU Mark Multi</Label>
                  <Input
                    id="cpu_mark_multi"
                    type="number"
                    placeholder="e.g., 35000"
                    {...register("cpu_mark_multi")}
                    aria-invalid={errors.cpu_mark_multi ? "true" : "false"}
                  />
                  {errors.cpu_mark_multi && (
                    <p className="text-sm text-destructive">{errors.cpu_mark_multi.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cpu_mark_single">CPU Mark Single</Label>
                  <Input
                    id="cpu_mark_single"
                    type="number"
                    placeholder="e.g., 4000"
                    {...register("cpu_mark_single")}
                    aria-invalid={errors.cpu_mark_single ? "true" : "false"}
                  />
                  {errors.cpu_mark_single && (
                    <p className="text-sm text-destructive">{errors.cpu_mark_single.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="igpu_mark">iGPU Mark</Label>
                  <Input
                    id="igpu_mark"
                    type="number"
                    placeholder="e.g., 1500"
                    {...register("igpu_mark")}
                    aria-invalid={errors.igpu_mark ? "true" : "false"}
                  />
                  {errors.igpu_mark && (
                    <p className="text-sm text-destructive">{errors.igpu_mark.message}</p>
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
                {isSubmitting ? "Creating..." : "Create CPU"}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/catalog/cpus">Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
