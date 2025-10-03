/**
 * Valuation display utilities
 */

export interface ValuationThresholds {
  good_deal: number;
  great_deal: number;
  premium_warning: number;
}

export const DEFAULT_THRESHOLDS: ValuationThresholds = {
  good_deal: 15.0,
  great_deal: 25.0,
  premium_warning: 10.0,
};

export type ColorVariant = 'green' | 'red' | 'gray';
export type ColorIntensity = 'light' | 'medium' | 'dark';
export type IconType = 'arrow-down' | 'arrow-up' | 'minus';

export interface ValuationStyle {
  color: ColorVariant;
  intensity: ColorIntensity;
  icon: IconType;
  className: string;
}

/**
 * Calculate the valuation style based on delta percentage and thresholds
 */
export function getValuationStyle(
  deltaPercent: number,
  thresholds: ValuationThresholds
): ValuationStyle {
  // Great deal (25%+ savings)
  if (deltaPercent >= thresholds.great_deal) {
    return {
      color: 'green',
      intensity: 'dark',
      icon: 'arrow-down',
      className: 'bg-green-800 text-white border-green-900',
    };
  }

  // Good deal (15-25% savings)
  if (deltaPercent >= thresholds.good_deal) {
    return {
      color: 'green',
      intensity: 'medium',
      icon: 'arrow-down',
      className: 'bg-green-600 text-white border-green-700',
    };
  }

  // Light savings (1-15%)
  if (deltaPercent > 0) {
    return {
      color: 'green',
      intensity: 'light',
      icon: 'arrow-down',
      className: 'bg-green-100 text-green-800 border-green-200',
    };
  }

  // Significant premium (10%+ markup)
  if (deltaPercent < 0 && Math.abs(deltaPercent) >= thresholds.premium_warning) {
    return {
      color: 'red',
      intensity: 'dark',
      icon: 'arrow-up',
      className: 'bg-red-600 text-white border-red-700',
    };
  }

  // Light premium
  if (deltaPercent < 0) {
    return {
      color: 'red',
      intensity: 'light',
      icon: 'arrow-up',
      className: 'bg-red-100 text-red-800 border-red-200',
    };
  }

  // Neutral (no change)
  return {
    color: 'gray',
    intensity: 'light',
    icon: 'minus',
    className: 'bg-gray-100 text-gray-600 border-gray-200',
  };
}

/**
 * Format currency for display
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Calculate savings delta
 */
export function calculateDelta(listPrice: number, adjustedPrice: number): {
  delta: number;
  deltaPercent: number;
} {
  const delta = listPrice - adjustedPrice;
  const deltaPercent = listPrice > 0 ? (delta / listPrice) * 100 : 0;

  return { delta, deltaPercent };
}
