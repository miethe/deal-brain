import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MetricsData {
  dollar_per_cpu_mark_multi: number | null;
  dollar_per_cpu_mark_single: number | null;
  composite_score: number | null;
}

interface PerformanceMetricsProps {
  metrics: MetricsData | null;
}

/**
 * Display CPU performance metrics and efficiency ratios
 *
 * Shows:
 * - $/CPU Mark (Multi-thread) - Lower is better
 * - $/CPU Mark (Single-thread) - Lower is better
 * - Composite Score - Overall rating out of 100
 */
export function PerformanceMetrics({ metrics }: PerformanceMetricsProps) {
  if (!metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Select CPU to see performance metrics
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Performance Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Multi-thread efficiency */}
        {metrics.dollar_per_cpu_mark_multi !== null && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">$/CPU Mark (Multi)</span>
            <span className="font-semibold tabular-nums">
              ${metrics.dollar_per_cpu_mark_multi.toFixed(4)}
            </span>
          </div>
        )}

        {/* Single-thread efficiency */}
        {metrics.dollar_per_cpu_mark_single !== null && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">$/CPU Mark (Single)</span>
            <span className="font-semibold tabular-nums">
              ${metrics.dollar_per_cpu_mark_single.toFixed(4)}
            </span>
          </div>
        )}

        {/* Composite score with visual indicator */}
        {metrics.composite_score !== null && (
          <>
            <div className="border-t pt-3 mt-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Composite Score</span>
                <span className="font-bold text-lg text-blue-600 tabular-nums">
                  {metrics.composite_score.toFixed(1)}/100
                </span>
              </div>

              {/* Visual score bar */}
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(metrics.composite_score, 100)}%` }}
                />
              </div>
            </div>

            {/* Score interpretation */}
            <div className="text-xs text-muted-foreground mt-2">
              {metrics.composite_score >= 80 && "Excellent overall value"}
              {metrics.composite_score >= 60 &&
                metrics.composite_score < 80 &&
                "Good overall value"}
              {metrics.composite_score >= 40 &&
                metrics.composite_score < 60 &&
                "Average overall value"}
              {metrics.composite_score < 40 && "Below average overall value"}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
