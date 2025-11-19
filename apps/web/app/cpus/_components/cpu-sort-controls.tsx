"use client";

import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { useSort, type SortField } from "@/stores/cpu-catalog-store";

/**
 * CPU Sort Controls Component
 *
 * Provides sorting controls for CPU catalog:
 * - Sort field dropdown (name, cores, threads, TDP, CPU marks, listing count, etc.)
 * - Sort direction toggle (ascending/descending)
 * - Visual indicators for current sort state
 *
 * Features:
 * - Persisted in Zustand store
 * - Server-side sorting via API
 * - Accessible keyboard navigation
 * - Clear visual feedback for sort direction
 */
export function CPUSortControls() {
  const { sort, setSort } = useSort();

  const sortFields: Array<{ value: SortField; label: string }> = [
    { value: 'name', label: 'Name' },
    { value: 'manufacturer', label: 'Manufacturer' },
    { value: 'cores', label: 'Cores' },
    { value: 'threads', label: 'Threads' },
    { value: 'tdp_w', label: 'TDP (Watts)' },
    { value: 'cpu_mark_multi', label: 'CPU Mark (Multi)' },
    { value: 'cpu_mark_single', label: 'CPU Mark (Single)' },
    { value: 'release_year', label: 'Release Year' },
    { value: 'listings_count', label: 'Listing Count' },
  ];

  const handleSortFieldChange = (value: SortField) => {
    setSort({ sortBy: value });
  };

  const toggleSortOrder = () => {
    setSort({ sortOrder: sort.sortOrder === 'asc' ? 'desc' : 'asc' });
  };

  const SortIcon = sort.sortOrder === 'asc' ? ArrowUp : ArrowDown;
  const sortOrderLabel = sort.sortOrder === 'asc' ? 'Ascending' : 'Descending';

  return (
    <div className="flex flex-wrap items-end gap-3">
      {/* Sort Field Dropdown */}
      <div className="flex-1 min-w-[200px] space-y-2">
        <Label htmlFor="sort-by">Sort By</Label>
        <Select
          value={sort.sortBy}
          onValueChange={handleSortFieldChange}
        >
          <SelectTrigger id="sort-by" className="w-full">
            <SelectValue placeholder="Sort by..." />
          </SelectTrigger>
          <SelectContent>
            {sortFields.map((field) => (
              <SelectItem key={field.value} value={field.value}>
                {field.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Sort Direction Toggle */}
      <Button
        variant="outline"
        size="default"
        onClick={toggleSortOrder}
        className="gap-2"
        aria-label={`Sort order: ${sortOrderLabel}. Click to toggle.`}
        title={sortOrderLabel}
      >
        <SortIcon className="h-4 w-4" />
        {sortOrderLabel}
      </Button>
    </div>
  );
}
