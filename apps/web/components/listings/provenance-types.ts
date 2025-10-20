/**
 * Type Definitions for Provenance Components
 *
 * Centralized type definitions for listing provenance and quality tracking.
 * These types should match the backend API schema for listing provenance data.
 */

/**
 * Data source provenance types
 *
 * - ebay_api: Data imported from eBay's official API
 * - jsonld: Data extracted from JSON-LD structured data on web pages
 * - scraper: Data obtained via web scraping
 * - excel: Data imported from Excel workbooks
 */
export type ProvenanceSource = 'ebay_api' | 'jsonld' | 'scraper' | 'excel';

/**
 * Data quality level
 *
 * - full: All required fields are present and validated
 * - partial: Some fields are missing or could not be extracted
 */
export type QualityLevel = 'full' | 'partial';

/**
 * Provenance metadata for a listing
 *
 * This interface represents the complete provenance information
 * that should be stored with each listing.
 */
export interface ListingProvenance {
  /**
   * The source system or method used to obtain this listing data
   */
  source: ProvenanceSource;

  /**
   * Quality level of the extracted data
   */
  quality: QualityLevel;

  /**
   * ISO datetime string of when this listing was last seen/updated
   */
  lastSeenAt: string;

  /**
   * Optional: List of field names that are missing (for partial quality)
   */
  missingFields?: string[];

  /**
   * Optional: Source URL where the data was obtained
   */
  sourceUrl?: string;

  /**
   * Optional: eBay listing ID (for ebay_api source)
   */
  ebayListingId?: string;

  /**
   * Optional: Confidence score (0-1) for scraped data
   */
  confidenceScore?: number;
}

/**
 * Extended listing interface with provenance
 *
 * Use this type when working with listings that include provenance data.
 */
export interface ListingWithProvenance {
  id: number;
  title: string;
  price: number;
  // ... other listing fields
  provenance?: ListingProvenance;
}

/**
 * Provenance statistics
 *
 * Aggregated statistics about data sources across all listings.
 */
export interface ProvenanceStats {
  totalListings: number;
  bySource: Record<ProvenanceSource, number>;
  byQuality: Record<QualityLevel, number>;
  averageAge: number; // Average days since last seen
}

/**
 * Type guard to check if a listing has provenance data
 */
export function hasProvenance(
  listing: Partial<ListingWithProvenance>
): listing is ListingWithProvenance & { provenance: ListingProvenance } {
  return listing.provenance !== undefined && listing.provenance !== null;
}

/**
 * Type guard to check if provenance quality is partial
 */
export function isPartialQuality(provenance: ListingProvenance): boolean {
  return provenance.quality === 'partial';
}

/**
 * Helper to determine if provenance data is stale
 * @param lastSeenAt ISO datetime string
 * @param staleDays Number of days to consider data stale (default: 7)
 */
export function isStaleProvenance(lastSeenAt: string, staleDays = 7): boolean {
  const lastSeen = new Date(lastSeenAt);
  const now = new Date();
  const daysDiff = (now.getTime() - lastSeen.getTime()) / (1000 * 60 * 60 * 24);
  return daysDiff > staleDays;
}
