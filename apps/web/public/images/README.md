# Product Images

This directory contains product images and fallback assets for the Deal Brain listings display.

## Directory Structure

```
images/
├── fallbacks/          # Fallback images (CPU manufacturers, form factors, generic)
│   ├── intel-logo.svg
│   ├── amd-logo.svg
│   ├── mini-pc-icon.svg
│   ├── desktop-icon.svg
│   └── generic-pc.svg
└── manufacturers/      # Manufacturer-specific logos (add as needed)
    └── (manufacturer logos)
```

## Fallback Hierarchy

The `ProductImageDisplay` component uses a 5-level fallback hierarchy:

1. **listing.thumbnail_url** - Primary product image (external URL)
2. **listing.image_url** - Secondary product image (external URL)
3. **Manufacturer logo** - `/images/manufacturers/{manufacturer-slug}.svg`
4. **CPU manufacturer logo** - `/images/fallbacks/{cpu-manufacturer}-logo.svg` (Intel/AMD)
5. **Form factor icon** - `/images/fallbacks/{form-factor-slug}-icon.svg`
6. **Generic fallback** - `/images/fallbacks/generic-pc.svg`

## Adding New Assets

### Manufacturer Logos

To add a new manufacturer logo:

1. Create an SVG file in `/images/manufacturers/`
2. Name it using a slugified version of the manufacturer name (lowercase, hyphen-separated)
3. Example: "Lenovo IdeaCentre" → `lenovo-ideacentre.svg`

### Form Factor Icons

To add a new form factor icon:

1. Create an SVG file in `/images/fallbacks/`
2. Name it using the pattern `{form-factor-slug}-icon.svg`
3. Example: "Small Form Factor" → `small-form-factor-icon.svg`

## Asset Guidelines

- **Format**: Use SVG for scalability
- **Size**: Recommended viewBox of 120x120
- **Colors**: Use neutral colors that work in light/dark mode
- **Simplicity**: Keep designs simple and recognizable

## Related Components

- `components/listings/product-image-display.tsx` - Main component using these assets
- `components/listings/listing-overview-modal.tsx` - Displays product images in modal
