"use client";

import Image from "next/image";
import { useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { resolveProductImage, getImageSource } from "@/lib/image-resolver";

interface ProductImageDisplayProps {
  listing: {
    id?: number;
    thumbnail_url?: string | null;
    image_url?: string | null;
    manufacturer?: string | null;
    series?: string | null;
    model_number?: string | null;
    cpu?: { manufacturer?: string | null } | null;
    form_factor?: string | null;
    title?: string | null;
  };
  className?: string;
}

/**
 * ProductImageDisplay component with 7-level fallback hierarchy
 *
 * Uses the centralized image-resolver utility for deterministic image resolution.
 * No longer manages fallback state - the resolver handles this at call time.
 *
 * Fallback order (via image-resolver):
 * 1. listing.thumbnail_url (external URL)
 * 2. Model-specific image (config-based)
 * 3. Series-specific image (config-based)
 * 4. Manufacturer logo (config-based)
 * 5. CPU vendor logo (config-based)
 * 6. Form factor icon (config-based)
 * 7. Generic fallback (always available)
 */
export function ProductImageDisplay({ listing, className }: ProductImageDisplayProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Resolve image using the centralized resolver (deterministic, no state needed)
  const imageSrc = resolveProductImage(listing);
  const { isExternal } = getImageSource(listing);
  const altText = listing.title || 'Product image';

  // Determine if we're using a config-based fallback image for styling purposes
  // External URLs (thumbnail_url) get less padding, config images get more padding
  const isUsingFallback = !isExternal;

  return (
    <>
      <div
        className={cn(
          "relative cursor-pointer group rounded-lg overflow-hidden bg-muted/30 border border-border",
          className
        )}
        onClick={() => setLightboxOpen(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setLightboxOpen(true);
          }
        }}
        aria-label="Open image in full size"
      >
        {isLoading && (
          <Skeleton className="w-full h-full absolute inset-0 rounded-lg" />
        )}
        <Image
          src={imageSrc}
          alt={altText}
          width={400}
          height={300}
          loading="lazy"
          quality={85}
          className={cn(
            "rounded-lg object-contain transition-all duration-200",
            "group-hover:opacity-90 group-hover:scale-[1.02]",
            isLoading && "opacity-0",
            isUsingFallback ? "p-8" : "p-2"
          )}
          onLoadingComplete={() => setIsLoading(false)}
          onLoad={() => setIsLoading(false)}
          onError={(e) => {
            setIsLoading(false);
            // Image resolver always returns a valid path, so errors should be rare
            // Log for debugging purposes only
            if (process.env.NODE_ENV === 'development') {
              console.warn('[ProductImageDisplay] Image failed to load:', imageSrc, e);
            }
          }}
        />
      </div>

      {/* Lightbox for full-size view */}
      <Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
        <DialogContent className="max-w-4xl p-0 overflow-hidden">
          <div className="relative w-full h-[80vh] bg-muted/20">
            <Image
              src={imageSrc}
              alt={altText}
              fill
              className={cn(
                "object-contain",
                isUsingFallback ? "p-12" : "p-4"
              )}
              sizes="(max-width: 1200px) 100vw, 1200px"
              quality={90}
              priority
            />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
