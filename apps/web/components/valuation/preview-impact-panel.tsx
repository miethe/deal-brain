"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, TrendingDown, Loader2, AlertCircle } from "lucide-react";
import { useDebounce } from "use-debounce";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { previewImpact } from "@/lib/api/baseline";
import { cn } from "@/lib/utils";

interface PreviewImpactPanelProps {
  entityKey: string;
  sampleSize?: number;
  className?: string;
}

export function PreviewImpactPanel({
  entityKey,
  sampleSize = 100,
  className,
}: PreviewImpactPanelProps) {
  // Debounce entity key to avoid too many requests during tab switches
  const [debouncedEntityKey] = useDebounce(entityKey, 300);

  const {
    data: impactData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["baseline-preview", debouncedEntityKey, sampleSize],
    queryFn: () => previewImpact(debouncedEntityKey, sampleSize),
    staleTime: 10000, // 10 seconds
    enabled: !!debouncedEntityKey,
  });

  // Auto-refetch when entity changes
  useEffect(() => {
    if (debouncedEntityKey) {
      refetch();
    }
  }, [debouncedEntityKey, refetch]);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">Preview Impact</CardTitle>
          <CardDescription>Analyzing override effects on listings...</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Calculating...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">Preview Impact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-2 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error instanceof Error ? error.message : "Failed to load preview"}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!impactData) {
    return null;
  }

  const { statistics, samples } = impactData;
  const hasImpact = statistics.matched_count > 0;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">Preview Impact</CardTitle>
        <CardDescription>
          Impact of current overrides on {statistics.total_listings} listings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Statistics Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Match Rate"
            value={`${statistics.match_percentage.toFixed(1)}%`}
            description={`${statistics.matched_count} of ${statistics.total_listings} listings`}
            variant={hasImpact ? "default" : "muted"}
          />
          <StatCard
            label="Avg Delta"
            value={formatCurrency(statistics.avg_delta)}
            description="Average price adjustment"
            variant={statistics.avg_delta > 0 ? "increase" : statistics.avg_delta < 0 ? "decrease" : "neutral"}
            icon={statistics.avg_delta > 0 ? <TrendingUp className="h-4 w-4" /> : statistics.avg_delta < 0 ? <TrendingDown className="h-4 w-4" /> : null}
          />
          <StatCard
            label="Min Delta"
            value={formatCurrency(statistics.min_delta)}
            description="Smallest adjustment"
            variant="muted"
          />
          <StatCard
            label="Max Delta"
            value={formatCurrency(statistics.max_delta)}
            description="Largest adjustment"
            variant="muted"
          />
        </div>

        {/* Sample Listings Table */}
        {samples.length > 0 && (
          <div>
            <h3 className="mb-3 text-sm font-semibold">Sample Listings</h3>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead className="text-right">Current</TableHead>
                    <TableHead className="text-right">Override</TableHead>
                    <TableHead className="text-right">Delta</TableHead>
                    <TableHead className="text-right">Change %</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {samples.slice(0, 10).map((sample) => (
                    <TableRow key={sample.id}>
                      <TableCell className="font-medium">
                        <div className="max-w-xs truncate">{sample.title}</div>
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(sample.current_price)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(sample.override_price)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge
                          variant={
                            sample.delta > 0
                              ? "default"
                              : sample.delta < 0
                              ? "destructive"
                              : "secondary"
                          }
                          className="font-mono text-xs"
                        >
                          {sample.delta >= 0 ? "+" : ""}
                          {formatCurrency(sample.delta)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-xs text-muted-foreground">
                        {sample.delta_pct >= 0 ? "+" : ""}
                        {sample.delta_pct.toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {samples.length > 10 && (
              <p className="mt-2 text-xs text-muted-foreground">
                Showing 10 of {samples.length} sample listings
              </p>
            )}
          </div>
        )}

        {!hasImpact && (
          <div className="py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No overrides active. Adjust fields above to see impact.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  description: string;
  variant?: "default" | "muted" | "increase" | "decrease" | "neutral";
  icon?: React.ReactNode;
}

function StatCard({ label, value, description, variant = "default", icon }: StatCardProps) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        {icon}
      </div>
      <div
        className={cn(
          "mt-2 text-2xl font-semibold",
          variant === "increase" && "text-green-600",
          variant === "decrease" && "text-red-600",
          variant === "muted" && "text-muted-foreground"
        )}
      >
        {value}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}
