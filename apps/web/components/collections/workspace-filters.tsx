"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import type { CollectionItem } from "@/types/collections";

export interface WorkspaceFilters {
  priceRange: [number, number];
  cpuFamily: string[];
  formFactor: string[];
  sortBy: "price" | "score" | "cpu_mark" | "added_date";
  sortOrder: "asc" | "desc";
}

interface WorkspaceFiltersProps {
  items: CollectionItem[];
  filters: WorkspaceFilters;
  onFiltersChange: (filters: WorkspaceFilters) => void;
}

/**
 * Workspace Filters
 *
 * Filter controls for collection workspace:
 * - Price range slider
 * - CPU family filter (multiselect)
 * - Form factor filter (checkboxes)
 * - Sort dropdown
 * - Clear filters button
 */
export function WorkspaceFiltersComponent({
  items,
  filters,
  onFiltersChange,
}: WorkspaceFiltersProps) {
  // Calculate min/max prices from items
  const prices = items.map((item) => item.listing.price_usd);
  const minPrice = Math.min(...prices, 0);
  const maxPrice = Math.max(...prices, 1000);

  // Get unique CPU families
  const cpuFamilies = Array.from(
    new Set(
      items
        .map((item) => {
          const cpuName = item.listing.cpu_name;
          if (!cpuName) return null;
          // Extract family (e.g., "Intel i5" from "Intel i5-9400")
          const match = cpuName.match(/^(Intel|AMD)\s+(\w+)/i);
          return match ? `${match[1]} ${match[2]}` : null;
        })
        .filter(Boolean)
    )
  ).sort();

  // Get unique form factors
  const formFactors = Array.from(
    new Set(
      items
        .map((item) => item.listing.form_factor)
        .filter(Boolean)
    )
  ).sort();

  const handleClearFilters = () => {
    onFiltersChange({
      priceRange: [minPrice, maxPrice],
      cpuFamily: [],
      formFactor: [],
      sortBy: "added_date",
      sortOrder: "desc",
    });
  };

  const hasActiveFilters =
    filters.priceRange[0] !== minPrice ||
    filters.priceRange[1] !== maxPrice ||
    filters.cpuFamily.length > 0 ||
    filters.formFactor.length > 0;

  return (
    <div className="border rounded-lg p-4 space-y-4 bg-muted/30">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-sm">Filters & Sort</h3>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearFilters}
            className="h-auto py-1 px-2 text-xs"
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Price Range */}
        <div className="space-y-2">
          <Label className="text-xs">
            Price: ${filters.priceRange[0]} - ${filters.priceRange[1]}
          </Label>
          <Slider
            min={minPrice}
            max={maxPrice}
            step={10}
            value={filters.priceRange}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, priceRange: value as [number, number] })
            }
            className="w-full"
          />
        </div>

        {/* CPU Family */}
        {cpuFamilies.length > 0 && (
          <div className="space-y-2">
            <Label className="text-xs">CPU Family</Label>
            <Select
              value={filters.cpuFamily[0] || "all"}
              onValueChange={(value) =>
                onFiltersChange({
                  ...filters,
                  cpuFamily: value === "all" ? [] : [value],
                })
              }
            >
              <SelectTrigger className="h-9">
                <SelectValue placeholder="All CPUs" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All CPUs</SelectItem>
                {cpuFamilies.map((family) => (
                  <SelectItem key={family} value={family}>
                    {family}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Form Factor */}
        {formFactors.length > 0 && (
          <div className="space-y-2">
            <Label className="text-xs">Form Factor</Label>
            <div className="flex flex-wrap gap-2">
              {formFactors.map((factor) => (
                <label
                  key={factor}
                  className="flex items-center gap-2 text-sm cursor-pointer"
                >
                  <Checkbox
                    checked={filters.formFactor.includes(factor)}
                    onCheckedChange={(checked) => {
                      const newFormFactors = checked
                        ? [...filters.formFactor, factor]
                        : filters.formFactor.filter((f) => f !== factor);
                      onFiltersChange({
                        ...filters,
                        formFactor: newFormFactors,
                      });
                    }}
                  />
                  <span className="text-xs">{factor}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Sort */}
        <div className="space-y-2">
          <Label className="text-xs">Sort By</Label>
          <div className="flex gap-2">
            <Select
              value={filters.sortBy}
              onValueChange={(value) =>
                onFiltersChange({
                  ...filters,
                  sortBy: value as WorkspaceFilters["sortBy"],
                })
              }
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="price">Price</SelectItem>
                <SelectItem value="score">Score</SelectItem>
                <SelectItem value="cpu_mark">CPU Mark</SelectItem>
                <SelectItem value="added_date">Added Date</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.sortOrder}
              onValueChange={(value) =>
                onFiltersChange({
                  ...filters,
                  sortOrder: value as "asc" | "desc",
                })
              }
            >
              <SelectTrigger className="h-9 w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="asc">Asc</SelectItem>
                <SelectItem value="desc">Desc</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  );
}
