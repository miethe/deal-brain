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
 * - Client-side filtering via cpu-filters
 * - Sorted by CPU Mark Multi (descending - highest performance first)
 * - Empty states for no CPUs and no filter results
 * - Loading skeletons during data fetch
 * - Memoized for performance optimization
 */
export function GridView({ cpus, isLoading }: GridViewProps) {
  const { filters } = useFilters();

  // Filter CPUs based on active filters
  const filteredCPUs = useMemo(() => {
    if (!cpus) return [];
    return filterCPUs(cpus, filters);
  }, [cpus, filters]);

  // Sort by CPU Mark Multi (descending - highest performance first)
  const sortedCPUs = useMemo(() => {
    return [...filteredCPUs].sort((a, b) => {
      const aValue = a.cpu_mark_multi ?? 0;
      const bValue = b.cpu_mark_multi ?? 0;
      return bValue - aValue;
    });
  }, [filteredCPUs]);

  // Check if any filters are active
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

  // Empty state - no results from filters
  if (sortedCPUs.length === 0 && hasActiveFilters) {
    return (
      <EmptyState
        icon={SearchX}
        heading="No CPUs match your filters"
        description="Try adjusting your filters to see more results, or clear all filters to start over."
      />
    );
  }

  // Grid with CPUs
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {sortedCPUs.map((cpu) => (
        <CPUCard key={cpu.id} cpu={cpu} />
      ))}
    </div>
  );
}
