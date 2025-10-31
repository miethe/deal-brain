import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface SummaryCardsGridProps {
  /**
   * Child summary cards to display in grid
   */
  children: ReactNode;

  /**
   * Number of columns to display (responsive by default)
   * @default "auto" - 1 col mobile, 2 cols tablet, 4 cols desktop
   */
  columns?: "auto" | 2 | 3 | 4 | 6;

  /**
   * Additional CSS classes
   */
  className?: string;
}

/**
 * Responsive grid layout for displaying SummaryCard components
 *
 * Provides consistent spacing and responsive behavior for summary cards
 * throughout the application.
 *
 * **Responsive Breakpoints:**
 * - Mobile (< 640px): 1 column
 * - Tablet (≥ 640px): 2 columns
 * - Desktop (≥ 1024px): 4 columns (or configured amount)
 *
 * @example
 * ```tsx
 * <SummaryCardsGrid>
 *   <SummaryCard title="Price" value="$599" />
 *   <SummaryCard title="Score" value={8.5} />
 *   <SummaryCard title="CPU" value="Intel i5" />
 *   <SummaryCard title="GPU" value="GTX 1660" />
 * </SummaryCardsGrid>
 * ```
 */
export function SummaryCardsGrid({
  children,
  columns = "auto",
  className,
}: SummaryCardsGridProps) {
  const columnClasses = {
    auto: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4",
    6: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6",
  };

  return (
    <div
      className={cn(
        "grid gap-3",
        columnClasses[columns],
        className
      )}
      role="grid"
      aria-label="Summary information grid"
    >
      {children}
    </div>
  );
}
