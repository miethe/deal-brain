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

  const valuation = build.build_snapshot.valuation;
  const metrics = build.build_snapshot.metrics;
  const delta = valuation?.delta_percentage || 0;

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">
          {build.name || "Shared PC Build"}
        </h1>
        <div className="flex gap-2 mt-3 flex-wrap">
          {build.is_public && (
            <Badge variant="secondary">Public Build</Badge>
          )}
        </div>
      </div>

      {/* Valuation */}
      {valuation && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Valuation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Base Price</span>
              <span className="font-semibold">
                ${parseFloat(valuation.base_price.toString()).toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-lg">
              <span>Adjusted Value</span>
              <span className="font-bold">
                ${parseFloat(valuation.adjusted_price.toString()).toFixed(2)}
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
      {metrics && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {metrics.dollar_per_cpu_mark_multi && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">$/CPU Mark (Multi)</span>
                <span className="font-semibold">
                  ${parseFloat(metrics.dollar_per_cpu_mark_multi.toString()).toFixed(4)}
                </span>
              </div>
            )}
            {metrics.dollar_per_cpu_mark_single && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">$/CPU Mark (Single)</span>
                <span className="font-semibold">
                  ${parseFloat(metrics.dollar_per_cpu_mark_single.toString()).toFixed(4)}
                </span>
              </div>
            )}
            {metrics.composite_score && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Composite Score</span>
                <span className="font-semibold text-blue-600">
                  {metrics.composite_score}/100
                </span>
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
