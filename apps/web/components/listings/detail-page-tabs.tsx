"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DETAIL_PAGE_TABS, type DetailPageTab, type ListingDetail } from "@/types/listing-detail";

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
        <Card>
          <CardHeader>
            <CardTitle>Technical Specifications</CardTitle>
            <CardDescription>Detailed hardware and configuration information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* CPU Section */}
            {listing.cpu && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Processor
                </h3>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <SpecRow label="Model" value={listing.cpu.model} />
                  <SpecRow label="Manufacturer" value={listing.cpu.manufacturer} />
                  <SpecRow
                    label="Cores / Threads"
                    value={
                      listing.cpu.cores && listing.cpu.threads
                        ? `${listing.cpu.cores} / ${listing.cpu.threads}`
                        : undefined
                    }
                  />
                  <SpecRow
                    label="Base Clock"
                    value={
                      listing.cpu.base_clock_ghz ? `${listing.cpu.base_clock_ghz} GHz` : undefined
                    }
                  />
                  <SpecRow
                    label="Boost Clock"
                    value={
                      listing.cpu.boost_clock_ghz ? `${listing.cpu.boost_clock_ghz} GHz` : undefined
                    }
                  />
                </div>
              </div>
            )}

            {/* GPU Section */}
            {listing.gpu && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Graphics
                </h3>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <SpecRow label="Model" value={listing.gpu.model} />
                  <SpecRow label="Manufacturer" value={listing.gpu.manufacturer} />
                  <SpecRow
                    label="VRAM"
                    value={listing.gpu.vram_gb ? `${listing.gpu.vram_gb} GB` : undefined}
                  />
                </div>
              </div>
            )}

            {/* Memory Section */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Memory
              </h3>
              <div className="grid gap-2 text-sm sm:grid-cols-2">
                <SpecRow label="Capacity" value={listing.ram_gb ? `${listing.ram_gb} GB` : undefined} />
                <SpecRow label="Type" value={listing.ram_type} />
                <SpecRow
                  label="Speed"
                  value={listing.ram_speed_mhz ? `${listing.ram_speed_mhz} MHz` : undefined}
                />
                {listing.ram_spec && (
                  <>
                    <SpecRow label="Generation" value={listing.ram_spec.ddr_generation} />
                    <SpecRow label="Module Count" value={listing.ram_spec.module_count} />
                  </>
                )}
              </div>
            </div>

            {/* Storage Section */}
            {(listing.primary_storage_gb || listing.secondary_storage_gb) && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Storage
                </h3>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <SpecRow
                    label="Primary"
                    value={
                      listing.primary_storage_gb
                        ? `${listing.primary_storage_gb} GB ${listing.primary_storage_type || ""}`
                        : undefined
                    }
                  />
                  <SpecRow
                    label="Secondary"
                    value={
                      listing.secondary_storage_gb
                        ? `${listing.secondary_storage_gb} GB ${listing.secondary_storage_type || ""}`
                        : undefined
                    }
                  />
                </div>
              </div>
            )}

            {/* Ports Section */}
            {listing.ports_profile && listing.ports_profile.usb_a_count !== undefined && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Connectivity
                </h3>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <SpecRow label="USB-A" value={listing.ports_profile.usb_a_count} />
                  <SpecRow label="USB-C" value={listing.ports_profile.usb_c_count} />
                  <SpecRow label="HDMI" value={listing.ports_profile.hdmi_count} />
                  <SpecRow label="DisplayPort" value={listing.ports_profile.displayport_count} />
                </div>
              </div>
            )}

            {/* Product Info Section */}
            {(listing.manufacturer || listing.series || listing.model_number || listing.form_factor) && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Product Information
                </h3>
                <div className="grid gap-2 text-sm sm:grid-cols-2">
                  <SpecRow label="Manufacturer" value={listing.manufacturer} />
                  <SpecRow label="Series" value={listing.series} />
                  <SpecRow label="Model Number" value={listing.model_number} />
                  <SpecRow label="Form Factor" value={listing.form_factor} />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="valuation" className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Valuation Breakdown</CardTitle>
            <CardDescription>
              Price adjustments and scoring details (Phase 6 integration coming soon)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">
              <p className="text-sm">
                Valuation breakdown details will be integrated here in Phase 6.
              </p>
              <p className="mt-2 text-xs">
                This will include rule-based adjustments, component valuations, and detailed scoring.
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="history" className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Price History</CardTitle>
            <CardDescription>Track price changes and updates over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">
              <p className="text-sm">Price history tracking coming soon.</p>
              <p className="mt-2 text-xs">
                This will show historical price changes, last updated timestamps, and trends.
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="notes" className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Notes & Comments</CardTitle>
            <CardDescription>Add personal notes and observations about this listing</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">
              <p className="text-sm">Notes feature coming soon.</p>
              <p className="mt-2 text-xs">
                This will allow you to add and manage personal notes for each listing.
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}

function SpecRow({ label, value }: { label: string; value: string | number | undefined | null }) {
  if (value === undefined || value === null) return null;

  return (
    <div className="flex justify-between border-b border-border/40 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
