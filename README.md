# Deal Brain

A full-stack price-to-performance assistant for small form factor PCs. The MVP ships with a FastAPI backend, React/Next.js frontend, Typer CLI, and Docker-based infrastructure so you can import your spreadsheet, normalize listings, and browse ranked deals with explainable scoring.

## Highlights
- **FastAPI + SQLAlchemy** backend with valuation engine, scoring profiles, and REST endpoints.
- **Next.js App Router** frontend featuring dashboard KPIs, listings table, detail explain view, profiles gallery, and import workflow.
- **CLI** commands for importing the Excel workbook, adding listings, exporting top picks, and inspecting valuation breakdowns.
- **Docker Compose** stack bundling Postgres, Redis, API, web, Celery worker, OTLP collector, Prometheus, and Grafana.
- **Shared domain package** (`packages/core`) so API, CLI, and future workers share schemas, scoring, and valuation logic.

## Getting Started
See `docs/setup.md` for environment setup, running the stack, and seeding data from your Excel workbook.

## Key Commands
```bash
make setup       # install dependencies
make up          # run docker-compose stack
make api         # run FastAPI with reload
make web         # run Next.js dev server
poetry run dealbrain-cli --help
```

## Docs
- `docs/architecture.md` – system overview
- `docs/valuation-rules.md` – how adjusted price rules work
- `docs/setup.md` – setup & workflows

## Roadmap
- Finish UI editing flows (profiles, valuation rules, listing edit)
- Flesh out automated tests (API + Playwright)
- Expand observability dashboards and Celery task orchestration
