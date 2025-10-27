"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ChevronRight, MemoryStick } from "lucide-react";
import { cn } from "@/lib/utils";

interface RAMSpec {
  id: number;
  capacity_gb: number;
  type?: string | null;
  speed_mhz?: number | null;
  latency?: string | null;
  voltage?: number | null;
  configuration?: string | null;
  manufacturer?: string | null;
  form_factor?: string | null;
  ecc_support?: boolean | null;
  notes?: string | null;
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

interface RAMSpecDetailLayoutProps {
  ramSpec: RAMSpec;
  listings: Listing[];
}

interface SpecFieldProps {
  label: string;
  value: string | number | boolean | null | undefined;
  className?: string;
}

function SpecField({ label, value, className }: SpecFieldProps) {
  if (value === null || value === undefined) {
    return null;
  }

  const displayValue = typeof value === "boolean" ? (value ? "Yes" : "No") : value;

  return (
    <div className={cn("space-y-1", className)}>
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-base font-semibold">{displayValue}</dd>
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

export function RAMSpecDetailLayout({ ramSpec, listings }: RAMSpecDetailLayoutProps) {
  const pageTitle = `${ramSpec.capacity_gb}GB ${ramSpec.type || "RAM"}`;

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
        <span className="text-foreground font-medium">RAM Spec Details</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{pageTitle}</h1>
        <div className="flex flex-wrap items-center gap-2 mt-2">
          {ramSpec.manufacturer && (
            <p className="text-lg text-muted-foreground">{ramSpec.manufacturer}</p>
          )}
          {ramSpec.type && (
            <Badge variant="default">{ramSpec.type}</Badge>
          )}
          {ramSpec.configuration && (
            <Badge variant="secondary">{ramSpec.configuration}</Badge>
          )}
          {ramSpec.ecc_support && (
            <Badge variant="outline">ECC</Badge>
          )}
        </div>
      </div>

      {/* Specifications Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MemoryStick className="h-5 w-5" />
            Specifications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <SpecField label="Capacity" value={`${ramSpec.capacity_gb}GB`} />
            <SpecField label="Type" value={ramSpec.type} />
            <SpecField
              label="Speed"
              value={ramSpec.speed_mhz ? `${ramSpec.speed_mhz} MHz` : null}
            />
            <SpecField label="Latency" value={ramSpec.latency} />
            <SpecField
              label="Voltage"
              value={ramSpec.voltage ? `${ramSpec.voltage}V` : null}
            />
            <SpecField label="Configuration" value={ramSpec.configuration} />
            <SpecField label="Manufacturer" value={ramSpec.manufacturer} />
            <SpecField label="Form Factor" value={ramSpec.form_factor} />
            <SpecField label="ECC Support" value={ramSpec.ecc_support} />
          </dl>
          {ramSpec.notes && (
            <div className="mt-6 pt-6 border-t">
              <dt className="text-sm text-muted-foreground mb-2">Notes</dt>
              <dd className="text-sm">{ramSpec.notes}</dd>
            </div>
          )}
        </CardContent>
      </Card>

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
              <MemoryStick className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                No listings currently use this RAM specification.
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
    </div>
  );
}
