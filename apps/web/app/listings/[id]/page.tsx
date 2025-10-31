import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/utils";
import { DetailPageLayout } from "@/components/listings/detail-page-layout";
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

export default async function ListingDetailPage({ params }: PageProps) {
  const listing = await getListingDetail(params.id);

  if (!listing) {
    notFound();
  }

  return <DetailPageLayout listing={listing} />;
}
