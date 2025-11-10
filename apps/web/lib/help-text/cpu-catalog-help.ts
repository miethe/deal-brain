/**
 * Centralized Help Text for CPU Catalog Feature
 *
 * @module cpu-catalog-help
 * @description Provides tooltips, empty states, error messages, and contextual help
 * for all CPU Catalog views and components. This centralized configuration ensures
 * consistency across the application and makes it easy to maintain and update help text.
 *
 * Usage:
 * ```typescript
 * import { METRIC_TOOLTIPS, EMPTY_STATES } from '@/lib/help-text/cpu-catalog-help';
 *
 * // In a tooltip
 * <TooltipContent>{METRIC_TOOLTIPS.cpuMark.content}</TooltipContent>
 *
 * // In an empty state
 * <EmptyState
 *   title={EMPTY_STATES.noResults.title}
 *   message={EMPTY_STATES.noResults.message}
 * />
 * ```
 *
 * Future i18n Support:
 * - All text strings are centralized for easy translation
 * - Can be converted to use i18n library keys
 * - Structure supports locale-specific content
 */

// ============================================================================
// TOOLTIPS - Metric Explanations
// ============================================================================

export const METRIC_TOOLTIPS = {
  // Performance Value Metrics
  performanceValueExcellent: {
    title: "Excellent Value",
    content:
      "This CPU offers exceptional price-to-performance ratio, ranking in the top 25% for value. You're getting the most performance per dollar spent.",
  },
  performanceValueGood: {
    title: "Good Value",
    content:
      "This CPU offers above-average price-to-performance ratio. A solid choice with good bang-for-buck.",
  },
  performanceValueFair: {
    title: "Fair Value",
    content:
      "This CPU offers average price-to-performance ratio. Consider whether other factors (features, availability) justify the price.",
  },
  performanceValuePoor: {
    title: "Poor Value",
    content:
      "This CPU has below-average price-to-performance ratio. Consider alternatives unless specific features are required.",
  },

  // Dollar Per Mark Metrics
  dollarPerMarkSingle: {
    title: "$/Single-Thread Mark",
    content:
      "Dollars per PassMark single-thread point. Lower is better. Single-thread performance matters for gaming, responsiveness, and tasks that don't parallelize well.",
  },
  dollarPerMarkMulti: {
    title: "$/Multi-Thread Mark (CPU Mark)",
    content:
      "Dollars per PassMark CPU Mark (multi-thread) point. Lower is better. Multi-thread performance matters for video editing, 3D rendering, and heavy multitasking.",
  },

  // Percentile
  performancePercentile: {
    title: "Value Percentile",
    content:
      "Statistical ranking of price efficiency among all CPUs. Lower percentile = better value (e.g., 15th percentile means top 15% for value).",
  },

  // Price Targets
  priceTargetGreat: {
    title: "Great Price (25th Percentile)",
    content:
      "An excellent deal. This price is lower than 75% of recent marketplace listings for this CPU. Strong buy signal if the listing is legitimate.",
  },
  priceTargetGood: {
    title: "Good Price (Median)",
    content:
      "A fair market price. This price represents the middle of the market - half of listings are higher, half are lower. A reasonable price to pay.",
  },
  priceTargetFair: {
    title: "Fair Price (75th Percentile)",
    content:
      "An acceptable but not optimal price. This price is higher than 75% of recent listings. Consider negotiating or waiting for a better deal.",
  },

  // Confidence Badges
  confidenceHigh: {
    title: "High Confidence",
    content:
      "Based on 10+ recent marketplace listings. Price targets are statistically reliable with strong sample size.",
  },
  confidenceMedium: {
    title: "Medium Confidence",
    content:
      "Based on 5-9 recent marketplace listings. Price targets are moderately reliable but could vary with more data.",
  },
  confidenceLow: {
    title: "Low Confidence",
    content:
      "Based on 2-4 recent marketplace listings. Price targets are less reliable due to limited sample size. Use with caution.",
  },
  confidenceInsufficient: {
    title: "Insufficient Data",
    content:
      "Fewer than 2 recent marketplace listings. Not enough data to calculate reliable price targets. Check back later or explore alternative models.",
  },

  // PassMark Scores
  cpuMark: {
    title: "CPU Mark (Multi-Thread)",
    content:
      "PassMark multi-threaded benchmark score. Higher is better. Measures overall CPU performance across multiple cores. Important for productivity, rendering, and multitasking.",
  },
  singleThreadRating: {
    title: "Single-Thread Rating",
    content:
      "PassMark single-core benchmark score. Higher is better. Measures single-core performance. Important for gaming, responsiveness, and single-threaded applications.",
  },
  igpuMark: {
    title: "iGPU Mark",
    content:
      "PassMark integrated graphics benchmark score. Higher is better. Measures performance of CPU's built-in graphics (if present). Relevant if not using a discrete GPU.",
  },

  // Specifications
  tdp: {
    title: "TDP (Thermal Design Power)",
    content:
      "Maximum heat output in watts. Lower TDP means less power consumption and heat, but may limit performance. Consider your cooling solution and power budget.",
  },
  socket: {
    title: "CPU Socket",
    content:
      "Physical connection to motherboard (e.g., LGA1700, AM5). Must match your motherboard socket. Different sockets are incompatible.",
  },
  releaseYear: {
    title: "Release Year",
    content:
      "Year this CPU model was released. Newer isn't always better for value; slightly older CPUs often offer excellent price-to-performance.",
  },
  cores: {
    title: "Core Count",
    content:
      "Number of physical CPU cores. More cores = better multitasking and multi-threaded performance. Most users need 6-8 cores; power users may want 12+.",
  },
  threads: {
    title: "Thread Count",
    content:
      "Number of simultaneous processing threads supported. Often double the core count with hyperthreading/SMT. More threads improve parallel processing.",
  },
  activeListingsCount: {
    title: "Active Listings",
    content:
      "Number of current marketplace listings for this CPU. More listings = more options and competitive pricing. Fewer listings = limited availability.",
  },
  manufacturer: {
    title: "Manufacturer",
    content:
      "CPU manufacturer (Intel or AMD). Each has different architectures, features, and pricing strategies. Check motherboard compatibility before purchasing.",
  },
} as const;

// ============================================================================
// FILTER HELP - Understanding Filter Controls
// ============================================================================

export const FILTER_HELP = {
  manufacturer: {
    label: "Manufacturer",
    help: "Filter by CPU manufacturer (Intel or AMD). Each has different architectures, features, and pricing strategies.",
  },
  socket: {
    label: "Socket Type",
    help: "Filter by motherboard socket (e.g., LGA1700, AM5). Must match your motherboard. Check your motherboard specs before filtering.",
  },
  cores: {
    label: "Core Count",
    help: "Filter by number of physical CPU cores. More cores = better multitasking and multi-threaded performance. Most users need 6-8 cores; power users may want 12+.",
  },
  releaseYear: {
    label: "Release Year",
    help: "Filter by CPU release year. Newer CPUs have latest features but cost more. Older CPUs (1-2 years) often offer better value.",
  },
  tdp: {
    label: "TDP (Watts)",
    help: "Filter by maximum power consumption. Lower TDP (35-65W) for low-power/small builds. Higher TDP (95-125W) for maximum performance.",
  },
  cpuMark: {
    label: "CPU Performance",
    help: "Filter by PassMark CPU Mark score (overall performance). Set minimum score based on your workload needs.",
  },
  priceRange: {
    label: "Price Range",
    help: "Filter by Good Price range. Set your budget to see CPUs with market prices within your range.",
  },
  performanceValue: {
    label: "Performance Value",
    help: "Filter by value rating (Excellent, Good, Fair, Poor). Focus on Excellent/Good for best bang-for-buck.",
  },
  hasListings: {
    label: "Has Active Listings",
    help: "Only show CPUs with current marketplace listings. Useful to filter out unavailable or rare models.",
  },
  hasIGPU: {
    label: "Has Integrated GPU",
    help: "Only show CPUs with integrated graphics. Useful if building without a discrete graphics card.",
  },
  search: {
    label: "Search",
    help: "Search by CPU name or model number. Supports partial matches (e.g., 'i7' or '7800X3D').",
  },
  minPassMark: {
    label: "Minimum PassMark",
    help: "Set minimum PassMark score (checks both single and multi-thread). Useful for filtering by performance tier.",
  },
} as const;

// ============================================================================
// EMPTY STATES - No Results or Missing Data
// ============================================================================

export const EMPTY_STATES = {
  noResults: {
    title: "No CPUs Found",
    message:
      "No CPUs match your current filters. Try broadening your search criteria or clearing some filters.",
    action: "Clear All Filters",
  },
  noCPUs: {
    title: "No CPUs Available",
    message:
      "The CPU catalog is empty. CPUs will appear once data is imported from marketplace listings.",
    action: null,
  },
  noListings: {
    title: "No Active Listings",
    message:
      "This CPU currently has no active marketplace listings. Check back later or explore alternative models.",
    action: "Browse Similar CPUs",
  },
  noPriceTargets: {
    title: "Insufficient Pricing Data",
    message:
      "Not enough marketplace listings to calculate reliable price targets. At least 2 listings are needed for statistical analysis.",
    action: null,
  },
  noPerformanceValue: {
    title: "Performance Data Unavailable",
    message:
      "Performance value cannot be calculated without benchmark scores and price data. Check PassMark for benchmark information.",
    action: "View on PassMark",
  },
  noChartData: {
    title: "Chart Data Unavailable",
    message:
      "Not enough data to generate this chart. More marketplace listings are needed for meaningful visualization.",
    action: null,
  },
  noSearchResults: {
    title: "No Matching CPUs",
    message:
      "Your search didn't match any CPUs. Check your spelling or try different keywords.",
    action: "Clear Search",
  },
  noAnalyticsData: {
    title: "Analytics Data Not Available",
    message:
      "Analytics data requires active listings and price history. Check back once more data is available.",
    action: null,
  },
  noBenchmarkData: {
    title: "Benchmark Data Missing",
    message:
      "PassMark benchmark scores are not available for this CPU. Performance metrics cannot be calculated.",
    action: null,
  },
} as const;

// ============================================================================
// ERROR MESSAGES - Actionable Error Handling
// ============================================================================

export const ERROR_MESSAGES = {
  loadCPUsFailed: {
    title: "Failed to Load CPUs",
    message:
      "Unable to load CPU catalog. Please check your connection and try again.",
    action: "Retry",
  },
  loadCPUDetailFailed: {
    title: "Failed to Load CPU Details",
    message:
      "Unable to load detailed information for this CPU. The data may be temporarily unavailable.",
    action: "Try Another CPU",
  },
  loadStatisticsFailed: {
    title: "Failed to Load Statistics",
    message:
      "Unable to load CPU catalog statistics. Filters may not work correctly until this is resolved.",
    action: "Refresh Page",
  },
  filterApplyFailed: {
    title: "Filter Error",
    message:
      "An error occurred while applying filters. Try clearing filters and reapplying.",
    action: "Clear Filters",
  },
  invalidCPUId: {
    title: "Invalid CPU",
    message:
      "The requested CPU could not be found. It may have been removed or the link is incorrect.",
    action: "Back to Catalog",
  },
  networkError: {
    title: "Network Error",
    message:
      "Unable to connect to the server. Check your internet connection and try again.",
    action: "Retry",
  },
  unexpectedError: {
    title: "Something Went Wrong",
    message:
      "An unexpected error occurred. If this persists, please contact support.",
    action: "Reload Page",
  },
  loadChartDataFailed: {
    title: "Chart Data Load Failed",
    message:
      "Unable to load chart data for analytics. The visualization cannot be displayed.",
    action: "Retry",
  },
  searchFailed: {
    title: "Search Error",
    message:
      "An error occurred while searching. Please try again or clear your search.",
    action: "Clear Search",
  },
} as const;

// ============================================================================
// INFO BANNERS - Contextual Guidance
// ============================================================================

export const INFO_BANNERS = {
  priceTargetsExplanation: {
    variant: "info" as const,
    title: "Understanding Price Targets",
    message:
      "Price targets are calculated from real marketplace listings. Great Price = top 25% deals, Good Price = median, Fair Price = top 75%. Higher confidence means more listings sampled.",
  },
  performanceValueExplanation: {
    variant: "info" as const,
    title: "What is Performance Value?",
    message:
      "Performance value measures dollars per PassMark point. Lower is better—you get more performance for your money. Excellent = top 25% value, Good = above average, Fair = average, Poor = below average.",
  },
  insufficientDataWarning: {
    variant: "warning" as const,
    title: "Limited Market Data",
    message:
      "This CPU has fewer than 2 active listings. Price targets and market insights are not available. Consider alternative models with more market activity.",
  },
  outdatedDataWarning: {
    variant: "warning" as const,
    title: "Outdated Price Targets",
    message:
      "Price targets were last updated over 7 days ago. Market conditions may have changed. Refresh is scheduled nightly.",
  },
  filterTipsInfo: {
    variant: "tip" as const,
    title: "Filtering Tips",
    message:
      "Start broad, then narrow. Filter by socket first (motherboard compatibility), then by core count (workload needs), then by budget (price range). Focus on Excellent/Good performance value for best deals.",
  },
  firstTimeUserTip: {
    variant: "tip" as const,
    title: "New to CPU Catalog?",
    message:
      "Start by filtering for your motherboard socket, then set a budget using the Price Range filter. Look for CPUs with 'Excellent' or 'Good' performance value badges for the best deals.",
  },
  analyticsInfo: {
    variant: "info" as const,
    title: "Analytics Insights",
    message:
      "Charts show market trends, price distribution, and value analysis based on active listings. Data refreshes daily to reflect current market conditions.",
  },
  confidenceInfo: {
    variant: "info" as const,
    title: "Confidence Levels",
    message:
      "High = 10+ listings (most reliable), Medium = 5-9 listings (moderately reliable), Low = 2-4 listings (use with caution). More listings = more accurate price targets.",
  },
} as const;

// ============================================================================
// VIEW DESCRIPTIONS - Help Text for Different Views
// ============================================================================

export const VIEW_DESCRIPTIONS = {
  gridView: {
    name: "Grid View",
    description:
      "Visual card layout showing CPU overview, performance value, and price targets. Best for browsing and comparing multiple CPUs at a glance.",
  },
  listView: {
    name: "List View",
    description:
      "Dense table layout with sortable columns and quick comparison. Best for analyzing specific metrics across many CPUs.",
  },
  masterDetailView: {
    name: "Master-Detail View",
    description:
      "Split-pane layout with CPU list and detailed panel. Best for exploring individual CPUs in depth while maintaining context.",
  },
  detailPanel: {
    name: "Detail Panel",
    description:
      "Comprehensive CPU information including specifications, performance metrics, price targets, and analytics charts. Best for in-depth analysis.",
  },
} as const;

// ============================================================================
// CHART DESCRIPTIONS - Help Text for Analytics Charts
// ============================================================================

export const CHART_DESCRIPTIONS = {
  priceDistribution: {
    title: "Price Distribution",
    description:
      "Histogram showing distribution of active listing prices. Helps identify common price points and outliers.",
  },
  priceHistory: {
    title: "Price History",
    description:
      "Time series of median, min, and max prices over time. Shows market trends and price stability.",
  },
  valueComparison: {
    title: "Value Comparison",
    description:
      "Scatter plot comparing price vs performance. CPUs closer to bottom-left offer better value (low price, high performance).",
  },
  marketShare: {
    title: "Market Share",
    description:
      "Pie chart showing distribution of active listings by manufacturer or socket type. Indicates market availability.",
  },
} as const;

// ============================================================================
// TYPE EXPORTS - For TypeScript Type Safety
// ============================================================================

export type MetricTooltipKey = keyof typeof METRIC_TOOLTIPS;
export type FilterHelpKey = keyof typeof FILTER_HELP;
export type EmptyStateKey = keyof typeof EMPTY_STATES;
export type ErrorMessageKey = keyof typeof ERROR_MESSAGES;
export type InfoBannerKey = keyof typeof INFO_BANNERS;
export type ViewDescriptionKey = keyof typeof VIEW_DESCRIPTIONS;
export type ChartDescriptionKey = keyof typeof CHART_DESCRIPTIONS;

// ============================================================================
// HELPER FUNCTIONS - Utility Functions for Help Text
// ============================================================================

/**
 * Get tooltip content for a metric
 *
 * @param key - Metric tooltip key
 * @returns Tooltip object with title and content
 *
 * @example
 * const tooltip = getMetricTooltip('cpuMark');
 * // { title: "CPU Mark (Multi-Thread)", content: "..." }
 */
export function getMetricTooltip(key: MetricTooltipKey) {
  return METRIC_TOOLTIPS[key];
}

/**
 * Get filter help content
 *
 * @param key - Filter help key
 * @returns Filter help object with label and help text
 *
 * @example
 * const help = getFilterHelp('socket');
 * // { label: "Socket Type", help: "..." }
 */
export function getFilterHelp(key: FilterHelpKey) {
  return FILTER_HELP[key];
}

/**
 * Get empty state content
 *
 * @param key - Empty state key
 * @returns Empty state object with title, message, and optional action
 *
 * @example
 * const emptyState = getEmptyState('noResults');
 * // { title: "No CPUs Found", message: "...", action: "Clear All Filters" }
 */
export function getEmptyState(key: EmptyStateKey) {
  return EMPTY_STATES[key];
}

/**
 * Get error message content
 *
 * @param key - Error message key
 * @returns Error message object with title, message, and action
 *
 * @example
 * const error = getErrorMessage('loadCPUsFailed');
 * // { title: "Failed to Load CPUs", message: "...", action: "Retry" }
 */
export function getErrorMessage(key: ErrorMessageKey) {
  return ERROR_MESSAGES[key];
}

/**
 * Get info banner content
 *
 * @param key - Info banner key
 * @returns Info banner object with variant, title, and message
 *
 * @example
 * const banner = getInfoBanner('priceTargetsExplanation');
 * // { variant: "info", title: "...", message: "..." }
 */
export function getInfoBanner(key: InfoBannerKey) {
  return INFO_BANNERS[key];
}

/**
 * Get confidence tooltip based on confidence level
 *
 * @param confidence - Confidence level
 * @returns Tooltip content for the confidence level
 *
 * @example
 * const tooltip = getConfidenceTooltip('high');
 * // { title: "High Confidence", content: "..." }
 */
export function getConfidenceTooltip(
  confidence: "high" | "medium" | "low" | "insufficient"
) {
  switch (confidence) {
    case "high":
      return METRIC_TOOLTIPS.confidenceHigh;
    case "medium":
      return METRIC_TOOLTIPS.confidenceMedium;
    case "low":
      return METRIC_TOOLTIPS.confidenceLow;
    case "insufficient":
      return METRIC_TOOLTIPS.confidenceInsufficient;
    default:
      return {
        title: "Unknown Confidence",
        content: "Confidence level not recognized.",
      };
  }
}

/**
 * Get performance value tooltip based on rating
 *
 * @param rating - Performance value rating
 * @returns Tooltip content for the rating
 *
 * @example
 * const tooltip = getPerformanceValueTooltip('excellent');
 * // { title: "Excellent Value", content: "..." }
 */
export function getPerformanceValueTooltip(
  rating: "excellent" | "good" | "fair" | "poor"
) {
  switch (rating) {
    case "excellent":
      return METRIC_TOOLTIPS.performanceValueExcellent;
    case "good":
      return METRIC_TOOLTIPS.performanceValueGood;
    case "fair":
      return METRIC_TOOLTIPS.performanceValueFair;
    case "poor":
      return METRIC_TOOLTIPS.performanceValuePoor;
    default:
      return {
        title: "Unknown Rating",
        content: "Performance value rating not recognized.",
      };
  }
}
