/**
 * Validate product-images.json configuration
 * This script can be run with Node.js without compilation
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const configPath = join(__dirname, '../config/product-images.json');

try {
  const configData = readFileSync(configPath, 'utf-8');
  const config = JSON.parse(configData);

  console.log('Validating product-images.json...');

  // Basic structure validation
  const requiredFields = ['version', 'baseUrl', 'manufacturers', 'formFactors', 'cpuVendors', 'gpuVendors', 'fallbacks'];
  const missingFields = requiredFields.filter(field => !(field in config));

  if (missingFields.length > 0) {
    throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
  }

  // Version format validation
  if (!/^\d+\.\d+(\.\d+)?$/.test(config.version)) {
    throw new Error(`Invalid version format: ${config.version}. Expected semantic versioning (e.g., "1.0.0")`);
  }

  // Base URL validation
  if (!config.baseUrl.startsWith('/')) {
    throw new Error(`Base URL must start with "/". Got: ${config.baseUrl}`);
  }

  // Fallback validation
  if (!config.fallbacks.generic) {
    throw new Error('Missing fallbacks.generic');
  }

  console.log('✓ Configuration is valid!');
  console.log('\nConfiguration summary:');
  console.log(`  Version: ${config.version}`);
  console.log(`  Base URL: ${config.baseUrl}`);
  console.log(`  Manufacturers: ${Object.keys(config.manufacturers).length}`);
  console.log(`  Form Factors: ${Object.keys(config.formFactors).length}`);
  console.log(`  CPU Vendors: ${Object.keys(config.cpuVendors).length}`);
  console.log(`  GPU Vendors: ${Object.keys(config.gpuVendors).length}`);
  console.log('\nManufacturers:', Object.keys(config.manufacturers).join(', ') || '(none)');
  console.log('Form Factors:', Object.keys(config.formFactors).join(', '));
  console.log('CPU Vendors:', Object.keys(config.cpuVendors).join(', '));
  console.log('GPU Vendors:', Object.keys(config.gpuVendors).join(', '));
  console.log('Generic fallback:', config.fallbacks.generic);

  process.exit(0);
} catch (error) {
  console.error('✗ Configuration validation failed!');
  console.error(error.message);
  process.exit(1);
}
