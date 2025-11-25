/**
 * CPU Mark Performance Metric Utilities
 *
 * Utilities for calculating, formatting, and styling CPU performance metrics
 * based on price-to-performance improvements.
 */

export interface CpuMarkThresholds {
  excellent: number;
  good: number;
  fair: number;
  neutral: number;
  poor: number;
  premium: number;
}

export const DEFAULT_CPU_MARK_THRESHOLDS: CpuMarkThresholds = {
  excellent: 20.0,   // ≥20% improvement
  good: 10.0,        // 10-20% improvement
  fair: 5.0,         // 5-10% improvement
  neutral: 0.0,      // 0-5% change
  poor: -10.0,       // -10-0% degradation
  premium: -20.0,    // <-10% degradation
};

export type CpuMarkColorClass = 'excellent' | 'good' | 'fair' | 'neutral' | 'poor' | 'premium';

export interface CpuMarkStyle {
  colorClass: CpuMarkColorClass;
  label: string;
  className: string;
}

/**
 * Calculate percentage improvement between base and adjusted values.
 * Positive improvement means adjusted value is LOWER (better price efficiency).
 *
 * @param baseValue - Base value (e.g., dollar per CPU mark using list price)
 * @param adjustedValue - Adjusted value (e.g., dollar per CPU mark using adjusted price)
 * @returns Improvement percentage (positive = better efficiency)
 *
 * @example
 * // List price: $1000, CPU Mark: 10000 → $0.100 per mark
 * // Adjusted price: $800, CPU Mark: 10000 → $0.080 per mark
 * // Improvement: ((0.100 - 0.080) / 0.100) * 100 = 20% (excellent!)
 */
export function calculateImprovement(baseValue: number, adjustedValue: number): number {
  if (baseValue === 0) return 0;

  // Lower is better for price-per-mark, so positive improvement means adjusted < base
  const improvement = ((baseValue - adjustedValue) / baseValue) * 100;
  return improvement;
}

/**
 * Determine CPU mark style based on improvement percentage and thresholds.
 * Includes CSS class names using CSS variables for theme-aware colors.
 *
 * @param improvement - Improvement percentage (from calculateImprovement)
 * @param thresholds - Threshold configuration
 * @returns Style object with color class, label, and CSS classes
 */
export function getCpuMarkStyle(
  improvement: number,
  thresholds: CpuMarkThresholds
): CpuMarkStyle {
  // Excellent: ≥20% improvement
  if (improvement >= thresholds.excellent) {
    return {
      colorClass: 'excellent',
      label: 'Excellent',
      className: 'bg-[hsl(var(--cpu-mark-excellent-bg))] text-[hsl(var(--cpu-mark-excellent-fg))] border-[hsl(var(--cpu-mark-excellent-bg))]',
    };
  }

  // Good: 10-20% improvement
  if (improvement >= thresholds.good) {
    return {
      colorClass: 'good',
      label: 'Good',
      className: 'bg-[hsl(var(--cpu-mark-good-bg))] text-[hsl(var(--cpu-mark-good-fg))] border-[hsl(var(--cpu-mark-good-bg))]',
    };
  }

  // Fair: 5-10% improvement
  if (improvement >= thresholds.fair) {
    return {
      colorClass: 'fair',
      label: 'Fair',
      className: 'bg-[hsl(var(--cpu-mark-fair-bg))] text-[hsl(var(--cpu-mark-fair-fg))] border-[hsl(var(--cpu-mark-fair-bg))]',
    };
  }

  // Neutral: 0-5% change
  if (improvement >= thresholds.neutral) {
    return {
      colorClass: 'neutral',
      label: 'Neutral',
      className: 'bg-[hsl(var(--cpu-mark-neutral-bg))] text-[hsl(var(--cpu-mark-neutral-fg))] border-[hsl(var(--cpu-mark-neutral-bg))]',
    };
  }

  // Poor: -10-0% degradation
  if (improvement >= thresholds.poor) {
    return {
      colorClass: 'poor',
      label: 'Poor',
      className: 'bg-[hsl(var(--cpu-mark-poor-bg))] text-[hsl(var(--cpu-mark-poor-fg))] border-[hsl(var(--cpu-mark-poor-bg))]',
    };
  }

  // Premium: <-10% degradation
  return {
    colorClass: 'premium',
    label: 'Premium',
    className: 'bg-[hsl(var(--cpu-mark-premium-bg))] text-[hsl(var(--cpu-mark-premium-fg))] border-[hsl(var(--cpu-mark-premium-bg))]',
  };
}

/**
 * Format CPU mark value for display with configurable precision.
 *
 * @param value - CPU mark value (e.g., dollar per CPU mark)
 * @param decimals - Number of decimal places (default: 3)
 * @returns Formatted string with fixed decimals
 *
 * @example
 * formatCpuMark(0.08512, 3) // "0.085"
 * formatCpuMark(0.08512, 4) // "0.0851"
 */
export function formatCpuMark(value: number, decimals: number = 3): string {
  return value.toFixed(decimals);
}

/**
 * Format improvement percentage for display.
 *
 * @param improvement - Improvement percentage
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted string with sign and percentage symbol
 *
 * @example
 * formatImprovement(15.7) // "+15.7%"
 * formatImprovement(-5.2) // "-5.2%"
 */
export function formatImprovement(improvement: number, decimals: number = 1): string {
  const sign = improvement > 0 ? '+' : '';
  return `${sign}${improvement.toFixed(decimals)}%`;
}

/**
 * Get arrow indicator based on improvement direction.
 * Positive improvement (better efficiency) shows downward arrow.
 * Negative improvement (worse efficiency) shows upward arrow.
 *
 * @param improvement - Improvement percentage
 * @returns Arrow symbol and aria label
 */
export function getImprovementArrow(improvement: number): {
  symbol: string;
  ariaLabel: string;
} {
  if (Math.abs(improvement) < 0.1) {
    return {
      symbol: '→',
      ariaLabel: 'no significant change',
    };
  }

  if (improvement > 0) {
    return {
      symbol: '↓',
      ariaLabel: 'improved efficiency',
    };
  }

  return {
    symbol: '↑',
    ariaLabel: 'reduced efficiency',
  };
}
