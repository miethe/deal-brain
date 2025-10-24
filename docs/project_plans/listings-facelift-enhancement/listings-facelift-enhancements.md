# Listings Facelift - Issues and Enhancements

**Date:** 2025-10-24

## Current Behaviors

- The listings detail modal does not show:
    - the CPU/GPU attached to the listing.
    - the product image for the listing.
    - any linked URLs for the listing.

- The Valuation tab on both the listing modal and detail page always shows "0 rules applied" and "No rule-based adjustments were applied to this listing.", even when there are rules that contributed to the valuation. However, within "View breakdown", the rules are shown correctly.

- On the listings detail page at `/listings/[id]`:
    - In the top right corner where CPU is shown below the Listing and Adjusted Prices, it always shows Unknown 
    - on the Specifications tab, the CPU field is always empty, even when a CPU is attached to the listing.
    - Many fields are missing entirely, such as linked URLs, Ports, Secondary storage, RAM details (only capacity is shown), etc.
    - There are no tooltips on the page. When RAM Spec or Storage Spec is set, there is a link, but it directs to a 404 and there is no tooltip on hover.


## Expected Behaviors

- The listings detail modal should show:
    - the CPU/GPU attached to the listing.
    - the product image for the listing.
    - any linked URLs for the listing.

- The listings catalog view (grid and table) should also show the linked CPU/GPU names with tooltips on hover.

- The Valuation tab on both the listing modal and detail page should show the correct number of rules applied and list the contributing rules directly, rather than showing "0 rules applied".

- On the listings detail page at `/listings/[id]`:
    - In the top right corner where CPU is shown below the Listing and Adjusted Prices, it should show the correct CPU name when a CPU is attached to the listing.
    - on the Specifications tab, the CPU field should show the correct CPU name when a CPU is attached to the listing.
    - All relevant fields should be present, such as linked URLs, Ports, Secondary storage, RAM details (including type and speed), etc, with relevant sections for each.
    - Tooltips should be added for all linked entities (CPU, GPU, RAM, Storage) to show key specifications on hover.

- Tooltips on hover should be available anywhere a linked entity is present (ie on catalog view, modal, listings detail page). The tooltips for linked entities should include all relevant specifications available for that entity, for example:
    - **CPU Tooltip:** Name, Cores, Threads, Base Clock, Boost Clock, TDP, single and multi-thread benchmarks, and all other relevant specs.
    - **GPU Tooltip:** Name, VRAM Size, Base Clock, Boost Clock
    - **RAM Tooltip:** Capacity, Type, Speed, Generation, Module Count
    - **Storage Tooltip:** Capacity, Type (SSD/HDD), Interface (SATA/NVMe)

- The listing detail page should make better use of space and layout to improve readability and user experience, while keeping the tabbed design recently implemented.
