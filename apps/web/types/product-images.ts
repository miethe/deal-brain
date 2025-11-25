/**
 * Product Images Configuration Types
 *
 * Type definitions for the image management system configuration.
 * These types define the structure for manufacturer logos, form factor icons,
 * CPU/GPU vendor images, and fallback images.
 */

/**
 * Manufacturer-specific image configuration
 */
export interface ManufacturerImages {
  /** Primary logo image path */
  logo: string;
  /** Optional series-specific images (e.g., EliteDesk, ProDesk for HP) */
  series?: Record<string, string>;
  /** Optional manufacturer-specific fallback image */
  fallback?: string;
}

/**
 * Form factor image configuration
 */
export interface FormFactorImages {
  /** Icon representing the form factor (e.g., mini PC, desktop) */
  icon: string;
  /** Optional generic product image for this form factor */
  generic?: string;
}

/**
 * Global fallback images
 */
export interface FallbackImages {
  /** Generic PC fallback image used when all other options fail */
  generic: string;
}

/**
 * Root image configuration schema
 */
export interface ImageConfig {
  /** Semantic version of the configuration schema */
  version: string;
  /** Base URL path for all images (typically "/images") */
  baseUrl: string;
  /** Manufacturer-specific image mappings (keyed by manufacturer slug) */
  manufacturers: Record<string, ManufacturerImages>;
  /** Form factor image mappings (keyed by form factor slug) */
  formFactors: Record<string, FormFactorImages>;
  /** CPU vendor logo mappings (keyed by vendor name: intel, amd, arm) */
  cpuVendors: Record<string, string>;
  /** GPU vendor logo mappings (keyed by vendor name: nvidia, amd, intel) */
  gpuVendors: Record<string, string>;
  /** Global fallback images */
  fallbacks: FallbackImages;
}
