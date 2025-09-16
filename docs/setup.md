# Deal Brain — Setup Guide

## Prerequisites
- Python 3.11+
- Node.js 20+ with pnpm (Corepack `pnpm@8.15`)
- Docker & Docker Compose

## Local Development
1. Copy `.env.example` to `.env` and adjust secrets as needed:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   make setup
   ```
3. Apply database migrations:
   ```bash
   poetry run alembic upgrade head
   ```
4. Launch the stack:
   ```bash
   make up
   ```
   Services exposed:
   - API: http://localhost:8000
   - Web: http://localhost:3000
   - Prometheus metrics: http://localhost:9090
   - Grafana: http://localhost:3001

## Seeding Data
Drop your Excel workbook in `data/imports/` and run:
```bash
poetry run dealbrain-cli import ./data/imports/deal-brain.xlsx
```
The importer normalizes CPUs, GPUs, valuation rules, profiles, and listings.

## Useful Commands
- `make api` – run the FastAPI server with reload
- `make web` – run Next.js dev server
- `make lint` / `make format`
- `make test`

## Running Tests
```bash
poetry run pytest
```

Playwright tests will be added once the UI flows stabilize.
