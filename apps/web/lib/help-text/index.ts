/**
 * Help Text Library - Main Export
 *
 * @module help-text
 * @description Centralized exports for all help text configurations.
 * Import from this file for clean, consistent imports throughout the app.
 *
 * @example
 * ```typescript
 * // Import specific exports
 * import { METRIC_TOOLTIPS, getMetricTooltip } from '@/lib/help-text';
 *
 * // Or import from specific module
 * import { METRIC_TOOLTIPS } from '@/lib/help-text/cpu-catalog-help';
 * ```
 */

// Re-export all CPU Catalog help text
export {
  // Tooltip constants
  METRIC_TOOLTIPS,
  FILTER_HELP,
  EMPTY_STATES,
  ERROR_MESSAGES,
  INFO_BANNERS,
  VIEW_DESCRIPTIONS,
  CHART_DESCRIPTIONS,

  // Helper functions
  getMetricTooltip,
  getFilterHelp,
  getEmptyState,
  getErrorMessage,
  getInfoBanner,
  getConfidenceTooltip,
  getPerformanceValueTooltip,

  // Type exports
  type MetricTooltipKey,
  type FilterHelpKey,
  type EmptyStateKey,
  type ErrorMessageKey,
  type InfoBannerKey,
  type ViewDescriptionKey,
  type ChartDescriptionKey,
} from './cpu-catalog-help';
