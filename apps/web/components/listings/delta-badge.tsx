/**
 * Delta badge component for displaying savings/premium indicators
 * Memoized for performance optimization
 */
import { memo } from 'react';
import { ArrowDown, ArrowUp, Minus } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/valuation-utils';
import type { IconType } from '@/lib/valuation-utils';

interface DeltaBadgeProps {
  delta: number;
  percent: number;
  icon: IconType;
  className?: string;
}

function DeltaBadgeComponent({ delta, percent, icon, className }: DeltaBadgeProps) {
  const IconComponent =
    icon === 'arrow-down' ? ArrowDown :
    icon === 'arrow-up' ? ArrowUp :
    Minus;

  const sign = delta >= 0 ? '-' : '+';
  const absoluteDelta = Math.abs(delta);
  const absolutePercent = Math.abs(percent);

  return (
    <Badge className={`flex items-center gap-1 px-2 py-0.5 ${className}`}>
      <IconComponent className="h-3 w-3" />
      <span className="tabular-nums text-sm font-medium">
        {sign}{formatCurrency(absoluteDelta)}
      </span>
      <span className="text-xs opacity-75 ml-0.5">
        ({absolutePercent.toFixed(1)}%)
      </span>
    </Badge>
  );
}

// Memoize to prevent re-renders when props haven't changed
export const DeltaBadge = memo(DeltaBadgeComponent);
