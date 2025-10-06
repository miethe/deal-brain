/**
 * Calculate optimal dropdown width based on content
 */

/**
 * Calculates the minimum width needed for a dropdown to display the longest option
 * without truncation.
 *
 * @param options - Array of option labels to measure
 * @returns Width in pixels, clamped between 120px and 400px
 */
export function calculateDropdownWidth(options: string[]): number {
  if (!options.length) return 120; // Minimum default

  // Calculate longest option (approximate: 8px per character + padding + chevron)
  const maxLength = Math.max(...options.map((o) => o.length));

  // Formula: character width * length + left padding + right padding + chevron + buffer
  // 8px per char + 12px left padding + 12px right padding + 24px chevron + 16px buffer
  const width = maxLength * 8 + 12 + 12 + 24 + 16;

  // Clamp between min (120px) and max (400px) to prevent extremes
  return Math.min(Math.max(width, 120), 400);
}

/**
 * Formats dropdown width for inline styles
 * @param options - Array of option labels
 * @returns CSS width value (e.g., "180px")
 */
export function getDropdownWidthStyle(options: string[]): string {
  return `${calculateDropdownWidth(options)}px`;
}
