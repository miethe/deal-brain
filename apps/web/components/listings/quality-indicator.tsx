/**
 * Quality Indicator Component
 *
 * Displays data quality level (Full/Partial) with tooltips explaining missing fields.
 *
 * Features:
 * - Full: Green checkmark (all required fields present)
 * - Partial: Orange warning icon (some fields missing)
 * - Tooltip showing which fields are missing
 * - Accessible (keyboard focus, screen reader support)
 * - WCAG 2.1 AA color contrast compliant
 */

"use client";

import { memo } from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

export type QualityLevel = 'full' | 'partial';

interface QualityIndicatorProps {
  quality: QualityLevel;
  missingFields?: string[];
  className?: string;
  showLabel?: boolean;
}

function QualityIndicatorComponent({
  quality,
  missingFields = [],
  className,
  showLabel = true,
}: QualityIndicatorProps) {
  const isFull = quality === 'full';
  const Icon = isFull ? CheckCircle2 : AlertCircle;
  const label = isFull ? 'Full' : 'Partial';

  const colorClass = isFull
    ? 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300 border-green-200 dark:border-green-800'
    : 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300 border-orange-200 dark:border-orange-800';

  const ariaLabel = isFull
    ? 'Data quality: Full - all required fields present'
    : `Data quality: Partial - ${missingFields.length} fields missing`;

  const badge = (
    <Badge
      variant="outline"
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium border',
        colorClass,
        className
      )}
      aria-label={ariaLabel}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {showLabel && <span className="font-medium">{label}</span>}
    </Badge>
  );

  // If partial quality and missing fields are provided, show tooltip
  if (!isFull && missingFields.length > 0) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="inline-flex" tabIndex={0}>
              {badge}
            </span>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs" side="top">
            <div className="space-y-1.5">
              <p className="font-medium text-sm">Missing Fields:</p>
              <ul className="list-disc list-inside space-y-0.5 text-sm">
                {missingFields.map((field) => (
                  <li key={field} className="text-muted-foreground">
                    {field}
                  </li>
                ))}
              </ul>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return badge;
}

// Memoize to prevent re-renders when props haven't changed
export const QualityIndicator = memo(QualityIndicatorComponent);
