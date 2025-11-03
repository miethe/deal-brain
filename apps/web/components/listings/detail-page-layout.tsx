"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { Trash2 } from "lucide-react";
import { BreadcrumbNav } from "./breadcrumb-nav";
import { DetailPageHero } from "./detail-page-hero";
import { DetailPageTabs } from "./detail-page-tabs";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
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

  return (
    <div className="container mx-auto space-y-4 px-4 py-6 sm:px-6 lg:px-8">
      {/* Header with Breadcrumb and Actions */}
      <div className="flex items-center justify-between gap-4">
        <BreadcrumbNav listingTitle={listing.title} />

        <Button
          variant="outline"
          size="sm"
          onClick={() => setDeleteConfirmOpen(true)}
          disabled={isDeleting}
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Delete
        </Button>
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
