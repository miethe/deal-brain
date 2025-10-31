# Phase 4: Image Management System

**Objectives:**
- Create JSON configuration for image mappings
- Implement image resolver utility
- Refactor ProductImageDisplay to use config
- Migrate existing images to new structure
- Document workflow for non-technical users

**Prerequisites:**
- None (independent phase)

**Estimated Duration:** 2 weeks

---

## IMG-001: Design and Create Image Configuration File

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 4 hours
**Dependencies:** None

**Acceptance Criteria:**
- [ ] JSON schema defined
- [ ] TypeScript types generated
- [ ] Configuration file created with existing images
- [ ] Validation logic implemented

**Implementation Steps:**

1. **Create config file** (`apps/web/config/product-images.json`):

```json
{
  "version": "1.0",
  "baseUrl": "/images",
  "manufacturers": {
    "hpe": {
      "logo": "/manufacturers/hpe.svg",
      "fallback": "generic"
    },
    "minisforum": {
      "logo": "/manufacturers/minisforum.svg",
      "series": {
        "elitemini": "/manufacturers/minisforum/elitemini.svg"
      },
      "fallback": "generic"
    }
  },
  "formFactors": {
    "mini_pc": {
      "icon": "/form-factors/mini-pc.svg",
      "generic": "/form-factors/mini-pc-generic.svg"
    },
    "desktop": {
      "icon": "/form-factors/desktop.svg"
    }
  },
  "cpuVendors": {
    "intel": "/cpu-vendors/intel.svg",
    "amd": "/cpu-vendors/amd.svg"
  },
  "fallbacks": {
    "generic": "/fallbacks/generic-pc.svg"
  }
}
```

2. **Generate TypeScript types:**

```typescript
// apps/web/types/product-images.ts

export interface ImageConfig {
  version: string;
  baseUrl: string;
  manufacturers: Record<string, ManufacturerImages>;
  formFactors: Record<string, FormFactorImages>;
  cpuVendors: Record<string, string>;
  fallbacks: {
    generic: string;
  };
}

export interface ManufacturerImages {
  logo: string;
  series?: Record<string, string>;
  fallback?: string;
}

export interface FormFactorImages {
  icon: string;
  generic?: string;
}
```

3. **Add validation:**

```typescript
// apps/web/lib/validate-image-config.ts

import { z } from 'zod';

const ImageConfigSchema = z.object({
  version: z.string(),
  baseUrl: z.string(),
  manufacturers: z.record(z.object({
    logo: z.string(),
    series: z.record(z.string()).optional(),
    fallback: z.string().optional(),
  })),
  formFactors: z.record(z.object({
    icon: z.string(),
    generic: z.string().optional(),
  })),
  cpuVendors: z.record(z.string()),
  fallbacks: z.object({
    generic: z.string(),
  }),
});

export function validateImageConfig(config: unknown) {
  return ImageConfigSchema.parse(config);
}
```

**Testing Requirements:**
- [ ] Unit test: Config validation passes
- [ ] Unit test: Invalid config throws error

---

## IMG-002: Implement Image Resolver Utility

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 8 hours
**Dependencies:** IMG-001

**Acceptance Criteria:**
- [ ] Resolver follows 7-level fallback hierarchy
- [ ] Returns correct image for all scenarios
- [ ] Handles missing config entries gracefully
- [ ] Performance: <1ms per resolution

**Implementation Steps:**

1. **Create resolver** (`apps/web/lib/image-resolver.ts`):

```typescript
import imageConfig from '@/config/product-images.json';
import type { ListingDetail, ListingRecord } from '@/types/listings';

export function resolveProductImage(
  listing: ListingDetail | ListingRecord
): string {
  // 1. Listing-specific URLs
  if (listing.thumbnail_url) {
    return listing.thumbnail_url;
  }
  if (listing.image_url) {
    return listing.image_url;
  }

  const manufacturer = listing.manufacturer?.toLowerCase();
  const series = listing.series?.toLowerCase().replace(/\s+/g, '_');
  const modelNumber = listing.model_number?.toLowerCase().replace(/\s+/g, '_');
  const formFactor = listing.form_factor?.toLowerCase().replace(/\s+/g, '_');
  const cpuVendor = listing.cpu?.manufacturer?.toLowerCase();

  // 2. Model-specific image
  if (manufacturer && modelNumber && imageConfig.manufacturers[manufacturer]?.series?.[modelNumber]) {
    return `${imageConfig.baseUrl}${imageConfig.manufacturers[manufacturer].series[modelNumber]}`;
  }

  // 3. Series-specific image
  if (manufacturer && series && imageConfig.manufacturers[manufacturer]?.series?.[series]) {
    return `${imageConfig.baseUrl}${imageConfig.manufacturers[manufacturer].series[series]}`;
  }

  // 4. Manufacturer logo
  if (manufacturer && imageConfig.manufacturers[manufacturer]?.logo) {
    return `${imageConfig.baseUrl}${imageConfig.manufacturers[manufacturer].logo}`;
  }

  // 5. CPU vendor logo
  if (cpuVendor && imageConfig.cpuVendors[cpuVendor]) {
    return `${imageConfig.baseUrl}${imageConfig.cpuVendors[cpuVendor]}`;
  }

  // 6. Form factor icon
  if (formFactor && imageConfig.formFactors[formFactor]?.icon) {
    return `${imageConfig.baseUrl}${imageConfig.formFactors[formFactor].icon}`;
  }

  // 7. Generic fallback
  return `${imageConfig.baseUrl}${imageConfig.fallbacks.generic}`;
}

// Helper: Get fallback type for debugging
export function getImageSource(listing: ListingDetail | ListingRecord): string {
  if (listing.thumbnail_url) return 'thumbnail';
  if (listing.image_url) return 'image_url';

  const manufacturer = listing.manufacturer?.toLowerCase();
  const series = listing.series?.toLowerCase().replace(/\s+/g, '_');

  if (manufacturer && series && imageConfig.manufacturers[manufacturer]?.series?.[series]) {
    return 'series';
  }
  if (manufacturer && imageConfig.manufacturers[manufacturer]?.logo) {
    return 'manufacturer';
  }
  if (listing.cpu?.manufacturer && imageConfig.cpuVendors[listing.cpu.manufacturer.toLowerCase()]) {
    return 'cpu_vendor';
  }
  if (listing.form_factor && imageConfig.formFactors[listing.form_factor.toLowerCase()]) {
    return 'form_factor';
  }

  return 'generic';
}
```

**Testing Requirements:**
- [ ] Unit test: All 7 fallback levels
- [ ] Unit test: Handles missing fields gracefully
- [ ] Performance test: <1ms resolution time

---

## IMG-003: Refactor ProductImageDisplay Component

**Type:** Frontend
**Priority:** P0-Critical
**Effort:** 12 hours
**Dependencies:** IMG-002

**Acceptance Criteria:**
- [ ] Uses image resolver for all image sources
- [ ] Maintains backward compatibility
- [ ] Supports all existing variants (card, hero, thumbnail)
- [ ] Error handling unchanged

**Implementation Steps:**

1. **Update component** (`apps/web/components/listings/product-image-display.tsx`):

```typescript
import { resolveProductImage, getImageSource } from '@/lib/image-resolver';
import { useState } from 'react';
import Image from 'next/image';
import { Dialog, DialogContent } from '@/components/ui/dialog';

interface ProductImageDisplayProps {
  listing: ListingDetail | ListingRecord;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'card' | 'hero' | 'thumbnail';
  showLightbox?: boolean;
  className?: string;
}

const SIZE_MAP = {
  sm: { width: 64, height: 64 },
  md: { width: 128, height: 128 },
  lg: { width: 256, height: 256 },
  xl: { width: 512, height: 512 },
};

export function ProductImageDisplay({
  listing,
  size = 'md',
  variant = 'card',
  showLightbox = false,
  className,
}: ProductImageDisplayProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [imgError, setImgError] = useState(false);

  const imageSrc = resolveProductImage(listing);
  const imageSource = getImageSource(listing);
  const dimensions = SIZE_MAP[size];

  // Use padding for fallback images (logos, icons)
  const isFallback = !['thumbnail', 'image_url'].includes(imageSource);
  const padding = isFallback ? 'p-8' : 'p-2';

  const handleImageClick = () => {
    if (showLightbox) {
      setLightboxOpen(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showLightbox && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      setLightboxOpen(true);
    }
  };

  return (
    <>
      <div
        className={cn(
          'relative overflow-hidden rounded-lg border bg-muted',
          padding,
          showLightbox && 'cursor-pointer hover:opacity-80 transition',
          className
        )}
        onClick={handleImageClick}
        onKeyDown={handleKeyDown}
        role={showLightbox ? 'button' : undefined}
        tabIndex={showLightbox ? 0 : undefined}
        aria-label={showLightbox ? 'View full-size image' : undefined}
      >
        <Image
          src={imageSrc}
          alt={listing.title || 'Product image'}
          width={dimensions.width}
          height={dimensions.height}
          className="object-contain"
          loading="lazy"
          quality={85}
          onError={() => setImgError(true)}
        />
      </div>

      {showLightbox && (
        <Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
          <DialogContent className="max-w-4xl">
            <Image
              src={imageSrc}
              alt={listing.title || 'Product image'}
              width={1024}
              height={1024}
              className="object-contain"
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
```

**Testing Requirements:**
- [ ] E2E test: All variants render correctly
- [ ] E2E test: Lightbox works
- [ ] Visual regression test: No UI changes

---

## IMG-004: Reorganize Image Directory Structure

**Type:** Infra
**Priority:** P1-High
**Effort:** 4 hours
**Dependencies:** IMG-001

**Acceptance Criteria:**
- [ ] Images organized by category
- [ ] Existing images migrated
- [ ] README files in each directory
- [ ] No broken images

**Implementation Steps:**

1. **Create new directory structure:**

```bash
cd apps/web/public/images

mkdir -p manufacturers cpu-vendors form-factors fallbacks

# Move existing files
mv hpe.svg manufacturers/
mv intel.svg cpu-vendors/
mv amd.svg cpu-vendors/
mv mini-pc-icon.svg form-factors/
mv desktop-icon.svg form-factors/
mv generic-pc.svg fallbacks/
```

2. **Create README files:**

```markdown
# Manufacturers

Add manufacturer logos here as SVG files.

Naming convention: `<manufacturer-slug>.svg`
Examples:
- `hpe.svg`
- `dell.svg`
- `minisforum.svg`

## Adding a New Manufacturer Logo

1. Obtain SVG logo (512x512px recommended)
2. Save as `<manufacturer-name>.svg` (lowercase, kebab-case)
3. Add entry to `/apps/web/config/product-images.json`:

```json
"manufacturers": {
  "manufacturer-name": {
    "logo": "/manufacturers/manufacturer-name.svg"
  }
}
```

4. Commit changes (no deployment needed!)
```

3. **Update image config to match new paths**

**Testing Requirements:**
- [ ] Manual test: All images load correctly
- [ ] E2E test: Catalog cards show images

---

## IMG-005: Documentation for Non-Technical Users

**Type:** Documentation
**Priority:** P2-Medium
**Effort:** 4 hours
**Dependencies:** IMG-004

**Acceptance Criteria:**
- [ ] Step-by-step guide for adding images
- [ ] Screenshots included
- [ ] Video tutorial (optional)
- [ ] Troubleshooting section

**Implementation Steps:**

1. **Create user guide** (`docs/guides/adding-product-images.md`):

```markdown
# Adding Product Images - User Guide

This guide explains how to add manufacturer logos, form factor icons, and series images to the Deal Brain catalog without needing to modify code or deploy.

## Prerequisites

- Access to the `/apps/web/public/images/` directory (file manager, FTP, or Git)
- SVG or PNG image file (512x512px recommended, max 200KB)
- Basic text editing skills

## Step 1: Prepare Your Image

1. Obtain the manufacturer logo or product image
2. Ensure it's in SVG format (preferred) or PNG
3. Resize to 512x512px for best quality
4. Optimize file size (max 200KB)
5. Name using lowercase kebab-case (e.g., `minisforum.svg`)

## Step 2: Upload Image

### Option A: File Manager

1. Navigate to `/apps/web/public/images/manufacturers/`
2. Upload your image file (e.g., `minisforum.svg`)
3. Verify file uploaded successfully

### Option B: Git

```bash
cd apps/web/public/images/manufacturers
cp ~/Downloads/minisforum.svg .
git add minisforum.svg
git commit -m "Add Minisforum manufacturer logo"
git push
```

## Step 3: Update Configuration

1. Open `/apps/web/config/product-images.json` in a text editor
2. Add an entry under `manufacturers`:

```json
{
  "manufacturers": {
    "minisforum": {
      "logo": "/manufacturers/minisforum.svg"
    }
  }
}
```

3. Save the file

## Step 4: Verify

1. Refresh the listings page
2. Find a listing with manufacturer "Minisforum"
3. Verify the logo appears in the catalog card

## Adding Series Images

For series-specific images (e.g., Dell OptiPlex):

1. Upload image to `/manufacturers/<manufacturer>/` (e.g., `/manufacturers/dell/optiplex.svg`)
2. Update config:

```json
{
  "manufacturers": {
    "dell": {
      "logo": "/manufacturers/dell.svg",
      "series": {
        "optiplex": "/manufacturers/dell/optiplex.svg"
      }
    }
  }
}
```

## Troubleshooting

**Image doesn't appear:**
- Check file path in config matches uploaded file location
- Verify file name is lowercase with no spaces
- Clear browser cache (Ctrl+Shift+R)

**Image is blurry:**
- Use SVG format instead of PNG
- Ensure minimum 512x512px resolution

**File too large:**
- Optimize SVG using https://jakearchibald.github.io/svgomg/
- Compress PNG using TinyPNG

## Support

For help, contact the engineering team or file an issue.
```

2. **Create video tutorial (optional):**
   - Record screen capture showing steps
   - Upload to internal documentation site

**Testing Requirements:**
- [ ] User testing: Non-technical user successfully adds image

---

**Phase 4 Summary:**

| Task | Type | Effort | Status |
|------|------|--------|--------|
| IMG-001 | Frontend | 4h | Pending |
| IMG-002 | Frontend | 8h | Pending |
| IMG-003 | Frontend | 12h | Pending |
| IMG-004 | Infra | 4h | Pending |
| IMG-005 | Documentation | 4h | Pending |
| Testing | All | 12h | Pending |
| **Total** | | **52h** | |
