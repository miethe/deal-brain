/**
 * Test script to validate the product-images.json configuration
 * This ensures the config file is valid before runtime
 */

import { validateImageConfig } from '../lib/validate-image-config';
import productImagesConfig from '../config/product-images.json';

try {
  console.log('Validating product-images.json...');
  const validatedConfig = validateImageConfig(productImagesConfig);
  console.log('✓ Configuration is valid!');
  console.log('\nConfiguration summary:');
  console.log(`  Version: ${validatedConfig.version}`);
  console.log(`  Base URL: ${validatedConfig.baseUrl}`);
  console.log(`  Manufacturers: ${Object.keys(validatedConfig.manufacturers).length}`);
  console.log(`  Form Factors: ${Object.keys(validatedConfig.formFactors).length}`);
  console.log(`  CPU Vendors: ${Object.keys(validatedConfig.cpuVendors).length}`);
  console.log(`  GPU Vendors: ${Object.keys(validatedConfig.gpuVendors).length}`);
  console.log('\nManufacturers:', Object.keys(validatedConfig.manufacturers).join(', '));
  console.log('Form Factors:', Object.keys(validatedConfig.formFactors).join(', '));
  console.log('CPU Vendors:', Object.keys(validatedConfig.cpuVendors).join(', '));
  console.log('GPU Vendors:', Object.keys(validatedConfig.gpuVendors).join(', '));
  console.log('Generic fallback:', validatedConfig.fallbacks.generic);
  process.exit(0);
} catch (error) {
  console.error('✗ Configuration validation failed!');
  console.error(error);
  process.exit(1);
}
