# Valuation Rules Guide

Valuation rules normalize a listing down to its barebones equivalent so comparisons stay fair. Each rule describes how to deduct value for a component depending on the listing's condition.

## Rule Fields
- **component_type** – enum (`ram`, `ssd`, `hdd`, `os_license`, `wifi`, `gpu`, `misc`).
- **metric** – how to apply `unit_value_usd`:
  - `per_gb`, `per_tb`, or `flat`.
- **unit_value_usd** – base deduction per unit.
- **condition_new/refurb/used** – multiplier applied depending on the listing's condition.
- **age_curve_json** – optional JSON payload for advanced depreciation (future enhancement).

## How the Engine Works
1. Valuation rules load into `ValuationRuleData` objects.
2. Listings generate component inputs:
   - RAM quantity (GB).
   - Storage (GB, auto-mapped to SSD/HDD by type string).
   - OS license (flat quantity = 1).
   - Additional `listing_component` rows (e.g., discrete GPU, Wi-Fi card).
3. `compute_adjusted_price` multiplies quantity × unit value × condition multiplier.
4. The API stores the resulting breakdown JSON, which powers the UI explain view and CLI `explain` command.

## Editing Rules
- POST `/v1/catalog/valuation-rules` to add new rules.
- CLI + future UI flows will support updates. For now, updating requires direct DB changes or new imports.

## Tips
- Keep unit values aligned with current market component pricing.
- Use condition multipliers to reflect expected resale delta (e.g., used RAM retains ~60% value).
- For Apple devices with unified memory, treat RAM as `ram` with smaller per-GB deduction if you prefer.
