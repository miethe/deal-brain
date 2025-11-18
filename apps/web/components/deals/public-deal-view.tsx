"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ProductImage } from "@/components/listings/product-image";
import { SummaryCard } from "@/components/listings/summary-card";
import { SummaryCardsGrid } from "@/components/listings/summary-cards-grid";
import { ValuationTooltip } from "@/components/listings/valuation-tooltip";
import { ValuationBreakdownModal } from "@/components/listings/valuation-breakdown-modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ExternalLink, Heart, Info } from "lucide-react";
import type { ListingDetail } from "@/types/listing-detail";

interface PublicDealViewProps {
  share: {
    id: number;
    listing_id: number;
    share_token: string;
    expires_at: string;
    view_count: number;
    created_by_id: number;
  };
  listing: ListingDetail;
}

export function PublicDealView({ share, listing }: PublicDealViewProps) {
  const router = useRouter();
  const [breakdownModalOpen, setBreakdownModalOpen] = useState(false);
  // TODO: Replace with actual auth check when implementing Phase 5
  const isAuthenticated = false;

  const formatCurrency = (value: number | null | undefined) =>
    value == null
      ? "—"
      : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);

  const formatNumber = (value: number | null | undefined) =>
    value == null ? "—" : value.toFixed(2);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  };

  const isExpired = new Date(share.expires_at) < new Date();

  const handleAddToCollection = () => {
    if (!isAuthenticated) {
      // Redirect to sign-up with return URL
      const returnUrl = encodeURIComponent(`/deals/${listing.id}/${share.share_token}`);
      router.push(`/auth/signup?return=${returnUrl}`);
    } else {
      // TODO: Open collection selector dialog
      console.log("Add to collection");
    }
  };

  // CPU summary
  const cpuText = listing.cpu?.model || listing.cpu_name || "Unknown";
  const cpuSubtitle =
    listing.cpu?.cores && listing.cpu?.threads
      ? `${listing.cpu.cores}C/${listing.cpu.threads}T`
      : undefined;

  // GPU summary
  const gpuText = listing.gpu?.model || listing.gpu_name || "None";
  const gpuSubtitle = listing.gpu?.vram_gb ? `${listing.gpu.vram_gb}GB VRAM` : undefined;

  // RAM summary
  const ramText = listing.ram_gb ? `${listing.ram_gb}GB` : "Unknown";
  const ramSubtitle =
    listing.ram_type || listing.ram_speed_mhz
      ? `${listing.ram_type || ""}${listing.ram_speed_mhz ? ` @ ${listing.ram_speed_mhz}MHz` : ""}`.trim()
      : undefined;

  // Storage summary
  const storageText = listing.primary_storage_gb
    ? `${listing.primary_storage_gb}GB`
    : "Unknown";
  const storageSubtitle = listing.primary_storage_type || undefined;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">Deal Brain</h1>
            <Badge variant="outline" className="text-xs">
              Shared Deal
            </Badge>
          </div>
          {isExpired && (
            <Badge variant="destructive" className="text-xs">
              Expired
            </Badge>
          )}
        </div>
      </div>

      <div className="container mx-auto space-y-6 px-4 py-6 sm:px-6 lg:px-8 max-w-6xl">
        {/* Expiration Warning */}
        {isExpired && (
          <Alert variant="destructive">
            <Info className="h-4 w-4" />
            <AlertTitle>Share Link Expired</AlertTitle>
            <AlertDescription>
              This share link expired on {formatDate(share.expires_at)}. The listing may no longer be available.
            </AlertDescription>
          </Alert>
        )}

        {/* Hero Section - Product Image and Summary */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left side: Product Image */}
          <div className="flex items-start justify-center lg:justify-start">
            <ProductImage listing={listing} className="h-64 w-full sm:h-80 lg:h-96" />
          </div>

          {/* Right side: Summary Cards */}
          <div className="space-y-4">
            {/* Title and basic info */}
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{listing.title}</h1>
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
                size="large"
              />

              <SummaryCard
                title="Adjusted Value"
                value={formatCurrency(listing.adjusted_price_usd)}
                size="large"
                icon={
                  listing.price_usd && listing.adjusted_price_usd ? (
                    <ValuationTooltip
                      listPrice={listing.price_usd}
                      adjustedValue={listing.adjusted_price_usd}
                      valuationBreakdown={listing.valuation_breakdown}
                      onViewDetails={() => setBreakdownModalOpen(true)}
                    />
                  ) : null
                }
              />

              <SummaryCard
                title="CPU"
                value={cpuText}
                subtitle={cpuSubtitle}
                size="medium"
                valueClassName="text-base"
              />

              <SummaryCard
                title="GPU"
                value={gpuText}
                subtitle={gpuSubtitle}
                size="medium"
                valueClassName="text-base"
              />

              <SummaryCard
                title="RAM"
                value={ramText}
                subtitle={ramSubtitle}
                size="medium"
                valueClassName="text-base"
              />

              <SummaryCard
                title="Storage"
                value={storageText}
                subtitle={storageSubtitle}
                size="medium"
                valueClassName="text-base"
              />
            </SummaryCardsGrid>

            {/* Score Display */}
            {listing.score_composite !== null && (
              <Card className="border-primary/20 bg-primary/5">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-xs uppercase tracking-wide text-muted-foreground">
                        Composite Score
                      </Label>
                      <p className="text-3xl font-bold text-primary">
                        {formatNumber(listing.score_composite)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">
                        Higher is better
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Add to Collection CTA */}
            <Button
              size="lg"
              className="w-full"
              onClick={handleAddToCollection}
              disabled={isExpired}
            >
              <Heart className="mr-2 h-5 w-5" />
              {isAuthenticated ? "Add to Collection" : "Sign Up to Save This Deal"}
            </Button>

            {!isAuthenticated && (
              <p className="text-center text-sm text-muted-foreground">
                Create a free account to save deals and build collections
              </p>
            )}
          </div>
        </div>

        <Separator className="my-6" />

        {/* Full Specifications */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Full Specifications</h2>

          <div className="grid gap-4 md:grid-cols-2">
            {/* Compute Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Compute</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <FieldGroup label="CPU" value={cpuText} subtitle={cpuSubtitle} />
                {listing.gpu && (
                  <FieldGroup label="GPU" value={gpuText} subtitle={gpuSubtitle} />
                )}
                {listing.score_gpu !== null && (
                  <FieldGroup label="GPU Score" value={listing.score_gpu.toFixed(1)} />
                )}
              </CardContent>
            </Card>

            {/* Memory & Storage Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Memory & Storage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <FieldGroup label="RAM" value={ramText} subtitle={ramSubtitle} />
                <FieldGroup label="Primary Storage" value={storageText} subtitle={storageSubtitle} />
                {listing.secondary_storage_gb && (
                  <FieldGroup
                    label="Secondary Storage"
                    value={`${listing.secondary_storage_gb}GB`}
                    subtitle={listing.secondary_storage_type || undefined}
                  />
                )}
              </CardContent>
            </Card>

            {/* Product Details */}
            {(listing.manufacturer || listing.series || listing.model_number || listing.form_factor) && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Product Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {listing.manufacturer && <FieldGroup label="Manufacturer" value={listing.manufacturer} />}
                  {listing.series && <FieldGroup label="Series" value={listing.series} />}
                  {listing.model_number && <FieldGroup label="Model Number" value={listing.model_number} />}
                  {listing.form_factor && <FieldGroup label="Form Factor" value={listing.form_factor} />}
                </CardContent>
              </Card>
            )}

            {/* Performance Metrics */}
            {(listing.dollar_per_cpu_mark_single || listing.dollar_per_cpu_mark_multi) && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {listing.dollar_per_cpu_mark_single && (
                    <FieldGroup
                      label="$/CPU Mark (Single-Thread)"
                      value={`$${listing.dollar_per_cpu_mark_single.toFixed(4)}`}
                    />
                  )}
                  {listing.dollar_per_cpu_mark_multi && (
                    <FieldGroup
                      label="$/CPU Mark (Multi-Thread)"
                      value={`$${listing.dollar_per_cpu_mark_multi.toFixed(4)}`}
                    />
                  )}
                </CardContent>
              </Card>
            )}

            {/* Connectivity */}
            {listing.ports_profile && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Connectivity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {listing.ports_profile.usb_a_count !== undefined &&
                      listing.ports_profile.usb_a_count !== null &&
                      listing.ports_profile.usb_a_count > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          USB-A ×{listing.ports_profile.usb_a_count}
                        </Badge>
                      )}
                    {listing.ports_profile.usb_c_count !== undefined &&
                      listing.ports_profile.usb_c_count !== null &&
                      listing.ports_profile.usb_c_count > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          USB-C ×{listing.ports_profile.usb_c_count}
                        </Badge>
                      )}
                    {listing.ports_profile.hdmi_count !== undefined &&
                      listing.ports_profile.hdmi_count !== null &&
                      listing.ports_profile.hdmi_count > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          HDMI ×{listing.ports_profile.hdmi_count}
                        </Badge>
                      )}
                    {listing.ports_profile.displayport_count !== undefined &&
                      listing.ports_profile.displayport_count !== null &&
                      listing.ports_profile.displayport_count > 0 && (
                        <Badge variant="secondary" className="text-xs">
                          DisplayPort ×{listing.ports_profile.displayport_count}
                        </Badge>
                      )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Listing Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Listing Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {listing.listing_url && (
                  <FieldGroup label="Listing URL">
                    <a
                      href={listing.listing_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                    >
                      View Original Listing
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </FieldGroup>
                )}
                <FieldGroup label="Condition" value={listing.condition} />
                <FieldGroup label="Status" value={listing.status} />
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Footer CTA */}
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center gap-4 text-center">
              <h3 className="text-xl font-semibold">Like this deal?</h3>
              <p className="text-muted-foreground max-w-md">
                {isAuthenticated
                  ? "Save it to your collection and get notified about similar deals"
                  : "Create a free Deal Brain account to save deals, build collections, and get personalized recommendations"}
              </p>
              <Button size="lg" onClick={handleAddToCollection} disabled={isExpired}>
                <Heart className="mr-2 h-5 w-5" />
                {isAuthenticated ? "Add to Collection" : "Create Free Account"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Valuation Breakdown Modal */}
      <ValuationBreakdownModal
        open={breakdownModalOpen}
        onOpenChange={setBreakdownModalOpen}
        listingId={listing.id}
        listingTitle={listing.title}
        thumbnailUrl={listing.thumbnail_url}
      />
    </div>
  );
}

/**
 * Reusable field group component for label/value pairs
 */
interface FieldGroupProps {
  label: string;
  value?: string | number | null;
  subtitle?: string;
  children?: React.ReactNode;
}

function FieldGroup({ label, value, subtitle, children }: FieldGroupProps) {
  return (
    <div className="space-y-1">
      <Label className="text-xs uppercase tracking-wide text-muted-foreground">{label}</Label>
      <div className="text-sm font-medium">
        {children || value || "—"}
        {subtitle && <span className="text-xs text-muted-foreground ml-1">({subtitle})</span>}
      </div>
    </div>
  );
}
