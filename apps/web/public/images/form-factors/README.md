# Form Factor Icons

Icons representing different PC form factors.

## Current Form Factors
- Desktop (`desktop.svg`)
- Mini PC (`mini-pc.svg`)

## Adding a New Form Factor
1. Save SVG icon as `form-factor-name.svg`
2. Update `/apps/web/config/product-images.json`:
   ```json
   "formFactors": {
     "form_factor_name": {
       "icon": "/images/form-factors/form-factor-name.svg"
     }
   }
   ```
