# Listings UI Reskin Proposal

## Iteration A — Card Grid (scan fast, edit later)

Purpose: discovery and triage.

What you see

* Responsive card grid, 2–4 columns.
* Big price vs **Adjusted** side-by-side, with green/amber accent if adjusted beats or trails sticker.
* CPU badge (name), score badge (ST / MT), device type, vendor, and up to two tags.
* Inline performance chips: **$/ST**, **$/MT**, **adj $/ST**, **adj $/MT**.
* Quick-edit and “Open” controls right on the card.

Why it works

* Perfect for hunting value: the per-perf chips make “deal density” obvious at a glance.
* Safe to skim hundreds of items while still surfacing the key math.

## Iteration B — Dense List (ops mode, spreadsheet energy)

Purpose: bulk decisions and keyboard-driven edits.

What you see

* Compact table with: Title, CPU, Price, Adjusted, $/ST, $/MT, Actions.
* Hover reveals ops cluster: **Details**, **Quick Edit**, **More**.
* Reads like your existing data grid but visually cleaner, perfect for elbow-grease sessions.

Why it works

* Maximum information per vertical pixel.
* A natural on-ramp from your current embedded table to a friendlier surface.

## Iteration C — Split Master/Detail + Compare Drawer

Purpose: evaluate alternatives without losing context.

What you see

* Left: scrollable list (title, CPU, adjusted price, compare checkbox).
* Right: rich detail card for the selected listing with KPI tiles (Price, Adjusted, $/ST, $/MT), perf badges, and key specs (RAM, storage, vendor, condition).
* Bottom sheet “Compare” that stacks mini-cards side-by-side for $/MT and adjusted price.

Why it works

* Keeps the mental stack small: pick, glance, compare, decide.
* Compare stays lightweight—no new page, no modal ping-pong.

## Shared UX spine (all iterations)

* Sticky **Filters bar** with: text search (title/CPU/tags), Form Factor, Manufacturer, and a price ceiling slider. This mirrors your current filter semantics so it slots into the same backend/query.
* **Details dialog** everywhere: click any card/row → modal with KPIs, perf chips, and “Expand full page.”
* **Data tab toggle**: persistent “Data” control that jumps to the raw table you already have.
* **Color semantics**: adjusted < price = emerald hint; adjusted > price = amber hint. It trains the eye.
* **Edit affordances**: “Quick Edit” opens a focused inline editor (title, price, condition, status, tags) without leaving the flow.

## Data & formatting (wired to your model)

* **$/ST** = `priceUSD / cpu.stMark`
* **$/MT** = `priceUSD / cpu.mtMark`
* **adj $/ST** = `adjustedUSD / cpu.stMark`
* **adj $/MT** = `adjustedUSD / cpu.mtMark`
* Always render currency as whole dollars in catalog; show cents only in detail.
* Scores display as `ST 10,000 / MT 48,500` (thousands-separated; no decimals).

## DX notes (how this lands cleanly)

* Component kit: `Card`, `Badge`, `Button`, `Tabs`, `Dialog`, `Sheet`, `Table`, `Slider`, `Tooltip` (shadcn/ui). Icons from `lucide-react`.
* State: a tiny client store (`q`, `type`, `manufacturer`, `priceRange`, `view`, and `details`) with memoized filtering. In the app, swap the inline filter logic for your server query to keep perf tight on large sets.
* Accessibility: focus traps in Dialog/Sheet; all interactive icons have a text fallback; badge color never the only signal (text labels back them).
* Keyboard: `/` focuses search, `j/k` moves selection in Master-Detail, `c` toggles compare on selected, `Enter` opens Details.

## Where it plugs in

* `/app/(dealbrain)/listings/page.tsx`: tabs for **Catalog** (default) and **Data**.
* `/app/(dealbrain)/listings/_components/`: `ListingsCatalog`, `ListingsFilters`, `ListingCard`, `ListingRow`, `ListingDetails`, `CompareDrawer`.
* API stays unchanged; catalog requests can use the same search endpoint with query params for filters.

## Next tiny enhancements

* “Smart sort”: default by **adj $/MT** ascending; secondary by **adj $/ST**.
* Save filter presets (“SFF < $600”, “Creator OLED”, “32GB RAM+”) with a pill switcher.
* Quick compare export: one-click CSV of selected rows with perf metrics.
* Deal alerts: bell icon on any filter preset to push notifications when a new listing beats your threshold.
