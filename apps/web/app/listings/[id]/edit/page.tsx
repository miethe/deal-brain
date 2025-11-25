import { notFound, redirect } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { EditListingForm } from "@/components/listings/edit-listing-form";
import type { ListingDetail } from "@/types/listing-detail";

interface PageProps {
  params: {
    id: string;
  };
}

async function getListingDetail(id: string): Promise<ListingDetail | null> {
  try {
    const listing = await apiFetch<ListingDetail>(`/v1/listings/${id}`);
    return listing;
  } catch (error) {
    return null;
  }
}

export default async function EditListingPage({ params }: PageProps) {
  const listing = await getListingDetail(params.id);

  if (!listing) {
    notFound();
  }

  return (
    <div className="container mx-auto space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Edit Listing</h1>
        <p className="text-muted-foreground">
          Update the details for {listing.title}
        </p>
      </div>

      <EditListingForm listing={listing} />
    </div>
  );
}
