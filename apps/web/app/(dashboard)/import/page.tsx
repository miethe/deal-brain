'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SingleUrlImportForm } from '@/components/ingestion/single-url-import-form';
import { BulkImportDialog } from '@/components/ingestion/bulk-import-dialog';
import { ImporterWorkspace } from '@/components/import/importer-workspace';
import { PartialImportModal } from '@/components/imports/PartialImportModal';
import { ListingRecord } from '@/types/listings';
import { telemetry } from '@/lib/telemetry';
import { Globe, FileSpreadsheet, Link, Upload, FileJson } from 'lucide-react';
import { JsonImportDropzone } from '@/components/import-export/json-import-button';

export default function ImportPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<string>('url');
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [partialListing, setPartialListing] = useState<ListingRecord | null>(null);
  const [completedListings, setCompletedListings] = useState<ListingRecord[]>([]);

  // Listen for import completion events from bulk status polling
  useEffect(() => {
    const handleImportComplete = (event: CustomEvent<{
      listing: ListingRecord;
      quality: string;
    }>) => {
      const { listing, quality } = event.detail;

      if (quality === 'partial') {
        setPartialListing(listing);
        telemetry.info('frontend.import.partial_detected', {
          listingId: listing.id,
          title: listing.title,
        });
      } else {
        setCompletedListings(prev => [...prev, listing]);
        telemetry.info('frontend.import.complete', {
          listingId: listing.id,
          quality,
        });
      }
    };

    window.addEventListener(
      'import-complete',
      handleImportComplete as EventListener
    );

    return () => {
      window.removeEventListener(
        'import-complete',
        handleImportComplete as EventListener
      );
    };
  }, []);

  const handlePartialComplete = () => {
    if (partialListing) {
      setCompletedListings(prev => [...prev, partialListing]);
      setPartialListing(null);

      // Invalidate queries to refresh listings
      queryClient.invalidateQueries({ queryKey: ['listings'] });

      telemetry.info('frontend.import.partial_completed', {
        listingId: partialListing.id,
      });
    }
  };

  const handlePartialSkip = () => {
    if (partialListing) {
      telemetry.info('frontend.import.partial_skipped', {
        listingId: partialListing.id,
      });
    }
    setPartialListing(null);
  };

  return (
    <div className="container max-w-6xl py-8 space-y-6">
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Import Data</h1>
        <p className="text-muted-foreground">
          Add individual listings from marketplace URLs or batch import from spreadsheet files.
        </p>
      </div>

      {/* Import Method Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-2xl grid-cols-3">
          <TabsTrigger value="url" className="gap-2">
            <Globe className="h-4 w-4" />
            URL Import
          </TabsTrigger>
          <TabsTrigger value="file" className="gap-2">
            <FileSpreadsheet className="h-4 w-4" />
            File Import
          </TabsTrigger>
          <TabsTrigger value="json" className="gap-2">
            <FileJson className="h-4 w-4" />
            JSON Import
          </TabsTrigger>
        </TabsList>

        {/* URL Import Tab */}
        <TabsContent value="url" className="space-y-6 mt-6">
          {/* Method Overview */}
          <ImportMethodCard
            icon={<Link className="h-5 w-5" />}
            title="Import from Marketplace URLs"
            description="Extract listing data from eBay, Amazon, Mercari, and other online marketplaces. Our parser automatically identifies PC components, pricing, and specifications."
            bestFor={[
              'Individual listing imports',
              'Real-time marketplace monitoring',
              'Quick data entry from online sources',
            ]}
            supports="eBay, Amazon, Mercari, and most retailer websites"
          />

          {/* Single URL Import Form */}
          <SingleUrlImportForm
            onSuccess={(result) => {
              telemetry.info('frontend.import.single.success', {
                listingId: result.listingId,
                provenance: result.provenance,
                quality: result.quality,
              });
              // Optionally navigate to the listing
              // router.push(`/listings/${result.listingId}`);
            }}
            onError={(error) => {
              telemetry.error('frontend.import.single.failed', {
                message: error?.message ?? 'Unknown error',
              });
            }}
          />

          {/* Bulk Import CTA */}
          <Card className="border-dashed">
            <CardContent className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6">
              <div className="space-y-1">
                <h3 className="font-medium">Need to import multiple URLs?</h3>
                <p className="text-sm text-muted-foreground">
                  Upload a CSV or paste up to 1000 URLs for batch processing.
                </p>
              </div>
              <Button onClick={() => setBulkDialogOpen(true)} size="lg" className="shrink-0">
                Bulk Import URLs
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* File Import Tab */}
        <TabsContent value="file" className="space-y-6 mt-6">
          {/* Method Overview */}
          <ImportMethodCard
            icon={<Upload className="h-5 w-5" />}
            title="Import from Spreadsheet Files"
            description="Upload Excel or CSV workbooks containing multiple listings, component catalogs, valuation rules, and scoring profiles. Review field mappings, resolve conflicts, and commit in one batch."
            bestFor={[
              'Large dataset imports',
              'Component catalog management',
              'Valuation rules configuration',
              'Initial system setup',
            ]}
            supports=".xlsx, .xls, .csv files with structured data"
            workflow={[
              'Upload your spreadsheet file',
              'Review and adjust column mappings',
              'Resolve any data conflicts',
              'Commit the import',
            ]}
          />

          {/* Importer Workspace */}
          <ImporterWorkspace />
        </TabsContent>

        {/* JSON Import Tab */}
        <TabsContent value="json" className="space-y-6 mt-6">
          {/* Method Overview */}
          <ImportMethodCard
            icon={<FileJson className="h-5 w-5" />}
            title="Import from JSON Export"
            description="Import previously exported listings or collections from JSON files. Supports duplicate detection with merge or skip options to avoid creating duplicate entries."
            bestFor={[
              'Restoring exported data',
              'Migrating between environments',
              'Sharing individual listings or collections',
              'Backup restoration',
            ]}
            supports="JSON files exported from Deal Brain"
            workflow={[
              'Select or drag and drop a JSON file',
              'Review import preview and duplicates',
              'Choose merge, skip, or create new',
              'Confirm import',
            ]}
          />

          {/* JSON Import Dropzone */}
          <JsonImportDropzone
            importType="listing"
            onSuccess={() => {
              queryClient.invalidateQueries({ queryKey: ['listings'] });
              telemetry.info('frontend.import.json.success', {
                type: 'listing',
              });
            }}
          />
        </TabsContent>
      </Tabs>

      {/* Bulk Import Dialog */}
      <BulkImportDialog
        open={bulkDialogOpen}
        onOpenChange={setBulkDialogOpen}
        onSuccess={(result) => {
          telemetry.info('frontend.import.bulk.success', {
            total: result.total_urls,
            success: result.success,
            failed: result.failed,
          });
        }}
        onError={(error) => {
          telemetry.error('frontend.import.bulk.failed', {
            message: error?.message ?? 'Unknown error',
          });
        }}
      />

      {/* Partial Import Modal */}
      {partialListing && (
        <PartialImportModal
          listing={partialListing}
          onComplete={handlePartialComplete}
          onSkip={handlePartialSkip}
        />
      )}

      {/* Completed Listings Section */}
      {completedListings.length > 0 && (
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>Imported Listings ({completedListings.length})</CardTitle>
              <CardDescription>
                Successfully imported listings in this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {completedListings.map((listing) => (
                  <div
                    key={listing.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{listing.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {listing.cpu?.name && `CPU: ${listing.cpu.name}`}
                        {listing.ram_gb && ` • RAM: ${listing.ram_gb}GB`}
                        {listing.price_usd && ` • $${listing.price_usd.toFixed(2)}`}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/listings/${listing.id}`)}
                    >
                      View Details
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// Helper Component: Import Method Description Card
interface ImportMethodCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  bestFor: string[];
  supports: string;
  workflow?: string[];
}

function ImportMethodCard({
  icon,
  title,
  description,
  bestFor,
  supports,
  workflow,
}: ImportMethodCardProps) {
  return (
    <Card className="border-2">
      <CardHeader>
        <div className="flex items-start gap-3">
          <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
          <div className="space-y-1.5">
            <CardTitle className="text-xl">{title}</CardTitle>
            <CardDescription className="text-base leading-relaxed">
              {description}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-6 md:grid-cols-2">
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Best For
          </h4>
          <ul className="space-y-1.5">
            {bestFor.map((item, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Supports
            </h4>
            <p className="text-sm">{supports}</p>
          </div>
          {workflow && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                How It Works
              </h4>
              <ol className="space-y-1.5">
                {workflow.map((step, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {index + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
