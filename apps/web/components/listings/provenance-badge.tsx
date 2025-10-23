/**
 * Provenance Badge Component
 *
 * Displays the data source origin for a listing with color-coded visual indicators.
 * Supports eBay API, JSON-LD, web scraper, and Excel import sources.
 *
 * Features:
 * - Icon + label for each source type
 * - Color-coded for quick recognition
 * - Accessible (WCAG 2.1 AA compliant)
 * - Keyboard navigable
 * - Screen reader friendly
 */

"use client";

import { memo } from 'react';
import {
  ShoppingCart,
  Code2,
  Globe,
  Sheet,
  type LucideIcon
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type ProvenanceSource = 'ebay_api' | 'jsonld' | 'scraper' | 'excel';

interface ProvenanceBadgeProps {
  provenance: ProvenanceSource;
  className?: string;
  showLabel?: boolean;
}

interface SourceConfig {
  icon: LucideIcon;
  label: string;
  colorClass: string;
  ariaLabel: string;
}

const sourceConfigs: Record<ProvenanceSource, SourceConfig> = {
  ebay_api: {
    icon: ShoppingCart,
    label: 'eBay API',
    colorClass: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border-blue-200 dark:border-blue-800',
    ariaLabel: 'Data from eBay API',
  },
  jsonld: {
    icon: Code2,
    label: 'Structured Data',
    colorClass: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300 border-green-200 dark:border-green-800',
    ariaLabel: 'Data from JSON-LD structured data',
  },
  scraper: {
    icon: Globe,
    label: 'Web Scraper',
    colorClass: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800',
    ariaLabel: 'Data from web scraper',
  },
  excel: {
    icon: Sheet,
    label: 'Excel Import',
    colorClass: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700',
    ariaLabel: 'Data from Excel import',
  },
};

function ProvenanceBadgeComponent({
  provenance,
  className,
  showLabel = true
}: ProvenanceBadgeProps) {
  const config = sourceConfigs[provenance];
  const IconComponent = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium border',
        config.colorClass,
        className
      )}
      aria-label={config.ariaLabel}
    >
      <IconComponent className="h-3.5 w-3.5" aria-hidden="true" />
      {showLabel && (
        <span className="font-medium">{config.label}</span>
      )}
    </Badge>
  );
}

// Memoize to prevent re-renders when props haven't changed
export const ProvenanceBadge = memo(ProvenanceBadgeComponent);
