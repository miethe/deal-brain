"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ChevronRight, Pencil, Plug } from "lucide-react";
import { cn } from "@/lib/utils";
import { EntityEditModal } from "@/components/entity/entity-edit-modal";
import { portsProfileEditSchema, type PortsProfileEditFormData } from "@/lib/schemas/entity-schemas";
import { useUpdatePortsProfile } from "@/hooks/use-entity-mutations";

interface Port {
  id: number;
  type: string;
  count: number;
  spec_notes?: string | null;
}

interface PortsProfile {
  id: number;
  name: string;
  description?: string | null;
  attributes?: Record<string, any>;
  ports: Port[];
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

interface PortsProfileDetailLayoutProps {
  profile: PortsProfile;
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

export function PortsProfileDetailLayout({ profile, listings }: PortsProfileDetailLayoutProps) {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const updatePortsProfileMutation = useUpdatePortsProfile(profile.id);

  const handleEditSubmit = async (data: PortsProfileEditFormData) => {
    await updatePortsProfileMutation.mutateAsync(data);
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
        <span className="text-foreground font-medium">Ports Profile Details</span>
      </nav>

      {/* Header with Edit button */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{profile.name}</h1>
          {profile.description && (
            <p className="text-lg text-muted-foreground mt-2">{profile.description}</p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsEditModalOpen(true)}
          aria-label={`Edit ${profile.name}`}
          className="flex-shrink-0"
        >
          <Pencil className="h-4 w-4 mr-2" />
          Edit
        </Button>
      </div>

      {/* Specifications Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plug className="h-5 w-5" />
            Specifications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 gap-6">
            <SpecField label="Name" value={profile.name} />
            <SpecField label="Description" value={profile.description} />
          </dl>
          {profile.attributes && Object.keys(profile.attributes).length > 0 && (
            <div className="mt-6 pt-6 border-t">
              <dt className="text-sm text-muted-foreground mb-4">Custom Attributes</dt>
              <dl className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(profile.attributes).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <dt className="text-xs text-muted-foreground">{key}</dt>
                    <dd className="text-sm font-medium">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Ports Card */}
      {profile.ports && profile.ports.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plug className="h-5 w-5" />
              Ports ({profile.ports.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Type
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Count
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">
                      Specifications
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {profile.ports.map((port) => (
                    <tr key={port.id} className="border-b last:border-0 hover:bg-accent transition-colors">
                      <td className="py-3 px-4 font-medium">{port.type}</td>
                      <td className="py-3 px-4">
                        <Badge variant="secondary">{port.count}</Badge>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {port.spec_notes || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
              <Plug className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                No listings currently use this ports profile.
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
        entityType="ports-profile"
        entityId={profile.id}
        initialValues={{
          name: profile.name,
          description: profile.description,
          attributes: profile.attributes,
        }}
        schema={portsProfileEditSchema}
        onSubmit={handleEditSubmit}
        onClose={() => setIsEditModalOpen(false)}
        isOpen={isEditModalOpen}
      />
    </div>
  );
}
