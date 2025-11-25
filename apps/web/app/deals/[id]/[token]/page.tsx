import { notFound } from "next/navigation";
import { Metadata } from "next";
import { apiFetch } from "@/lib/utils";
import { PublicDealView } from "@/components/deals/public-deal-view";
import type { ListingDetail } from "@/types/listing-detail";

interface ShareResponse {
  share: {
    id: number;
    listing_id: number;
    share_token: string;
    expires_at: string;
    view_count: number;
    created_by_id: number;
  };
  listing: ListingDetail;
}

interface PageProps {
  params: {
    id: string;
    token: string;
  };
}

async function getSharedDeal(id: string, token: string): Promise<ShareResponse | null> {
  try {
    const response = await apiFetch<ShareResponse>(`/v1/deals/${id}/${token}`);
    return response;
  } catch (error) {
    return null;
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const data = await getSharedDeal(params.id, params.token);

  if (!data) {
    return {
      title: "Deal Not Found | Deal Brain",
      description: "This deal may have expired or been removed.",
    };
  }

  const { listing } = data;

  // Generate title with key specs
  const cpuName = listing.cpu?.model || listing.cpu_name || "Unknown CPU";
  const ramSize = listing.ram_gb ? `${listing.ram_gb}GB RAM` : "";
  const titleParts = [listing.title, cpuName, ramSize].filter(Boolean);
  const title = titleParts.join(" • ");

  // Generate description with price and score
  const price = listing.price_usd
    ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(listing.price_usd)
    : "Price unavailable";

  const adjustedValue = listing.adjusted_price_usd
    ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(listing.adjusted_price_usd)
    : null;

  const score = listing.score_composite ? listing.score_composite.toFixed(2) : null;

  const descriptionParts = [
    `Listed at ${price}`,
    adjustedValue ? `Adjusted value: ${adjustedValue}` : null,
    score ? `Composite score: ${score}` : null,
  ].filter(Boolean);

  const description = descriptionParts.join(" | ");

  // Image URL for OpenGraph
  const imageUrl = listing.thumbnail_url || "/images/fallbacks/generic-pc.svg";
  const absoluteImageUrl = imageUrl.startsWith("http")
    ? imageUrl
    : `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}${imageUrl}`;

  // Full share URL
  const shareUrl = `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}/deals/${params.id}/${params.token}`;

  return {
    title: `${title} | Deal Brain`,
    description,
    openGraph: {
      title,
      description,
      url: shareUrl,
      siteName: "Deal Brain",
      images: [
        {
          url: absoluteImageUrl,
          width: 1200,
          height: 630,
          alt: listing.title,
        },
      ],
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [absoluteImageUrl],
    },
  };
}

export default async function PublicDealPage({ params }: PageProps) {
  const data = await getSharedDeal(params.id, params.token);

  if (!data) {
    notFound();
  }

  return <PublicDealView share={data.share} listing={data.listing} />;
}
