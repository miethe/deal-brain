/**
 * CatalogTab Integration Example
 *
 * This file demonstrates how to integrate the CPUFilters component
 * with the CatalogTab component for client-side filtering.
 *
 * DO NOT USE THIS FILE DIRECTLY - it's a reference implementation.
 * Apply these patterns to the actual catalog-tab.tsx component.
 */

"use client";

import { useMemo } from "react";
import { useCPUs } from "@/hooks/use-cpus";
import { useFilters } from "@/stores/cpu-catalog-store";
import { CPUFilters, filterCPUs } from "./cpu-filters";
import type { CPURecord } from "@/types/cpus";

export function CatalogTabExample() {
  // Fetch CPUs with analytics data
  const { data: cpus = [], isLoading, error } = useCPUs(true);

  // Get current filter state from store
  const { filters } = useFilters();

  // Apply client-side filtering with memoization
  const filteredCPUs = useMemo(
    () => filterCPUs(cpus, filters),
    [cpus, filters]
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        <CPUFilters />
        <div className="flex items-center justify-center py-12">
          <div className="text-muted-foreground">Loading CPUs...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-4">
        <CPUFilters />
        <div className="flex items-center justify-center py-12">
          <div className="text-destructive">
            Error loading CPUs: {(error as Error).message}
          </div>
        </div>
      </div>
    );
  }

  // Empty state (no CPUs match filters)
  if (filteredCPUs.length === 0) {
    return (
      <div className="space-y-4">
        <CPUFilters />
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-muted-foreground">
            No CPUs match your current filters.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            Try adjusting your search criteria or clearing filters.
          </p>
        </div>
      </div>
    );
  }

  // Main content with filtered CPUs
  return (
    <div className="space-y-4">
      {/* Filter controls */}
      <CPUFilters />

      {/* Results count */}
      <div className="flex items-center justify-between px-2">
        <p className="text-sm text-muted-foreground">
          Showing {filteredCPUs.length} of {cpus.length} CPUs
        </p>
      </div>

      {/* CPU Grid/List (replace with actual view component) */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredCPUs.map((cpu: CPURecord) => (
          <div
            key={cpu.id}
            className="rounded-lg border p-4"
          >
            <h3 className="font-medium">{cpu.name}</h3>
            <p className="text-sm text-muted-foreground">
              {cpu.manufacturer} • {cpu.socket}
            </p>
            <p className="text-sm text-muted-foreground">
              {cpu.cores} cores • {cpu.tdp_w}W TDP
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Integration Steps for catalog-tab.tsx:
 *
 * 1. Import the CPUFilters component and filterCPUs function:
 *    ```tsx
 *    import { CPUFilters, filterCPUs } from "./cpu-filters";
 *    ```
 *
 * 2. Import useFilters hook from store:
 *    ```tsx
 *    import { useFilters } from "@/stores/cpu-catalog-store";
 *    ```
 *
 * 3. Get filter state in your component:
 *    ```tsx
 *    const { filters } = useFilters();
 *    ```
 *
 * 4. Apply client-side filtering with memoization:
 *    ```tsx
 *    const filteredCPUs = useMemo(
 *      () => filterCPUs(cpus, filters),
 *      [cpus, filters]
 *    );
 *    ```
 *
 * 5. Add the CPUFilters component above your view content:
 *    ```tsx
 *    return (
 *      <div className="space-y-4">
 *        <CPUFilters />
 *        <YourViewComponent cpus={filteredCPUs} />
 *      </div>
 *    );
 *    ```
 *
 * 6. Show filtered count for user feedback:
 *    ```tsx
 *    <p className="text-sm text-muted-foreground">
 *      Showing {filteredCPUs.length} of {cpus.length} CPUs
 *    </p>
 *    ```
 */
