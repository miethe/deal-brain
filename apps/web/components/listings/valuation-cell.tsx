/**
 * Valuation cell component with color-coded pricing display
 * Memoized for performance in large tables
 */
'use client';

import { memo } from 'react';
import { Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DeltaBadge } from './delta-badge';
import { formatCurrency, getValuationStyle, calculateDelta } from '@/lib/valuation-utils';
import type { ValuationThresholds } from '@/lib/valuation-utils';

interface ValuationCellProps {
  adjustedPrice: number;
  listPrice: number;
  thresholds: ValuationThresholds;
  onDetailsClick: () => void;
}

function ValuationCellComponent({
  adjustedPrice,
  listPrice,
  thresholds,
  onDetailsClick,
}: ValuationCellProps) {
  const { delta, deltaPercent } = calculateDelta(listPrice, adjustedPrice);
  const style = getValuationStyle(deltaPercent, thresholds);

  return (
    <div className="flex items-center gap-2">
      <span className="text-lg font-semibold tabular-nums">
        {formatCurrency(adjustedPrice)}
      </span>
      <DeltaBadge
        delta={delta}
        percent={deltaPercent}
        icon={style.icon}
        className={style.className}
      />
      <Button
        variant="ghost"
        size="sm"
        onClick={onDetailsClick}
        className="h-6 w-6 p-0"
        aria-label="View valuation breakdown"
      >
        <Info className="h-4 w-4" />
      </Button>
    </div>
  );
}

// Memoize to prevent re-renders when props haven't changed
export const ValuationCell = memo(ValuationCellComponent);
