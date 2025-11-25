'use client';

import * as React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { Upload, Link } from 'lucide-react';
import { API_URL } from '@/lib/utils';

export interface ImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function ImportModal({ open, onOpenChange, onSuccess }: ImportModalProps) {
  const { toast } = useToast();
  const [isImporting, setIsImporting] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState<'url' | 'file'>('url');

  // URL import state
  const [importUrl, setImportUrl] = React.useState('');

  // File import state
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);

  const handleUrlImport = async () => {
    if (!importUrl.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a URL',
        variant: 'destructive',
      });
      return;
    }

    setIsImporting(true);

    try {
      // Call import API - using the ingestion endpoint for URL imports
      const response = await fetch(`${API_URL}/api/v1/ingest/single`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: importUrl,
          priority: 'normal'
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Import failed' }));
        throw new Error(error.detail || error.message || 'Import failed');
      }

      const result = await response.json();

      toast({
        title: 'Success',
        description: `Import job created successfully (Job ID: ${result.job_id})`,
      });

      // Reset state
      setImportUrl('');

      // Close modal and call success callback
      onOpenChange(false);
      onSuccess?.();

    } catch (error: any) {
      toast({
        title: 'Import Failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileImport = async () => {
    if (!selectedFile) {
      toast({
        title: 'Error',
        description: 'Please select a file',
        variant: 'destructive',
      });
      return;
    }

    setIsImporting(true);

    try {
      const formData = new FormData();
      formData.append('upload', selectedFile);

      const response = await fetch(`${API_URL}/v1/imports/sessions`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Import failed' }));
        throw new Error(error.detail || error.message || 'Import failed');
      }

      const result = await response.json();

      toast({
        title: 'Success',
        description: `File uploaded successfully. Session ID: ${result.id}`,
      });

      // Reset state
      setSelectedFile(null);

      // Close modal and call success callback
      onOpenChange(false);
      onSuccess?.();

    } catch (error: any) {
      toast({
        title: 'Import Failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setIsImporting(false);
    }
  };

  // Reset state when modal closes
  React.useEffect(() => {
    if (!open) {
      setImportUrl('');
      setSelectedFile(null);
      setIsImporting(false);
      setActiveTab('url');
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Import Listings</DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'url' | 'file')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="url">
              <Link className="h-4 w-4 mr-2" />
              URL
            </TabsTrigger>
            <TabsTrigger value="file">
              <Upload className="h-4 w-4 mr-2" />
              File
            </TabsTrigger>
          </TabsList>

          <TabsContent value="url" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="import-url">Listing URL</Label>
              <Input
                id="import-url"
                type="url"
                placeholder="https://www.ebay.com/itm/..."
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                disabled={isImporting}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !isImporting && importUrl.trim()) {
                    handleUrlImport();
                  }
                }}
              />
              <p className="text-xs text-muted-foreground">
                Supports eBay, Amazon, and most retail websites
              </p>
            </div>

            <Button
              onClick={handleUrlImport}
              disabled={isImporting || !importUrl.trim()}
              className="w-full"
            >
              {isImporting ? 'Importing...' : 'Import from URL'}
            </Button>
          </TabsContent>

          <TabsContent value="file" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="import-file">Excel Workbook</Label>
              <Input
                id="import-file"
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                disabled={isImporting}
              />
              {selectedFile && (
                <p className="text-sm text-muted-foreground">
                  Selected: {selectedFile.name}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                Upload .xlsx, .xls, or .csv files with listing data
              </p>
            </div>

            <Button
              onClick={handleFileImport}
              disabled={isImporting || !selectedFile}
              className="w-full"
            >
              {isImporting ? 'Importing...' : 'Import from File'}
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
