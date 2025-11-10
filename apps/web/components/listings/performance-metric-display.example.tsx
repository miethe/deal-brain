/**
 * Example Usage of PerformanceMetricDisplay Component
 *
 * This file demonstrates various use cases for the PerformanceMetricDisplay component.
 */

import { PerformanceMetricDisplay } from './performance-metric-display';
import type { ListingRecord } from '@/types/listings';

/**
 * Example 1: Display CPU Mark Multi-Thread Efficiency
 *
 * Shows price-per-mark for multi-threaded performance with color coding.
 */
export function Example1_CPUMarkMulti({ listing }: { listing: ListingRecord }) {
  return (
    <PerformanceMetricDisplay
      label="$/CPU Mark Multi"
      baseValue={listing.dollar_per_cpu_mark_multi}
      adjustedValue={listing.dollar_per_cpu_mark_multi_adjusted}
      listPrice={listing.price_usd}
      adjustedPrice={listing.adjusted_price_usd || listing.price_usd}
      cpuMark={listing.cpu?.cpu_mark_multi || undefined}
      prefix="$"
      decimals={3}
      showColorCoding
    />
  );
}

/**
 * Example 2: Display CPU Mark Single-Thread Efficiency
 *
 * Shows price-per-mark for single-threaded performance.
 */
export function Example2_CPUMarkSingle({ listing }: { listing: ListingRecord }) {
  return (
    <PerformanceMetricDisplay
      label="$/CPU Mark Single"
      baseValue={listing.dollar_per_cpu_mark_single}
      adjustedValue={listing.dollar_per_cpu_mark_single_adjusted}
      listPrice={listing.price_usd}
      adjustedPrice={listing.adjusted_price_usd || listing.price_usd}
      cpuMark={listing.cpu?.cpu_mark_single || undefined}
      prefix="$"
      decimals={3}
      showColorCoding
    />
  );
}

/**
 * Example 3: Display with Score
 *
 * Shows both a composite score and the efficiency metric.
 */
export function Example3_WithScore({ listing }: { listing: ListingRecord }) {
  return (
    <PerformanceMetricDisplay
      label="CPU Multi-Thread"
      score={listing.score_cpu_multi || undefined}
      baseValue={listing.dollar_per_cpu_mark_multi}
      adjustedValue={listing.dollar_per_cpu_mark_multi_adjusted}
      listPrice={listing.price_usd}
      adjustedPrice={listing.adjusted_price_usd || listing.price_usd}
      cpuMark={listing.cpu?.cpu_mark_multi || undefined}
      prefix="$"
      suffix="/mark"
      decimals={3}
      showColorCoding
    />
  );
}

/**
 * Example 4: Simple Display (No Tooltip)
 *
 * Shows just the metric without detailed calculation tooltip.
 */
export function Example4_SimpleDisplay({ listing }: { listing: ListingRecord }) {
  return (
    <PerformanceMetricDisplay
      label="Efficiency"
      adjustedValue={listing.dollar_per_cpu_mark_multi_adjusted}
      prefix="$"
      decimals={3}
      showColorCoding={false}
    />
  );
}

/**
 * Example 5: In a Table Cell
 *
 * Demonstrates usage within a table structure.
 */
export function Example5_TableUsage({ listings }: { listings: ListingRecord[] }) {
  return (
    <table className="w-full">
      <thead>
        <tr>
          <th>Title</th>
          <th>Price</th>
          <th>CPU Mark Efficiency</th>
        </tr>
      </thead>
      <tbody>
        {listings.map((listing) => (
          <tr key={listing.id}>
            <td>{listing.title}</td>
            <td>${listing.price_usd.toFixed(0)}</td>
            <td>
              <PerformanceMetricDisplay
                label="$/CPU Mark"
                baseValue={listing.dollar_per_cpu_mark_multi}
                adjustedValue={listing.dollar_per_cpu_mark_multi_adjusted}
                listPrice={listing.price_usd}
                adjustedPrice={listing.adjusted_price_usd || listing.price_usd}
                cpuMark={listing.cpu?.cpu_mark_multi || undefined}
                prefix="$"
                decimals={3}
                showColorCoding
                delayDuration={200} // Slightly longer delay for table cells
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/**
 * Example 6: Custom Formatting
 *
 * Shows custom prefix, suffix, and decimal precision.
 */
export function Example6_CustomFormatting({ listing }: { listing: ListingRecord }) {
  return (
    <PerformanceMetricDisplay
      label="Performance Per Dollar"
      baseValue={
        listing.cpu?.cpu_mark_multi && listing.price_usd
          ? listing.cpu.cpu_mark_multi / listing.price_usd
          : undefined
      }
      adjustedValue={
        listing.cpu?.cpu_mark_multi && listing.adjusted_price_usd
          ? listing.cpu.cpu_mark_multi / listing.adjusted_price_usd
          : undefined
      }
      prefix=""
      suffix=" marks/$"
      decimals={2}
      showColorCoding
    />
  );
}

/**
 * Example 7: Handling Missing Data
 *
 * Gracefully handles cases where performance metrics are unavailable.
 */
export function Example7_MissingData({ listing }: { listing: ListingRecord }) {
  return (
    <div className="space-y-2">
      <PerformanceMetricDisplay
        label="$/CPU Mark Multi"
        baseValue={listing.dollar_per_cpu_mark_multi}
        adjustedValue={listing.dollar_per_cpu_mark_multi_adjusted}
        prefix="$"
        decimals={3}
      />

      {!listing.dollar_per_cpu_mark_multi && (
        <p className="text-xs text-muted-foreground">
          CPU benchmark data not available
        </p>
      )}
    </div>
  );
}
