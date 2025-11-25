"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { ExternalLink } from "lucide-react";
import type { ListingDetail } from "@/types/listing-detail";
import { EntityTooltip } from "./entity-tooltip";
import { QuickAddComputeDialog } from "./quick-add-compute-dialog";
import { QuickAddMemoryDialog } from "./quick-add-memory-dialog";
import { QuickAddStorageDialog } from "./quick-add-storage-dialog";
import { QuickAddConnectivityDialog } from "./quick-add-connectivity-dialog";
import { PerformanceMetricDisplay } from "./performance-metric-display";

interface SpecificationsTabProps {
  listing: ListingDetail;
}

/**
 * Reusable subsection component for specifications
 */
interface SpecificationSubsectionProps {
  title: string;
  children: React.ReactNode;
  isEmpty?: boolean;
  onAddClick?: () => void;
}

function SpecificationSubsection({
  title,
  children,
  isEmpty,
  onAddClick,
}: SpecificationSubsectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center justify-between">
          {title}
          {isEmpty && onAddClick && (
            <Button variant="ghost" size="sm" onClick={onAddClick}>
              Add +
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <p className="text-sm text-muted-foreground">No data available</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {children}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Comprehensive specifications tab component
 *
 * Displays all listing details organized into logical sections:
 * - Compute: CPU, GPU, Performance Metrics
 * - Memory: RAM specs
 * - Storage: Primary and Secondary storage
 * - Connectivity: Ports profile
 * - Product Details & Listing Info: 2-column layout on desktop
 * - Metadata: Collapsible accordion
 * - Custom Fields: Dynamic attributes
 *
 * Uses EntityTooltip for hardware components to show rich previews.
 *
 * @example
 * ```tsx
 * <SpecificationsTab listing={listing} />
 * ```
 */
export function SpecificationsTab({ listing }: SpecificationsTabProps) {
  const [computeDialogOpen, setComputeDialogOpen] = useState(false);
  const [memoryDialogOpen, setMemoryDialogOpen] = useState(false);
  const [storageDialogOpen, setStorageDialogOpen] = useState(false);
  const [connectivityDialogOpen, setConnectivityDialogOpen] = useState(false);

  return (
    <div className="space-y-4">
      {/* Compute Subsection */}
      <SpecificationSubsection
        title="Compute"
        isEmpty={!listing.cpu && !listing.cpu_name && !listing.gpu}
        onAddClick={() => setComputeDialogOpen(true)}
      >
        {/* CPU */}
        {(listing.cpu || listing.cpu_name) && (
          <FieldGroup label="CPU">
            {listing.cpu && listing.cpu.id ? (
              <EntityTooltip
                entityType="cpu"
                entityId={listing.cpu.id}
                variant="inline"
              >
                {listing.cpu.model || listing.cpu_name || "—"}
              </EntityTooltip>
            ) : (
              <span>{listing.cpu_name || "—"}</span>
            )}
          </FieldGroup>
        )}

        {/* GPU */}
        {listing.gpu && listing.gpu.id && (
          <FieldGroup label="GPU">
            <EntityTooltip
              entityType="gpu"
              entityId={listing.gpu.id}
              variant="inline"
            >
              {listing.gpu.model || listing.gpu.name || listing.gpu_name || "—"}
            </EntityTooltip>
          </FieldGroup>
        )}

        {/* GPU Score */}
        {listing.score_gpu !== null && (
          <FieldGroup label="GPU Score" value={listing.score_gpu.toFixed(1)} />
        )}
      </SpecificationSubsection>

      {/* Performance Metrics Section - Paired CPU metrics */}
      {(listing.cpu?.cpu_mark_single || listing.cpu?.cpu_mark_multi) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Single-Thread Metrics */}
            {listing.cpu?.cpu_mark_single && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-muted/50 rounded-lg">
                <PerformanceMetricDisplay
                  label="Single-Thread Score"
                  score={listing.cpu.cpu_mark_single}
                  prefix=""
                  suffix=""
                  decimals={0}
                />
                <PerformanceMetricDisplay
                  label="$/Single-Thread Mark"
                  baseValue={listing.dollar_per_cpu_mark_single ?? undefined}
                  adjustedValue={listing.dollar_per_cpu_mark_single_adjusted ?? undefined}
                  showColorCoding
                  listPrice={listing.price_usd ?? undefined}
                  adjustedPrice={listing.adjusted_price_usd ?? undefined}
                  cpuMark={listing.cpu.cpu_mark_single}
                  prefix="$"
                  decimals={4}
                />
              </div>
            )}

            {/* Multi-Thread Metrics */}
            {listing.cpu?.cpu_mark_multi && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-3 bg-muted/50 rounded-lg">
                <PerformanceMetricDisplay
                  label="Multi-Thread Score"
                  score={listing.cpu.cpu_mark_multi}
                  prefix=""
                  suffix=""
                  decimals={0}
                />
                <PerformanceMetricDisplay
                  label="$/Multi-Thread Mark"
                  baseValue={listing.dollar_per_cpu_mark_multi ?? undefined}
                  adjustedValue={listing.dollar_per_cpu_mark_multi_adjusted ?? undefined}
                  showColorCoding
                  listPrice={listing.price_usd ?? undefined}
                  adjustedPrice={listing.adjusted_price_usd ?? undefined}
                  cpuMark={listing.cpu.cpu_mark_multi}
                  prefix="$"
                  decimals={4}
                />
              </div>
            )}

            {/* Performance/Watt (if available) */}
            {listing.perf_per_watt !== null && listing.perf_per_watt !== undefined && (
              <div className="grid grid-cols-1 gap-4 p-3 bg-muted/50 rounded-lg">
                <FieldGroup label="Performance/Watt" value={listing.perf_per_watt.toFixed(2)} />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Memory Subsection */}
      <SpecificationSubsection
        title="Memory"
        isEmpty={!listing.ram_gb && !listing.ram_type}
        onAddClick={() => setMemoryDialogOpen(true)}
      >
        <FieldGroup label="RAM">
          {listing.ram_spec && listing.ram_spec_id ? (
            <EntityTooltip
              entityType="ram-spec"
              entityId={listing.ram_spec_id}
              variant="inline"
            >
              {listing.ram_gb ? `${listing.ram_gb} GB` : "—"}
              {listing.ram_type && ` ${listing.ram_type}`}
              {listing.ram_speed_mhz && ` @ ${listing.ram_speed_mhz} MHz`}
            </EntityTooltip>
          ) : (
            <span>
              {listing.ram_gb ? `${listing.ram_gb} GB` : "—"}
              {listing.ram_type && ` ${listing.ram_type}`}
              {listing.ram_speed_mhz && ` @ ${listing.ram_speed_mhz} MHz`}
            </span>
          )}
        </FieldGroup>
      </SpecificationSubsection>

      {/* Storage Subsection */}
      <SpecificationSubsection
        title="Storage"
        isEmpty={!listing.primary_storage_gb && !listing.secondary_storage_gb}
        onAddClick={() => setStorageDialogOpen(true)}
      >
        {/* Primary Storage */}
        {listing.primary_storage_gb && (
          <FieldGroup label="Primary Storage">
            {listing.primary_storage_profile && listing.primary_storage_profile_id ? (
              <EntityTooltip
                entityType="storage-profile"
                entityId={listing.primary_storage_profile_id}
                variant="inline"
              >
                {listing.primary_storage_gb} GB
                {listing.primary_storage_type && ` ${listing.primary_storage_type}`}
              </EntityTooltip>
            ) : (
              <span>
                {listing.primary_storage_gb} GB
                {listing.primary_storage_type && ` ${listing.primary_storage_type}`}
              </span>
            )}
          </FieldGroup>
        )}

        {/* Secondary Storage */}
        {listing.secondary_storage_gb && (
          <FieldGroup label="Secondary Storage">
            {listing.secondary_storage_profile && listing.secondary_storage_profile_id ? (
              <EntityTooltip
                entityType="storage-profile"
                entityId={listing.secondary_storage_profile_id}
                variant="inline"
              >
                {listing.secondary_storage_gb} GB
                {listing.secondary_storage_type && ` ${listing.secondary_storage_type}`}
              </EntityTooltip>
            ) : (
              <span>
                {listing.secondary_storage_gb} GB
                {listing.secondary_storage_type && ` ${listing.secondary_storage_type}`}
              </span>
            )}
          </FieldGroup>
        )}
      </SpecificationSubsection>

      {/* Connectivity Subsection */}
      <SpecificationSubsection
        title="Connectivity"
        isEmpty={!listing.ports_profile}
        onAddClick={() => setConnectivityDialogOpen(true)}
      >
        {listing.ports_profile && (
          <FieldGroup label="Ports">
            <div className="flex flex-wrap gap-1">
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
          </FieldGroup>
        )}
      </SpecificationSubsection>

      <Separator />

      {/* Product Details & Listing Info - 2 column layout on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Product Details Section */}
        {(listing.manufacturer || listing.series || listing.model_number || listing.form_factor) && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Product Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4">
                {listing.manufacturer && <FieldGroup label="Manufacturer" value={listing.manufacturer} />}
                {listing.series && <FieldGroup label="Series" value={listing.series} />}
                {listing.model_number && <FieldGroup label="Model Number" value={listing.model_number} />}
                {listing.form_factor && <FieldGroup label="Form Factor" value={listing.form_factor} />}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Listing Info Section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Listing Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4">
              {listing.seller && <FieldGroup label="Seller" value={listing.seller} />}

              {listing.listing_url && (
                <FieldGroup label="Listing URL">
                  <a
                    href={listing.listing_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                  >
                    View Listing
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </FieldGroup>
              )}

              {listing.other_urls && listing.other_urls.length > 0 && (
                <FieldGroup label="Other URLs">
                  <div className="flex flex-col gap-1">
                    {listing.other_urls.map((link, index) => (
                      <a
                        key={index}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                      >
                        {link.label || `Link ${index + 1}`}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ))}
                  </div>
                </FieldGroup>
              )}

              <FieldGroup label="Condition">
                <Badge variant={getConditionVariant(listing.condition)}>
                  {listing.condition}
                </Badge>
              </FieldGroup>

              <FieldGroup label="Status">
                <Badge variant={getStatusVariant(listing.status)}>
                  {listing.status}
                </Badge>
              </FieldGroup>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metadata - Collapsed by default in accordion */}
      <Accordion type="single" collapsible>
        <AccordionItem value="metadata">
          <AccordionTrigger className="text-base font-semibold">Additional Information</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
              <FieldGroup label="Created" value={new Date(listing.created_at).toLocaleString()} />
              <FieldGroup label="Last Updated" value={new Date(listing.updated_at).toLocaleString()} />
              {listing.ruleset_id && <FieldGroup label="Ruleset ID" value={listing.ruleset_id} />}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Custom Fields Section */}
      {listing.attributes && Object.keys(listing.attributes).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Custom Fields</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(listing.attributes).map(([key, value]) => (
                <FieldGroup
                  key={key}
                  label={formatFieldName(key)}
                  value={renderFieldValue(value)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick-Add Dialogs */}
      <QuickAddComputeDialog
        listingId={listing.id}
        open={computeDialogOpen}
        onOpenChange={setComputeDialogOpen}
      />
      <QuickAddMemoryDialog
        listingId={listing.id}
        open={memoryDialogOpen}
        onOpenChange={setMemoryDialogOpen}
      />
      <QuickAddStorageDialog
        listingId={listing.id}
        open={storageDialogOpen}
        onOpenChange={setStorageDialogOpen}
      />
      <QuickAddConnectivityDialog
        listingId={listing.id}
        open={connectivityDialogOpen}
        onOpenChange={setConnectivityDialogOpen}
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
  children?: React.ReactNode;
}

function FieldGroup({ label, value, children }: FieldGroupProps) {
  return (
    <div className="space-y-1">
      <Label className="text-xs uppercase tracking-wide text-muted-foreground">{label}</Label>
      <div className="text-sm font-medium">
        {children || value || "—"}
      </div>
    </div>
  );
}

/**
 * Format custom field names (convert snake_case to Title Case)
 */
function formatFieldName(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Render custom field values based on type
 */
function renderFieldValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

/**
 * Get badge variant based on condition
 */
function getConditionVariant(condition: string): "default" | "secondary" | "destructive" | "outline" {
  const lower = condition.toLowerCase();
  if (lower.includes("new") || lower.includes("excellent")) return "default";
  if (lower.includes("good") || lower.includes("refurb")) return "secondary";
  if (lower.includes("fair") || lower.includes("poor")) return "outline";
  return "secondary";
}

/**
 * Get badge variant based on status
 */
function getStatusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  const lower = status.toLowerCase();
  if (lower.includes("available") || lower.includes("active")) return "default";
  if (lower.includes("sold") || lower.includes("archived")) return "secondary";
  if (lower.includes("pending")) return "outline";
  return "secondary";
}
