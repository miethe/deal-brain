"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ChevronRight, Gauge, TrendingUp, Pencil, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { EntityEditModal } from "@/components/entity/entity-edit-modal";
import { EntityDeleteDialog } from "@/components/entity/entity-delete-dialog";
import { gpuEditSchema, type GPUEditFormData } from "@/lib/schemas/entity-schemas";
import { useUpdateGpu, useDeleteGpu } from "@/hooks/use-entity-mutations";

interface GPU {
  id: number;
  model: string;
  manufacturer?: string | null;
  gpu_type?: "integrated" | "discrete" | null;
  vram_capacity_gb?: number | null;
  vram_type?: string | null;
  architecture?: string | null;
  generation?: string | null;
  benchmark_score?: number | null;
  gpu_mark?: number | null;
  three_d_mark?: number | null;
  release_year?: number | null;
  tdp_watts?: number | null;
  notes?: string | null;
  attributes_json?: Record<string, any>;
}

interface Listing {
  id: number;
  title: string;
  price_usd: number;
  adjusted_price_usd: number | null;
  manufacturer?: string | null;
  model_number?: string | null;
  form_factor?: string | null;
  condition: string;
  status: string;
  cpu_name?: string | null;
  ram_gb?: number | null;
  primary_storage_gb?: number | null;
  primary_storage_type?: string | null;
}

interface GPUDetailLayoutProps {
  gpu: GPU;
  listings: Listing[];
}

interface SpecFieldProps {
  label: string;
  value: string | number | null | undefined;
  className?: string;
}

function SpecField({ label, value, className }: SpecFieldProps) {
  if (value === null || value === undefined) {
    return null;
  }

  return (
    <div className={cn("space-y-1", className)}>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-base font-semibold">{value}</dd>
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: number | null | undefined;
  icon: React.ReactNode;
  description?: string;
}

function MetricCard({ label, value, icon, description }: MetricCardProps) {
  if (value === null || value === undefined) {
    return null;
  }

  const formattedValue = value.toLocaleString();

  return (
    <div className="rounded-lg border bg-card p-6 transition-colors hover:bg-accent">
      <div className="flex items-center gap-3 mb-2">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          {icon}
        </div>
        <div className="flex-1">
          <div className="text-sm text-muted-foreground">{label}</div>
          <div className="text-2xl font-bold">{formattedValue}</div>
        </div>
      </div>
      {description && (
        <p className="text-xs text-muted-foreground mt-2">{description}</p>
      )}
    </div>
  );
}

interface ListingCardProps {
  listing: Listing;
}

function ListingCard({ listing }: ListingCardProps) {
  const displayPrice = listing.adjusted_price_usd ?? listing.price_usd;

  return (
    <Link
      href={`/listings/${listing.id}`}
      className="block p-4 rounded-lg border bg-card hover:bg-accent transition-colors group"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-base mb-1 truncate group-hover:text-primary transition-colors">
            {listing.title}
          </h3>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            {listing.manufacturer && (
              <span>{listing.manufacturer}</span>
            )}
            {listing.form_factor && (
              <>
                <span className="text-muted-foreground/50">•</span>
                <span>{listing.form_factor}</span>
              </>
            )}
            {listing.ram_gb && (
              <>
                <span className="text-muted-foreground/50">•</span>
                <span>{listing.ram_gb}GB RAM</span>
              </>
            )}
            {listing.primary_storage_gb && (
              <>
                <span className="text-muted-foreground/50">•</span>
                <span>
                  {listing.primary_storage_gb}GB {listing.primary_storage_type || "Storage"}
                </span>
              </>
            )}
          </div>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant={listing.condition === "new" ? "default" : "secondary"}>
              {listing.condition}
            </Badge>
            <Badge variant="outline">{listing.status}</Badge>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="text-xl font-bold">
            ${displayPrice.toLocaleString()}
          </div>
          {listing.adjusted_price_usd && listing.adjusted_price_usd !== listing.price_usd && (
            <div className="text-sm text-muted-foreground line-through">
              ${listing.price_usd.toLocaleString()}
            </div>
          )}
          <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
      </div>
    </Link>
  );
}

export function GPUDetailLayout({ gpu, listings }: GPUDetailLayoutProps) {
  const router = useRouter();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const updateGpuMutation = useUpdateGpu(gpu.id);
  const deleteGpuMutation = useDeleteGpu(gpu.id, {
    onSuccess: () => {
      router.push("/catalog/gpus");
    },
  });

  const hasSpecs = gpu.manufacturer || gpu.gpu_type || gpu.vram_capacity_gb || gpu.architecture || gpu.generation || gpu.tdp_watts || gpu.release_year;
  const hasBenchmarks = gpu.benchmark_score || gpu.gpu_mark || gpu.three_d_mark;
  const usedInCount = listings.length;

  const getGPUTypeBadgeVariant = () => {
    if (gpu.gpu_type === "integrated") return "secondary";
    if (gpu.gpu_type === "discrete") return "default";
    return "outline";
  };

  const formatVRAM = () => {
    if (!gpu.vram_capacity_gb) return null;
    const vramText = `${gpu.vram_capacity_gb}GB`;
    return gpu.vram_type ? `${vramText} ${gpu.vram_type}` : vramText;
  };

  const handleEditSubmit = async (data: GPUEditFormData) => {
    await updateGpuMutation.mutateAsync(data);
    setIsEditModalOpen(false);
  };

  const handleDeleteConfirm = async () => {
    await deleteGpuMutation.mutateAsync();
    setShowDeleteDialog(false);
  };

  return (
    <div className="container mx-auto py-8 space-y-6 px-4 sm:px-6 lg:px-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-muted-foreground" aria-label="Breadcrumb">
        <Link href="/listings" className="hover:text-primary transition-colors">
          Listings
        </Link>
        <ChevronRight className="h-4 w-4" />
        <Link href="/catalog" className="hover:text-primary transition-colors">
          Catalog
        </Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-foreground font-medium">GPU Details</span>
      </nav>

      {/* Header with Edit and Delete buttons */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{gpu.model}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {gpu.manufacturer && (
              <p className="text-lg text-muted-foreground">{gpu.manufacturer}</p>
            )}
            {gpu.gpu_type && (
              <Badge variant={getGPUTypeBadgeVariant()}>
                {gpu.gpu_type === "integrated" ? "Integrated" : "Discrete"}
              </Badge>
            )}
            {gpu.generation && (
              <Badge variant="secondary">{gpu.generation}</Badge>
            )}
            {gpu.release_year && (
              <Badge variant="outline">{gpu.release_year}</Badge>
            )}
            {usedInCount > 0 && (
              <Badge variant="outline" className="cursor-default">
                Used in {usedInCount} listing{usedInCount === 1 ? "" : "s"}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsEditModalOpen(true)}
            aria-label={`Edit ${gpu.model}`}
            className="flex-shrink-0"
          >
            <Pencil className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteDialog(true)}
            aria-label={`Delete ${gpu.model}`}
            className="flex-shrink-0"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Specifications Card */}
      {hasSpecs && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Gauge className="h-5 w-5" />
              Specifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <SpecField label="Manufacturer" value={gpu.manufacturer} />
              <SpecField label="GPU Type" value={gpu.gpu_type ? (gpu.gpu_type === "integrated" ? "Integrated" : "Discrete") : null} />
              <SpecField label="VRAM" value={formatVRAM()} />
              <SpecField label="Architecture" value={gpu.architecture} />
              <SpecField label="Generation" value={gpu.generation} />
              <SpecField
                label="TDP"
                value={gpu.tdp_watts ? `${gpu.tdp_watts}W` : null}
              />
              <SpecField label="Release Year" value={gpu.release_year} />
            </dl>
            {gpu.notes && (
              <div className="mt-6 pt-6 border-t">
                <dt className="text-sm text-muted-foreground mb-2">Notes</dt>
                <dd className="text-sm">{gpu.notes}</dd>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Benchmark Scores Card */}
      {hasBenchmarks && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Benchmark Scores
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {gpu.gpu_mark && (
                <MetricCard
                  label="GPU Mark"
                  value={gpu.gpu_mark}
                  icon={<Gauge className="h-4 w-4" />}
                  description="Overall GPU performance score"
                />
              )}
              {gpu.three_d_mark && (
                <MetricCard
                  label="3D Mark"
                  value={gpu.three_d_mark}
                  icon={<TrendingUp className="h-4 w-4" />}
                  description="3D graphics performance score"
                />
              )}
              {gpu.benchmark_score && (
                <MetricCard
                  label="Benchmark Score"
                  value={gpu.benchmark_score}
                  icon={<Gauge className="h-4 w-4" />}
                  description="General benchmark performance"
                />
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Used In Listings Card */}
      <Card id="used-in-listings">
        <CardHeader>
          <CardTitle>
            Used In Listings {listings.length > 0 && `(${listings.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {listings.length === 0 ? (
            <div className="text-center py-12">
              <Gauge className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                No listings currently use this GPU.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Edit Modal */}
      <EntityEditModal
        entityType="gpu"
        entityId={gpu.id}
        initialValues={{
          name: gpu.model,
          manufacturer: gpu.manufacturer,
          gpu_mark: gpu.gpu_mark,
          metal_score: gpu.three_d_mark,
          notes: gpu.notes,
          attributes: gpu.attributes_json,
        }}
        schema={gpuEditSchema}
        onSubmit={handleEditSubmit}
        onClose={() => setIsEditModalOpen(false)}
        isOpen={isEditModalOpen}
      />

      {/* Delete Dialog */}
      <EntityDeleteDialog
        entityType="gpu"
        entityId={gpu.id}
        entityName={gpu.model}
        usedInCount={usedInCount}
        isOpen={showDeleteDialog}
        onCancel={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
}
