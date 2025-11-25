"use client";

import { useMemo } from "react";
import { CPURecord } from "@/types/cpus";
import { CPUCard } from "./cpu-card";
import { CPUCardSkeleton } from "./cpu-card-skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { PackageOpen, SearchX } from "lucide-react";
import { useFilters } from "@/stores/cpu-catalog-store";
import { filterCPUs } from "../cpu-filters";

interface GridViewProps {
  cpus: CPURecord[];
  isLoading?: boolean;
}

/**
 * Grid View Component for CPU Catalog
 *
 * Responsive grid layout for CPU catalog view:
 * - Mobile: 1 column
 * - Tablet: 2 columns
 * - Desktop: 3 columns
 * - Large desktop: 4 columns
 *
 * Features:
 * - Client-side filtering for search, manufacturer, socket, cores, TDP, year, iGPU, PassMark
 * - Server-side sorting (configured via sort controls)
 * - Server-side filtering for "only with listings" (performance optimization)
 * - Empty states for no CPUs and no filter results
 * - Loading skeletons during data fetch
 * - Memoized for performance optimization
 *
 * Note: CPUs are pre-sorted by the API based on sort controls.
 * Additional client-side filters are applied without re-sorting.
 */
export function GridView({ cpus, isLoading }: GridViewProps) {
  const { filters } = useFilters();

  // Filter CPUs based on active filters (client-side)
  // Note: "activeListingsOnly" filter is applied server-side for performance
  const filteredCPUs = useMemo(() => {
    if (!cpus) return [];
    return filterCPUs(cpus, filters);
  }, [cpus, filters]);

  // Check if any client-side filters are active
  const hasActiveFilters = useMemo(() => {
    return (
      filters.searchQuery !== "" ||
      filters.manufacturer.length > 0 ||
      filters.socket.length > 0 ||
      filters.coreRange[0] !== 2 ||
      filters.coreRange[1] !== 64 ||
      filters.tdpRange[0] !== 15 ||
      filters.tdpRange[1] !== 280 ||
      filters.yearRange !== null ||
      filters.hasIGPU !== null ||
      filters.minPassMark !== null ||
      filters.performanceRating !== null
    );
  }, [filters]);

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <CPUCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Empty state - no CPUs at all
  if (!cpus || cpus.length === 0) {
    return (
      <EmptyState
        icon={PackageOpen}
        heading="No CPUs in catalog"
        description="The CPU catalog is empty. Import CPU data to get started."
      />
    );
  }

  // Empty state - no results from client-side filters
  if (filteredCPUs.length === 0 && hasActiveFilters) {
    return (
      <EmptyState
        icon={SearchX}
        heading="No CPUs match your filters"
        description="Try adjusting your filters to see more results, or clear all filters to start over."
      />
    );
  }

  // Empty state - no results when "only with listings" server filter is active
  if (filteredCPUs.length === 0 && filters.activeListingsOnly) {
    return (
      <EmptyState
        icon={PackageOpen}
        heading="No CPUs with active listings"
        description="There are no CPUs with active listings at the moment. Try disabling the 'Show Only CPUs with Active Listings' filter."
      />
    );
  }

  // Grid with CPUs (pre-sorted by API)
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {filteredCPUs.map((cpu) => (
        <CPUCard key={cpu.id} cpu={cpu} />
      ))}
    </div>
  );
}
