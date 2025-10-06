"use client";

import { memo } from "react";
import { X, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { useFilters } from "@/stores/catalog-store";
import { useDebouncedCallback } from "use-debounce";

/**
 * Shared Filters Component
 *
 * Sticky filter bar that works across all catalog views.
 * Filters are synchronized with Zustand store and URL params.
 */

// TODO: These should be fetched from API or derived from listings data
const FORM_FACTORS = [
  "all",
  "Mini-PC",
  "Laptop",
  "Desktop",
  "NUC",
  "SFF",
  "Stick PC",
  "Other",
];

const MANUFACTURERS = [
  "all",
  "ASUS",
  "Intel",
  "Dell",
  "HP",
  "Lenovo",
  "MSI",
  "Gigabyte",
  "Other",
];

export const ListingsFilters = memo(function ListingsFilters() {
  const { filters, setFilters, clearFilters } = useFilters();

  // Debounce search input to avoid excessive store updates
  const debouncedSearchUpdate = useDebouncedCallback((value: string) => {
    setFilters({ searchQuery: value });
  }, 200);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Update local input immediately, debounce store update
    debouncedSearchUpdate(e.target.value);
  };

  const handleClearFilters = () => {
    clearFilters();
    // Reset local search input
    const searchInput = document.querySelector<HTMLInputElement>('input[type="text"]');
    if (searchInput) {
      searchInput.value = '';
    }
  };

  const hasActiveFilters =
    filters.searchQuery ||
    filters.formFactor !== "all" ||
    filters.manufacturer !== "all" ||
    filters.priceRange !== 10000;

  return (
    <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
      <div className="flex flex-col sm:flex-row gap-4 p-4">
        {/* Search Input */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by title, CPU, or description..."
              defaultValue={filters.searchQuery}
              onChange={handleSearchChange}
              className="pl-9"
            />
          </div>
        </div>

        {/* Form Factor Dropdown */}
        <div className="w-full sm:w-[180px]">
          <Select
            value={filters.formFactor}
            onValueChange={(value) => setFilters({ formFactor: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Form Factor" />
            </SelectTrigger>
            <SelectContent>
              {FORM_FACTORS.map((factor) => (
                <SelectItem key={factor} value={factor}>
                  {factor === "all" ? "All Form Factors" : factor}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Manufacturer Dropdown */}
        <div className="w-full sm:w-[180px]">
          <Select
            value={filters.manufacturer}
            onValueChange={(value) => setFilters({ manufacturer: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Manufacturer" />
            </SelectTrigger>
            <SelectContent>
              {MANUFACTURERS.map((manufacturer) => (
                <SelectItem key={manufacturer} value={manufacturer}>
                  {manufacturer === "all" ? "All Manufacturers" : manufacturer}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Price Range Slider */}
        <div className="w-full sm:w-[200px] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Max Price</span>
            <span className="text-sm font-medium">
              ${filters.priceRange.toLocaleString()}
            </span>
          </div>
          <Slider
            value={[filters.priceRange]}
            onValueChange={(value) => setFilters({ priceRange: value[0] })}
            min={0}
            max={10000}
            step={100}
            className="cursor-pointer"
          />
        </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearFilters}
              className="h-10"
            >
              <X className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        )}
      </div>
    </div>
  );
});
