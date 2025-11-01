/**
 * Product Image Resolver
 *
 * High-performance image resolution utility implementing a 7-level fallback hierarchy.
 * Performance target: <1ms resolution time per call.
 *
 * Fallback Hierarchy:
 * 1. listing.thumbnail_url (External URL - highest priority)
 * 2. Model-specific image (Config: manufacturers[x].series[model_number])
 * 3. Series-specific image (Config: manufacturers[x].series[series])
 * 4. Manufacturer logo (Config: manufacturers[x].logo)
 * 5. CPU vendor logo (Config: cpuVendors[cpu.manufacturer])
 * 6. Form factor icon (Config: formFactors[form_factor].icon)
 * 7. Generic fallback (Config: fallbacks.generic)
 */

import imageConfig from '@/config/product-images.json';
import type { ImageConfig } from '@/types/product-images';
import type { ListingDetail } from '@/types/listing-detail';
import type { ListingRecord } from '@/types/listings';

// Type-cast the imported JSON to ensure type safety
const config: ImageConfig = imageConfig as ImageConfig;

/**
 * Image source types for debugging and analytics
 */
export type ImageSource =
  | 'thumbnail_url'
  | 'model_specific'
  | 'series_specific'
  | 'manufacturer_logo'
  | 'cpu_vendor_logo'
  | 'form_factor_icon'
  | 'generic_fallback';

/**
 * Result from image resolution including source metadata
 */
export interface ImageResolutionResult {
  /** Resolved image path or URL */
  path: string;
  /** Source level that provided the image */
  source: ImageSource;
  /** Whether the path is an external URL */
  isExternal: boolean;
}

/**
 * Union type for supported listing types
 */
type SupportedListing = ListingDetail | ListingRecord;

/**
 * Normalizes a string value for configuration lookups.
 * Converts to lowercase and replaces spaces with underscores.
 *
 * @param value - Raw string value from listing
 * @returns Normalized string for config key lookup
 */
function normalizeKey(value: string | null | undefined): string | null {
  if (!value || typeof value !== 'string') {
    return null;
  }
  return value.toLowerCase().trim().replace(/\s+/g, '_');
}

/**
 * Checks if a string is a valid external URL
 *
 * @param value - String to check
 * @returns True if value is a valid HTTP/HTTPS URL
 */
function isExternalUrl(value: string | null | undefined): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }
  return value.startsWith('http://') || value.startsWith('https://');
}

/**
 * Resolves the best available image for a product listing using the 7-level fallback hierarchy.
 * Optimized for early exit - stops on first successful match.
 *
 * @param listing - Listing object (ListingDetail or ListingRecord)
 * @returns Resolved image path or URL
 */
export function resolveProductImage(listing: SupportedListing): string {
  // Level 1: Direct thumbnail URL (external)
  if (listing.thumbnail_url && isExternalUrl(listing.thumbnail_url)) {
    return listing.thumbnail_url;
  }

  // Normalize values for config lookups
  const manufacturer = normalizeKey(listing.manufacturer);
  const series = normalizeKey(listing.series);
  const modelNumber = normalizeKey(listing.model_number);
  const formFactor = normalizeKey(listing.form_factor);
  const cpuVendor = normalizeKey(listing.cpu?.manufacturer);

  // Level 2: Model-specific image
  if (manufacturer && modelNumber) {
    const modelImage = config.manufacturers[manufacturer]?.series?.[modelNumber];
    if (modelImage) {
      return `${config.baseUrl}${modelImage}`;
    }
  }

  // Level 3: Series-specific image
  if (manufacturer && series) {
    const seriesImage = config.manufacturers[manufacturer]?.series?.[series];
    if (seriesImage) {
      return `${config.baseUrl}${seriesImage}`;
    }
  }

  // Level 4: Manufacturer logo
  if (manufacturer) {
    const manufacturerLogo = config.manufacturers[manufacturer]?.logo;
    if (manufacturerLogo) {
      return manufacturerLogo;
    }
  }

  // Level 5: CPU vendor logo
  if (cpuVendor) {
    const cpuVendorLogo = config.cpuVendors[cpuVendor];
    if (cpuVendorLogo) {
      return cpuVendorLogo;
    }
  }

  // Level 6: Form factor icon
  if (formFactor) {
    const formFactorIcon = config.formFactors[formFactor]?.icon;
    if (formFactorIcon) {
      return formFactorIcon;
    }
  }

  // Level 7: Generic fallback (always available)
  return config.fallbacks.generic;
}

/**
 * Resolves image with detailed source information for debugging and analytics.
 * Follows the same 7-level fallback hierarchy as resolveProductImage.
 *
 * @param listing - Listing object (ListingDetail or ListingRecord)
 * @returns Image resolution result with source metadata
 */
export function getImageSource(listing: SupportedListing): ImageResolutionResult {
  // Level 1: Direct thumbnail URL (external)
  if (listing.thumbnail_url && isExternalUrl(listing.thumbnail_url)) {
    return {
      path: listing.thumbnail_url,
      source: 'thumbnail_url',
      isExternal: true,
    };
  }

  // Normalize values for config lookups
  const manufacturer = normalizeKey(listing.manufacturer);
  const series = normalizeKey(listing.series);
  const modelNumber = normalizeKey(listing.model_number);
  const formFactor = normalizeKey(listing.form_factor);
  const cpuVendor = normalizeKey(listing.cpu?.manufacturer);

  // Level 2: Model-specific image
  if (manufacturer && modelNumber) {
    const modelImage = config.manufacturers[manufacturer]?.series?.[modelNumber];
    if (modelImage) {
      return {
        path: `${config.baseUrl}${modelImage}`,
        source: 'model_specific',
        isExternal: false,
      };
    }
  }

  // Level 3: Series-specific image
  if (manufacturer && series) {
    const seriesImage = config.manufacturers[manufacturer]?.series?.[series];
    if (seriesImage) {
      return {
        path: `${config.baseUrl}${seriesImage}`,
        source: 'series_specific',
        isExternal: false,
      };
    }
  }

  // Level 4: Manufacturer logo
  if (manufacturer) {
    const manufacturerLogo = config.manufacturers[manufacturer]?.logo;
    if (manufacturerLogo) {
      return {
        path: manufacturerLogo,
        source: 'manufacturer_logo',
        isExternal: false,
      };
    }
  }

  // Level 5: CPU vendor logo
  if (cpuVendor) {
    const cpuVendorLogo = config.cpuVendors[cpuVendor];
    if (cpuVendorLogo) {
      return {
        path: cpuVendorLogo,
        source: 'cpu_vendor_logo',
        isExternal: false,
      };
    }
  }

  // Level 6: Form factor icon
  if (formFactor) {
    const formFactorIcon = config.formFactors[formFactor]?.icon;
    if (formFactorIcon) {
      return {
        path: formFactorIcon,
        source: 'form_factor_icon',
        isExternal: false,
      };
    }
  }

  // Level 7: Generic fallback (always available)
  return {
    path: config.fallbacks.generic,
    source: 'generic_fallback',
    isExternal: false,
  };
}

/**
 * Batch resolve images for multiple listings with optimized performance.
 * Useful for table/list views where many images need resolution at once.
 *
 * @param listings - Array of listings to resolve images for
 * @returns Array of resolved image paths in same order as input
 */
export function batchResolveProductImages(listings: SupportedListing[]): string[] {
  return listings.map(resolveProductImage);
}

/**
 * Preload images for better perceived performance.
 * Returns a promise that resolves when all images are loaded.
 *
 * @param imagePaths - Array of image paths to preload
 * @returns Promise that resolves when all images are loaded
 */
export function preloadImages(imagePaths: string[]): Promise<void[]> {
  const promises = imagePaths.map((src) => {
    return new Promise<void>((resolve, reject) => {
      // Skip external URLs in preloading (browser will handle them)
      if (isExternalUrl(src)) {
        resolve();
        return;
      }

      const img = new Image();
      img.onload = () => resolve();
      img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
      img.src = src;
    });
  });

  return Promise.all(promises);
}
