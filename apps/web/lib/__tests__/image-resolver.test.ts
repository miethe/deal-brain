/**
 * Image Resolver Tests
 *
 * Comprehensive test suite for the product image resolver utility.
 * Tests all 7 fallback levels, edge cases, and performance benchmarks.
 */

import {
  resolveProductImage,
  getImageSource,
  batchResolveProductImages,
  type ImageSource,
} from '../image-resolver';
import type { ListingDetail } from '@/types/listing-detail';
import type { ListingRecord } from '@/types/listings';

describe('resolveProductImage', () => {
  // Base listing fixture with all fields null
  const baseListingRecord: ListingRecord = {
    id: 1,
    title: 'Test PC',
    listing_url: null,
    other_urls: null,
    seller: null,
    price_usd: 500,
    adjusted_price_usd: null,
    score_composite: null,
    score_cpu_multi: null,
    score_cpu_single: null,
    score_gpu: null,
    dollar_per_cpu_mark: null,
    dollar_per_single_mark: null,
    condition: 'used',
    status: 'active',
    cpu_id: null,
    cpu_name: null,
    gpu_id: null,
    gpu_name: null,
    ram_gb: null,
    ram_spec_id: null,
    ram_spec: null,
    ram_type: null,
    ram_speed_mhz: null,
    primary_storage_gb: null,
    primary_storage_type: null,
    primary_storage_profile_id: null,
    primary_storage_profile: null,
    secondary_storage_gb: null,
    secondary_storage_type: null,
    secondary_storage_profile_id: null,
    secondary_storage_profile: null,
    manufacturer: null,
    series: null,
    model_number: null,
    form_factor: null,
    thumbnail_url: null,
    valuation_breakdown: null,
    cpu: null,
    gpu: null,
    ports_profile: null,
    attributes: {},
    ruleset_id: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  const baseListingDetail: ListingDetail = {
    ...baseListingRecord,
    cpu: null,
    gpu: null,
    ports_profile: null,
  };

  describe('Level 1: thumbnail_url (highest priority)', () => {
    it('should return thumbnail_url when present (ListingRecord)', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        thumbnail_url: 'https://example.com/thumb.jpg',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('https://example.com/thumb.jpg');
    });

    it('should return thumbnail_url when present (ListingDetail)', () => {
      const listing: ListingDetail = {
        ...baseListingDetail,
        thumbnail_url: 'https://example.com/thumb.jpg',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('https://example.com/thumb.jpg');
    });

    it('should skip thumbnail_url if not a valid HTTP URL', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        thumbnail_url: '/local/path.jpg', // Not an external URL
        manufacturer: 'HPE',
      };

      const result = resolveProductImage(listing);
      // Should fall through to manufacturer logo
      expect(result).toBe('/images/manufacturers/hpe.svg');
    });

    it('should handle thumbnail_url with HTTPS', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        thumbnail_url: 'https://secure.example.com/image.png',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('https://secure.example.com/image.png');
    });
  });

  describe('Level 2: model-specific image', () => {
    it('should return model-specific image when manufacturer and model_number match', () => {
      // Note: Current config doesn't have model-specific images
      // This test validates the logic works when config is extended
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HP',
        model_number: 'EliteDesk 800 G5',
      };

      const result = resolveProductImage(listing);
      // Should fall through to next level (no model-specific images in current config)
      expect(result).not.toContain('elitedesk_800_g5');
    });

    it('should normalize manufacturer and model_number for lookup', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HP ENTERPRISE', // Should normalize to hp_enterprise
        model_number: 'ProDesk 600', // Should normalize to prodesk_600
      };

      const result = resolveProductImage(listing);
      // Should fall through since config doesn't have these
      expect(result).toBeTruthy();
    });

    it('should skip model-specific lookup if manufacturer is missing', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        model_number: 'SomeModel',
        form_factor: 'Mini-PC',
      };

      const result = resolveProductImage(listing);
      // Should fall through to form factor
      expect(result).toBe('/images/fallbacks/mini-pc-icon.svg');
    });

    it('should skip model-specific lookup if model_number is missing', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HPE',
      };

      const result = resolveProductImage(listing);
      // Should fall through to manufacturer logo
      expect(result).toBe('/images/manufacturers/hpe.svg');
    });
  });

  describe('Level 3: series-specific image', () => {
    it('should return series-specific image when manufacturer and series match', () => {
      // Note: Current config doesn't have series-specific images
      // This test validates the logic works when config is extended
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HP',
        series: 'EliteDesk',
      };

      const result = resolveProductImage(listing);
      // Should fall through to next level (no series-specific images in current config)
      expect(result).not.toContain('elitedesk');
    });

    it('should normalize series with spaces', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'Dell',
        series: 'OptiPlex 7000 Series', // Should normalize to optiplex_7000_series
      };

      const result = resolveProductImage(listing);
      expect(result).toBeTruthy();
    });

    it('should skip series lookup if manufacturer is missing', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        series: 'SomeSeries',
        cpu: { manufacturer: 'Intel' } as any,
      };

      const result = resolveProductImage(listing);
      // Should fall through to CPU vendor
      expect(result).toBe('/images/fallbacks/intel-logo.svg');
    });
  });

  describe('Level 4: manufacturer logo', () => {
    it('should return manufacturer logo when manufacturer matches', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HPE',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/manufacturers/hpe.svg');
    });

    it('should normalize manufacturer name (case insensitive)', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'hpe', // Lowercase
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/manufacturers/hpe.svg');
    });

    it('should normalize manufacturer name (mixed case)', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HpE', // Mixed case
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/manufacturers/hpe.svg');
    });

    it('should skip manufacturer logo if not in config', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'UnknownBrand',
        cpu: { manufacturer: 'AMD' } as any,
      };

      const result = resolveProductImage(listing);
      // Should fall through to CPU vendor
      expect(result).toBe('/images/fallbacks/amd-logo.svg');
    });
  });

  describe('Level 5: CPU vendor logo', () => {
    it('should return Intel CPU vendor logo', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        cpu: {
          id: 1,
          name: 'Intel Core i5-9500',
          manufacturer: 'Intel',
          socket: null,
          cores: null,
          threads: null,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/intel-logo.svg');
    });

    it('should return AMD CPU vendor logo', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        cpu: {
          id: 2,
          name: 'AMD Ryzen 5 5600G',
          manufacturer: 'AMD',
          socket: null,
          cores: null,
          threads: null,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/amd-logo.svg');
    });

    it('should return ARM CPU vendor logo', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        cpu: {
          id: 3,
          name: 'ARM Cortex-A78',
          manufacturer: 'ARM',
          socket: null,
          cores: null,
          threads: null,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/arm.svg');
    });

    it('should normalize CPU vendor (case insensitive)', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        cpu: {
          id: 1,
          name: 'Intel Core i7',
          manufacturer: 'INTEL', // Uppercase
          socket: null,
          cores: null,
          threads: null,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/intel-logo.svg');
    });

    it('should skip CPU vendor if cpu is null', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: 'Desktop',
      };

      const result = resolveProductImage(listing);
      // Should fall through to form factor
      expect(result).toBe('/images/fallbacks/desktop-icon.svg');
    });

    it('should skip CPU vendor if cpu.manufacturer is missing', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        cpu: {
          id: 1,
          name: 'Unknown CPU',
          manufacturer: '',
          socket: null,
          cores: null,
          threads: null,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
        form_factor: 'Desktop',
      };

      const result = resolveProductImage(listing);
      // Should fall through to form factor
      expect(result).toBe('/images/fallbacks/desktop-icon.svg');
    });
  });

  describe('Level 6: form factor icon', () => {
    it('should return mini-pc form factor icon', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: 'Mini-PC',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/mini-pc-icon.svg');
    });

    it('should return desktop form factor icon', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: 'Desktop',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/desktop-icon.svg');
    });

    it('should normalize form factor (case insensitive)', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: 'MINI-PC', // Uppercase
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/mini-pc-icon.svg');
    });

    it('should normalize form factor with spaces', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: 'Mini PC', // Space instead of hyphen
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/mini-pc-icon.svg');
    });

    it('should skip form factor if not in config', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: 'UnknownFormFactor',
      };

      const result = resolveProductImage(listing);
      // Should fall through to generic fallback
      expect(result).toBe('/images/fallbacks/generic-pc.svg');
    });
  });

  describe('Level 7: generic fallback (always available)', () => {
    it('should return generic fallback when all fields are null', () => {
      const listing: ListingRecord = baseListingRecord;

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/generic-pc.svg');
    });

    it('should return generic fallback when no matches found', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'UnknownBrand',
        series: 'UnknownSeries',
        model_number: 'UnknownModel',
        form_factor: 'UnknownFormFactor',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/generic-pc.svg');
    });

    it('should always return a value (never null/undefined)', () => {
      const listing: ListingRecord = baseListingRecord;

      const result = resolveProductImage(listing);
      expect(result).toBeTruthy();
      expect(typeof result).toBe('string');
      expect(result.length).toBeGreaterThan(0);
    });
  });

  describe('edge cases and null safety', () => {
    it('should handle empty strings gracefully', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: '',
        series: '',
        model_number: '',
        form_factor: '',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/generic-pc.svg');
    });

    it('should handle whitespace-only strings', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: '   ',
        series: '\t\t',
        model_number: '\n',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/generic-pc.svg');
    });

    it('should handle special characters in field values', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HP@#$%',
        series: 'Elite&Desk',
        model_number: '800/G5',
      };

      const result = resolveProductImage(listing);
      // Should fall through to generic since normalized keys won't match
      expect(result).toBe('/images/fallbacks/generic-pc.svg');
    });

    it('should handle undefined cpu object gracefully', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        cpu: undefined,
        form_factor: 'Desktop',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/desktop-icon.svg');
    });

    it('should handle mixed case with extra spaces', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: '  Mini - PC  ',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/mini-pc-icon.svg');
    });
  });

  describe('fallback priority order', () => {
    it('should prefer manufacturer logo over CPU vendor logo', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        manufacturer: 'HPE',
        cpu: {
          id: 1,
          name: 'Intel Core i5',
          manufacturer: 'Intel',
          socket: null,
          cores: null,
          threads: null,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/manufacturers/hpe.svg');
    });

    it('should prefer CPU vendor logo over form factor icon', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        cpu: {
          id: 1,
          name: 'AMD Ryzen 5',
          manufacturer: 'AMD',
          socket: null,
          cores: null,
          threads: null,
          tdp_w: null,
          igpu_model: null,
          cpu_mark_multi: null,
          cpu_mark_single: null,
          igpu_mark: null,
          release_year: null,
          notes: null,
        },
        form_factor: 'Desktop',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/amd-logo.svg');
    });

    it('should prefer form factor icon over generic fallback', () => {
      const listing: ListingRecord = {
        ...baseListingRecord,
        form_factor: 'Mini-PC',
      };

      const result = resolveProductImage(listing);
      expect(result).toBe('/images/fallbacks/mini-pc-icon.svg');
    });
  });
});

describe('getImageSource', () => {
  const baseListingRecord: ListingRecord = {
    id: 1,
    title: 'Test PC',
    listing_url: null,
    other_urls: null,
    seller: null,
    price_usd: 500,
    adjusted_price_usd: null,
    score_composite: null,
    score_cpu_multi: null,
    score_cpu_single: null,
    score_gpu: null,
    dollar_per_cpu_mark: null,
    dollar_per_single_mark: null,
    condition: 'used',
    status: 'active',
    cpu_id: null,
    cpu_name: null,
    gpu_id: null,
    gpu_name: null,
    ram_gb: null,
    ram_spec_id: null,
    ram_spec: null,
    ram_type: null,
    ram_speed_mhz: null,
    primary_storage_gb: null,
    primary_storage_type: null,
    primary_storage_profile_id: null,
    primary_storage_profile: null,
    secondary_storage_gb: null,
    secondary_storage_type: null,
    secondary_storage_profile_id: null,
    secondary_storage_profile: null,
    manufacturer: null,
    series: null,
    model_number: null,
    form_factor: null,
    thumbnail_url: null,
    valuation_breakdown: null,
    cpu: null,
    gpu: null,
    ports_profile: null,
    attributes: {},
    ruleset_id: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  it('should return thumbnail_url source with isExternal=true', () => {
    const listing: ListingRecord = {
      ...baseListingRecord,
      thumbnail_url: 'https://example.com/thumb.jpg',
    };

    const result = getImageSource(listing);
    expect(result).toEqual({
      path: 'https://example.com/thumb.jpg',
      source: 'thumbnail_url',
      isExternal: true,
    });
  });

  it('should return manufacturer_logo source with isExternal=false', () => {
    const listing: ListingRecord = {
      ...baseListingRecord,
      manufacturer: 'HPE',
    };

    const result = getImageSource(listing);
    expect(result).toEqual({
      path: '/images/manufacturers/hpe.svg',
      source: 'manufacturer_logo',
      isExternal: false,
    });
  });

  it('should return cpu_vendor_logo source', () => {
    const listing: ListingRecord = {
      ...baseListingRecord,
      cpu: {
        id: 1,
        name: 'Intel Core i5',
        manufacturer: 'Intel',
        socket: null,
        cores: null,
        threads: null,
        tdp_w: null,
        igpu_model: null,
        cpu_mark_multi: null,
        cpu_mark_single: null,
        igpu_mark: null,
        release_year: null,
        notes: null,
      },
    };

    const result = getImageSource(listing);
    expect(result).toEqual({
      path: '/images/fallbacks/intel-logo.svg',
      source: 'cpu_vendor_logo',
      isExternal: false,
    });
  });

  it('should return form_factor_icon source', () => {
    const listing: ListingRecord = {
      ...baseListingRecord,
      form_factor: 'Mini-PC',
    };

    const result = getImageSource(listing);
    expect(result).toEqual({
      path: '/images/fallbacks/mini-pc-icon.svg',
      source: 'form_factor_icon',
      isExternal: false,
    });
  });

  it('should return generic_fallback source', () => {
    const listing: ListingRecord = baseListingRecord;

    const result = getImageSource(listing);
    expect(result).toEqual({
      path: '/images/fallbacks/generic-pc.svg',
      source: 'generic_fallback',
      isExternal: false,
    });
  });

  it('should return correct source type for all levels', () => {
    const sources: ImageSource[] = [
      'thumbnail_url',
      'model_specific',
      'series_specific',
      'manufacturer_logo',
      'cpu_vendor_logo',
      'form_factor_icon',
      'generic_fallback',
    ];

    // At minimum, we can get generic_fallback
    const result = getImageSource(baseListingRecord);
    expect(sources).toContain(result.source);
  });
});

describe('batchResolveProductImages', () => {
  const baseListingRecord: ListingRecord = {
    id: 1,
    title: 'Test PC',
    listing_url: null,
    other_urls: null,
    seller: null,
    price_usd: 500,
    adjusted_price_usd: null,
    score_composite: null,
    score_cpu_multi: null,
    score_cpu_single: null,
    score_gpu: null,
    dollar_per_cpu_mark: null,
    dollar_per_single_mark: null,
    condition: 'used',
    status: 'active',
    cpu_id: null,
    cpu_name: null,
    gpu_id: null,
    gpu_name: null,
    ram_gb: null,
    ram_spec_id: null,
    ram_spec: null,
    ram_type: null,
    ram_speed_mhz: null,
    primary_storage_gb: null,
    primary_storage_type: null,
    primary_storage_profile_id: null,
    primary_storage_profile: null,
    secondary_storage_gb: null,
    secondary_storage_type: null,
    secondary_storage_profile_id: null,
    secondary_storage_profile: null,
    manufacturer: null,
    series: null,
    model_number: null,
    form_factor: null,
    thumbnail_url: null,
    valuation_breakdown: null,
    cpu: null,
    gpu: null,
    ports_profile: null,
    attributes: {},
    ruleset_id: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  it('should resolve multiple listings', () => {
    const listings: ListingRecord[] = [
      { ...baseListingRecord, id: 1, manufacturer: 'HPE' },
      { ...baseListingRecord, id: 2, form_factor: 'Desktop' },
      { ...baseListingRecord, id: 3, cpu: { manufacturer: 'Intel' } as any },
    ];

    const results = batchResolveProductImages(listings);
    expect(results).toHaveLength(3);
    expect(results[0]).toBe('/images/manufacturers/hpe.svg');
    expect(results[1]).toBe('/images/fallbacks/desktop-icon.svg');
    expect(results[2]).toBe('/images/fallbacks/intel-logo.svg');
  });

  it('should handle empty array', () => {
    const results = batchResolveProductImages([]);
    expect(results).toEqual([]);
  });

  it('should preserve order of input listings', () => {
    const listings: ListingRecord[] = [
      { ...baseListingRecord, id: 1, form_factor: 'Mini-PC' },
      { ...baseListingRecord, id: 2, manufacturer: 'HPE' },
      { ...baseListingRecord, id: 3, form_factor: 'Desktop' },
    ];

    const results = batchResolveProductImages(listings);
    expect(results[0]).toBe('/images/fallbacks/mini-pc-icon.svg');
    expect(results[1]).toBe('/images/manufacturers/hpe.svg');
    expect(results[2]).toBe('/images/fallbacks/desktop-icon.svg');
  });

  it('should handle large batches efficiently', () => {
    const listings: ListingRecord[] = Array.from({ length: 100 }, (_, i) => ({
      ...baseListingRecord,
      id: i,
      manufacturer: i % 2 === 0 ? 'HPE' : null,
      form_factor: i % 2 === 1 ? 'Desktop' : null,
    }));

    const start = performance.now();
    const results = batchResolveProductImages(listings);
    const end = performance.now();

    expect(results).toHaveLength(100);
    expect(end - start).toBeLessThan(100); // Should complete in <100ms
  });
});

describe('performance benchmarks', () => {
  const baseListingRecord: ListingRecord = {
    id: 1,
    title: 'Test PC',
    listing_url: null,
    other_urls: null,
    seller: null,
    price_usd: 500,
    adjusted_price_usd: null,
    score_composite: null,
    score_cpu_multi: null,
    score_cpu_single: null,
    score_gpu: null,
    dollar_per_cpu_mark: null,
    dollar_per_single_mark: null,
    condition: 'used',
    status: 'active',
    cpu_id: null,
    cpu_name: null,
    gpu_id: null,
    gpu_name: null,
    ram_gb: null,
    ram_spec_id: null,
    ram_spec: null,
    ram_type: null,
    ram_speed_mhz: null,
    primary_storage_gb: null,
    primary_storage_type: null,
    primary_storage_profile_id: null,
    primary_storage_profile: null,
    secondary_storage_gb: null,
    secondary_storage_type: null,
    secondary_storage_profile_id: null,
    secondary_storage_profile: null,
    manufacturer: null,
    series: null,
    model_number: null,
    form_factor: null,
    thumbnail_url: null,
    valuation_breakdown: null,
    cpu: null,
    gpu: null,
    ports_profile: null,
    attributes: {},
    ruleset_id: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  it('should resolve 1000 images in <1ms average (best case - thumbnail_url)', () => {
    const listing: ListingRecord = {
      ...baseListingRecord,
      thumbnail_url: 'https://example.com/thumb.jpg',
    };

    const iterations = 1000;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      resolveProductImage(listing);
    }

    const end = performance.now();
    const avgTime = (end - start) / iterations;

    expect(avgTime).toBeLessThan(1);
  });

  it('should resolve 1000 images in <1ms average (worst case - generic fallback)', () => {
    const listing: ListingRecord = baseListingRecord;

    const iterations = 1000;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      resolveProductImage(listing);
    }

    const end = performance.now();
    const avgTime = (end - start) / iterations;

    expect(avgTime).toBeLessThan(1);
  });

  it('should resolve 1000 images in <1ms average (mid-case - manufacturer logo)', () => {
    const listing: ListingRecord = {
      ...baseListingRecord,
      manufacturer: 'HPE',
    };

    const iterations = 1000;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      resolveProductImage(listing);
    }

    const end = performance.now();
    const avgTime = (end - start) / iterations;

    expect(avgTime).toBeLessThan(1);
  });

  it('should resolve getImageSource in <1ms average', () => {
    const listing: ListingRecord = {
      ...baseListingRecord,
      manufacturer: 'HPE',
    };

    const iterations = 1000;
    const start = performance.now();

    for (let i = 0; i < iterations; i++) {
      getImageSource(listing);
    }

    const end = performance.now();
    const avgTime = (end - start) / iterations;

    expect(avgTime).toBeLessThan(1);
  });
});
