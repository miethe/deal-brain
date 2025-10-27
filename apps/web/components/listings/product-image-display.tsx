"use client";

import Image from "next/image";
import { useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface ProductImageDisplayProps {
  listing: {
    id?: number;
    thumbnail_url?: string | null;
    image_url?: string | null;
    manufacturer?: string | null;
    cpu?: { manufacturer?: string | null } | null;
    form_factor?: string | null;
    title?: string | null;
  };
  className?: string;
}

/**
 * ProductImageDisplay component with 5-level fallback hierarchy
 *
 * Fallback order:
 * 1. listing.thumbnail_url (if available and no error)
 * 2. listing.image_url (if available and no error)
 * 3. Manufacturer logo: /images/manufacturers/{manufacturer-slug}.svg
 * 4. CPU manufacturer logo: /images/fallbacks/{cpu-manufacturer}-logo.svg (intel or amd)
 * 5. Form factor icon: /images/fallbacks/{form-factor-slug}-icon.svg
 * 6. Generic fallback: /images/fallbacks/generic-pc.svg
 */
export function ProductImageDisplay({ listing, className }: ProductImageDisplayProps) {
  const [imageError, setImageError] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Converts a string to a URL-friendly slug
   */
  const slugify = (text: string): string => {
    return text
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '-')
      .replace(/[^\w-]/g, '');
  };

  /**
   * Determines the image source based on fallback hierarchy
   */
  const getImageSrc = (): string => {
    // Level 1: Listing thumbnail (if no error yet)
    if (!imageError && listing.thumbnail_url) {
      return listing.thumbnail_url;
    }

    // Level 2: Listing image URL (if no error yet)
    if (!imageError && listing.image_url) {
      return listing.image_url;
    }

    // Level 3: Manufacturer logo
    if (listing.manufacturer) {
      const manufacturerSlug = slugify(listing.manufacturer);
      return `/images/manufacturers/${manufacturerSlug}.svg`;
    }

    // Level 4: CPU manufacturer logo (Intel/AMD)
    if (listing.cpu?.manufacturer) {
      const cpuManufacturer = listing.cpu.manufacturer.toLowerCase();
      if (cpuManufacturer.includes('intel') || cpuManufacturer.includes('amd')) {
        const cleanManufacturer = cpuManufacturer.includes('intel') ? 'intel' : 'amd';
        return `/images/fallbacks/${cleanManufacturer}-logo.svg`;
      }
    }

    // Level 5: Form factor icon
    if (listing.form_factor) {
      const formFactorSlug = slugify(listing.form_factor);
      return `/images/fallbacks/${formFactorSlug}-icon.svg`;
    }

    // Level 6: Generic placeholder
    return '/images/fallbacks/generic-pc.svg';
  };

  const imageSrc = getImageSrc();
  const altText = listing.title || 'Product image';

  // Determine if we're using a fallback image for styling purposes
  const isUsingFallback = imageError || !listing.thumbnail_url && !listing.image_url;

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
          onError={() => {
            setImageError(true);
            setIsLoading(false);
            if (process.env.NODE_ENV === 'development') {
              console.warn(`[ProductImageDisplay] Image failed to load: ${imageSrc}`);
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
