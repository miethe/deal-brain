import type { ListingRecord, CpuRecord, PortsProfileRecord } from "./listings";

/**
 * Extended CPU record with additional fields for detail page
 */
export interface CpuRecordDetail extends CpuRecord {
  model?: string | null;
  base_clock_ghz?: number | null;
  boost_clock_ghz?: number | null;
}

/**
 * Extended GPU record with additional fields for detail page
 */
export interface GpuRecordDetail {
  id?: number | null;
  name?: string | null;
  model?: string | null;
  manufacturer?: string | null;
  vram_gb?: number | null;
}

/**
 * Extended ports profile with additional fields for detail page
 */
export interface PortsProfileRecordDetail extends PortsProfileRecord {
  usb_a_count?: number | null;
  usb_c_count?: number | null;
  hdmi_count?: number | null;
  displayport_count?: number | null;
}

/**
 * Extended listing type for detail page view
 * Includes all fields from ListingRecord with explicit nested relationships
 */
export interface ListingDetail extends Omit<ListingRecord, "cpu" | "gpu" | "ports_profile"> {
  cpu?: CpuRecordDetail | null;
  gpu?: GpuRecordDetail | null;
  ports_profile?: PortsProfileRecordDetail | null;
}

/**
 * Manufacturer logo mapping for fallback images
 */
export const MANUFACTURER_LOGOS: Record<string, string> = {
  Intel: "/images/fallbacks/intel.svg",
  AMD: "/images/fallbacks/amd.svg",
  NVIDIA: "/images/fallbacks/nvidia.svg",
  "NVIDIA GeForce": "/images/fallbacks/nvidia.svg",
  Default: "/images/fallbacks/pc-generic.svg",
};

/**
 * Tab identifiers for detail page navigation
 */
export type DetailPageTab = "specifications" | "valuation" | "history" | "notes";

/**
 * Valid tab values for URL query params
 */
export const DETAIL_PAGE_TABS: readonly DetailPageTab[] = [
  "specifications",
  "valuation",
  "history",
  "notes",
] as const;
