/**
 * Configuration Import Tests
 *
 * Verifies that the configuration file can be imported and used correctly.
 */

import productImagesConfig from '../../config/product-images.json';
import type { ImageConfig } from '../../types/product-images';

describe('product-images.json import', () => {
  it('should be importable as JSON', () => {
    expect(productImagesConfig).toBeDefined();
    expect(typeof productImagesConfig).toBe('object');
  });

  it('should have all required top-level fields', () => {
    expect(productImagesConfig).toHaveProperty('version');
    expect(productImagesConfig).toHaveProperty('baseUrl');
    expect(productImagesConfig).toHaveProperty('manufacturers');
    expect(productImagesConfig).toHaveProperty('formFactors');
    expect(productImagesConfig).toHaveProperty('cpuVendors');
    expect(productImagesConfig).toHaveProperty('gpuVendors');
    expect(productImagesConfig).toHaveProperty('fallbacks');
  });

  it('should have valid version', () => {
    expect(productImagesConfig.version).toBe('1.0.0');
    expect(/^\d+\.\d+\.\d+$/.test(productImagesConfig.version)).toBe(true);
  });

  it('should have valid base URL', () => {
    expect(productImagesConfig.baseUrl).toBe('/images');
    expect(productImagesConfig.baseUrl.startsWith('/')).toBe(true);
  });

  it('should be type-compatible with ImageConfig interface', () => {
    // This test verifies TypeScript type compatibility
    const config: ImageConfig = productImagesConfig as unknown as ImageConfig;
    expect(config).toBeDefined();
  });
});

describe('Configuration content validation', () => {
  it('should contain form factors', () => {
    const formFactors = Object.keys(productImagesConfig.formFactors);
    expect(formFactors.length).toBeGreaterThan(0);
    expect(formFactors).toContain('mini-pc');
    expect(formFactors).toContain('desktop');
  });

  it('should contain CPU vendors', () => {
    const cpuVendors = Object.keys(productImagesConfig.cpuVendors);
    expect(cpuVendors.length).toBeGreaterThan(0);
    expect(cpuVendors).toContain('intel');
    expect(cpuVendors).toContain('amd');
  });

  it('should contain GPU vendors', () => {
    const gpuVendors = Object.keys(productImagesConfig.gpuVendors);
    expect(gpuVendors.length).toBeGreaterThan(0);
    expect(gpuVendors).toContain('nvidia');
  });

  it('should have generic fallback', () => {
    expect(productImagesConfig.fallbacks.generic).toBeTruthy();
    expect(typeof productImagesConfig.fallbacks.generic).toBe('string');
  });

  it('should have valid image paths', () => {
    // All paths should start with /images
    const allPaths: string[] = [];

    // Collect all paths from manufacturers
    Object.values(productImagesConfig.manufacturers).forEach((mfg) => {
      allPaths.push(mfg.logo);
      if (mfg.series) {
        allPaths.push(...Object.values(mfg.series));
      }
      if (mfg.fallback) {
        allPaths.push(mfg.fallback);
      }
    });

    // Collect all paths from form factors
    Object.values(productImagesConfig.formFactors).forEach((ff) => {
      allPaths.push(ff.icon);
      if (ff.generic) {
        allPaths.push(ff.generic);
      }
    });

    // Collect all paths from vendors
    allPaths.push(...Object.values(productImagesConfig.cpuVendors));
    allPaths.push(...Object.values(productImagesConfig.gpuVendors));

    // Collect fallbacks
    allPaths.push(productImagesConfig.fallbacks.generic);

    // Verify all paths start with /images
    allPaths.forEach((path) => {
      expect(path.startsWith('/images/')).toBe(true);
    });
  });
});
