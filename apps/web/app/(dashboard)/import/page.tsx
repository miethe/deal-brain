'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SingleUrlImportForm } from '@/components/ingestion/single-url-import-form';
import { BulkImportDialog } from '@/components/ingestion/bulk-import-dialog';
import { ImporterWorkspace } from '@/components/import/importer-workspace';
import { Globe, FileSpreadsheet, Link, Upload } from 'lucide-react';

export default function ImportPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<string>('url');
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);

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
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="url" className="gap-2">
            <Globe className="h-4 w-4" />
            URL Import
          </TabsTrigger>
          <TabsTrigger value="file" className="gap-2">
            <FileSpreadsheet className="h-4 w-4" />
            File Import
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
              console.log('Import successful:', result);
              // Optionally navigate to the listing
              // router.push(`/listings/${result.listingId}`);
            }}
            onError={(error) => {
              console.error('Import failed:', error);
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
      </Tabs>

      {/* Bulk Import Dialog */}
      <BulkImportDialog
        open={bulkDialogOpen}
        onOpenChange={setBulkDialogOpen}
        onSuccess={(result) => {
          console.log('Bulk import successful:', result);
        }}
        onError={(error) => {
          console.error('Bulk import failed:', error);
        }}
      />
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
