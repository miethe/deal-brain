"use client";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { useCPUCatalogStore } from "@/stores/cpu-catalog-store";
import { useCPUs } from "@/hooks/use-cpus";
import { useCPUUrlSync } from "@/hooks/use-cpu-url-sync";
import { Plus, Upload } from "lucide-react";

/**
 * CPU Catalog Main Page
 *
 * Dual-tab interface for browsing CPU catalog:
 * - Catalog Tab: Grid/List/Master-Detail views with filters (FE-003, FE-004, FE-005)
 * - Data Tab: Legacy table view for power users
 *
 * Features:
 * - React Query integration for data fetching with analytics
 * - Zustand store for view state and tab persistence
 * - URL sync for shareable state (FE-007)
 * - Loading and error states
 * - Accessible, responsive layout
 */
export default function CPUsPage() {
  // Fetch CPUs with analytics data (price targets, performance values)
  const { data: cpus, isLoading, error } = useCPUs(true);

  // Store state management
  const activeTab = useCPUCatalogStore((state) => state.activeTab);
  const setActiveTab = useCPUCatalogStore((state) => state.setActiveTab);

  // URL sync for shareable state (FE-007)
  useCPUUrlSync();

  // Error state rendering
  if (error) {
    return (
      <div className="w-full space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">CPUs</h1>
            <p className="text-sm text-muted-foreground">
              Browse CPU catalog with performance metrics and pricing analytics.
            </p>
          </div>
        </div>
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            Failed to load CPU data. Please try again later.
          </p>
          {error instanceof Error && (
            <p className="mt-2 text-xs text-destructive/80">
              Error: {error.message}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">CPUs</h1>
          <p className="text-sm text-muted-foreground">
            Browse CPU catalog with performance metrics and pricing analytics.
          </p>
        </div>

        {/* Action Buttons - Future: Import and Add CPU functionality */}
        <div className="flex gap-2">
          <Button variant="outline" disabled>
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Button disabled>
            <Plus className="mr-2 h-4 w-4" />
            Add CPU
          </Button>
        </div>
      </div>

      {/* Dual-Tab Interface */}
      <Tabs
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as 'catalog' | 'data')}
      >
        <TabsList>
          <TabsTrigger value="catalog">Catalog</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
        </TabsList>

        {/* Catalog Tab - Multi-view interface for browsing CPUs */}
        <TabsContent value="catalog" className="space-y-4">
          {/* Placeholder for CatalogTab component (FE-002 Part 2) */}
          <div className="rounded-lg border border-dashed border-muted-foreground/25 p-12 text-center">
            <p className="text-sm text-muted-foreground">
              CPU Catalog Tab
            </p>
            <p className="mt-1 text-xs text-muted-foreground/75">
              Views will be implemented in FE-003 (Grid), FE-004 (List), FE-005 (Master-Detail)
            </p>

            {/* Loading feedback */}
            {isLoading && (
              <p className="mt-4 text-xs text-muted-foreground">
                Loading CPU data...
              </p>
            )}

            {/* Success feedback */}
            {!isLoading && cpus && (
              <div className="mt-4 space-y-1">
                <p className="text-xs font-medium text-muted-foreground">
                  Ready to display
                </p>
                <p className="text-2xl font-bold text-foreground">
                  {cpus.length}
                </p>
                <p className="text-xs text-muted-foreground">
                  CPUs with analytics
                </p>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Data Tab - Legacy table view for power users */}
        <TabsContent value="data" className="space-y-4">
          {/* Placeholder for Data table view */}
          <div className="rounded-lg border border-dashed border-muted-foreground/25 p-12 text-center">
            <p className="text-sm text-muted-foreground">
              CPU Data Table
            </p>
            <p className="mt-1 text-xs text-muted-foreground/75">
              Legacy table view with advanced filtering (to be implemented later)
            </p>

            {/* Data preview */}
            {!isLoading && cpus && cpus.length > 0 && (
              <div className="mt-4 space-y-1">
                <p className="text-xs text-muted-foreground">
                  {cpus.length} rows ready for table display
                </p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
