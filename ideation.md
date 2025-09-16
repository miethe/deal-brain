Here’s a tight, battle-ready product plan for your price-to-performance tracker—built to start simple (solo-use, local) and scale into a clean OSS app when you feel like sharing. I inspected your attached workbook and kept the data model and flows aligned with your current columns. You can also grab the quick schema summary I generated: Download JSON summary.

North Star

A personal, web-based “deal brain” for small form factor PCs (and similar), that:
	•	Ingests listings you find (manually, API, CLI; later: scrapers).
	•	Auto-resolves CPU/GPU → benchmark rows.
	•	Applies your “non-barebones” adjustment logic to value RAM/SSD add-ons.
	•	Ranks devices by configurable price/perf, perf/watt, and use-case profiles.
	•	Surfaces a live dashboard of best picks, with explainable scoring.

Primary user & use cases
	•	You (power user, homelab buyer):
	•	Log a device you found, with CPU/GPU/RAM/SSD/ports/price/link/condition.
	•	See a ranked list by “best price per CPU Mark,” “best under $400,” “best Plex/Quick Sync,” “best Proxmox node,” “best AV1 encode,” “best Apple Silicon.”
	•	Tweak valuation rules (e.g., how much a 32GB DDR4 kit reduces “net device price”).
	•	Export/share shortlists.
	•	Future OSS users: same patterns, possibly multi-user.

MVP scope (v0.1)

In
	•	Web UI to add and view listings.
	•	CPU/GPU lookup against a local catalog imported from your sheet.
	•	Your valuation rules (from Reference sheet) to compute Adjusted Price.
	•	Core metrics you already track:
	•	$/Mark, $/Single-Mark, Mark/W, % of “Pi” baselines (optional), “Total Est Value”.
	•	Dashboard cards: “Top price/perf today,” “Top under $X,” “Top by use-case profile.”
	•	Importer from your Excel sheets → database.

Out (for now)
	•	Automated web scraping (add in v0.4+).
	•	Multi-currency, tax/shipping normalization (v0.2/0.3).
	•	Multi-user auth (v0.3+).

Data model (grounded in your workbook)

Your workbook sheets I found:
	•	CPUs (1006×21): Manufacturer, CPU, Socket, CPU Mark - Multi, Single Thread, Cores, Threads, GPU, TDP, Est Values, Cost, $/Mark, $/Single Mark, Mark/W, % of Pi, Mark/W of Pi…
	•	SFF PCs (40×17): Device, CPU, Memory, Storage 1/2, CPU Mark, Single Thread, GPU Mark, Cost, Adjusted Cost, $/Mark, $/Mark-Adj, Mark/W, % of Pi…
	•	Reference (52×14): Component, Metric, Unit cost (suggested), Manufacturer, GPU Model, GPU Mark Score, Component Type, Adjustment Amount…
	•	Macs / Macs 725: Apple-specific models, GPU Cores, Adj Price, $/100 Multi, etc.

Core entities & tables
	1.	cpu

	•	id, name (e.g., “i5-13500”), manufacturer, socket, cores, threads, tdp_w, i_gpu_model (nullable), cpu_mark_multi, cpu_mark_single, cost_est (optional), notes
	•	Seed from CPUs sheet.

	2.	gpu

	•	id, name, manufacturer, gpu_mark (PassMark/GPU Mark), geekbench_metal (for Apple), notes
	•	Seed from Reference.GPU Model/GPU Mark and Apple mappings from Macs sheets. (We’ll normalize to a gpu_score later—see Algorithm.)

	3.	device_model (optional at MVP; helpful for ports/expandability templates)

	•	id, name (e.g., “Minisforum UM790 Pro”), cpu_id (default), ports_profile_id (default), form_factor (SFF/NUC/SFF-tower), expandability_notes
	•	Lets you pre-template port sets.

	4.	ports_profile & port

	•	ports_profile: id, name
	•	port: id, ports_profile_id, type (enum: usb_a, usb_c, tb4, hdmi, dp, rj45_1g, rj45_2_5g, sdxc, audio, pcie_x16 (internal), m2_slots, sata_2_5_bays, etc.), count, spec_notes
	•	You can quickly apply a ports profile to a listing, then tweak.

	5.	listing (the star)

	•	id, title, device_model_id (nullable), cpu_id (resolved), gpu_id (nullable),
ram_gb, storage_primary_gb, storage_secondary_gb,
condition (enum: new, refurb, used), price_usd, price_date,
url, seller (free text), location, notes.
	•	Derived fields (materialized columns for speed):
adjusted_price_usd, score_cpu, score_gpu, score_composite,
dollar_per_cpu_mark, dollar_per_single_mark, mark_per_watt, explain_json.

	6.	valuation_rule (from your Reference sheet)

	•	id, component_type (ram, ssd, hdd, wifi, os_license, etc.),
metric (e.g., per-GB, per-TB, flat),
unit_value_usd, condition_factor_new, condition_factor_refurb, condition_factor_used,
age_depreciation_curve (json), notes.
	•	These define how to subtract value for included components to get Adjusted Price (i.e., estimate “barebones equivalent”).

	7.	benchmark_source (for provenance, later)

	•	id, name (PassMark, Geekbench 6, internal), url, license_notes.

Algorithms

1) Adjusted Price (your “not-barebones” logic)

Goal: Normalize listings to a barebones-equivalent price so apples compare to apples.

AdjustedPrice = ListingPrice
  - Valuation(RAM_gb, spec, condition)
  - Valuation(Storage_primary_gb, type, condition)
  - Valuation(Storage_secondary_gb, type, condition)
  - Valuation(OS_license, if present)
  - Valuation(Misc components matched by rules)

	•	Valuation() uses valuation_rule by component_type and metric.
	•	Condition multipliers (defaults): new=1.0, refurb=0.75, used=0.6 (editable).
	•	Optional age curve (years since release) to reduce valuations.

Explainability: store a per-listing explain_json with rule hits and numbers so the UI can show you exactly how the adjusted price was computed.

2) GPU normalization (Apple + PC GPUs)
	•	Maintain both gpu_mark (PassMark) and geekbench_metal for Apple Silicon.
	•	Create a gpu_score by min-max scaling each metric within its family, then blending with a family weight:
	•	If Apple GPU present: gpu_score = blend(scale(geekbench_metal), scale(gpu_mark_if_any)), default 0.8 Metal / 0.2 GPU Mark.
	•	If PC GPU: gpu_score = scale(gpu_mark).
	•	Store gpu_score in listing for unified comparisons and in explain_json (with source values).

3) Composite utility scores (use-case profiles)
	•	Define named profiles with weights:
	•	General SFF Node: 0.6 CPU_multi + 0.2 CPU_single + 0.2 perf/watt
	•	Plex/Transcode: favor iGPU with HEVC/AV1 → add encoder_capability flag; 0.4 CPU_single + 0.4 encoder_cap + 0.2 perf/watt
	•	Proxmox/VM host: 0.5 CPU_multi + 0.2 RAM capacity + 0.2 expandability + 0.1 perf/watt
	•	Light Gaming: 0.4 GPU + 0.3 CPU_single + 0.2 ports (HDMI/DP) + 0.1 perf/watt
	•	Apple dev/test: 0.5 CPU_single + 0.3 Metal + 0.2 RAM
	•	Each profile defines how score_composite is calculated. Profiles are editable in UI.

4) Ranking
	•	Primary sort by $ per target score (e.g., AdjustedPrice / CPU_mark_multi or / score_composite).
	•	Secondary tie-breakers: perf/watt, ports fit (if you set must-have ports), recent price date.

UX & flows

Create listing flow
	•	Typeahead CPU lookup (from cpu table, seeded from your CPUs sheet).
	•	Optional GPU pick (or auto-set from CPU’s iGPU; overrideable).
	•	Add RAM/Storage with quick chips (8/16/32GB DDR4; 256/512/1TB NVMe).
	•	Pick ports profile (e.g., “UM790 Pro default”) then tweak.
	•	Paste URL + price + condition.
	•	On submit: compute Adjusted Price, perf metrics, composite score, store explain_json.
	•	Show a one-line “why it ranks” tooltip.

Dashboard
	•	Top Cards:
	•	Best $/CPU Mark (Adj)
	•	Best under $X
	•	Best perf/watt
	•	Best by Profile (dropdown: Plex, Proxmox, etc.)
	•	Quick Filters: Price ceiling, CPU gen, AV1 encode, 2.5GbE, M.2 slots ≥2, etc.
	•	Explain on hover: show valuation breakdown and profile weighting summary.

Importer (from your spreadsheet)
	•	Map:
	•	CPUs → cpu catalog.
	•	Reference → valuation_rule (+ seed gpu rows).
	•	SFF PCs + Macs + Macs 725 → listing (with Apple GPU handling).
	•	Provide dry-run preview (“N rows → X CPUs, Y GPUs, Z listings; conflicts detected: …”).

System architecture

MVP (simple & fast)
	•	Backend: FastAPI (Python 3.11+)
	•	DB: SQLite (file), via SQLAlchemy; pg ready later
	•	Worker (optional at MVP; later for scrapers): RQ or Celery (Redis)
	•	Frontend: FastAPI + Jinja or HTMX + Tailwind for speed, or Next.js if you prefer React. (Given your personal tool + speed, HTMX/Tailwind is perfect for v0.1.)
	•	Container: Docker Compose (api, db file volume, optional redis)
	•	Tests: Pytest + Playwright (for later scrapers)

Later (v0.3+)
	•	DB: Postgres
	•	Cache: Redis
	•	Frontend: Next.js (if you want richer UI/filters)
	•	Background jobs: Celery + Flower (or RQ + RQ-Dashboard)
	•	Metrics: OpenTelemetry traces to Grafana Tempo; logs to Loki; dashboards in Grafana.

API & CLI (for your workflows)

REST examples
	•	POST /listings

{
  "title":"UM690S – 32GB/512GB",
  "cpu":"Ryzen 9 6900HX",
  "ram_gb":32,
  "storage_primary_gb":512,
  "price_usd":399,
  "condition":"used",
  "url":"https://…",
  "ports":[{"type":"rj45_2_5g","count":1},{"type":"usb_c","count":2}],
  "seller":"eBay/AnkerOfficial"
}

→ returns computed adjusted_price_usd, $per_cpu_mark, score_composite, explain.

	•	GET /rankings?metric=pp_cpu_multi&max_price=500&profile=proxmox

CLI (click/typer)
	•	deals import ./CPUs.xlsx
	•	deals add --title "M2 Mac mini 24/512" --price 725 --cpu "Apple M2" --ram 24 --storage 512 --link …
	•	deals top --metric pp_cpu_multi --under 400 --limit 10
	•	deals explain <listing_id>

Data quality & normalization
	•	CPU normalizer: fuzzy match input CPU strings → canonical cpu.name.
	•	Apple GPU handling: map Macs 725.GPU Cores + model → geekbench_metal estimate (seed table; editable).
	•	Perf/Watt: default to CPU TDP if actual draw unknown; allow manual override on listings.
	•	Ports taxonomy: keep enum small and pragmatic; allow “other” notes.

Security & licensing
	•	Local only by default. Optional basic auth if you expose it.
	•	OSS: MIT or Apache-2.0, with a one-page “Data sources & ToS” note (respect PassMark/Geekbench terms).

Roadmap

v0.1 (MVP – local only)
	•	Importer for CPUs, Reference, SFF PCs, Macs, Macs 725.
	•	Listing creation + valuation engine + ranking.
	•	Dashboard cards + filters.
	•	CLI basics.

v0.2
	•	Profiles (saved weight sets) + per-profile leaderboards.
	•	Export CSV/JSON; snapshot “buy list.”
	•	Better Apple GPU normalization (Metal table).

v0.3
	•	Postgres migration, user auth (if sharing), audit log.
	•	Price history (re-save listings to track deltas), charts.

v0.4
	•	Scraper framework (Playwright): modules for eBay search, Amazon Warehouse, Best Buy Open-Box, MicroCenter, Minisforum, Beelink, Apple Refurb. Rate-limits, retries, human-like pacing, HTML snapshots, ToS-aware toggles.

v0.5
	•	Alerts: “Notify when $/CPU Mark under X” or “UM790 Pro under $500.”
	•	Simple rules engine UI for alerts.

Acceptance criteria (MVP)
	•	I can import my current Excel and see:
	•	≥95% CPUs in catalog with correct multi/single/tdp.
	•	Listings from SFF PCs & Macs* appear with computed Adjusted Price within ±$5 of my sheet.
	•	Creating a listing in the web UI:
	•	CPU auto-resolves in ≤150 ms (local).
	•	Adjusted Price is computed with visible line-item explanation.
	•	Dashboard immediately reflects ranking.
	•	Profiles:
	•	I can switch profile and see ordering change predictably.
	•	CLI:
	•	I can add, list top N by metric, and export JSON.

Gotchas & mitigations
	•	Benchmark licensing: cache locally; do not re-publish scraped tables wholesale. Document provenance.
	•	Apple GPU comparability: Metal vs GPU Mark is apples vs oranges; keep a profile switch and show the underlying sources transparently.
	•	Condition ambiguity: used/refurb quality varies; expose condition multipliers in settings and show their effect in the explain panel.
	•	Tax/shipping: optional toggles per listing; store them separately to avoid polluting base price.
	•	Duplicate listings: URL hash + fuzzy title matching to dedupe.

Implementation sketch
	•	Repo layout

/api        # FastAPI app, SQLAlchemy models, valuation engine
/ui         # HTMX+Tailwind templates (or Next.js if chosen)
/data       # seed CSVs derived from your Excel sheets
/cli        # Typer-based CLI
/workers    # (later) scrapers, RQ/Celery tasks
/infra      # docker-compose, env, migrations


	•	Valuation engine
	•	Pure Python module with rule registry → returns (adjusted_price, breakdown[]).
	•	100% unit-tested with snapshots from your sheet rows.
	•	Importer
	•	Pandas → canonical CSV → upserts (on natural keys: cpu.name, gpu.name).
	•	Dry-run mode shows diffs before commit.

Dashboard cards (initial set)
	•	Top $/CPU Mark (Adj) under $400
	•	Top Perf/Watt (Mark/W)
	•	Top Plex profile (HEVC/AV1 flag + single-thread)
	•	Top Proxmox profile (cores/threads + RAM path + expandability flag)
	•	Apple picks (Metal-weighted composite)

What I already aligned to your workbook
	•	CPU catalog fields mirror CPUs columns (multi, single, TDP, iGPU, derived $/Mark).
	•	Listings mirror SFF PCs & Macs columns (Adjusted Cost/Adj Price; GPU Cores for Apple).
	•	Valuation rules use Reference’s Component Type, Unit cost (suggested), Adjustment Amount.
	•	Metrics included: $ / Mark, $ / Single Mark, Mark / W, plus composite profiles.
