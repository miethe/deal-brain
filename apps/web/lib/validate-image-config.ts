/**
 * Image Configuration Validation
 *
 * Provides Zod schema validation for the product images configuration file.
 * Ensures type safety and catches configuration errors at build time.
 */

import { z } from 'zod';
import type { ImageConfig } from '../types/product-images';

/**
 * Zod schema for manufacturer-specific images
 */
const manufacturerImagesSchema = z.object({
  logo: z.string().min(1, 'Logo path cannot be empty'),
  series: z.record(z.string().min(1, 'Series image path cannot be empty')).optional(),
  fallback: z.string().min(1, 'Fallback path cannot be empty').optional(),
});

/**
 * Zod schema for form factor images
 */
const formFactorImagesSchema = z.object({
  icon: z.string().min(1, 'Icon path cannot be empty'),
  generic: z.string().min(1, 'Generic image path cannot be empty').optional(),
});

/**
 * Zod schema for fallback images
 */
const fallbackImagesSchema = z.object({
  generic: z.string().min(1, 'Generic fallback path cannot be empty'),
});

/**
 * Root image configuration schema
 *
 * Validates the entire product-images.json configuration structure.
 */
export const imageConfigSchema = z.object({
  version: z
    .string()
    .regex(/^\d+\.\d+(\.\d+)?$/, 'Version must be in semantic versioning format (e.g., "1.0.0")'),
  baseUrl: z
    .string()
    .min(1, 'Base URL cannot be empty')
    .refine(
      (url) => url.startsWith('/'),
      'Base URL must start with "/" for Next.js public directory'
    ),
  manufacturers: z.record(manufacturerImagesSchema),
  formFactors: z.record(formFactorImagesSchema),
  cpuVendors: z.record(z.string().min(1, 'CPU vendor image path cannot be empty')),
  gpuVendors: z.record(z.string().min(1, 'GPU vendor image path cannot be empty')),
  fallbacks: fallbackImagesSchema,
});

/**
 * Validates the image configuration object
 *
 * @param config - The configuration object to validate
 * @returns The validated and typed configuration
 * @throws {z.ZodError} If validation fails with detailed error messages
 *
 * @example
 * ```typescript
 * import productImagesConfig from '@/config/product-images.json';
 * import { validateImageConfig } from '@/lib/validate-image-config';
 *
 * try {
 *   const config = validateImageConfig(productImagesConfig);
 *   console.log('Configuration is valid:', config);
 * } catch (error) {
 *   if (error instanceof z.ZodError) {
 *     console.error('Configuration validation errors:', error.errors);
 *   }
 * }
 * ```
 */
export function validateImageConfig(config: unknown): ImageConfig {
  return imageConfigSchema.parse(config) as ImageConfig;
}

/**
 * Safely validates the image configuration without throwing errors
 *
 * @param config - The configuration object to validate
 * @returns Success object with data, or failure object with error
 *
 * @example
 * ```typescript
 * const result = safeValidateImageConfig(config);
 * if (result.success) {
 *   console.log('Valid config:', result.data);
 * } else {
 *   console.error('Validation errors:', result.error.errors);
 * }
 * ```
 */
export function safeValidateImageConfig(config: unknown) {
  return imageConfigSchema.safeParse(config);
}
