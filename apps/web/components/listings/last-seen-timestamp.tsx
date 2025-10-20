/**
 * Last Seen Timestamp Component
 *
 * Displays when listing data was last updated with relative time formatting.
 *
 * Features:
 * - Relative time format ("2 days ago")
 * - Tooltip with exact date/time
 * - Accessible (keyboard focus, screen reader support)
 * - Auto-updates display periodically (optional)
 */

"use client";

import { memo } from 'react';
import { Clock } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface LastSeenTimestampProps {
  lastSeenAt: string; // ISO datetime string
  className?: string;
  showIcon?: boolean;
  showLabel?: boolean;
}

function LastSeenTimestampComponent({
  lastSeenAt,
  className,
  showIcon = true,
  showLabel = true,
}: LastSeenTimestampProps) {
  const date = new Date(lastSeenAt);
  const relativeTime = formatDistanceToNow(date, { addSuffix: true });
  const exactDateTime = format(date, 'PPpp'); // e.g., "Apr 29, 2025, 9:30:00 AM"

  const ariaLabel = `Last updated ${relativeTime}`;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              'inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-help',
              className
            )}
            tabIndex={0}
            aria-label={ariaLabel}
          >
            {showIcon && <Clock className="h-3.5 w-3.5" aria-hidden="true" />}
            {showLabel && (
              <span>
                Last seen <time dateTime={lastSeenAt}>{relativeTime}</time>
              </span>
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent side="top">
          <div className="space-y-1">
            <p className="font-medium text-sm">Last Seen</p>
            <p className="text-sm text-muted-foreground">
              <time dateTime={lastSeenAt}>{exactDateTime}</time>
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// Memoize to prevent re-renders when props haven't changed
export const LastSeenTimestamp = memo(LastSeenTimestampComponent);
