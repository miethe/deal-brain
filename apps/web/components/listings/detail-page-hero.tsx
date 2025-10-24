import { ProductImage } from "./product-image";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
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
        <div className="grid gap-3 sm:grid-cols-2">
          {/* Price Card */}
          <Card>
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Listing Price
              </div>
              <div className="mt-1 text-2xl font-semibold">
                {formatCurrency(listing.price_usd)}
              </div>
            </CardContent>
          </Card>

          {/* Adjusted Price Card */}
          <Card>
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Adjusted Price
              </div>
              <div className="mt-1 text-2xl font-semibold">
                {formatCurrency(listing.adjusted_price_usd)}
              </div>
            </CardContent>
          </Card>

          {/* CPU Info Card */}
          <Card>
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">CPU</div>
              <div className="mt-1 text-sm font-medium">
                {listing.cpu?.model || listing.cpu_name || "Unknown"}
              </div>
              {listing.cpu && (
                <div className="mt-1 text-xs text-muted-foreground">
                  {listing.cpu.cores && listing.cpu.threads && (
                    <span>
                      {listing.cpu.cores}C/{listing.cpu.threads}T
                    </span>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* GPU Info Card */}
          <Card>
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">GPU</div>
              <div className="mt-1 text-sm font-medium">
                {listing.gpu?.model || listing.gpu_name || "None"}
              </div>
              {listing.gpu?.vram_gb && (
                <div className="mt-1 text-xs text-muted-foreground">{listing.gpu.vram_gb}GB VRAM</div>
              )}
            </CardContent>
          </Card>

          {/* RAM Info Card */}
          <Card>
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">RAM</div>
              <div className="mt-1 text-sm font-medium">
                {listing.ram_gb ? `${listing.ram_gb}GB` : "Unknown"}
              </div>
              {(listing.ram_type || listing.ram_speed_mhz) && (
                <div className="mt-1 text-xs text-muted-foreground">
                  {listing.ram_type}
                  {listing.ram_speed_mhz && ` @ ${listing.ram_speed_mhz}MHz`}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Performance Score Card */}
          <Card>
            <CardContent className="p-4">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                Composite Score
              </div>
              <div className="mt-1 text-2xl font-semibold">
                {formatNumber(listing.score_composite)}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
