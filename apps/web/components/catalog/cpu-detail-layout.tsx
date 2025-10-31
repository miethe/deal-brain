"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { ChevronRight, Cpu, TrendingUp, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface CPU {
  id: number;
  model: string;
  manufacturer: string;
  generation?: string | null;
  cores?: number | null;
  threads?: number | null;
  base_clock_ghz?: number | null;
  boost_clock_ghz?: number | null;
  tdp_watts?: number | null;
  cpu_mark?: number | null;
  single_thread_rating?: number | null;
  igpu_mark?: number | null;
  socket?: string | null;
  igpu_model?: string | null;
  release_year?: number | null;
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

interface CPUDetailLayoutProps {
  cpu: CPU;
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

export function CPUDetailLayout({ cpu, listings }: CPUDetailLayoutProps) {
  const hasSpecs = cpu.cores || cpu.threads || cpu.base_clock_ghz || cpu.boost_clock_ghz || cpu.tdp_watts || cpu.socket || cpu.generation || cpu.igpu_model || cpu.release_year;
  const hasBenchmarks = cpu.cpu_mark || cpu.single_thread_rating || cpu.igpu_mark;

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
        <span className="text-foreground font-medium">CPU Details</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{cpu.model}</h1>
        <div className="flex flex-wrap items-center gap-2 mt-2">
          <p className="text-lg text-muted-foreground">{cpu.manufacturer}</p>
          {cpu.generation && (
            <Badge variant="secondary">{cpu.generation}</Badge>
          )}
          {cpu.release_year && (
            <Badge variant="outline">{cpu.release_year}</Badge>
          )}
        </div>
      </div>

      {/* Specifications Card */}
      {hasSpecs && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              Specifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <SpecField label="Cores" value={cpu.cores} />
              <SpecField label="Threads" value={cpu.threads} />
              <SpecField
                label="Base Clock"
                value={cpu.base_clock_ghz ? `${cpu.base_clock_ghz} GHz` : null}
              />
              <SpecField
                label="Boost Clock"
                value={cpu.boost_clock_ghz ? `${cpu.boost_clock_ghz} GHz` : null}
              />
              <SpecField
                label="TDP"
                value={cpu.tdp_watts ? `${cpu.tdp_watts}W` : null}
              />
              <SpecField label="Socket" value={cpu.socket} />
              <SpecField label="Integrated GPU" value={cpu.igpu_model} />
              <SpecField label="Generation" value={cpu.generation} />
              <SpecField label="Release Year" value={cpu.release_year} />
            </dl>
            {cpu.notes && (
              <div className="mt-6 pt-6 border-t">
                <dt className="text-sm text-muted-foreground mb-2">Notes</dt>
                <dd className="text-sm">{cpu.notes}</dd>
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
              {cpu.cpu_mark && (
                <MetricCard
                  label="CPU Mark (Multi-core)"
                  value={cpu.cpu_mark}
                  icon={<Cpu className="h-4 w-4" />}
                  description="PassMark multi-threaded performance score"
                />
              )}
              {cpu.single_thread_rating && (
                <MetricCard
                  label="Single Thread Rating"
                  value={cpu.single_thread_rating}
                  icon={<Zap className="h-4 w-4" />}
                  description="PassMark single-threaded performance score"
                />
              )}
              {cpu.igpu_mark && (
                <MetricCard
                  label="iGPU Mark"
                  value={cpu.igpu_mark}
                  icon={<TrendingUp className="h-4 w-4" />}
                  description="Integrated GPU performance score"
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
              <Cpu className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                No listings currently use this CPU.
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
