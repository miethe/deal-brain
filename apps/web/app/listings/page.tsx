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
import { CatalogTab } from "./_components/catalog-tab";
import { QuickEditDialog } from "../../components/listings/quick-edit-dialog";
import { ListingDetailsDialog } from "../../components/listings/listing-details-dialog";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../lib/utils";
import { ListingRecord } from "../../types/listings";
import { useToast } from "@/hooks/use-toast";

export default function ListingsPage() {
  const [addModalOpen, setAddModalOpen] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch listings data
  const { data: listings, isLoading } = useQuery({
    queryKey: ["listings", "records"],
    queryFn: () => apiFetch<ListingRecord[]>("/v1/listings"),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Sync URL with store
  useUrlSync();

  // Get tab state from store
  const activeTab = useCatalogStore((state) => state.activeTab);
  const setActiveTab = useCatalogStore((state) => state.setActiveTab);

  const handleSuccess = (listingId: number) => {
    setAddModalOpen(false);

    // Set URL param for highlight
    const params = new URLSearchParams(window.location.search);
    params.set('highlight', String(listingId));
    router.replace(`${window.location.pathname}?${params.toString()}`, { scroll: false });

    // Invalidate both listings queries to refresh data
    queryClient.invalidateQueries({ queryKey: ["listings", "records"] });
    queryClient.invalidateQueries({ queryKey: ["listings", "count"] });

    // Show success toast notification
    toast({
      title: "Listing created successfully",
      description: "Your new listing has been added to the catalog.",
      duration: 3000,
    });
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
          <CatalogTab
            listings={listings || []}
            isLoading={isLoading}
            onAddListing={() => setAddModalOpen(true)}
          />
        </TabsContent>

        <TabsContent value="data" className="space-y-4">
          <ListingsTable />

          <Card>
            <CardHeader>
              <CardTitle>How scoring works</CardTitle>
              <CardDescription>Composite scores update automatically after each valuation run.</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Adjusted value removes RAM, storage, and OS value using your valuation rules. Composite scores blend CPU, GPU,
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

      {/* Catalog Dialogs */}
      <QuickEditDialog />
      <ListingDetailsDialog />
    </div>
  );
}
