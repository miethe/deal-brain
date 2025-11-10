# Manufacturer Logos

Add manufacturer logos here as SVG files.

## Naming Convention
- Use lowercase with hyphens: `manufacturer-name.svg`
- Examples: `hpe.svg`, `dell.svg`, `lenovo.svg`

## Adding a New Logo
1. Save SVG file (512x512px recommended, max 200KB)
2. Add entry to `/apps/web/config/product-images.json`:
   ```json
   "manufacturers": {
     "manufacturer-name": {
       "logo": "/images/manufacturers/manufacturer-name.svg"
     }
   }
   ```
3. Commit and push (no deployment needed!)
