# Product Images Configuration

This directory contains the JSON configuration file for the image management system.

## Files

- `product-images.json` - Main configuration file defining image paths and fallback hierarchy

## Configuration Structure

The `product-images.json` file defines:

1. **Version**: Semantic version of the configuration schema
2. **Base URL**: Base path for all image assets (default: `/images`)
3. **Manufacturers**: Manufacturer logos and optional series-specific images
4. **Form Factors**: Form factor icons (e.g., Mini PC, Desktop)
5. **CPU Vendors**: CPU manufacturer logos (Intel, AMD, ARM)
6. **GPU Vendors**: GPU manufacturer logos (NVIDIA, AMD, Intel)
7. **Fallbacks**: Generic fallback images for when other images fail

## Example Configuration

```json
{
  "version": "1.0.0",
  "baseUrl": "/images",
  "manufacturers": {
    "hp": {
      "logo": "/images/manufacturers/hp.svg",
      "series": {
        "elitedesk": "/images/manufacturers/hp-elitedesk.svg"
      },
      "fallback": "/images/manufacturers/hp-generic.svg"
    }
  },
  "formFactors": {
    "mini-pc": {
      "icon": "/images/form-factors/mini-pc.svg",
      "generic": "/images/fallbacks/mini-pc-generic.svg"
    }
  },
  "cpuVendors": {
    "intel": "/images/cpu-vendors/intel.svg",
    "amd": "/images/cpu-vendors/amd.svg"
  },
  "gpuVendors": {
    "nvidia": "/images/fallbacks/nvidia.svg"
  },
  "fallbacks": {
    "generic": "/images/fallbacks/generic-pc.svg"
  }
}
```

## Adding New Images

### Adding a Manufacturer

1. Add the manufacturer SVG file to `/public/images/manufacturers/`
2. Update `product-images.json`:

```json
{
  "manufacturers": {
    "dell": {
      "logo": "/images/manufacturers/dell.svg"
    }
  }
}
```

### Adding a Form Factor

1. Add the form factor icon to `/public/images/fallbacks/`
2. Update `product-images.json`:

```json
{
  "formFactors": {
    "tower": {
      "icon": "/images/fallbacks/tower-icon.svg"
    }
  }
}
```

### Adding a CPU/GPU Vendor

1. Add the vendor logo to `/public/images/fallbacks/`
2. Update `product-images.json`:

```json
{
  "cpuVendors": {
    "qualcomm": "/images/fallbacks/qualcomm.svg"
  }
}
```

## Validation

The configuration file is validated using Zod schemas. To validate:

```bash
# Using the Node.js validation script
node scripts/validate-config.mjs

# Or during build time (automatic)
pnpm build
```

## TypeScript Support

Type definitions are available in `/types/product-images.ts`:

```typescript
import type { ImageConfig } from '@/types/product-images';
import { validateImageConfig } from '@/lib/validate-image-config';
import productImagesConfig from '@/config/product-images.json';

// Validate and use the configuration
const config = validateImageConfig(productImagesConfig);
```

## Image Resolver

The configuration is consumed by the `ProductImageResolver` service (see IMG-002), which:

1. Loads and validates the configuration at startup
2. Resolves image paths based on listing metadata
3. Implements the 6-level fallback hierarchy
4. Provides type-safe image path resolution

## Best Practices

1. **Always use relative paths** starting with `/images/`
2. **Use SVG format** for logos and icons when possible
3. **Validate configuration** before committing changes
4. **Follow naming conventions**:
   - Manufacturer logos: `{manufacturer-slug}.svg`
   - Form factor icons: `{form-factor-slug}-icon.svg`
   - Vendor logos: `{vendor-name}-logo.svg` or `{vendor-name}.svg`
5. **Use kebab-case** for file names and configuration keys
6. **Document new fields** in this README

## Version History

- **1.0.0** (2025-11-01): Initial release
  - Manufacturer logos support
  - Form factor icons support
  - CPU and GPU vendor logos (separated)
  - Series-specific manufacturer images
  - Generic fallback system
