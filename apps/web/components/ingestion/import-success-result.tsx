'use client';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, ExternalLink, Database, AlertCircle } from 'lucide-react';
import type { ImportSuccessResultProps } from './types';
import { formatDistanceToNow } from 'date-fns';

export function ImportSuccessResult({
  result,
  onViewListing,
  onImportAnother,
}: ImportSuccessResultProps) {
  const provenanceBadgeConfig = {
    ebay_api: {
      label: 'eBay API',
      className: 'bg-blue-100 text-blue-700 border-blue-200',
    },
    jsonld: {
      label: 'JSON-LD',
      className: 'bg-purple-100 text-purple-700 border-purple-200',
    },
    scraper: {
      label: 'Scraper',
      className: 'bg-gray-100 text-gray-700 border-gray-200',
    },
  };

  const qualityBadgeConfig = {
    full: {
      label: 'Full data',
      icon: CheckCircle2,
      className: 'bg-green-100 text-green-700 border-green-200',
    },
    partial: {
      label: 'Partial data',
      icon: AlertCircle,
      className: 'bg-amber-100 text-amber-700 border-amber-200',
    },
  };

  const provenance = provenanceBadgeConfig[result.provenance];
  const quality = qualityBadgeConfig[result.quality];
  const QualityIcon = quality.icon;

  const timeAgo = formatDistanceToNow(new Date(result.createdAt), { addSuffix: true });

  return (
    <Alert variant="default" className="border-green-500/50 bg-green-50/50">
      <CheckCircle2 className="h-5 w-5 text-green-600" />
      <div className="flex-1">
        <AlertTitle className="text-green-700">
          Listing imported successfully!
        </AlertTitle>
        <AlertDescription className="mt-3 space-y-3">
          {/* Listing Preview Card */}
          <div className="rounded-lg border bg-card p-3 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <h4 className="font-medium text-sm line-clamp-2">
                {result.title}
              </h4>
              <Badge variant="secondary" className="text-xs shrink-0">
                #{result.listingId}
              </Badge>
            </div>

            {/* Metadata Row */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
              <Badge
                variant="outline"
                className={`gap-1 ${provenance.className}`}
              >
                <Database className="h-3 w-3" />
                {provenance.label}
              </Badge>

              <Badge
                variant="outline"
                className={`gap-1 ${quality.className}`}
              >
                <QualityIcon className="h-3 w-3" />
                {quality.label}
              </Badge>

              <span className="ml-auto">
                {timeAgo}
              </span>
            </div>
          </div>

          {/* Partial Data Warning */}
          {result.quality === 'partial' && (
            <Alert variant="default" className="bg-blue-50 border-blue-200">
              <AlertCircle className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-xs text-blue-700">
                Some details may be missing. You can edit the listing to add
                CPU, RAM, or storage info.
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onViewListing}
              className="flex-1"
            >
              <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
              View Listing
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={onImportAnother}
              className="flex-1"
            >
              Import Another
            </Button>
          </div>
        </AlertDescription>
      </div>
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        Listing imported successfully. Listing number {result.listingId}.
      </div>
    </Alert>
  );
}
