"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { Trash2, Download, Loader2, MoreVertical, Edit, Image as ImageIcon } from "lucide-react";
import { BreadcrumbNav } from "./breadcrumb-nav";
import { DetailPageHero } from "./detail-page-hero";
import { DetailPageTabs } from "./detail-page-tabs";
import { CardDownloadModal } from "./card-download-modal";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { API_URL } from "@/lib/utils";
import type { ListingDetail } from "@/types/listing-detail";

interface DetailPageLayoutProps {
  listing: ListingDetail;
}

export function DetailPageLayout({ listing }: DetailPageLayoutProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Delete mutation
  const { mutate: deleteListing, isPending: isDeleting } = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`${API_URL}/v1/listings/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to delete listing' }));
        throw new Error(error.detail || 'Failed to delete listing');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] });
      toast({
        title: 'Success',
        description: 'Listing deleted successfully',
      });
      router.push('/listings'); // Navigate back to catalog
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: `Delete failed: ${error.message}`,
        variant: 'destructive',
      });
    },
  });

  // Export handler
  const handleExport = async () => {
    try {
      setIsExporting(true);
      const response = await fetch(`${API_URL}/v1/listings/${listing.id}/export`);

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Get the filename from Content-Disposition header or create one
      const contentDisposition = response.headers.get('Content-Disposition');
      const listingTitle = listing.title.replace(/[^a-zA-Z0-9-_]/g, '-').substring(0, 50);
      const date = new Date().toISOString().split('T')[0];
      let filename = `listing-${listingTitle}-${date}.json`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Export successful',
        description: 'Listing exported as JSON',
      });
    } catch (error) {
      toast({
        title: 'Export failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="container mx-auto space-y-4 px-4 py-6 sm:px-6 lg:px-8">
      {/* Header with Breadcrumb and Actions */}
      <div className="flex items-center justify-between gap-4">
        <BreadcrumbNav listingTitle={listing.title} />

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/listings/${listing.id}/edit`}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Link>
          </Button>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" disabled={isExporting || isDeleting}>
              {isExporting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <MoreVertical className="h-4 w-4" />
                  <span className="sr-only">Actions</span>
                </>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleExport} disabled={isExporting}>
              <Download className="h-4 w-4 mr-2" />
              Export as JSON
            </DropdownMenuItem>
            <CardDownloadModal
              listing={listing}
              trigger={
                <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                  <ImageIcon className="h-4 w-4 mr-2" />
                  Download Card
                </DropdownMenuItem>
              }
            />
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => setDeleteConfirmOpen(true)}
              disabled={isDeleting}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Hero Section */}
      <DetailPageHero listing={listing} />

      <Separator className="my-4" />

      {/* Tabbed Content */}
      <DetailPageTabs listing={listing} />

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        open={deleteConfirmOpen}
        onOpenChange={setDeleteConfirmOpen}
        title="Delete Listing?"
        description="This action cannot be undone. The listing and all related data will be permanently deleted."
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
        onConfirm={() => deleteListing(listing.id)}
        isLoading={isDeleting}
      />
    </div>
  );
}
