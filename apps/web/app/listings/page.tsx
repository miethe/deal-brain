"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ListingsTable } from "../../components/listings/listings-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../components/ui/tabs";
import { AddListingModal } from "../../components/listings/add-listing-modal";
import { useCatalogStore } from "@/stores/catalog-store";
import { useUrlSync } from "@/hooks/use-url-sync";
import { ListingsFilters } from "./_components/listings-filters";

export default function ListingsPage() {
  const [addModalOpen, setAddModalOpen] = useState(false);
  const router = useRouter();

  // Sync URL with store
  useUrlSync();

  // Get tab state from store
  const activeTab = useCatalogStore((state) => state.activeTab);
  const setActiveTab = useCatalogStore((state) => state.setActiveTab);

  const handleSuccess = () => {
    setAddModalOpen(false);
    // Refresh the page to show new listing
    router.refresh();
  };

  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Listings</h1>
          <p className="text-sm text-muted-foreground">Browse your listings in catalog or data table view.</p>
        </div>
        <Button onClick={() => setAddModalOpen(true)}>
          Add listing
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={(value: string) => setActiveTab(value as 'catalog' | 'data')}>
        <TabsList>
          <TabsTrigger value="catalog">Catalog</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
        </TabsList>

        <TabsContent value="catalog" className="space-y-4">
          <ListingsFilters />
          <div className="flex items-center justify-center h-96 border-2 border-dashed border-muted-foreground/25 rounded-lg">
            <div className="text-center space-y-2">
              <p className="text-lg font-medium">Catalog View Coming Soon</p>
              <p className="text-sm text-muted-foreground">
                Grid, list, and master-detail views will be available here
              </p>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="data" className="space-y-4">
          <ListingsTable />

          <Card>
            <CardHeader>
              <CardTitle>How scoring works</CardTitle>
              <CardDescription>Composite scores update automatically after each valuation run.</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Adjusted price removes RAM, storage, and OS value using your valuation rules. Composite scores blend CPU, GPU,
              perf-per-watt, and RAM metrics according to the active profile, so the table is always ready for comparison.
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <AddListingModal
        open={addModalOpen}
        onOpenChange={setAddModalOpen}
        onSuccess={handleSuccess}
      />
    </div>
  );
}
