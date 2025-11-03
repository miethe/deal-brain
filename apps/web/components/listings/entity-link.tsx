import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface EntityLinkProps {
  /**
   * Entity type for routing
   */
  entityType: "cpu" | "gpu" | "ram-spec" | "storage-profile";

  /**
   * Entity ID for navigation
   */
  entityId: number;

  /**
   * Display text for the link
   */
  children: ReactNode;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Optional custom href (overrides default entity routing)
   */
  href?: string;

  /**
   * Display variant
   * @default "link"
   */
  variant?: "link" | "inline";

  /**
   * Optional click handler (in addition to navigation)
   */
  onClick?: (e: React.MouseEvent<HTMLAnchorElement>) => void;

  /**
   * Disable link functionality (render as span instead)
   * Use when inside clickable containers to avoid nested anchor tags
   * @default false
   */
  disableLink?: boolean;
}

/**
 * Clickable entity link component with consistent styling and routing
 *
 * Provides consistent navigation to entity detail pages with proper
 * keyboard accessibility and hover states.
 *
 * **Routes:**
 * - cpu → /catalog/cpus/{id}
 * - gpu → /catalog/gpus/{id}
 * - ram-spec → /catalog/ram-specs/{id}
 * - storage-profile → /catalog/storage-profiles/{id}
 *
 * @example
 * ```tsx
 * <EntityLink entityType="cpu" entityId={123}>
 *   Intel Core i5-12400
 * </EntityLink>
 *
 * <EntityLink entityType="gpu" entityId={456} variant="inline">
 *   NVIDIA GTX 1660 Ti
 * </EntityLink>
 * ```
 */
export function EntityLink({
  entityType,
  entityId,
  children,
  className,
  href,
  variant = "link",
  onClick,
  disableLink = false,
}: EntityLinkProps) {
  // Route mapping for entity types to catalog pages
  const routeMap: Record<string, string> = {
    cpu: "/catalog/cpus",
    gpu: "/catalog/gpus",
    "ram-spec": "/catalog/ram-specs",
    "storage-profile": "/catalog/storage-profiles",
  };

  // Generate default href based on entity type
  const basePath = routeMap[entityType];

  if (!basePath && process.env.NODE_ENV === "development") {
    console.warn(`EntityLink: Unknown entity type "${entityType}"`);
  }

  const defaultHref = basePath ? `${basePath}/${entityId}` : "#";
  const finalHref = href || defaultHref;

  const variantClasses = {
    link: "font-medium text-primary underline-offset-4 hover:underline",
    inline: "text-foreground underline-offset-2 hover:underline hover:text-primary",
  };

  // If disableLink is true, render as span
  if (disableLink) {
    return (
      <span
        className={cn(
          "cursor-default",
          variantClasses[variant],
          className
        )}
      >
        {children}
      </span>
    );
  }

  return (
    <Link
      href={finalHref}
      className={cn(
        "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        variantClasses[variant],
        className
      )}
      onClick={onClick}
    >
      {children}
    </Link>
  );
}
