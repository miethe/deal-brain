.PHONY: help setup up down api web lint format test migrate seed seed-test security-audit load-test

help:
	@echo "Available targets: setup, up, down, api, web, lint, format, test, migrate, seed, seed-test, security-audit, load-test"

setup:
	poetry install
	pnpm install --frozen-lockfile=false

up:
	docker-compose up --build -d

down:
	docker-compose down

api:
	poetry run dealbrain-api

web:
	pnpm --filter web dev

lint:
	poetry run ruff check .
	pnpm --filter web lint

format:
	poetry run black .
	poetry run isort .
	pnpm --filter web lint --fix

test:
	poetry run pytest

migrate:
	poetry run alembic upgrade head

seed:
	poetry run python -m dealbrain_api.seeds

seed-test:
	poetry run python scripts/seed_test_data.py

security-audit:
	poetry run python scripts/security_audit.py

load-test:
	poetry run python scripts/load_test.py

