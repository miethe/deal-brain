"use client";

import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import { EntityLink } from "./entity-link";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";

export interface EntityTooltipProps {
  /**
   * Entity type for routing and data fetching
   */
  entityType: "cpu" | "gpu" | "ram-spec" | "storage-profile";

  /**
   * Entity ID for navigation and data fetching
   */
  entityId: number;

  /**
   * Display text for the link
   */
  children: ReactNode;

  /**
   * Tooltip content component (receives entity data)
   * Rendered when tooltip is opened
   */
  tooltipContent: (data: any) => ReactNode;

  /**
   * Function to fetch entity data on hover
   * Should return a Promise that resolves to entity data
   */
  fetchData?: (entityType: string, entityId: number) => Promise<any>;

  /**
   * Optional custom href (overrides default entity routing)
   */
  href?: string;

  /**
   * Display variant for the link
   * @default "link"
   */
  variant?: "link" | "inline";

  /**
   * Additional CSS classes for the link
   */
  className?: string;

  /**
   * Delay before showing tooltip (milliseconds)
   * @default 200
   */
  openDelay?: number;
}

/**
 * Entity link with hover tooltip displaying rich entity information
 *
 * Combines EntityLink with Radix UI Popover to provide:
 * - Lazy loading of entity data on hover
 * - Keyboard accessible (Tab, Enter, Escape)
 * - Loading and error states
 * - Configurable delay before showing
 * - Explicit hover handlers to work with Next.js Link components
 *
 * @example
 * ```tsx
 * <EntityTooltip
 *   entityType="cpu"
 *   entityId={123}
 *   tooltipContent={(cpu) => (
 *     <div>
 *       <h4>{cpu.name}</h4>
 *       <p>{cpu.cores} cores / {cpu.threads} threads</p>
 *     </div>
 *   )}
 *   fetchData={fetchCpuData}
 * >
 *   Intel Core i5-12400
 * </EntityTooltip>
 * ```
 */
export function EntityTooltip({
  entityType,
  entityId,
  children,
  tooltipContent,
  fetchData,
  href,
  variant = "link",
  className,
  openDelay = 200,
}: EntityTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [timeoutId]);

  const handleOpenChange = async (open: boolean) => {
    setIsOpen(open);

    // Fetch data when tooltip opens if not already loaded
    if (open && !data && !isLoading && !error && fetchData) {
      setIsLoading(true);
      setError(null);

      try {
        const result = await fetchData(entityType, entityId);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleMouseEnter = () => {
    // Clear any existing timeout
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    // Set new timeout to open after delay
    const id = setTimeout(() => {
      handleOpenChange(true);
    }, openDelay);

    setTimeoutId(id);
  };

  const handleMouseLeave = () => {
    // Clear pending timeout if user moves away before delay completes
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }

    // Close immediately
    handleOpenChange(false);
  };

  return (
    <Popover open={isOpen} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <span
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className="inline-block"
        >
          <EntityLink
            entityType={entityType}
            entityId={entityId}
            href={href}
            variant={variant}
            className={className}
          >
            {children}
          </EntityLink>
        </span>
      </PopoverTrigger>

      <PopoverContent className="w-80" aria-live="polite">
        {/* Loading state */}
        {isLoading && (
          <div className="space-y-2" role="status" aria-label="Loading entity details">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-5/6" />
            <span className="sr-only">Loading...</span>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="flex items-start gap-2 text-sm text-destructive" role="alert">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">Failed to load details</p>
              <p className="text-xs text-muted-foreground">{error}</p>
            </div>
          </div>
        )}

        {/* Content state */}
        {data && !isLoading && !error && tooltipContent(data)}

        {/* No data and no fetch function */}
        {!data && !isLoading && !error && !fetchData && (
          <div className="text-sm text-muted-foreground">
            No tooltip content available
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
