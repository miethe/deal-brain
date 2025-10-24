"use client";

import { ListingValuationTab } from "./listing-valuation-tab";
import type { ListingDetail } from "@/types/listing-detail";

interface ValuationTabPageProps {
  listing: ListingDetail;
}

/**
 * Valuation tab wrapper component for detail page
 *
 * Reuses existing ListingValuationTab component that displays:
 * - Top 4 contributing valuation rules (sorted by impact)
 * - Rule details with color-coded adjustments
 * - "View Full Breakdown" button to open modal
 * - Ruleset override controls
 *
 * @example
 * ```tsx
 * <ValuationTabPage listing={listing} />
 * ```
 */
export function ValuationTabPage({ listing }: ValuationTabPageProps) {
  return <ListingValuationTab listing={listing} />;
}
