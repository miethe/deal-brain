# URL Ingestion - Follow-Up Work

**Date:** October 22, 2025

## Current Behaviors

- When a user begins an import via URL, the web app updates and shows a progress bar, which slowly fills and shows a timer. This progress bar never completes, and seems to be purely cosmetic and isn't tied to any real backend progress.
- Ingested listings via URLs create a new listing and populate the name, price, and condition.

## Expected Behaviors

- The progress bar should accurately reflect the real-time status of the import job, completing when the import is fully processed. Recent attempted fixes (ie git commit f44dea388016a87d1bd17c7e4643c2fccbcef879) have tried to resolve this but have not yet succeeded. It is ok for the progress bar to be approximate, but it should not stall indefinitely and must update when complete or failed based on real backend status.
- Ingested listings should attempt to populate ALL available fields for a Listing. This should always include at least title, price, condition, and image URL. If available from the source URL, it should also populate description, brand, model number, and category.
    - In addition to details available on the product page, the adapter should attempt to parse data from the product's title or even description as needed. For example, if an eBay listing had the product title "MINISFORUM Venus NAB9 Mini PC | Intel Core i9-12900H | 32GB RAM | 1TB SSD |", the adapter should parse out the brand "MINISFORUM" and model "Venus NAB9" even if those details are not explicitly labeled on the page. It should also pull the CPU model "Intel Core i9-12900H", RAM "32GB", and storage "1TB SSD" if not definitively available in structured data.
    - All fields should be sanitized and normalized as needed based on expected formats. For example, prices should be stored as numeric values in USD, conditions should be mapped to standard enums (New, Used - Like New, Used - Good, etc), and text fields should have extraneous whitespace trimmed.
    - Fields which exist as a spec, ie RAM, should attempt to populate with an existing spec if possible, or creating a new spec if all the required data is available, or otherwise only populating the raw fields directly. ie for the above example, the ram_gb should be set to 32, as the title doesn't indicate generation, speed, number of modules, etc. If the remaining needed data was available on the product page for the other fields, the spec should be created and linked to the listing. This should then backfill the raw fields as well automatically.