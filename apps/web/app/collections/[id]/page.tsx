"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { WorkspaceHeader } from "@/components/collections/workspace-header";
import { WorkspaceFiltersComponent, type WorkspaceFilters } from "@/components/collections/workspace-filters";
import { WorkspaceTable } from "@/components/collections/workspace-table";
import { WorkspaceCards } from "@/components/collections/workspace-cards";
import { ItemDetailsPanel } from "@/components/collections/item-details-panel";
import { useCollection } from "@/hooks/use-collections";
import type { CollectionItem } from "@/types/collections";

/**
 * Collection Workspace View
 *
 * Main comparison view for collections with:
 * - Header (name, export, view controls)
 * - Filters (price, CPU, form factor, sort)
 * - Table view (sortable columns, checkboxes)
 * - Card view (mobile-friendly)
 * - Item details panel (notes, status)
 */
export default function CollectionWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const collectionId = params.id as string;

  // View mode state - default to cards on mobile
  const [viewMode, setViewMode] = useState<"table" | "cards">(() => {
    if (typeof window !== "undefined") {
      return window.innerWidth < 768 ? "cards" : "table";
    }
    return "table";
  });

  // Selected item for details panel
  const [selectedItem, setSelectedItem] = useState<CollectionItem | null>(null);
  const [detailsPanelOpen, setDetailsPanelOpen] = useState(false);

  // Fetch collection with items
  const {
    data: collection,
    isLoading,
    error,
  } = useCollection(collectionId);

  // Calculate initial price range from collection data
  const initialPriceRange = useMemo((): [number, number] => {
    if (!collection || collection.items.length === 0) {
      return [0, 10000];
    }
    const prices = collection.items.map((item) => item.listing.price_usd);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    return [minPrice, maxPrice];
  }, [collection]);

  // Filters state
  const initialFilters: WorkspaceFilters = {
    priceRange: initialPriceRange,
    cpuFamily: [],
    formFactor: [],
    sortBy: "added_date",
    sortOrder: "desc",
  };
  const [filters, setFilters] = useState<WorkspaceFilters>(initialFilters);

  // Update price range when collection data changes
  useEffect(() => {
    setFilters((prev) => ({
      ...prev,
      priceRange: initialPriceRange,
    }));
  }, [initialPriceRange]);

  // Apply filters and sorting
  const filteredItems = useMemo(() => {
    if (!collection) return [];

    let filtered = [...collection.items];

    // Price filter
    filtered = filtered.filter(
      (item) =>
        item.listing.price_usd >= filters.priceRange[0] &&
        item.listing.price_usd <= filters.priceRange[1]
    );

    // CPU family filter
    if (filters.cpuFamily.length > 0) {
      filtered = filtered.filter((item) => {
        const cpuName = item.listing.cpu_name;
        if (!cpuName) return false;
        return filters.cpuFamily.some((family) =>
          cpuName.toLowerCase().includes(family.toLowerCase())
        );
      });
    }

    // Form factor filter
    if (filters.formFactor.length > 0) {
      filtered = filtered.filter((item) =>
        filters.formFactor.includes(item.listing.form_factor || "")
      );
    }

    // Sorting
    filtered.sort((a, b) => {
      let comparison = 0;

      switch (filters.sortBy) {
        case "price":
          comparison = a.listing.price_usd - b.listing.price_usd;
          break;
        case "score":
          comparison =
            (a.listing.score_composite || 0) - (b.listing.score_composite || 0);
          break;
        case "cpu_mark":
          comparison =
            (a.listing.cpu?.cpu_mark_multi || 0) -
            (b.listing.cpu?.cpu_mark_multi || 0);
          break;
        case "added_date":
          comparison =
            new Date(a.added_at).getTime() - new Date(b.added_at).getTime();
          break;
      }

      return filters.sortOrder === "asc" ? comparison : -comparison;
    });

    return filtered;
  }, [collection, filters]);

  const handleItemExpand = (item: CollectionItem) => {
    setSelectedItem(item);
    setDetailsPanelOpen(true);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="w-full space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/collections">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to collections
            </Button>
          </Link>
        </div>
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="w-full space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/collections">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to collections
            </Button>
          </Link>
        </div>
        <Alert variant="destructive">
          <AlertDescription>
            {error instanceof Error ? error.message : "Failed to load collection"}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Not found
  if (!collection) {
    return (
      <div className="w-full space-y-6">
        <div className="flex items-center gap-4">
          <Link href="/collections">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to collections
            </Button>
          </Link>
        </div>
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
          <h2 className="text-xl font-semibold mb-2">Collection not found</h2>
          <p className="text-muted-foreground mb-4">
            This collection doesn't exist or you don't have access to it.
          </p>
          <Button onClick={() => router.push("/collections")}>
            View all collections
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Back Button */}
      <div className="flex items-center gap-4">
        <Link href="/collections">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to collections
          </Button>
        </Link>
      </div>

      {/* Header */}
      <WorkspaceHeader
        collection={collection}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* Filters */}
      <WorkspaceFiltersComponent
        items={collection.items}
        filters={filters}
        onFiltersChange={setFilters}
      />

      {/* Main Content */}
      <div className="pb-8">
        {viewMode === "table" ? (
          <WorkspaceTable
            collectionId={collectionId}
            items={filteredItems}
            onItemExpand={handleItemExpand}
          />
        ) : (
          <WorkspaceCards
            collectionId={collectionId}
            items={filteredItems}
            onItemExpand={handleItemExpand}
          />
        )}
      </div>

      {/* Item Details Panel */}
      <ItemDetailsPanel
        collectionId={collectionId}
        item={selectedItem}
        open={detailsPanelOpen}
        onOpenChange={setDetailsPanelOpen}
      />
    </div>
  );
}
