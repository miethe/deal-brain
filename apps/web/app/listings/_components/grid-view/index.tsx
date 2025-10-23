"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { ListingRecord } from "@/types/listings";
import { ListingCard } from "./listing-card";
import { ListingCardSkeleton } from "./listing-card-skeleton";
import { NoListingsEmptyState, NoFilterResultsEmptyState } from "@/components/ui/empty-state";
import { useFilters } from "@/stores/catalog-store";

interface GridViewProps {
  listings: ListingRecord[];
  isLoading?: boolean;
  onAddListing?: () => void;
  highlightedId?: number | null;
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
export function GridView({ listings, isLoading, onAddListing, highlightedId }: GridViewProps) {
  const { filters } = useFilters();
  const router = useRouter();
  const highlightedRef = useRef<HTMLDivElement>(null);

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

  // Handle highlighting and scrolling
  useEffect(() => {
    if (highlightedId && highlightedRef.current) {
      // Scroll into view with smooth behavior
      highlightedRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });

      // Focus for accessibility
      highlightedRef.current.focus();

      // Clear highlight param after 2 seconds
      const timer = setTimeout(() => {
        const params = new URLSearchParams(window.location.search);
        params.delete('highlight');
        const newSearch = params.toString();
        router.replace(
          `${window.location.pathname}${newSearch ? `?${newSearch}` : ''}`,
          { scroll: false }
        );
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [highlightedId, router]);

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <ListingCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Empty state - no listings at all
  if (!listings || listings.length === 0) {
    return <NoListingsEmptyState onAddListing={onAddListing} />;
  }

  // Empty state - no results from filters
  if (sortedListings.length === 0) {
    return <NoFilterResultsEmptyState />;
  }

  // Grid with listings
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {sortedListings.map((listing) => {
        const isHighlighted = highlightedId === listing.id;
        return (
          <div
            key={listing.id}
            ref={isHighlighted ? highlightedRef : null}
            data-highlighted={isHighlighted}
            tabIndex={isHighlighted ? -1 : undefined}
            aria-label={isHighlighted ? "Newly created listing" : undefined}
            className="outline-none"
          >
            <ListingCard listing={listing} />
          </div>
        );
      })}
    </div>
  );
}
