"use client";

import { useState } from "react";
import Image from "next/image";
import { Package } from "lucide-react";
import { cn } from "@/lib/utils";
import { MANUFACTURER_LOGOS } from "@/types/listing-detail";
import type { ListingDetail } from "@/types/listing-detail";

interface ProductImageProps {
  listing: ListingDetail;
  className?: string;
}

export function ProductImage({ listing, className }: ProductImageProps) {
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  // Three-tier fallback hierarchy
  const getPrimaryImageUrl = () => listing.thumbnail_url;

  const getSecondaryImageUrl = () => {
    const manufacturer = listing.cpu?.manufacturer || listing.gpu?.manufacturer;
    if (manufacturer && MANUFACTURER_LOGOS[manufacturer]) {
      return MANUFACTURER_LOGOS[manufacturer];
    }
    return null;
  };

  const getTertiaryImageUrl = () => MANUFACTURER_LOGOS.Default;

  // Determine which image to show
  const primaryUrl = getPrimaryImageUrl();
  const secondaryUrl = getSecondaryImageUrl();
  const tertiaryUrl = getTertiaryImageUrl();

  const currentImageUrl = !imageError && primaryUrl ? primaryUrl : secondaryUrl || tertiaryUrl;
  const isUsingFallback = !primaryUrl || imageError;

  // Alt text generation
  const getAltText = () => {
    if (!isUsingFallback && primaryUrl) {
      return `Product image for ${listing.title}`;
    }
    const manufacturer = listing.cpu?.manufacturer || listing.gpu?.manufacturer;
    if (manufacturer && secondaryUrl) {
      return `${manufacturer} logo`;
    }
    return "Generic PC icon";
  };

  return (
    <div
      className={cn(
        "relative flex items-center justify-center overflow-hidden rounded-lg border bg-muted/50",
        className
      )}
    >
      {currentImageUrl ? (
        <div className="relative h-full w-full">
          {imageLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-8 w-8 animate-pulse rounded-full bg-muted" />
            </div>
          )}
          <Image
            src={currentImageUrl}
            alt={getAltText()}
            fill
            className={cn(
              "object-contain transition-opacity duration-300",
              imageLoading ? "opacity-0" : "opacity-100",
              isUsingFallback ? "p-8" : "p-4"
            )}
            sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 400px"
            onLoad={() => setImageLoading(false)}
            onError={() => {
              setImageError(true);
              setImageLoading(false);
            }}
            priority
          />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-2 p-8 text-muted-foreground">
          <Package className="h-16 w-16" />
          <p className="text-sm">No image available</p>
        </div>
      )}
    </div>
  );
}
