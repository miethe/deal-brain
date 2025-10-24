import type { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface SummaryCardProps {
  /**
   * Title/label displayed at the top of the card
   */
  title: string;

  /**
   * Primary value displayed prominently (e.g., price, score)
   */
  value: string | number | ReactNode;

  /**
   * Optional subtitle/description displayed below value
   */
  subtitle?: string | ReactNode;

  /**
   * Optional icon displayed next to title
   */
  icon?: ReactNode;

  /**
   * Optional click handler for interactive cards
   */
  onClick?: () => void;

  /**
   * Size variant for different use cases
   * @default "medium"
   */
  size?: "small" | "medium" | "large";

  /**
   * Color variant for visual distinction
   * @default "default"
   */
  variant?: "default" | "success" | "warning" | "info";

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Additional CSS classes for the value element
   */
  valueClassName?: string;
}

/**
 * Reusable summary card component for displaying key metrics
 *
 * Used in detail page hero section and potentially other locations
 * for consistent display of summary information.
 *
 * @example
 * ```tsx
 * <SummaryCard
 *   title="Listing Price"
 *   value="$599.99"
 *   size="medium"
 * />
 *
 * <SummaryCard
 *   title="Composite Score"
 *   value={8.5}
 *   subtitle="Very Good"
 *   variant="success"
 * />
 * ```
 */
export function SummaryCard({
  title,
  value,
  subtitle,
  icon,
  onClick,
  size = "medium",
  variant = "default",
  className,
  valueClassName,
}: SummaryCardProps) {
  const sizeClasses = {
    small: "p-3",
    medium: "p-4",
    large: "p-6",
  };

  const valueSizeClasses = {
    small: "text-lg",
    medium: "text-2xl",
    large: "text-3xl",
  };

  const variantClasses = {
    default: "",
    success: "border-green-500/20 bg-green-500/5",
    warning: "border-yellow-500/20 bg-yellow-500/5",
    info: "border-blue-500/20 bg-blue-500/5",
  };

  return (
    <Card
      className={cn(
        variantClasses[variant],
        onClick && "cursor-pointer transition-colors hover:bg-accent",
        className
      )}
      onClick={onClick}
    >
      <CardContent className={cn(sizeClasses[size])}>
        {/* Title with optional icon */}
        <div className="flex items-center gap-2">
          {icon && <span className="text-muted-foreground">{icon}</span>}
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            {title}
          </div>
        </div>

        {/* Primary value */}
        <div
          className={cn(
            "mt-1 font-semibold",
            valueSizeClasses[size],
            valueClassName
          )}
        >
          {value}
        </div>

        {/* Optional subtitle */}
        {subtitle && (
          <div className="mt-1 text-xs text-muted-foreground">
            {subtitle}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
