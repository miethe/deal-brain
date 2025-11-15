import { getSharedBuild } from "@/lib/api/builder";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function SharedBuildPage({
  params,
}: {
  params: { token: string };
}) {
  let build;

  try {
    build = await getSharedBuild(params.token);
  } catch (error) {
    notFound();
  }

  const valuationSnapshot = build.pricing_snapshot;
  const metricsSnapshot = build.metrics_snapshot;

  const basePrice = valuationSnapshot
    ? parseFloat(valuationSnapshot.base_price)
    : null;
  const adjustedPrice = valuationSnapshot
    ? parseFloat(valuationSnapshot.adjusted_price)
    : null;
  const delta = valuationSnapshot?.delta_percentage ?? 0;

  const dollarPerCpuMark = metricsSnapshot?.dollar_per_cpu_mark_multi
    ? parseFloat(metricsSnapshot.dollar_per_cpu_mark_multi)
    : null;
  const dollarPerCpuMarkSingle = metricsSnapshot?.dollar_per_cpu_mark_single
    ? parseFloat(metricsSnapshot.dollar_per_cpu_mark_single)
    : null;
  const compositeScore = metricsSnapshot?.composite_score ?? null;

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">
          {build.name || "Shared PC Build"}
        </h1>
        <div className="flex gap-2 mt-3 flex-wrap">
          {build.visibility === "public" && (
            <Badge variant="secondary">Public Build</Badge>
          )}
          {build.visibility === "unlisted" && (
            <Badge variant="outline">Unlisted Build</Badge>
          )}
        </div>
      </div>

      {/* Valuation */}
      {valuationSnapshot && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Valuation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Base Price</span>
              <span className="font-semibold">
                {basePrice != null ? `$${basePrice.toFixed(2)}` : "—"}
              </span>
            </div>
            <div className="flex justify-between text-lg">
              <span>Adjusted Value</span>
              <span className="font-bold">
                {adjustedPrice != null ? `$${adjustedPrice.toFixed(2)}` : "—"}
              </span>
            </div>
            <div
              className={`text-center p-3 rounded-lg ${
                delta >= 25
                  ? "bg-green-50 text-green-700"
                  : delta >= 15
                  ? "bg-green-50 text-green-600"
                  : delta >= 0
                  ? "bg-yellow-50 text-yellow-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              <div className="text-2xl font-bold">
                {delta > 0 ? "+" : ""}
                {delta.toFixed(1)}%
              </div>
              <div className="text-sm mt-1">
                {delta >= 25
                  ? "Great Deal!"
                  : delta >= 15
                  ? "Good Deal"
                  : delta >= 0
                  ? "Fair Value"
                  : "Premium Price"}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Metrics */}
      {metricsSnapshot && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {dollarPerCpuMark !== null && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">$/CPU Mark (Multi)</span>
                <span className="font-semibold">${dollarPerCpuMark.toFixed(4)}</span>
              </div>
            )}
            {dollarPerCpuMarkSingle !== null && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">$/CPU Mark (Single)</span>
                <span className="font-semibold">${dollarPerCpuMarkSingle.toFixed(4)}</span>
              </div>
            )}
            {compositeScore && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Composite Score</span>
                <span className="font-semibold text-blue-600">{compositeScore}/100</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* CTA */}
      <div className="flex justify-center mt-8">
        <Link href="/builder">
          <Button size="lg">Build Your Own</Button>
        </Link>
      </div>

      <div className="text-center text-sm text-muted-foreground mt-4">
        Created {new Date(build.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}
