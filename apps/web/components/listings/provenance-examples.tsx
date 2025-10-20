/**
 * Provenance Components Usage Examples
 *
 * This file demonstrates various ways to use the provenance badge components.
 * These examples can be used for documentation, testing, or as a starting point
 * for implementing provenance displays in listing pages.
 *
 * NOT FOR PRODUCTION USE - This is a reference/demo component.
 */

"use client";

import { ProvenanceBadge } from './provenance-badge';
import { QualityIndicator } from './quality-indicator';
import { LastSeenTimestamp } from './last-seen-timestamp';
import { ListingProvenanceDisplay } from './listing-provenance-display';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

export function ProvenanceExamples() {
  // Example data
  const exampleDate = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(); // 2 days ago
  const missingFields = ['RAM Size', 'Storage Type', 'GPU Model'];

  return (
    <div className="space-y-8 p-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold mb-2">Provenance Badge Components</h1>
        <p className="text-muted-foreground">
          Examples demonstrating the usage of provenance badge components for Deal Brain listings.
        </p>
      </div>

      <Separator />

      {/* Individual Components */}
      <Card>
        <CardHeader>
          <CardTitle>Individual Components</CardTitle>
          <CardDescription>
            Each component can be used independently for specific use cases.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Provenance Badges */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-muted-foreground">Provenance Sources</h3>
            <div className="flex flex-wrap gap-2">
              <ProvenanceBadge provenance="ebay_api" />
              <ProvenanceBadge provenance="jsonld" />
              <ProvenanceBadge provenance="scraper" />
              <ProvenanceBadge provenance="excel" />
            </div>
          </div>

          <Separator className="my-4" />

          {/* Quality Indicators */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-muted-foreground">Quality Indicators</h3>
            <div className="flex flex-wrap gap-2">
              <QualityIndicator quality="full" />
              <QualityIndicator quality="partial" missingFields={missingFields} />
            </div>
          </div>

          <Separator className="my-4" />

          {/* Last Seen Timestamp */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-muted-foreground">Last Seen Timestamp</h3>
            <div className="flex flex-wrap gap-2">
              <LastSeenTimestamp lastSeenAt={exampleDate} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Composite Display - Horizontal Layout */}
      <Card>
        <CardHeader>
          <CardTitle>Composite Display - Horizontal Layout</CardTitle>
          <CardDescription>
            All provenance information displayed in a horizontal row (default).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Full data - eBay API */}
          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">eBay API - Full Quality</p>
            <ListingProvenanceDisplay
              provenance="ebay_api"
              quality="full"
              lastSeenAt={exampleDate}
            />
          </div>

          {/* Partial data - JSON-LD */}
          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">JSON-LD - Partial Quality</p>
            <ListingProvenanceDisplay
              provenance="jsonld"
              quality="partial"
              lastSeenAt={exampleDate}
              missingFields={missingFields}
            />
          </div>

          {/* Scraper source */}
          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">Web Scraper - Full Quality</p>
            <ListingProvenanceDisplay
              provenance="scraper"
              quality="full"
              lastSeenAt={exampleDate}
            />
          </div>

          {/* Excel import */}
          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">Excel Import - No Quality Data</p>
            <ListingProvenanceDisplay
              provenance="excel"
              lastSeenAt={exampleDate}
              showQuality={false}
            />
          </div>
        </CardContent>
      </Card>

      {/* Composite Display - Vertical Layout */}
      <Card>
        <CardHeader>
          <CardTitle>Composite Display - Vertical Layout</CardTitle>
          <CardDescription>
            All provenance information displayed in a vertical stack.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-3">eBay API - Partial Quality (Vertical)</p>
            <ListingProvenanceDisplay
              provenance="ebay_api"
              quality="partial"
              lastSeenAt={exampleDate}
              missingFields={['GPU Model']}
              layout="vertical"
            />
          </div>
        </CardContent>
      </Card>

      {/* Compact Mode */}
      <Card>
        <CardHeader>
          <CardTitle>Compact Mode</CardTitle>
          <CardDescription>
            Icons only, no labels - useful for table cells or tight spaces.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">Compact Display</p>
            <ListingProvenanceDisplay
              provenance="ebay_api"
              quality="full"
              lastSeenAt={exampleDate}
              compact
            />
          </div>
        </CardContent>
      </Card>

      {/* Selective Display */}
      <Card>
        <CardHeader>
          <CardTitle>Selective Display</CardTitle>
          <CardDescription>
            Show only specific elements as needed.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">Source + Quality Only</p>
            <ListingProvenanceDisplay
              provenance="jsonld"
              quality="full"
              showTimestamp={false}
            />
          </div>

          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">Source + Timestamp Only</p>
            <ListingProvenanceDisplay
              provenance="scraper"
              lastSeenAt={exampleDate}
              showQuality={false}
            />
          </div>

          <div className="p-4 border rounded-lg">
            <p className="text-sm font-medium mb-2">Source Only</p>
            <ListingProvenanceDisplay
              provenance="excel"
              showQuality={false}
              showTimestamp={false}
            />
          </div>
        </CardContent>
      </Card>

      {/* Usage in Listing Card Context */}
      <Card>
        <CardHeader>
          <CardTitle>Example: Listing Card Integration</CardTitle>
          <CardDescription>
            How provenance badges might appear in an actual listing card.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-semibold text-lg">
                  Dell OptiPlex 7090 Micro - i7-11700T
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  16GB RAM • 512GB NVMe • Intel UHD Graphics 750
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-600">$459</p>
                <p className="text-sm text-muted-foreground line-through">$549</p>
              </div>
            </div>

            <Separator />

            <div className="flex items-center justify-between flex-wrap gap-2">
              <ListingProvenanceDisplay
                provenance="ebay_api"
                quality="full"
                lastSeenAt={exampleDate}
              />
              <div className="text-sm text-muted-foreground">
                Score: 8.7/10
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Accessibility Notes */}
      <Card>
        <CardHeader>
          <CardTitle>Accessibility Features</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <ul className="list-disc list-inside space-y-1 text-muted-foreground">
            <li>All badges include proper ARIA labels for screen readers</li>
            <li>Tooltips are keyboard accessible (focus with Tab key)</li>
            <li>Color is not the sole indicator (icons accompany colors)</li>
            <li>WCAG 2.1 AA color contrast compliance in light and dark modes</li>
            <li>Semantic HTML with proper time elements for timestamps</li>
            <li>Grouped provenance information has role="group" with descriptive label</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
