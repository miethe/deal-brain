# Listings Facelift - Enhancements V2

**Date:** 2025-10-26

## Expected Behaviors

The following tasks need completed:

1. **Product Image Display**
   - Display product images in overview modal
   - Image loading states and fallbacks (Image from Listing > Manufacturer Logo > CPU Logo > Form Factor Icon > Generic Placeholder)

2. **Additional Info in Modal**
   - Display GPU names in overview modal header/info section
   - Display linked URLs as clickable links in the overview modal

3. **Enhanced Specifications Tab (Detail Page)**
    - For the Listing Detail Page (`/listings/[id]`), there should be dedicated subsections within each of the key sections on the Specifications tab (ie Compute, Memory, Storage, Connectivity) to better organize the information. When empty, these sections should indicate "No data available" with an option to quickly add relevant details with a small "Add +" button.
    - All available information for the Listing should have a dedicated section on the detail page within the Specifications tab. 

4. **Detail Page Overview Tooltips**
   - The overview section at the top of the Detail page, above the Tabbed pane, should have hover tooltips for all linked entities (CPU, GPU, RAM, Storage) to show key specifications on hover. These tooltips should be identical to what is found in the Specifications tab.

5. **Layout Optimization**
   - Audit and optimize detail page layout following enhancements from Section 3 above.
   - Improve space utilization and information hierarchy.

6. **Valuation Tab Rules Shown**
    - The Valuation tab on both the listing modal and detail page should list the contributing rules directly, rather than showing "No rule-based adjustments were applied to this listing".

7. **Entity Link Routing**
    - Currently, clicking an entity link (`/catalog/cpus/{entity_id}`) fails with a 404 error.
    - Create an entity detail page for each entity type (CPU, GPU, RAM Spec, Storage Spec, etc).
    - Fix 404 errors when clicking entity links