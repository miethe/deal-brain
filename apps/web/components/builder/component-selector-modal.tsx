"use client";

import { useState, useMemo, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus } from "lucide-react";
import { Card } from "@/components/ui/card";

/**
 * Generic component item for selection
 */
export interface ComponentItem {
  id: number;
  name: string;
  price?: number;
  specs?: string;
  manufacturer?: string;
  metadata?: Record<string, unknown>;
}

export interface ComponentSelectorModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  componentType: string;
  components: ComponentItem[];
  onSelect: (component: ComponentItem) => void;
  isLoading?: boolean;
}

type SortOption =
  | "name-asc"
  | "name-desc"
  | "price-asc"
  | "price-desc"
  | "cpu-mark-multi-asc"
  | "cpu-mark-multi-desc"
  | "cpu-mark-single-asc"
  | "cpu-mark-single-desc"
  | "gpu-mark-asc"
  | "gpu-mark-desc"
  | "ram-speed-asc"
  | "ram-speed-desc"
  | "ram-capacity-asc"
  | "ram-capacity-desc"
  | "storage-capacity-asc"
  | "storage-capacity-desc"
  | "storage-tier-asc"
  | "storage-tier-desc";

interface FilterState {
  manufacturers: string[];
  priceMin?: number;
  priceMax?: number;
  cpuCores: string[];
  gpuTiers: string[];
  ramGenerations: string[];
  ramCapacities: string[];
  storageInterfaces: string[];
  storageMediums: string[];
}

/**
 * Get creation route for component type
 */
function getCreateRoute(componentType: string): string | null {
  const type = componentType.toLowerCase();

  if (type.includes("cpu")) {
    return "/catalog/cpus/new";
  }
  if (type.includes("gpu")) {
    return "/catalog/gpus/new";
  }
  if (type.includes("ram") || type.includes("memory")) {
    return "/catalog/ram-specs/new";
  }
  if (type.includes("storage")) {
    return "/catalog/storage-profiles/new";
  }

  return null;
}

/**
 * Get friendly component type name
 */
function getComponentTypeName(componentType: string): string {
  const type = componentType.toLowerCase();

  if (type.includes("cpu")) return "CPU";
  if (type.includes("gpu")) return "GPU";
  if (type.includes("ram") || type.includes("memory")) return "RAM Spec";
  if (type.includes("storage")) return "Storage Profile";

  return componentType;
}

/**
 * Modal for searching and selecting components from catalog
 */
export function ComponentSelectorModal({
  open,
  onOpenChange,
  title,
  componentType,
  components,
  onSelect,
  isLoading = false,
}: ComponentSelectorModalProps) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("name-asc");
  const [filters, setFilters] = useState<FilterState>({
    manufacturers: [],
    cpuCores: [],
    gpuTiers: [],
    ramGenerations: [],
    ramCapacities: [],
    storageInterfaces: [],
    storageMediums: [],
  });

  // Reset filters and search when modal closes
  useEffect(() => {
    if (!open) {
      setSearch("");
      setSortBy("name-asc");
      setFilters({
        manufacturers: [],
        cpuCores: [],
        gpuTiers: [],
        ramGenerations: [],
        ramCapacities: [],
        storageInterfaces: [],
        storageMediums: [],
      });
    }
  }, [open]);

  // Extract unique manufacturers from components
  const availableManufacturers = useMemo(() => {
    const manufacturers = new Set<string>();
    components.forEach((c) => {
      if (c.manufacturer) manufacturers.add(c.manufacturer);
    });
    return Array.from(manufacturers).sort();
  }, [components]);

  // Extract filter options based on component type
  const filterOptions = useMemo(() => {
    const type = componentType.toLowerCase();

    if (type.includes("cpu")) {
      // Extract core counts from metadata
      const cores = new Set<string>();
      components.forEach((c) => {
        const coreCount = c.metadata?.cores as number;
        if (coreCount) {
          if (coreCount >= 16) cores.add("16+");
          else cores.add(String(coreCount));
        }
      });
      return { cpuCores: Array.from(cores).sort((a, b) => {
        const aNum = a === "16+" ? 16 : parseInt(a);
        const bNum = b === "16+" ? 16 : parseInt(b);
        return aNum - bNum;
      }) };
    }

    if (type.includes("gpu")) {
      // GPU tiers based on GPU Mark ranges
      return {
        gpuTiers: ["Entry (0-5k)", "Mid (5k-15k)", "High (15k-25k)", "Enthusiast (25k+)"]
      };
    }

    if (type.includes("ram") || type.includes("memory")) {
      const generations = new Set<string>();
      const capacities = new Set<string>();
      components.forEach((c) => {
        const gen = c.metadata?.generation as string;
        const capacity = c.metadata?.capacity_gb as number;
        if (gen) generations.add(gen);
        if (capacity) capacities.add(`${capacity}GB`);
      });
      return {
        ramGenerations: Array.from(generations).sort(),
        ramCapacities: Array.from(capacities).sort((a, b) => {
          const aNum = parseInt(a);
          const bNum = parseInt(b);
          return aNum - bNum;
        })
      };
    }

    if (type.includes("storage")) {
      const interfaces = new Set<string>();
      const mediums = new Set<string>();
      components.forEach((c) => {
        const iface = c.metadata?.interface as string;
        const medium = c.metadata?.medium as string;
        if (iface) interfaces.add(iface);
        if (medium) mediums.add(medium);
      });
      return {
        storageInterfaces: Array.from(interfaces).sort(),
        storageMediums: Array.from(mediums).sort()
      };
    }

    return {};
  }, [components, componentType]);

  // Filter and sort components
  const filteredAndSortedComponents = useMemo(() => {
    let filtered = components;

    // Apply search filter
    if (search.trim()) {
      const query = search.toLowerCase();
      filtered = filtered.filter((component) => {
        const nameMatch = component.name.toLowerCase().includes(query);
        const specsMatch = component.specs?.toLowerCase().includes(query);
        const manufacturerMatch = component.manufacturer?.toLowerCase().includes(query);
        return nameMatch || specsMatch || manufacturerMatch;
      });
    }

    // Apply manufacturer filter
    if (filters.manufacturers.length > 0) {
      filtered = filtered.filter((c) =>
        c.manufacturer && filters.manufacturers.includes(c.manufacturer)
      );
    }

    // Apply price range filter
    if (filters.priceMin !== undefined) {
      filtered = filtered.filter((c) =>
        c.price !== undefined && c.price >= filters.priceMin!
      );
    }
    if (filters.priceMax !== undefined) {
      filtered = filtered.filter((c) =>
        c.price !== undefined && c.price <= filters.priceMax!
      );
    }

    // Apply CPU core count filter
    if (filters.cpuCores.length > 0) {
      filtered = filtered.filter((c) => {
        const cores = c.metadata?.cores as number;
        if (!cores) return false;
        return filters.cpuCores.some((filter) => {
          if (filter === "16+") return cores >= 16;
          return cores === parseInt(filter);
        });
      });
    }

    // Apply GPU tier filter
    if (filters.gpuTiers.length > 0) {
      filtered = filtered.filter((c) => {
        const gpuMark = c.metadata?.gpu_mark as number;
        if (gpuMark === undefined) return false;
        return filters.gpuTiers.some((tier) => {
          if (tier.startsWith("Entry")) return gpuMark < 5000;
          if (tier.startsWith("Mid")) return gpuMark >= 5000 && gpuMark < 15000;
          if (tier.startsWith("High")) return gpuMark >= 15000 && gpuMark < 25000;
          if (tier.startsWith("Enthusiast")) return gpuMark >= 25000;
          return false;
        });
      });
    }

    // Apply RAM generation filter
    if (filters.ramGenerations.length > 0) {
      filtered = filtered.filter((c) => {
        const gen = c.metadata?.generation as string;
        return gen && filters.ramGenerations.includes(gen);
      });
    }

    // Apply RAM capacity filter
    if (filters.ramCapacities.length > 0) {
      filtered = filtered.filter((c) => {
        const capacity = c.metadata?.capacity_gb as number;
        return capacity && filters.ramCapacities.includes(`${capacity}GB`);
      });
    }

    // Apply storage interface filter
    if (filters.storageInterfaces.length > 0) {
      filtered = filtered.filter((c) => {
        const iface = c.metadata?.interface as string;
        return iface && filters.storageInterfaces.includes(iface);
      });
    }

    // Apply storage medium filter
    if (filters.storageMediums.length > 0) {
      filtered = filtered.filter((c) => {
        const medium = c.metadata?.medium as string;
        return medium && filters.storageMediums.includes(medium);
      });
    }

    // Sort components
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case "name-asc":
          return a.name.localeCompare(b.name);
        case "name-desc":
          return b.name.localeCompare(a.name);
        case "price-asc":
          if (a.price === undefined) return 1;
          if (b.price === undefined) return -1;
          return a.price - b.price;
        case "price-desc":
          if (a.price === undefined) return 1;
          if (b.price === undefined) return -1;
          return b.price - a.price;
        case "cpu-mark-multi-asc":
          return (a.metadata?.cpu_mark as number || 0) - (b.metadata?.cpu_mark as number || 0);
        case "cpu-mark-multi-desc":
          return (b.metadata?.cpu_mark as number || 0) - (a.metadata?.cpu_mark as number || 0);
        case "cpu-mark-single-asc":
          return (a.metadata?.single_thread_mark as number || 0) - (b.metadata?.single_thread_mark as number || 0);
        case "cpu-mark-single-desc":
          return (b.metadata?.single_thread_mark as number || 0) - (a.metadata?.single_thread_mark as number || 0);
        case "gpu-mark-asc":
          return (a.metadata?.gpu_mark as number || 0) - (b.metadata?.gpu_mark as number || 0);
        case "gpu-mark-desc":
          return (b.metadata?.gpu_mark as number || 0) - (a.metadata?.gpu_mark as number || 0);
        case "ram-speed-asc":
          return (a.metadata?.speed_mhz as number || 0) - (b.metadata?.speed_mhz as number || 0);
        case "ram-speed-desc":
          return (b.metadata?.speed_mhz as number || 0) - (a.metadata?.speed_mhz as number || 0);
        case "ram-capacity-asc":
          return (a.metadata?.capacity_gb as number || 0) - (b.metadata?.capacity_gb as number || 0);
        case "ram-capacity-desc":
          return (b.metadata?.capacity_gb as number || 0) - (a.metadata?.capacity_gb as number || 0);
        case "storage-capacity-asc":
          return (a.metadata?.capacity_gb as number || 0) - (b.metadata?.capacity_gb as number || 0);
        case "storage-capacity-desc":
          return (b.metadata?.capacity_gb as number || 0) - (a.metadata?.capacity_gb as number || 0);
        case "storage-tier-asc":
          return (a.metadata?.performance_tier as number || 0) - (b.metadata?.performance_tier as number || 0);
        case "storage-tier-desc":
          return (b.metadata?.performance_tier as number || 0) - (a.metadata?.performance_tier as number || 0);
        default:
          return 0;
      }
    });

    return sorted;
  }, [components, search, sortBy, filters]);

  const handleSelect = (component: ComponentItem) => {
    onSelect(component);
    onOpenChange(false);
  };

  const handleCreateNew = () => {
    const route = getCreateRoute(componentType);
    if (route) {
      onOpenChange(false);
      router.push(route);
    }
  };

  const getSortOptions = (): { value: SortOption; label: string }[] => {
    const type = componentType.toLowerCase();
    const baseOptions = [
      { value: "name-asc" as SortOption, label: "Name (A-Z)" },
      { value: "name-desc" as SortOption, label: "Name (Z-A)" },
      { value: "price-asc" as SortOption, label: "Price (Low-High)" },
      { value: "price-desc" as SortOption, label: "Price (High-Low)" },
    ];

    if (type.includes("cpu")) {
      return [
        ...baseOptions,
        { value: "cpu-mark-multi-desc" as SortOption, label: "Multi-Thread (High-Low)" },
        { value: "cpu-mark-multi-asc" as SortOption, label: "Multi-Thread (Low-High)" },
        { value: "cpu-mark-single-desc" as SortOption, label: "Single-Thread (High-Low)" },
        { value: "cpu-mark-single-asc" as SortOption, label: "Single-Thread (Low-High)" },
      ];
    }

    if (type.includes("gpu")) {
      return [
        ...baseOptions,
        { value: "gpu-mark-desc" as SortOption, label: "GPU Mark (High-Low)" },
        { value: "gpu-mark-asc" as SortOption, label: "GPU Mark (Low-High)" },
      ];
    }

    if (type.includes("ram") || type.includes("memory")) {
      return [
        ...baseOptions,
        { value: "ram-speed-desc" as SortOption, label: "Speed (High-Low)" },
        { value: "ram-speed-asc" as SortOption, label: "Speed (Low-High)" },
        { value: "ram-capacity-desc" as SortOption, label: "Capacity (High-Low)" },
        { value: "ram-capacity-asc" as SortOption, label: "Capacity (Low-High)" },
      ];
    }

    if (type.includes("storage")) {
      return [
        ...baseOptions,
        { value: "storage-capacity-desc" as SortOption, label: "Capacity (High-Low)" },
        { value: "storage-capacity-asc" as SortOption, label: "Capacity (Low-High)" },
        { value: "storage-tier-desc" as SortOption, label: "Performance Tier (High-Low)" },
        { value: "storage-tier-asc" as SortOption, label: "Performance Tier (Low-High)" },
      ];
    }

    return baseOptions;
  };

  const toggleManufacturer = (manufacturer: string) => {
    setFilters((prev) => ({
      ...prev,
      manufacturers: prev.manufacturers.includes(manufacturer)
        ? prev.manufacturers.filter((m) => m !== manufacturer)
        : [...prev.manufacturers, manufacturer],
    }));
  };

  const toggleFilter = (filterKey: keyof FilterState, value: string) => {
    setFilters((prev) => {
      const currentValues = prev[filterKey] as string[];
      return {
        ...prev,
        [filterKey]: currentValues.includes(value)
          ? currentValues.filter((v) => v !== value)
          : [...currentValues, value],
      };
    });
  };

  const clearFilters = () => {
    setFilters({
      manufacturers: [],
      cpuCores: [],
      gpuTiers: [],
      ramGenerations: [],
      ramCapacities: [],
      storageInterfaces: [],
      storageMediums: [],
    });
    setSortBy("name-asc");
  };

  const hasActiveFilters =
    filters.manufacturers.length > 0 ||
    filters.priceMin !== undefined ||
    filters.priceMax !== undefined ||
    filters.cpuCores.length > 0 ||
    filters.gpuTiers.length > 0 ||
    filters.ramGenerations.length > 0 ||
    filters.ramCapacities.length > 0 ||
    filters.storageInterfaces.length > 0 ||
    filters.storageMediums.length > 0 ||
    sortBy !== "name-asc";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 flex-1 flex flex-col min-h-0">
          {/* Sort and Filter Controls */}
          <div className="space-y-3 pb-3 border-b">
            {/* Sort Control */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium shrink-0">Sort by:</label>
              <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
                <SelectTrigger className="w-[240px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {getSortOptions().map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Filter Controls */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Manufacturer Filter */}
              {availableManufacturers.length > 0 && (
                <Select
                  value={filters.manufacturers[0] || ""}
                  onValueChange={toggleManufacturer}
                >
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Manufacturer" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableManufacturers.map((manufacturer) => (
                      <SelectItem key={manufacturer} value={manufacturer}>
                        {manufacturer}
                        {filters.manufacturers.includes(manufacturer) && " ✓"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* Price Range Filter */}
              <Input
                type="number"
                placeholder="Min price"
                className="w-[110px]"
                value={filters.priceMin ?? ""}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    priceMin: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
              />
              <Input
                type="number"
                placeholder="Max price"
                className="w-[110px]"
                value={filters.priceMax ?? ""}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    priceMax: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
              />

              {/* CPU Core Count Filter */}
              {filterOptions.cpuCores && filterOptions.cpuCores.length > 0 && (
                <Select
                  value={filters.cpuCores[0] || ""}
                  onValueChange={(value) => toggleFilter("cpuCores", value)}
                >
                  <SelectTrigger className="w-[130px]">
                    <SelectValue placeholder="Core count" />
                  </SelectTrigger>
                  <SelectContent>
                    {filterOptions.cpuCores.map((cores) => (
                      <SelectItem key={cores} value={cores}>
                        {cores} cores
                        {filters.cpuCores.includes(cores) && " ✓"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* GPU Tier Filter */}
              {filterOptions.gpuTiers && filterOptions.gpuTiers.length > 0 && (
                <Select
                  value={filters.gpuTiers[0] || ""}
                  onValueChange={(value) => toggleFilter("gpuTiers", value)}
                >
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Performance tier" />
                  </SelectTrigger>
                  <SelectContent>
                    {filterOptions.gpuTiers.map((tier) => (
                      <SelectItem key={tier} value={tier}>
                        {tier}
                        {filters.gpuTiers.includes(tier) && " ✓"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* RAM Generation Filter */}
              {filterOptions.ramGenerations && filterOptions.ramGenerations.length > 0 && (
                <Select
                  value={filters.ramGenerations[0] || ""}
                  onValueChange={(value) => toggleFilter("ramGenerations", value)}
                >
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Generation" />
                  </SelectTrigger>
                  <SelectContent>
                    {filterOptions.ramGenerations.map((gen) => (
                      <SelectItem key={gen} value={gen}>
                        {gen}
                        {filters.ramGenerations.includes(gen) && " ✓"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* RAM Capacity Filter */}
              {filterOptions.ramCapacities && filterOptions.ramCapacities.length > 0 && (
                <Select
                  value={filters.ramCapacities[0] || ""}
                  onValueChange={(value) => toggleFilter("ramCapacities", value)}
                >
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Capacity" />
                  </SelectTrigger>
                  <SelectContent>
                    {filterOptions.ramCapacities.map((capacity) => (
                      <SelectItem key={capacity} value={capacity}>
                        {capacity}
                        {filters.ramCapacities.includes(capacity) && " ✓"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* Storage Interface Filter */}
              {filterOptions.storageInterfaces && filterOptions.storageInterfaces.length > 0 && (
                <Select
                  value={filters.storageInterfaces[0] || ""}
                  onValueChange={(value) => toggleFilter("storageInterfaces", value)}
                >
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Interface" />
                  </SelectTrigger>
                  <SelectContent>
                    {filterOptions.storageInterfaces.map((iface) => (
                      <SelectItem key={iface} value={iface}>
                        {iface}
                        {filters.storageInterfaces.includes(iface) && " ✓"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* Storage Medium Filter */}
              {filterOptions.storageMediums && filterOptions.storageMediums.length > 0 && (
                <Select
                  value={filters.storageMediums[0] || ""}
                  onValueChange={(value) => toggleFilter("storageMediums", value)}
                >
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Medium" />
                  </SelectTrigger>
                  <SelectContent>
                    {filterOptions.storageMediums.map((medium) => (
                      <SelectItem key={medium} value={medium}>
                        {medium}
                        {filters.storageMediums.includes(medium) && " ✓"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {/* Clear Filters Button */}
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  Clear Filters
                </Button>
              )}
            </div>
          </div>

          {/* Search Input */}
          <Input
            placeholder={`Search ${componentType}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />

          {/* Results Count */}
          {!isLoading && (
            <div className="text-sm text-muted-foreground">
              Showing {filteredAndSortedComponents.length} of {components.length} components
            </div>
          )}

          {/* Component List */}
          <ScrollArea className="flex-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">Loading components...</p>
              </div>
            ) : (
              <div className="space-y-2 pr-4">
                {/* Create New Button */}
                {getCreateRoute(componentType) && (
                  <Card
                    className="flex items-center gap-3 p-4 border-2 border-dashed border-muted-foreground/30 bg-muted/30 hover:bg-muted/50 hover:border-muted-foreground/50 cursor-pointer transition-all"
                    onClick={handleCreateNew}
                    role="button"
                    tabIndex={0}
                    aria-label={`Create new ${getComponentTypeName(componentType)}`}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleCreateNew();
                      }
                    }}
                  >
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10 text-primary flex-shrink-0">
                      <Plus className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground">
                        Create New {getComponentTypeName(componentType)}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Add a new {getComponentTypeName(componentType).toLowerCase()} to the catalog
                      </p>
                    </div>
                  </Card>
                )}

                {/* Component Items */}
                {filteredAndSortedComponents.length === 0 ? (
                  <div className="flex items-center justify-center py-8">
                    <p className="text-muted-foreground">
                      {search || hasActiveFilters ? "No components found" : "No components available"}
                    </p>
                  </div>
                ) : (
                  filteredAndSortedComponents.map((component) => (
                    <div
                      key={component.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                      onClick={() => handleSelect(component)}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium truncate">{component.name}</p>
                          {component.manufacturer && (
                            <Badge variant="outline" className="flex-shrink-0">
                              {component.manufacturer}
                            </Badge>
                          )}
                        </div>
                        {component.specs && (
                          <p className="text-sm text-muted-foreground truncate">
                            {component.specs}
                          </p>
                        )}
                      </div>
                      {component.price !== undefined && (
                        <p className="font-semibold flex-shrink-0 ml-4">
                          ${component.price.toFixed(2)}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}
