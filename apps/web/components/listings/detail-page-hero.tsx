import { ProductImage } from "./product-image";
import { SummaryCard } from "./summary-card";
import { SummaryCardsGrid } from "./summary-cards-grid";
import { Badge } from "@/components/ui/badge";
import type { ListingDetail } from "@/types/listing-detail";

interface DetailPageHeroProps {
  listing: ListingDetail;
}

export function DetailPageHero({ listing }: DetailPageHeroProps) {
  const formatCurrency = (value: number | null | undefined) =>
    value == null
      ? "—"
      : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);

  const formatNumber = (value: number | null | undefined) =>
    value == null ? "—" : value.toFixed(2);

  // CPU summary
  const cpuValue = listing.cpu?.model || listing.cpu_name || "Unknown";
  const cpuSubtitle =
    listing.cpu?.cores && listing.cpu?.threads
      ? `${listing.cpu.cores}C/${listing.cpu.threads}T`
      : undefined;

  // GPU summary
  const gpuValue = listing.gpu?.model || listing.gpu_name || "None";
  const gpuSubtitle = listing.gpu?.vram_gb ? `${listing.gpu.vram_gb}GB VRAM` : undefined;

  // RAM summary
  const ramValue = listing.ram_gb ? `${listing.ram_gb}GB` : "Unknown";
  const ramSubtitle =
    listing.ram_type || listing.ram_speed_mhz
      ? `${listing.ram_type || ""}${listing.ram_speed_mhz ? ` @ ${listing.ram_speed_mhz}MHz` : ""}`.trim()
      : undefined;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Left side: Product Image */}
      <div className="flex items-start justify-center lg:justify-start">
        <ProductImage listing={listing} className="h-64 w-full sm:h-80 lg:h-96" />
      </div>

      {/* Right side: Summary Cards */}
      <div className="space-y-4">
        {/* Title and basic info */}
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{listing.title}</h1>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="capitalize">
              {listing.condition}
            </Badge>
            {listing.status && (
              <Badge variant="secondary" className="capitalize">
                {listing.status}
              </Badge>
            )}
            {listing.seller && (
              <span className="text-sm text-muted-foreground">Seller: {listing.seller}</span>
            )}
          </div>
        </div>

        {/* Summary Cards Grid */}
        <SummaryCardsGrid columns={2}>
          <SummaryCard
            title="Listing Price"
            value={formatCurrency(listing.price_usd)}
            size="medium"
          />

          <SummaryCard
            title="Adjusted Price"
            value={formatCurrency(listing.adjusted_price_usd)}
            size="medium"
          />

          <SummaryCard
            title="CPU"
            value={cpuValue}
            subtitle={cpuSubtitle}
            size="medium"
            valueClassName="text-sm"
          />

          <SummaryCard
            title="GPU"
            value={gpuValue}
            subtitle={gpuSubtitle}
            size="medium"
            valueClassName="text-sm"
          />

          <SummaryCard
            title="RAM"
            value={ramValue}
            subtitle={ramSubtitle}
            size="medium"
            valueClassName="text-sm"
          />

          <SummaryCard
            title="Composite Score"
            value={formatNumber(listing.score_composite)}
            size="medium"
          />
        </SummaryCardsGrid>
      </div>
    </div>
  );
}
