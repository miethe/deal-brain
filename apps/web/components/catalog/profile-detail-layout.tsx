"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ChevronRight, Target, BarChart3, Star, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";
import { EntityEditModal } from "@/components/entity/entity-edit-modal";
import { profileEditSchema, type ProfileEditFormData } from "@/lib/schemas/entity-schemas";
import { useUpdateProfile } from "@/hooks/use-entity-mutations";

interface Profile {
  id: number;
  name: string;
  description?: string | null;
  weights_json: Record<string, number>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
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

interface ProfileDetailLayoutProps {
  profile: Profile;
  listings: Listing[];
}

interface WeightRowProps {
  metric: string;
  weight: number;
}

function WeightRow({ metric, weight }: WeightRowProps) {
  const percentage = (weight * 100).toFixed(0);

  return (
    <div className="flex items-center justify-between py-3 border-b last:border-0">
      <div className="flex-1">
        <span className="font-medium">{formatMetricName(metric)}</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="w-48">
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="text-sm text-muted-foreground w-12 text-right">{percentage}%</span>
          </div>
        </div>
        <span className="text-sm font-semibold w-16 text-right">{weight.toFixed(2)}</span>
      </div>
    </div>
  );
}

function formatMetricName(metric: string): string {
  // Convert snake_case to Title Case
  return metric
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
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

export function ProfileDetailLayout({ profile, listings }: ProfileDetailLayoutProps) {
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const updateProfileMutation = useUpdateProfile(profile.id);

  const hasWeights = Object.keys(profile.weights_json).length > 0;
  const totalWeight = Object.values(profile.weights_json).reduce((sum, weight) => sum + weight, 0);

  const handleEditSubmit = async (data: ProfileEditFormData) => {
    await updateProfileMutation.mutateAsync(data);
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
        <span className="text-foreground font-medium">Scoring Profile</span>
      </nav>

      {/* Header with Edit button */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{profile.name}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {profile.description && (
              <p className="text-lg text-muted-foreground">{profile.description}</p>
            )}
            {profile.is_default && (
              <Badge variant="default" className="gap-1">
                <Star className="h-3 w-3 fill-current" />
                Default Profile
              </Badge>
            )}
          </div>
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

      {/* Profile Details Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Profile Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <dt className="text-sm text-muted-foreground">Name</dt>
              <dd className="text-base font-semibold">{profile.name}</dd>
            </div>
            {profile.description && (
              <div className="space-y-1 md:col-span-2">
                <dt className="text-sm text-muted-foreground">Description</dt>
                <dd className="text-base">{profile.description}</dd>
              </div>
            )}
            <div className="space-y-1">
              <dt className="text-sm text-muted-foreground">Status</dt>
              <dd className="text-base">
                {profile.is_default ? (
                  <Badge variant="default" className="gap-1">
                    <Star className="h-3 w-3 fill-current" />
                    Default Profile
                  </Badge>
                ) : (
                  <Badge variant="outline">Custom Profile</Badge>
                )}
              </dd>
            </div>
            <div className="space-y-1">
              <dt className="text-sm text-muted-foreground">Total Weight</dt>
              <dd className="text-base font-semibold">{totalWeight.toFixed(2)}</dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Scoring Weights Card */}
      {hasWeights && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Scoring Weights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {Object.entries(profile.weights_json)
                .sort(([, a], [, b]) => b - a)
                .map(([metric, weight]) => (
                  <WeightRow key={metric} metric={metric} weight={weight} />
                ))}
            </div>
            {totalWeight !== 1.0 && (
              <div className="mt-4 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-900">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  Note: Total weight is {totalWeight.toFixed(2)}. Typically weights should sum to 1.0 for normalized scoring.
                </p>
              </div>
            )}
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
              <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                No listings currently use this scoring profile.
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
        entityType="profile"
        entityId={profile.id}
        initialValues={{
          name: profile.name,
          description: profile.description,
          is_default: profile.is_default,
          weights_json: profile.weights_json,
        }}
        schema={profileEditSchema}
        onSubmit={handleEditSubmit}
        onClose={() => setIsEditModalOpen(false)}
        isOpen={isEditModalOpen}
      />
    </div>
  );
}
