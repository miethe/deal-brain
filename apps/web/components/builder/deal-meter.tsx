import { cn } from "@/lib/utils";

interface DealMeterProps {
  deltaPercentage: number;
}

/**
 * Color-coded deal quality indicator
 *
 * Thresholds:
 * - Great Deal: 25%+ savings
 * - Good Deal: 15-25% savings
 * - Fair Value: 0-15% savings
 * - Premium Price: negative savings (paying more than value)
 */
export function DealMeter({ deltaPercentage }: DealMeterProps) {
  const getDealQuality = (delta: number) => {
    if (delta >= 25) {
      return {
        label: "Great Deal!",
        color: "text-green-600 bg-green-50 border-green-200",
        description: "Excellent value for money",
      };
    }
    if (delta >= 15) {
      return {
        label: "Good Deal",
        color: "text-green-500 bg-green-50 border-green-200",
        description: "Above average value",
      };
    }
    if (delta >= 0) {
      return {
        label: "Fair Value",
        color: "text-yellow-600 bg-yellow-50 border-yellow-200",
        description: "Market rate pricing",
      };
    }
    return {
      label: "Premium Price",
      color: "text-red-600 bg-red-50 border-red-200",
      description: "Paying more than estimated value",
    };
  };

  const quality = getDealQuality(deltaPercentage);

  return (
    <div className={cn("p-4 rounded-lg text-center border-2", quality.color)}>
      <div className="text-3xl font-bold tabular-nums">
        {deltaPercentage > 0 ? "+" : ""}
        {deltaPercentage.toFixed(1)}%
      </div>
      <div className="text-sm font-semibold mt-1">{quality.label}</div>
      <div className="text-xs mt-1 opacity-75">{quality.description}</div>
    </div>
  );
}
