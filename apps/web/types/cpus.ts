/**
 * TypeScript type definitions for CPU API integration
 *
 * Matches backend Pydantic schemas from:
 * - packages/core/dealbrain_core/schemas/cpu.py (CPUWithAnalytics, CPUStatistics)
 * - packages/core/dealbrain_core/schemas/catalog.py (CpuRead)
 * - apps/api/dealbrain_api/api/cpus.py (API responses)
 */

/**
 * Base CPU record with analytics
 *
 * Includes:
 * - Core CPU specifications (name, manufacturer, socket, cores, threads, TDP, iGPU)
 * - Benchmark scores (PassMark single/multi-thread, iGPU Mark)
 * - Price targets from analytics (good, great, fair with confidence levels)
 * - Performance value metrics ($/mark ratios and percentile rankings)
 * - Timestamps and related data counts
 */
export interface CPURecord {
  // Core identification
  id: number;
  name: string;
  manufacturer: string; // "AMD" | "Intel"

  // Hardware specifications
  socket: string | null; // "AM4", "LGA1700", etc.
  cores: number | null;
  threads: number | null;
  tdp_w: number | null; // Thermal Design Power in Watts
  igpu_model: string | null; // Integrated GPU model name
  release_year: number | null;

  // Benchmark scores (from PassMark)
  cpu_mark_single: number | null; // Single-thread PassMark score
  cpu_mark_multi: number | null; // Multi-thread PassMark score
  igpu_mark: number | null; // Integrated GPU PassMark score

  // PassMark metadata
  passmark_slug: string | null;
  passmark_category: string | null;
  passmark_id: string | null;

  // Additional data
  notes: string | null;
  attributes_json: Record<string, any>;

  // Price targets from analytics (computed from listing data)
  price_target_good: number | null; // Average adjusted price (typical market price)
  price_target_great: number | null; // One std dev below average (better deals)
  price_target_fair: number | null; // One std dev above average (premium pricing)
  price_target_sample_size: number; // Number of listings used for calculation
  price_target_confidence: 'high' | 'medium' | 'low' | 'insufficient'; // Confidence level
  price_target_stddev: number | null; // Standard deviation of prices
  price_target_updated_at: string | null; // ISO datetime

  // Performance value from analytics ($/PassMark metrics)
  dollar_per_mark_single: number | null; // Price per single-thread PassMark point
  dollar_per_mark_multi: number | null; // Price per multi-thread PassMark point
  performance_value_percentile: number | null; // Percentile rank (0=best, 100=worst)
  performance_value_rating: 'excellent' | 'good' | 'fair' | 'poor' | null; // Value rating
  performance_metrics_updated_at: string | null; // ISO datetime

  // Related data counts
  listings_count: number;

  // Timestamps
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

/**
 * Price target detail
 *
 * Price targets are calculated from active listing adjusted prices:
 * - good: Average adjusted price (typical market price)
 * - great: One standard deviation below average (better deals)
 * - fair: One standard deviation above average (premium pricing)
 *
 * Confidence levels based on sample size:
 * - high: 10+ listings
 * - medium: 5-9 listings
 * - low: 2-4 listings
 * - insufficient: <2 listings
 */
export interface PriceTarget {
  good: number | null;
  great: number | null;
  fair: number | null;
  sample_size: number;
  confidence: 'high' | 'medium' | 'low' | 'insufficient';
  stddev: number | null;
  updated_at: string | null; // ISO datetime
}

/**
 * Performance value detail
 *
 * Measures price efficiency based on PassMark benchmark scores:
 * - Lower $/mark ratio = better value
 * - Percentile ranks CPUs where 0 = best value, 100 = worst value
 *
 * Rating quartiles:
 * - excellent: 0-25th percentile (top 25% value)
 * - good: 25-50th percentile
 * - fair: 50-75th percentile
 * - poor: 75-100th percentile (bottom 25% value)
 */
export interface PerformanceValue {
  dollar_per_mark_single: number | null;
  dollar_per_mark_multi: number | null;
  percentile: number | null; // 0-100 where 0 is best value
  rating: 'excellent' | 'good' | 'fair' | 'poor' | null;
  updated_at: string | null; // ISO datetime
}

/**
 * CPU Detail response (for detail modal/panel)
 *
 * Extends CPURecord with market data:
 * - Top 10 associated listings (cheapest by adjusted price)
 * - Price distribution for histogram visualization
 *
 * Response structure from GET /v1/cpus/{id}:
 * - All CPURecord fields (flattened at top level)
 * - associated_listings: Array of listing previews
 * - market_data: Object containing price_distribution array
 */
export interface CPUDetail extends CPURecord {
  associated_listings: ListingPreview[]; // Top 10 associated listings
  market_data: {
    price_distribution: number[]; // Array of price values for histogram
  };
}

/**
 * Listing preview for CPU detail view
 *
 * Minimal listing data for display in CPU detail modal
 */
export interface ListingPreview {
  id: number;
  title: string;
  base_price_usd: number;
  adjusted_price_usd: number;
  marketplace: string;
  condition: string;
  url: string | null;
  status: string;
}

/**
 * Statistics for filters
 *
 * Provides metadata about available CPUs for building filter UI controls.
 * Used in CPU catalog views to populate filter dropdowns and range sliders.
 */
export interface CPUStatistics {
  manufacturers: string[]; // Unique manufacturers in the catalog (sorted)
  sockets: string[]; // Unique socket types in the catalog (sorted)
  core_range: [number, number]; // [min, max] core counts
  tdp_range: [number, number]; // [min, max] TDP values in watts
  year_range: [number, number]; // [min, max] release years
  total_count: number; // Total number of CPUs in catalog
}
