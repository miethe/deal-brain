.PHONY: help setup up down api web lint format test migrate seed

help:
	@echo "Available targets: setup, up, down, api, web, lint, format, test, migrate, seed"

setup:
	poetry install
	pnpm install --frozen-lockfile=false

up:
	docker-compose up --build

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

