"use client";

import { useEffect, useState } from "react";
import { useDebouncedCallback } from "use-debounce";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useFilters } from "@/stores/cpu-catalog-store";
import { useCPUStatistics } from "@/hooks/use-cpus";

/**
 * CPU Filters Component
 *
 * Comprehensive filter controls for CPU catalog with client-side filtering.
 * Includes search, manufacturer, socket, cores, TDP, release year, iGPU,
 * performance rating, and minimum PassMark filters.
 *
 * Features:
 * - Debounced search input (200ms)
 * - Dynamic filter options from API statistics
 * - Active filter count badge
 * - Clear all filters button
 * - Responsive grid layout
 * - Integration with cpu-catalog-store for state management
 */
export function CPUFilters() {
  const { filters, setFilters, clearFilters } = useFilters();
  const { data: statistics } = useCPUStatistics();

  // Local search state for debouncing
  const [searchValue, setSearchValue] = useState(filters.searchQuery);

  // Debounced search update to avoid excessive store updates
  const debouncedSearchUpdate = useDebouncedCallback((value: string) => {
    setFilters({ searchQuery: value });
  }, 200);

  // Sync local search with store on mount
  useEffect(() => {
    setSearchValue(filters.searchQuery);
  }, [filters.searchQuery]);

  // Count active filters for badge display
  const activeFilterCount = [
    filters.searchQuery !== "",
    filters.manufacturer.length > 0,
    filters.socket.length > 0,
    filters.coreRange[0] !== 2 || filters.coreRange[1] !== 64,
    filters.tdpRange[0] !== 15 || filters.tdpRange[1] !== 280,
    filters.yearRange !== null,
    filters.hasIGPU !== null,
    filters.minPassMark !== null,
    filters.performanceRating !== null,
    !filters.activeListingsOnly, // Count as active when DISABLED (since default is true)
  ].filter(Boolean).length;

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    debouncedSearchUpdate(value);
  };

  // Handle search clear
  const handleSearchClear = () => {
    setSearchValue("");
    setFilters({ searchQuery: "" });
  };

  // Handle clear all filters
  const handleClearAll = () => {
    clearFilters();
    setSearchValue("");
  };

  return (
    <div className="sticky top-0 z-10 space-y-4 rounded-lg border bg-background/95 p-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Header with Clear All button */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Filters</h3>
        {activeFilterCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearAll}
            className="h-8 px-2 lg:px-3"
          >
            Clear all
            <Badge variant="secondary" className="ml-2">
              {activeFilterCount}
            </Badge>
          </Button>
        )}
      </div>

      {/* Filter Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {/* Search Input */}
        <div className="space-y-2">
          <Label htmlFor="search">Search</Label>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              id="search"
              placeholder="CPU name..."
              value={searchValue}
              onChange={handleSearchChange}
              className="pl-8"
            />
            {searchValue && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1 h-7 w-7 p-0"
                onClick={handleSearchClear}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        {/* Manufacturer Dropdown */}
        <div className="space-y-2">
          <Label htmlFor="manufacturer">Manufacturer</Label>
          <Select
            value={filters.manufacturer[0] || "all"}
            onValueChange={(value) =>
              setFilters({
                manufacturer: value === "all" ? [] : [value],
              })
            }
          >
            <SelectTrigger id="manufacturer">
              <SelectValue placeholder="All manufacturers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {statistics?.manufacturers.map((mfr) => (
                <SelectItem key={mfr} value={mfr}>
                  {mfr}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Socket Dropdown */}
        <div className="space-y-2">
          <Label htmlFor="socket">Socket</Label>
          <Select
            value={filters.socket[0] || "all"}
            onValueChange={(value) =>
              setFilters({
                socket: value === "all" ? [] : [value],
              })
            }
          >
            <SelectTrigger id="socket">
              <SelectValue placeholder="All sockets" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {statistics?.sockets.map((socket) => (
                <SelectItem key={socket} value={socket}>
                  {socket}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Performance Rating */}
        <div className="space-y-2">
          <Label htmlFor="performance">Performance</Label>
          <Select
            value={filters.performanceRating || "all"}
            onValueChange={(value) =>
              setFilters({
                performanceRating: value === "all" ? null : value,
              })
            }
          >
            <SelectTrigger id="performance">
              <SelectValue placeholder="All ratings" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="excellent">Excellent</SelectItem>
              <SelectItem value="good">Good</SelectItem>
              <SelectItem value="fair">Fair</SelectItem>
              <SelectItem value="poor">Poor</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Cores Range Slider */}
        <div className="space-y-2">
          <Label>
            Cores: {filters.coreRange[0]}-{filters.coreRange[1]}
          </Label>
          <Slider
            value={filters.coreRange}
            onValueChange={(value) =>
              setFilters({ coreRange: value as [number, number] })
            }
            min={statistics?.core_range?.[0] ?? 2}
            max={statistics?.core_range?.[1] ?? 64}
            step={2}
            className="pt-2"
          />
        </div>

        {/* TDP Range Slider */}
        <div className="space-y-2">
          <Label>
            TDP: {filters.tdpRange[0]}-{filters.tdpRange[1]}W
          </Label>
          <Slider
            value={filters.tdpRange}
            onValueChange={(value) =>
              setFilters({ tdpRange: value as [number, number] })
            }
            min={statistics?.tdp_range?.[0] ?? 15}
            max={statistics?.tdp_range?.[1] ?? 280}
            step={5}
            className="pt-2"
          />
        </div>

        {/* Year Range Slider */}
        {statistics?.year_range && (
          <div className="space-y-2">
            <Label>
              Year:{" "}
              {filters.yearRange
                ? `${filters.yearRange[0]}-${filters.yearRange[1]}`
                : "All"}
            </Label>
            <Slider
              value={filters.yearRange || statistics.year_range}
              onValueChange={(value) =>
                setFilters({ yearRange: value as [number, number] })
              }
              min={statistics.year_range[0]}
              max={statistics.year_range[1]}
              step={1}
              className="pt-2"
            />
          </div>
        )}

        {/* Has iGPU Checkbox */}
        <div className="flex items-center space-x-2 pt-6">
          <Checkbox
            id="igpu"
            checked={filters.hasIGPU === true}
            onCheckedChange={(checked) =>
              setFilters({ hasIGPU: checked ? true : null })
            }
          />
          <Label htmlFor="igpu" className="cursor-pointer">
            Has Integrated GPU
          </Label>
        </div>

        {/* Active Listings Only Checkbox */}
        <div className="flex items-center space-x-2 pt-6">
          <Checkbox
            id="activeListings"
            checked={filters.activeListingsOnly}
            onCheckedChange={(checked) =>
              setFilters({ activeListingsOnly: checked === true })
            }
          />
          <Label htmlFor="activeListings" className="cursor-pointer text-sm font-medium">
            Show Only CPUs with Active Listings
          </Label>
        </div>

        {/* Min PassMark Input */}
        <div className="space-y-2">
          <Label htmlFor="minMark">Min PassMark</Label>
          <Input
            id="minMark"
            type="number"
            placeholder="e.g., 10000"
            value={filters.minPassMark ?? ""}
            onChange={(e) =>
              setFilters({
                minPassMark: e.target.value ? Number(e.target.value) : null,
              })
            }
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Client-side filtering function for CPUs
 *
 * Filters the CPU array based on active filter state.
 * This function should be memoized in the consuming component
 * to avoid unnecessary recalculations.
 *
 * @param cpus - Array of CPU records to filter
 * @param filters - Current filter state
 * @returns Filtered array of CPU records
 *
 * @example
 * ```tsx
 * import { useMemo } from 'react';
 * import { useCPUs } from '@/hooks/use-cpus';
 * import { useFilters } from '@/stores/cpu-catalog-store';
 * import { filterCPUs } from './cpu-filters';
 *
 * export function CatalogTab() {
 *   const { data: cpus = [] } = useCPUs(true);
 *   const { filters } = useFilters();
 *
 *   const filteredCPUs = useMemo(
 *     () => filterCPUs(cpus, filters),
 *     [cpus, filters]
 *   );
 *
 *   return <CPUTable cpus={filteredCPUs} />;
 * }
 * ```
 */
export function filterCPUs(
  cpus: any[], // CPURecord type from @/types/cpus
  filters: {
    searchQuery: string;
    manufacturer: string[];
    socket: string[];
    coreRange: [number, number];
    tdpRange: [number, number];
    yearRange: [number, number] | null;
    hasIGPU: boolean | null;
    minPassMark: number | null;
    performanceRating: string | null;
    activeListingsOnly: boolean;
  }
): any[] {
  return cpus.filter((cpu) => {
    // Search query (CPU name) - case insensitive
    if (
      filters.searchQuery &&
      !cpu.name.toLowerCase().includes(filters.searchQuery.toLowerCase())
    ) {
      return false;
    }

    // Manufacturer filter
    if (
      filters.manufacturer.length > 0 &&
      !filters.manufacturer.includes(cpu.manufacturer)
    ) {
      return false;
    }

    // Socket filter
    if (
      filters.socket.length > 0 &&
      (!cpu.socket || !filters.socket.includes(cpu.socket))
    ) {
      return false;
    }

    // Cores range filter
    if (cpu.cores !== null) {
      if (cpu.cores < filters.coreRange[0] || cpu.cores > filters.coreRange[1]) {
        return false;
      }
    }

    // TDP range filter
    if (cpu.tdp_w !== null) {
      if (cpu.tdp_w < filters.tdpRange[0] || cpu.tdp_w > filters.tdpRange[1]) {
        return false;
      }
    }

    // Year range filter
    if (filters.yearRange && cpu.release_year) {
      if (
        cpu.release_year < filters.yearRange[0] ||
        cpu.release_year > filters.yearRange[1]
      ) {
        return false;
      }
    }

    // Has iGPU filter
    if (filters.hasIGPU === true && !cpu.igpu_model) {
      return false;
    }

    // Min PassMark filter (checks both single and multi-thread)
    if (filters.minPassMark) {
      const hasSufficientMark =
        (cpu.cpu_mark_single && cpu.cpu_mark_single >= filters.minPassMark) ||
        (cpu.cpu_mark_multi && cpu.cpu_mark_multi >= filters.minPassMark);
      if (!hasSufficientMark) {
        return false;
      }
    }

    // Performance rating filter
    if (
      filters.performanceRating &&
      cpu.performance_value_rating !== filters.performanceRating
    ) {
      return false;
    }

    // Active listings filter - show only CPUs with active listings when enabled
    if (filters.activeListingsOnly && (!cpu.listings_count || cpu.listings_count === 0)) {
      return false;
    }

    return true;
  });
}
