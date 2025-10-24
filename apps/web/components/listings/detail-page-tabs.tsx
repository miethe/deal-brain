"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DETAIL_PAGE_TABS, type DetailPageTab, type ListingDetail } from "@/types/listing-detail";
import { SpecificationsTab } from "./specifications-tab";
import { ValuationTabPage } from "./valuation-tab-page";
import { HistoryTab } from "./history-tab";
import { NotesTab } from "./notes-tab";

interface DetailPageTabsProps {
  listing: ListingDetail;
}

export function DetailPageTabs({ listing }: DetailPageTabsProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentTab = (searchParams.get("tab") as DetailPageTab) || "specifications";

  const handleTabChange = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", value);
    router.push(`?${params.toString()}`, { scroll: false });
  };

  return (
    <Tabs value={currentTab} onValueChange={handleTabChange} className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="specifications">Specifications</TabsTrigger>
        <TabsTrigger value="valuation">Valuation</TabsTrigger>
        <TabsTrigger value="history">History</TabsTrigger>
        <TabsTrigger value="notes">Notes</TabsTrigger>
      </TabsList>

      <TabsContent value="specifications" className="mt-6">
        <SpecificationsTab listing={listing} />
      </TabsContent>

      <TabsContent value="valuation" className="mt-6">
        <ValuationTabPage listing={listing} />
      </TabsContent>

      <TabsContent value="history" className="mt-6">
        <HistoryTab listing={listing} />
      </TabsContent>

      <TabsContent value="notes" className="mt-6">
        <NotesTab />
      </TabsContent>
    </Tabs>
  );
}
