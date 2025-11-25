# CPU Vendor Logos

CPU manufacturer logos for fallback display.

## Current Vendors
- Intel (`intel.svg`)
- AMD (`amd.svg`)
- ARM (`arm.svg`)

## Adding a New CPU Vendor
1. Save SVG logo as `vendor-name.svg`
2. Update `/apps/web/config/product-images.json`:
   ```json
   "cpuVendors": {
     "vendor-name": "/images/cpu-vendors/vendor-name.svg"
   }
   ```
