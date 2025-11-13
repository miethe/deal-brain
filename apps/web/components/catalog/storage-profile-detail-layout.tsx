"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ChevronRight, HardDrive, Gauge, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";
import { EntityEditModal } from "@/components/entity/entity-edit-modal";
import { storageProfileEditSchema, type StorageProfileEditFormData } from "@/lib/schemas/entity-schemas";
import { useUpdateStorageProfile } from "@/hooks/use-entity-mutations";

interface StorageProfile {
  id: number;
  capacity_gb: number;
  type?: string | null;
  interface?: string | null;
  form_factor?: string | null;
  sequential_read_mb_s?: number | null;
  sequential_write_mb_s?: number | null;
  random_read_iops?: number | null;
  random_write_iops?: number | null;
  manufacturer?: string | null;
  model?: string | null;
  generation?: string | null;
  notes?: string | null;
  label?: string | null;
  medium?: string | null;
  performance_tier?: string | null;
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

interface StorageProfileDetailLayoutProps {
  storageProfile: StorageProfile;
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
  unit: string;
  icon: React.ReactNode;
  description?: string;
}

function MetricCard({ label, value, unit, icon, description }: MetricCardProps) {
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
          <div className="text-2xl font-bold">
            {formattedValue}
            <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
          </div>
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

export function StorageProfileDetailLayout({ storageProfile, listings }: StorageProfileDetailLayoutProps) {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const updateStorageProfileMutation = useUpdateStorageProfile(storageProfile.id);

  const capacityDisplay = storageProfile.capacity_gb >= 1024
    ? `${(storageProfile.capacity_gb / 1024).toFixed(0)}TB`
    : `${storageProfile.capacity_gb}GB`;

  const pageTitle = storageProfile.label || (storageProfile.model
    ? `${storageProfile.model} (${capacityDisplay})`
    : `${capacityDisplay} ${storageProfile.type || storageProfile.medium || "Storage"}`);

  const hasSpecs = storageProfile.type || storageProfile.medium || storageProfile.interface || storageProfile.form_factor || storageProfile.manufacturer || storageProfile.generation;
  const hasPerformance = storageProfile.sequential_read_mb_s || storageProfile.sequential_write_mb_s || storageProfile.random_read_iops || storageProfile.random_write_iops;

  const handleEditSubmit = async (data: StorageProfileEditFormData) => {
    await updateStorageProfileMutation.mutateAsync(data);
    setIsEditModalOpen(false);
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
        <span className="text-foreground font-medium">Storage Profile Details</span>
      </nav>

      {/* Header with Edit button */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{pageTitle}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {storageProfile.manufacturer && (
              <p className="text-lg text-muted-foreground">{storageProfile.manufacturer}</p>
            )}
            {(storageProfile.type || storageProfile.medium) && (
              <Badge variant="default">{storageProfile.type || storageProfile.medium}</Badge>
            )}
            {storageProfile.interface && (
              <Badge variant="secondary">{storageProfile.interface}</Badge>
            )}
            {storageProfile.generation && (
              <Badge variant="outline">{storageProfile.generation}</Badge>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsEditModalOpen(true)}
          aria-label={`Edit ${pageTitle}`}
          className="flex-shrink-0"
        >
          <Pencil className="h-4 w-4 mr-2" />
          Edit
        </Button>
      </div>

      {/* Specifications Card */}
      {hasSpecs && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HardDrive className="h-5 w-5" />
              Specifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <SpecField label="Capacity" value={capacityDisplay} />
              <SpecField label="Type" value={storageProfile.type || storageProfile.medium} />
              <SpecField label="Interface" value={storageProfile.interface} />
              <SpecField label="Form Factor" value={storageProfile.form_factor} />
              <SpecField label="Manufacturer" value={storageProfile.manufacturer} />
              <SpecField label="Model" value={storageProfile.model} />
              <SpecField label="Generation" value={storageProfile.generation} />
              {storageProfile.performance_tier && (
                <SpecField label="Performance Tier" value={storageProfile.performance_tier} />
              )}
            </dl>
            {storageProfile.notes && (
              <div className="mt-6 pt-6 border-t">
                <dt className="text-sm text-muted-foreground mb-2">Notes</dt>
                <dd className="text-sm">{storageProfile.notes}</dd>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Performance Metrics Card */}
      {hasPerformance && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Gauge className="h-5 w-5" />
              Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {storageProfile.sequential_read_mb_s && (
                <MetricCard
                  label="Sequential Read"
                  value={storageProfile.sequential_read_mb_s}
                  unit="MB/s"
                  icon={<Gauge className="h-4 w-4" />}
                  description="Maximum sequential read speed"
                />
              )}
              {storageProfile.sequential_write_mb_s && (
                <MetricCard
                  label="Sequential Write"
                  value={storageProfile.sequential_write_mb_s}
                  unit="MB/s"
                  icon={<Gauge className="h-4 w-4" />}
                  description="Maximum sequential write speed"
                />
              )}
              {storageProfile.random_read_iops && (
                <MetricCard
                  label="Random Read"
                  value={storageProfile.random_read_iops}
                  unit="IOPS"
                  icon={<Gauge className="h-4 w-4" />}
                  description="Random read operations per second"
                />
              )}
              {storageProfile.random_write_iops && (
                <MetricCard
                  label="Random Write"
                  value={storageProfile.random_write_iops}
                  unit="IOPS"
                  icon={<Gauge className="h-4 w-4" />}
                  description="Random write operations per second"
                />
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Used In Listings Card */}
      <Card>
        <CardHeader>
          <CardTitle>
            Used In Listings {listings.length > 0 && `(${listings.length})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {listings.length === 0 ? (
            <div className="text-center py-12">
              <HardDrive className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                No listings currently use this storage profile.
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
        entityType="storage-profile"
        entityId={storageProfile.id}
        initialValues={{
          label: storageProfile.label,
          medium: storageProfile.medium,
          interface: storageProfile.interface,
          form_factor: storageProfile.form_factor,
          capacity_gb: storageProfile.capacity_gb,
          performance_tier: storageProfile.performance_tier,
          notes: storageProfile.notes,
          attributes: storageProfile.attributes_json,
        }}
        schema={storageProfileEditSchema}
        onSubmit={handleEditSubmit}
        onClose={() => setIsEditModalOpen(false)}
        isOpen={isEditModalOpen}
      />
    </div>
  );
}
