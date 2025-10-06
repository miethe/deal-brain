"use client";

import { useMemo } from "react";
import { ListingRecord } from "@/types/listings";
import { ListingCard } from "./listing-card";
import { useFilters } from "@/stores/catalog-store";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface GridViewProps {
  listings: ListingRecord[];
  isLoading?: boolean;
  onAddListing?: () => void;
}

/**
 * Grid View Component
 *
 * Responsive grid layout for catalog view:
 * - Mobile: 1 column
 * - Tablet: 2 columns
 * - Desktop: 3 columns
 * - Large desktop: 4 columns
 *
 * Filters listings based on Zustand store state.
 */
export function GridView({ listings, isLoading, onAddListing }: GridViewProps) {
  const { filters } = useFilters();

  // Filter listings based on active filters
  const filteredListings = useMemo(() => {
    if (!listings) return [];

    return listings.filter((listing) => {
      // Search query filter
      if (filters.searchQuery) {
        const term = filters.searchQuery.toLowerCase();
        const searchableText = [
          listing.title,
          listing.cpu_name,
          listing.manufacturer,
          listing.series,
          listing.model_number,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        if (!searchableText.includes(term)) {
          return false;
        }
      }

      // Form factor filter
      if (filters.formFactor !== "all" && listing.form_factor !== filters.formFactor) {
        return false;
      }

      // Manufacturer filter
      if (filters.manufacturer !== "all" && listing.manufacturer !== filters.manufacturer) {
        return false;
      }

      // Price range filter
      if (listing.price_usd > filters.priceRange) {
        return false;
      }

      return true;
    });
  }, [listings, filters]);

  // Sort by adjusted $/MT (ascending - best value first)
  const sortedListings = useMemo(() => {
    return [...filteredListings].sort((a, b) => {
      const aMetric = a.dollar_per_cpu_mark_multi_adjusted ?? Infinity;
      const bMetric = b.dollar_per_cpu_mark_multi_adjusted ?? Infinity;
      return aMetric - bMetric;
    });
  }, [filteredListings]);

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="h-80 bg-muted animate-pulse rounded-lg"
          />
        ))}
      </div>
    );
  }

  // Empty state - no listings at all
  if (!listings || listings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 border-2 border-dashed border-muted-foreground/25 rounded-lg">
        <div className="text-center space-y-4">
          <h3 className="text-lg font-medium">No listings yet</h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Get started by adding your first listing to compare deals and find the best value.
          </p>
          {onAddListing && (
            <Button onClick={onAddListing}>
              <Plus className="h-4 w-4 mr-2" />
              Add Listing
            </Button>
          )}
        </div>
      </div>
    );
  }

  // Empty state - no results from filters
  if (sortedListings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 border-2 border-dashed border-muted-foreground/25 rounded-lg">
        <div className="text-center space-y-4">
          <h3 className="text-lg font-medium">No listings match your filters</h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Try adjusting your filters to see more results.
          </p>
        </div>
      </div>
    );
  }

  // Grid with listings
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {sortedListings.map((listing) => (
        <ListingCard key={listing.id} listing={listing} />
      ))}
    </div>
  );
}
