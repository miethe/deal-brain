"use client";

import { Badge } from "@/components/ui/badge";
import { Lock, Users, Globe } from "lucide-react";
import type { CollectionVisibility } from "@/types/collections";
import { cn } from "@/lib/utils";

interface VisibilityBadgeProps {
  visibility: CollectionVisibility;
  className?: string;
  showLabel?: boolean;
}

const visibilityConfig = {
  private: {
    icon: Lock,
    label: "Private",
    color: "text-muted-foreground bg-muted",
    description: "Only me",
  },
  unlisted: {
    icon: Users,
    label: "Unlisted",
    color: "text-blue-700 bg-blue-50 border-blue-200 dark:text-blue-400 dark:bg-blue-950 dark:border-blue-800",
    description: "Anyone with link",
  },
  public: {
    icon: Globe,
    label: "Public",
    color: "text-green-700 bg-green-50 border-green-200 dark:text-green-400 dark:bg-green-950 dark:border-green-800",
    description: "Everyone can discover",
  },
} as const;

/**
 * Visibility Badge Component
 *
 * Displays collection visibility status with color-coded badge
 * - Private (gray): Only visible to owner
 * - Unlisted (blue): Accessible via share link
 * - Public (green): Discoverable by everyone
 */
export function VisibilityBadge({
  visibility,
  className,
  showLabel = true,
}: VisibilityBadgeProps) {
  const config = visibilityConfig[visibility];
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        "flex items-center gap-1.5 shrink-0",
        config.color,
        className
      )}
      aria-label={`Visibility: ${config.label} - ${config.description}`}
    >
      <Icon className="w-3 h-3" aria-hidden="true" />
      {showLabel && <span>{config.label}</span>}
    </Badge>
  );
}
