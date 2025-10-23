/**
 * Listing Provenance Display Component
 *
 * Composite component that displays all provenance information:
 * - Data source badge
 * - Quality indicator
 * - Last seen timestamp
 *
 * This component provides a complete view of listing data origin and quality.
 * Can be used in listing cards, detail pages, or tables.
 *
 * Features:
 * - Flexible layout (horizontal/vertical)
 * - Optional elements (can hide any badge)
 * - Responsive design
 * - Accessible (WCAG 2.1 AA compliant)
 */

"use client";

import { memo } from 'react';
import { ProvenanceBadge, type ProvenanceSource } from './provenance-badge';
import { QualityIndicator, type QualityLevel } from './quality-indicator';
import { LastSeenTimestamp } from './last-seen-timestamp';
import { cn } from '@/lib/utils';

interface ListingProvenanceDisplayProps {
  provenance: ProvenanceSource;
  quality?: QualityLevel;
  lastSeenAt?: string; // ISO datetime
  missingFields?: string[];
  className?: string;
  layout?: 'horizontal' | 'vertical';
  showSource?: boolean;
  showQuality?: boolean;
  showTimestamp?: boolean;
  compact?: boolean; // Hide labels, show only icons
}

function ListingProvenanceDisplayComponent({
  provenance,
  quality,
  lastSeenAt,
  missingFields,
  className,
  layout = 'horizontal',
  showSource = true,
  showQuality = true,
  showTimestamp = true,
  compact = false,
}: ListingProvenanceDisplayProps) {
  const isHorizontal = layout === 'horizontal';

  // Screen reader announcement combining all provenance info
  const ariaLabel = [
    showSource && `Data source: ${provenance.replace('_', ' ')}`,
    showQuality && quality && `Quality: ${quality}`,
    showTimestamp && lastSeenAt && `Last seen ${new Date(lastSeenAt).toLocaleDateString()}`,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2',
        isHorizontal ? 'flex-row flex-wrap' : 'flex-col items-start',
        className
      )}
      role="group"
      aria-label={ariaLabel}
    >
      {showSource && (
        <ProvenanceBadge
          provenance={provenance}
          showLabel={!compact}
        />
      )}

      {showQuality && quality && (
        <QualityIndicator
          quality={quality}
          missingFields={missingFields}
          showLabel={!compact}
        />
      )}

      {showTimestamp && lastSeenAt && (
        <LastSeenTimestamp
          lastSeenAt={lastSeenAt}
          showIcon={!compact}
          showLabel={!compact}
        />
      )}
    </div>
  );
}

// Memoize to prevent re-renders when props haven't changed
export const ListingProvenanceDisplay = memo(ListingProvenanceDisplayComponent);
