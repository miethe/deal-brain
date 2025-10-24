import { BreadcrumbNav } from "./breadcrumb-nav";
import { DetailPageHero } from "./detail-page-hero";
import { DetailPageTabs } from "./detail-page-tabs";
import type { ListingDetail } from "@/types/listing-detail";

interface DetailPageLayoutProps {
  listing: ListingDetail;
}

export function DetailPageLayout({ listing }: DetailPageLayoutProps) {
  return (
    <div className="container mx-auto space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Breadcrumb Navigation */}
      <BreadcrumbNav listingTitle={listing.title} />

      {/* Hero Section */}
      <DetailPageHero listing={listing} />

      {/* Tabbed Content */}
      <DetailPageTabs listing={listing} />
    </div>
  );
}
