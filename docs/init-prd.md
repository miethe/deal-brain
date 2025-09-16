SFF Deal Brain — MVP Product Requirements Document (PRD)

A full-stack web app that turns your spreadsheet workflow into a fast, explainable “deal brain” for SFF PCs and mini-workstations. Built for your personal use first, but clean enough to open-source.

⸻

0) TL;DR
	•	Frontend: React (Next.js App Router) + Tailwind design tokens + shadcn/ui (Radix primitives, TanStack Table, Cmd-K, Dialogs).
	•	Backend: FastAPI (Python 3.11+), Postgres, SQLAlchemy, Alembic, Redis (jobs/cache), Celery workers.
	•	Core MVP: manual listing input; CPU/GPU auto-resolve; valuation engine → Adjusted Price; composite scoring profiles; dashboard leaderboards; import from your Excel; explainable breakdowns.
	•	Deliverables: working app, API + CLI, seed data from your workbook, acceptance tests, observability, Docker Compose.
	•	Future: scrapers (Playwright), alerts, price history charts, auth/multi-user, React Native companion, GraphQL, mobile-first PWA, more benchmark sources.

Design mocks (PNG renders):
	•	Dashboard: download
	•	Add Listing: download
	•	Listing Detail + Explain: download
	•	Rankings: download
	•	Scoring Profiles: download
	•	Valuation Rules: download
	•	Import Wizard: download

⸻

1) Problem, Goals, Non-Goals

Problem
Manually comparing SFF listings across sites is noisy and inconsistent: bundled RAM/SSD distort value, CPU/GPU benchmarks live elsewhere, and “best pick” depends on context (Proxmox vs Plex vs dev).

Goals (MVP)
	1.	One-shot input for a listing (web, API, CLI) with CPU/GPU auto-resolve.
	2.	Deterministic Adjusted Price to normalize non-barebones devices (transparent line-item math).
	3.	Rankings by price/perf (CPU multi/single, composite profiles), perf/watt, and budget caps.
	4.	Dashboard surfacing “today’s best” for your saved profiles.
	5.	Import your current Excel → Postgres seed; reproduce your sheet’s numbers within tolerance.
	6.	Explainability everywhere (hover/expand shows valuation & scoring).

Non-Goals (MVP)
	•	Automated scraping, price-alerts, account system, multi-tenant, mobile app, tax/shipping normalization.
	•	Republishing third-party benchmark datasets wholesale.

⸻

2) Users & Primary Use Cases
	•	Nick (single user / admin)
	•	Add, edit, dedupe listings quickly.
	•	Flip between profiles (Proxmox, Plex, Apple dev, Gaming light, General SFF) and budgets.
	•	Inspect math for trust; export a shortlist.
	•	Open-source users (later)
	•	Same flows; optional login; optional shared catalogs.

⸻

3) Key Concepts & Algorithms

3.1 Adjusted Price (normalize to barebones)

AdjustedPrice = ListingPrice
  - value(RAM_gb, ddr_gen, sticks, condition)
  - value(PrimaryStorage, type, condition)
  - value(SecondaryStorage, ...)
  - value(OS license)
  - value(Other components matched by rules)

	•	Rules come from editable Valuation Rules table: component_type, metric (per-GB, per-TB, flat), unit_value_usd, condition multipliers (new/refurb/used), optional age depreciation curve (years since release).
	•	Persist full explain_json for each listing (inputs, rules hit, per-line deduction, totals).

3.2 GPU normalization (Apple + PC)
	•	Keep raw GPU Mark and Geekbench Metal.
	•	Compute unified gpu_score:
	•	If Apple: gpu_score = 0.8 * scale(metal) + 0.2 * scale(gpu_mark_if_present)
	•	If PC: gpu_score = scale(gpu_mark)
	•	Persist raw sources and blended score in explain JSON.

3.3 Composite Scoring Profiles (weights)

Editable profiles (UI sliders) combine:
	•	cpu_mark_multi, cpu_mark_single, gpu_score, perf_per_watt, ports_fit, ram_capacity_path, expandability_flag, encoder_capability (HEVC/AV1).
Example – Proxmox: 0.5 multi + 0.2 RAM capacity + 0.2 expandability + 0.1 perf/watt.
Plex: 0.4 single + 0.4 encoder_cap + 0.2 perf/watt.

3.4 Ranking
	•	Primary: AdjustedPrice / target_score (e.g., CPU multi or composite).
	•	Ties: higher perf/watt, more recent price, ports fit.
	•	Budget filter (e.g., under $400).

⸻

4) Scope & Requirements

4.1 Functional Requirements (MVP)

FR-1 Listing CRUD
	•	Create via Web UI (typeahead CPU/GPU), API, CLI.
	•	Fields: title, url, seller, price, condition, cpu, gpu (optional/iGPU), ram_gb, storage_primary {size,type}, storage_secondary, ports profile attach + tweaks, notes.
	•	On create/update: compute adjusted_price, derived metrics, explain_json.

FR-2 Catalogs
	•	CPU catalog from seed (imported) with: maker, socket, cores/threads, tdp_w, iGPU model, cpu_mark_multi, cpu_mark_single.
	•	GPU catalog with gpu_mark, optional metal.
	•	Edit CPU/GPU (admin-only).

FR-3 Valuation Rules
	•	CRUD rules; previews show effect on a sample listing.
	•	Rule types: RAM, SSD, HDD, OS, Wi-Fi, misc.

FR-4 Profiles
	•	CRUD scoring profiles with sliders and named weights.
	•	Apply profile to dashboard & ranking.

FR-5 Dashboard & Rankings
	•	Cards: Best $/CPU Mark (Adj), Best perf/watt, Best under $X, Best by active profile, Apple picks.
	•	Table (TanStack): sortable, column chooser, saved views.
	•	Quick filters: price cap, CPU gen, AV1, 2.5GbE, M.2 ≥ 2, etc.

FR-6 Listing Detail
	•	Metrics at a glance; ports & specs; Explain Valuation table; “Benchmark sources” popover; duplicate button.

FR-7 Import
	•	Wizard: upload Excel → preview mapping → upsert into CPU/GPU/ValuationRules/Listings.
	•	Dry-run with conflict report (e.g., CPU name mismatches).

FR-8 Export
	•	CSV/JSON of current ranking or a selected set.

4.2 Non-Functional Requirements
	•	Performance:
	•	Autocomplete lookups ≤150 ms p95 (local).
	•	Ranking query ≤400 ms p95 for 10k listings.
	•	Reliability:
	•	Idempotent imports; transactionally safe upserts.
	•	Explainability:
	•	Every computed number linked to inputs; one-click copy of breakdown.
	•	Observability:
	•	OTel traces (API routes, valuation), metrics (duration, cache hit rate), structured logs (Loki).
	•	Portability:
	•	Docker Compose one-command up; dev on macOS/Linux.
	•	Licensing:
	•	MIT/Apache-2.0; benchmark source attributions retained.
	•	Privacy:
	•	Local-only by default; optional basic auth.

⸻

5) System Architecture

5.1 High-level
	•	Web: Next.js (React 18, App Router), Tailwind + shadcn/ui (Radix), TanStack Table/Query, CmdK for quick open, Tremor/Recharts for charts.
	•	API: FastAPI api/v1, Pydantic models, SQLAlchemy ORM, Alembic migrations.
	•	DB: PostgreSQL (primary).
	•	Cache/Jobs: Redis; Celery workers (valuation batch, import, future scrapers).
	•	Storage: local for uploads; S3/MinIO optional later.
	•	Observability: OTel SDK → Grafana Tempo/Prometheus; logs → Loki.
	•	Auth (later): JWT (PyJWT) + NextAuth (Email/Pass, OAuth opt-in).

5.2 Monorepo layout (Turborepo)

/apps
  /web           # Next.js + shadcn/ui + Tailwind tokens
  /api           # FastAPI service
  /worker        # Celery tasks
/packages
  /ui            # shared UI tokens/components
  /schemas       # OpenAPI/JSON schemas, TS types (openapi-typescript)
  /client        # TS API client (generated)
  /cli           # Python Typer CLI (packaged)
/infra
  docker-compose.yml
  grafana/ loki/ tempo/ prometheus/ (optional stack)

5.3 Environment & Dev
	•	.env (dev): DATABASE_URL=postgres://..., REDIS_URL=redis://..., OTEL_EXPORTER_OTLP_ENDPOINT=...
	•	Docker Compose services: web, api, worker, db, redis, grafana (optional).
	•	CI: GitHub Actions → lint, type-check, unit/integration tests, build images, run Alembic migrations.

⸻

6) Data Model (Postgres)

cpu
	•	id PK, name (uniq), manufacturer, socket, cores int, threads int, tdp_w int,
igpu_model text null, cpu_mark_multi int, cpu_mark_single int, release_year int null, notes text.

gpu
	•	id PK, name (uniq), manufacturer, gpu_mark int null, metal_score int null, notes.

device_model (optional, helpful for default ports/expandability)
	•	id, name uniq, cpu_id ref null, ports_profile_id ref null, form_factor, expandability_notes.

ports_profile
	•	id, name uniq.
port
	•	id, ports_profile_id ref, type enum (usb_a, usb_c, tb4, hdmi, dp, rj45_1g, rj45_2_5g, sdxc, audio, m2_slot, sata_bay, pcie_slot, other), count int, spec_notes text.

valuation_rule
	•	id, component_type enum (ram, ssd, hdd, os, wifi, misc), metric enum (per_gb, per_tb, flat),
unit_value_usd numeric(10,2), condition_new float, condition_refurb float, condition_used float,
age_curve_json jsonb null, notes.

profile
	•	id, name uniq, weights_json jsonb  (keys: cpu_multi, cpu_single, gpu, perf_watt, ports_fit, ram_capacity, expandability, encoder_cap), default bool.

listing
	•	id, title, url, seller, price_usd numeric(10,2), price_date date default now, condition enum,
cpu_id ref, gpu_id ref null, ram_gb int, primary_storage_gb int, primary_storage_type enum,
secondary_storage_gb int null, secondary_storage_type enum null,
ports_profile_id ref null, notes text,
derived/materialized:
adjusted_price_usd numeric(10,2), score_cpu_multi float, score_cpu_single float, score_gpu float,
score_composite float, dollar_per_cpu_mark float, dollar_per_single_mark float, perf_per_watt float,
explain_json jsonb.
Indexes: (price_date), GIN on explain_json (optional), btree on (adjusted_price_usd, score_cpu_multi).

benchmark_source
	•	id, name, url, notes.

(Alembic migrations produce these; enums stored via sqlalchemy.Enum.)

⸻

7) API Spec (REST, api/v1)

7.1 Listings
	•	POST /listings
Request:

{
  "title":"UM690S – 32/512",
  "url":"https://…",
  "seller":"eBay",
  "price_usd":399.0,
  "condition":"used",
  "cpu":"Ryzen 9 6900HX",
  "gpu":"Radeon 680M",
  "ram_gb":32,
  "primary_storage_gb":512,
  "primary_storage_type":"nvme",
  "ports":[{"type":"rj45_2_5g","count":1},{"type":"usb_c","count":2}]
}

Response (201): listing with derived metrics + explain_json.

	•	GET /listings?search=&min_price=&max_price=&cpu=&profile=proxmox&limit=50&sort=pp_cpu_multi
	•	GET /listings/{id} (detail)
	•	PUT /listings/{id} (recompute on change)
	•	DELETE /listings/{id}

7.2 Catalog
	•	GET /cpus?search= / GET /gpus?search= (typeahead)
	•	POST /cpus / POST /gpus (admin)

7.3 Profiles
	•	GET /profiles
	•	POST /profiles body { "name": "Proxmox", "weights": { "cpu_multi":0.5, ... } }
	•	PUT /profiles/{id} / DELETE /profiles/{id}
	•	POST /profiles/{id}/activate

7.4 Valuation Rules
	•	GET /valuation-rules
	•	POST /valuation-rules / PUT /valuation-rules/{id} / DELETE /valuation-rules/{id}
	•	POST /valuation/apply → dry-run on a hypothetical listing, returns breakdown.

7.5 Import/Export
	•	POST /import/excel (multipart) → dry-run preview, job_id
	•	POST /import/commit?job_id=
	•	GET /export?format=csv&view=rankings

OpenAPI auto-generated; TS client generated with openapi-typescript.

⸻

8) Frontend UX (React + shadcn/ui)

Design tokens (Tailwind):
	•	Base dark theme; slate/stone palette; accent brand blue (primary), emerald (positive), amber (warn).
	•	Radii: md (cards), sm (table), shadows subtle.
	•	Spacing scale 1–10; typography Inter/Mono.

Key views
	1.	Dashboard — cards + two charts (price distribution, CPU gen share) + top table; floating “Add Listing”.
	2.	Listings — searchable table (TanStack), column presets; row action → Detail.
	3.	Listing Detail — hero price & KPIs; specs; ports; Explain Valuation card.
	4.	Add/Edit Listing — multi-step dialog or drawer; preview panel shows live Adjusted Price and $/Mark.
	5.	Rankings — saved views; profile/budget selector; export.
	6.	Profiles — sliders with live preview; duplicate + set default.
	7.	Valuation Rules — table with “Edit Rule” sheet; quick test pane.
	8.	Import Wizard — upload → mapping → preview → commit.

(See PNGs linked in TL;DR)

⸻

9) Valuation & Scoring — Implementation Details

Valuation engine (pure Python module)

def adjusted_price(listing, rules, now=date.today()):
    lines = []
    price = listing.price_usd
    # RAM
    ram_rule = rules.get('ram')
    ram_val = ram_rule.unit_value_usd * listing.ram_gb * condition_mult(listing.condition, ram_rule)
    lines.append(('RAM', ram_val))
    # Storage primary
    s_rule = rules.get(listing.primary_storage_type)  # ssd/hdd
    s_val = value_storage(s_rule, listing.primary_storage_gb, listing.condition)
    lines.append(('Storage (primary)', s_val))
    # Secondary, OS, misc ...
    adjusted = price - sum(v for _, v in lines)
    return adjusted, lines

	•	Unit tests assert reproduction of your spreadsheet values within ±$5 for seeded rows.

GPU score

def gpu_score(gpu):
    if gpu.metal_score and gpu.manufacturer.lower() == 'apple':
        return 0.8 * scale(gpu.metal_score) + 0.2 * scale(gpu.gpu_mark or 0)
    return scale(gpu.gpu_mark or 0)

Composite

def composite(listing, weights):
    return (
      weights.cpu_multi   * norm(listing.score_cpu_multi) +
      weights.cpu_single  * norm(listing.score_cpu_single) +
      weights.gpu         * norm(listing.score_gpu) +
      weights.perf_watt   * norm(listing.perf_per_watt) +
      ...
    )


⸻

10) Acceptance Criteria
	1.	Import parity: After importing your Excel, ≥95% CPU/GPU rows resolve; for a sample of 20 listings, Adjusted Price within ±$5 of the sheet.
	2.	Create listing: From UI, user can create a listing in ≤60s; preview updates Adjusted Price live with per-line math.
	3.	Ranking: Sorting by $ / CPU Mark (Adj) reflects expected order and reacts to price/profile changes instantly.
	4.	Profiles: Changing active profile updates ordering; sliders persist and serialize weights.
	5.	Explainability: Listing detail shows breakdown totaling exactly to Adjusted Price; copy-to-clipboard works.
	6.	Performance: p95 latencies: typeahead ≤150 ms; ranking ≤400 ms on 10k listings.
	7.	Observability: Traces visible for POST /listings and GET /rankings; error logs include correlation IDs.
	8.	CI: PR checks enforce tests, linters, type checks; images build; Alembic migration runs in pipeline.
	9.	Docker up: docker compose up brings a working stack with seeded data.

⸻

11) Telemetry & Analytics
	•	Events: listing.created, listing.updated, import.started/completed, profile.changed, valuation.rule.changed.
	•	Metrics: valuation duration, lookup cache hit rate, ranking query time, import row throughput.
	•	Traces: user → API → DB; attributes: listing_id, cpu_id, profile_name.
	•	Dashboards: latency SLOs, errors by route, top rules used, profile adoption.

⸻

12) Security, Privacy, Compliance
	•	Local instance; optional basic auth (reverse proxy) for MVP.
	•	API keys (future) for CLI; rate limiting (reverse proxy).
	•	Input validation (Pydantic); server-side filtering of HTML.
	•	Attribution page for benchmarks; configurable source toggles.

⸻

13) Ops: Backups, Migrations, Releases
	•	Backups: nightly pg_dump to local volume (S3 optional).
	•	Migrations: Alembic; every PR with schema changes includes an autogen + hand-edited migration.
	•	Releases: Semver tags v0.1.0 (MVP), v0.2.0 (profiles/export), etc.
	•	Feature flags: lightweight env toggles for experimental views.

⸻

14) Test Plan
	•	Unit: valuation math, GPU score blending, profile weighting.
	•	Integration: create listing → computed fields persisted; import dry-run/commit; ranking sort stability.
	•	E2E (Playwright): add listing flow; edit valuation rule affects Adjusted Price; profile slider changes ordering.
	•	Data: seed snapshot tests against known rows from your sheet.

⸻

15) Risks & Mitigations
	•	Benchmark comparability (Metal vs GPU Mark) → disclose sources; let profile weights handle differences.
	•	Condition variability → expose multipliers in rules; show sensitivity analysis in explain popover (±10%).
	•	Legal/ToS for scraping (future) → toggles per-site; cache HTML; respect robots/ToS; personal use disclaimer.
	•	Filename/URL weirdness → robust parsing & dedup by URL hash + fuzzy title.

⸻

16) Roadmap (with explicit future call-outs)

v0.1 — MVP (this PRD)
	•	Web UI, API, CLI; import; valuation engine; profiles; dashboard/rankings; explainability; Docker; observability.

v0.2 — Profiles & Exports+
	•	Saved ranking views; CSV/JSON export; price caps & filter presets; better Apple GPU table; perf/watt overrides.

v0.3 — Multi-user & History
	•	NextAuth + JWT; Postgres → role tables; price history on listing updates; trend charts.

v0.4 — Scrapers & Alerts
	•	Playwright modules: eBay saved searches, Amazon Warehouse, BestBuy Open-Box, MicroCenter, Minisforum/Beelink, Apple Refurb.
	•	Alert rules: notify when $ / CPU Mark under X, or model under $Y.
	•	Jobs dashboard (Flower/RQ-Dash equivalent).

v0.5 — React Native Companion / PWA polish
	•	React Native (Expo) read-only leaderboard & quick add (camera URL scan).
	•	Share sheet; offline notes → sync.

v0.6 — GraphQL & RAG (optional)
	•	GraphQL gateway; semantic search over listings and ports; compare-view diff; knowledge cards per CPU/GPU.

Stretch
	•	Tax/shipping normalization & region support.
	•	Energy cost modeling (TDP × $/kWh).
	•	Recommendation agent (“for your homelab profile…”) with explainable feature importances.

⸻

17) Open Questions / Assumptions
	•	Backend remains FastAPI (Python) per this doc; if you prefer Node/Nest later, we keep Postgres schema and TS client intact.
	•	Benchmarks: we assume local cached datasets imported from your workbook; live scraping/API can be added behind flags.
	•	Ports taxonomy: we’ll start pragmatic; you can extend via “other/spec notes”.

⸻

18) Definition of Done (MVP)
	•	You can import your Excel, add three new listings from the web UI, switch to “Proxmox” profile, and export a top-10 CSV—all without touching the DB or code—and every number shown has an explain panel that reconciles to raw inputs.

⸻

Appendix A — Example SQL (abridged)

create table cpu (
  id serial primary key,
  name text unique not null,
  manufacturer text not null,
  socket text,
  cores int, threads int, tdp_w int,
  igpu_model text,
  cpu_mark_multi int, cpu_mark_single int,
  release_year int, notes text
);

create table gpu (
  id serial primary key,
  name text unique not null,
  manufacturer text not null,
  gpu_mark int, metal_score int, notes text
);

create table valuation_rule (
  id serial primary key,
  component_type text not null,
  metric text not null,
  unit_value_usd numeric(10,2) not null,
  condition_new float default 1.0,
  condition_refurb float default 0.75,
  condition_used float default 0.6,
  age_curve_json jsonb, notes text
);

create table profile (
  id serial primary key,
  name text unique not null,
  weights_json jsonb not null,
  "default" boolean default false
);

create table listing (
  id serial primary key,
  title text not null,
  url text, seller text,
  price_usd numeric(10,2) not null,
  price_date date default now(),
  condition text not null,
  cpu_id int references cpu(id),
  gpu_id int references gpu(id),
  ram_gb int default 0,
  primary_storage_gb int default 0,
  primary_storage_type text,
  secondary_storage_gb int,
  secondary_storage_type text,
  ports_profile_id int,
  notes text,
  adjusted_price_usd numeric(10,2),
  score_cpu_multi float, score_cpu_single float, score_gpu float,
  score_composite float,
  dollar_per_cpu_mark float, dollar_per_single_mark float,
  perf_per_watt float,
  explain_json jsonb
);


⸻

Appendix B — Component Library Map
	•	Layout: shadcn/ui AppShell, Sidebar, TopNav, ThemeToggle.
	•	Cards & KPIs: Card, Badge, Stat.
	•	Tables: TanStack Table + shadcn Table, DropdownMenu for columns.
	•	Forms: shadcn Form, Input, Select, Combobox, Slider.
	•	Overlays: Radix Dialog (Add Listing), Sheet (rule edit), HoverCard (explain mini).
	•	Command Palette: cmdk for quick add/search.
	•	Charts: Tremor or Recharts (price distribution, gen share).
