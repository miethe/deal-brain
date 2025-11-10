/**
 * Image Resolver Validation Script
 *
 * Standalone validation script to verify the image resolver utility works correctly.
 * This can be run independently without a test framework.
 */

import {
  resolveProductImage,
  getImageSource,
  batchResolveProductImages,
  type ImageSource,
} from '../image-resolver';
import type { ListingRecord } from '@/types/listings';

// Test fixture
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

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
}

const results: TestResult[] = [];

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function runTest(name: string, testFn: () => void): void {
  try {
    testFn();
    results.push({ name, passed: true });
  } catch (error) {
    results.push({
      name,
      passed: false,
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

// Test Level 1: thumbnail_url
runTest('Level 1: thumbnail_url (external URL)', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    thumbnail_url: 'https://example.com/thumb.jpg',
  };
  const result = resolveProductImage(listing);
  assert(result === 'https://example.com/thumb.jpg', `Expected thumbnail_url, got ${result}`);
});

// Test Level 5: manufacturer logo
runTest('Level 5: manufacturer logo (HPE)', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    manufacturer: 'HPE',
  };
  const result = resolveProductImage(listing);
  assert(
    result === '/images/manufacturers/hpe.svg',
    `Expected HPE logo, got ${result}`
  );
});

// Test Level 6: CPU vendor logo (Intel)
runTest('Level 6: CPU vendor logo (Intel)', () => {
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
  const result = resolveProductImage(listing);
  assert(
    result === '/images/cpu-vendors/intel.svg',
    `Expected Intel logo, got ${result}`
  );
});

// Test Level 6: CPU vendor logo (AMD)
runTest('Level 6: CPU vendor logo (AMD)', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    cpu: {
      id: 2,
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
  };
  const result = resolveProductImage(listing);
  assert(
    result === '/images/cpu-vendors/amd.svg',
    `Expected AMD logo, got ${result}`
  );
});

// Test Level 7: form factor icon (Mini-PC)
runTest('Level 7: form factor icon (Mini-PC)', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    form_factor: 'Mini-PC',
  };
  const result = resolveProductImage(listing);
  assert(
    result === '/images/form-factors/mini-pc.svg',
    `Expected Mini-PC icon, got ${result}`
  );
});

// Test Level 7: form factor icon (Desktop)
runTest('Level 7: form factor icon (Desktop)', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    form_factor: 'Desktop',
  };
  const result = resolveProductImage(listing);
  assert(
    result === '/images/form-factors/desktop.svg',
    `Expected Desktop icon, got ${result}`
  );
});

// Test Level 8: generic fallback
runTest('Level 8: generic fallback', () => {
  const listing: ListingRecord = baseListingRecord;
  const result = resolveProductImage(listing);
  assert(
    result === '/images/fallbacks/generic-pc.svg',
    `Expected generic fallback, got ${result}`
  );
});

// Test normalization (case insensitive)
runTest('Normalization: case insensitive manufacturer', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    manufacturer: 'hpe', // lowercase
  };
  const result = resolveProductImage(listing);
  assert(
    result === '/images/manufacturers/hpe.svg',
    `Expected HPE logo with normalized case, got ${result}`
  );
});

// Test normalization (spaces to underscores)
runTest('Normalization: form factor with space', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    form_factor: 'Mini PC', // Space instead of hyphen
  };
  const result = resolveProductImage(listing);
  assert(
    result === '/images/form-factors/mini-pc.svg',
    `Expected Mini-PC icon with normalized form factor, got ${result}`
  );
});

// Test priority order
runTest('Priority: manufacturer logo over CPU vendor', () => {
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
  assert(
    result === '/images/manufacturers/hpe.svg',
    `Expected manufacturer logo over CPU vendor, got ${result}`
  );
});

// Test getImageSource
runTest('getImageSource: returns correct source metadata', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    manufacturer: 'HPE',
  };
  const result = getImageSource(listing);
  assert(result.path === '/images/manufacturers/hpe.svg', `Expected correct path`);
  assert(result.source === 'manufacturer_logo', `Expected manufacturer_logo source`);
  assert(result.isExternal === false, `Expected isExternal to be false`);
});

// Test getImageSource with external URL
runTest('getImageSource: identifies external URLs', () => {
  const listing: ListingRecord = {
    ...baseListingRecord,
    thumbnail_url: 'https://example.com/thumb.jpg',
  };
  const result = getImageSource(listing);
  assert(result.isExternal === true, `Expected isExternal to be true for external URL`);
  assert(result.source === 'thumbnail_url', `Expected thumbnail_url source`);
});

// Test batch resolution
runTest('batchResolveProductImages: resolves multiple listings', () => {
  const listings: ListingRecord[] = [
    { ...baseListingRecord, id: 1, manufacturer: 'HPE' },
    { ...baseListingRecord, id: 2, form_factor: 'Desktop' },
    {
      ...baseListingRecord,
      id: 3,
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
    },
  ];

  const results = batchResolveProductImages(listings);
  assert(results.length === 3, `Expected 3 results, got ${results.length}`);
  assert(
    results[0] === '/images/manufacturers/hpe.svg',
    `Expected HPE logo for first listing`
  );
  assert(
    results[1] === '/images/form-factors/desktop.svg',
    `Expected Desktop icon for second listing`
  );
  assert(
    results[2] === '/images/cpu-vendors/intel.svg',
    `Expected Intel logo for third listing`
  );
});

// Performance benchmark
runTest('Performance: <1ms average (1000 iterations)', () => {
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

  assert(
    avgTime < 1,
    `Average time ${avgTime.toFixed(3)}ms exceeds 1ms target`
  );
});

// Print results
console.log('\n=== Image Resolver Validation Results ===\n');

const passed = results.filter((r) => r.passed).length;
const failed = results.filter((r) => !r.passed).length;

results.forEach((result) => {
  const status = result.passed ? '✓ PASS' : '✗ FAIL';
  console.log(`${status}: ${result.name}`);
  if (!result.passed && result.error) {
    console.log(`  Error: ${result.error}`);
  }
});

console.log(`\nTotal: ${results.length} tests`);
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log(`Coverage: ${((passed / results.length) * 100).toFixed(1)}%\n`);

if (failed > 0) {
  process.exit(1);
}
