# GPU Vendor Logos

GPU manufacturer logos for fallback display.

## Current Vendors
- NVIDIA (`nvidia.svg`)

## Adding a New GPU Vendor
1. Save SVG logo as `vendor-name.svg`
2. Update `/apps/web/config/product-images.json`:
   ```json
   "gpuVendors": {
     "vendor-name": "/images/gpu-vendors/vendor-name.svg"
   }
   ```
