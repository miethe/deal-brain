"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";

interface RulePreviewPanelProps {
  conditions: any[];
  actions: any[];
  sampleListingId?: number;
}

export function RulePreviewPanel({ conditions, actions, sampleListingId }: RulePreviewPanelProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["rule-preview", conditions, actions, sampleListingId],
    queryFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/valuation-rules/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conditions,
          actions,
          sample_size: 10,
        }),
      });
      if (!response.ok) {
        throw new Error("Failed to preview rule");
      }
      return response.json();
    },
    enabled: conditions.length > 0 && actions.length > 0,
  });

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading preview...</div>;
  }

  if (!data) {
    return <div className="text-sm text-muted-foreground">Add conditions and actions to see preview</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Rule Preview</CardTitle>
        <CardDescription>Impact on sample listings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Matched</div>
              <div className="text-2xl font-semibold">{data.statistics.matched_count || 0}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Avg Adjustment</div>
              <div className="text-2xl font-semibold">
                ${(data.statistics.avg_adjustment || 0).toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Listings</div>
              <div className="text-2xl font-semibold">{data.statistics.total_listings_checked || 0}</div>
            </div>
          </div>

          {/* Sample matched listings */}
          {data.sample_matched_listings && data.sample_matched_listings.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium">Sample Matched Listings</h4>
              <div className="space-y-2">
                {data.sample_matched_listings.slice(0, 3).map((listing: any) => (
                  <div key={listing.id} className="rounded-lg border p-3">
                    <div className="font-medium">{listing.title}</div>
                    <div className="mt-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        ${listing.original_price} → ${listing.adjusted_price}
                      </span>
                      <span className={listing.adjustment < 0 ? "text-green-600" : "text-red-600"}>
                        {listing.adjustment > 0 ? "+" : ""}${listing.adjustment.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
