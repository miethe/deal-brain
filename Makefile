.PHONY: help setup up down api web lint format test migrate seed seed-test security-audit load-test test-playwright test-s3 warm-cache

help:
	@echo "Available targets: setup, up, down, api, web, lint, format, test, migrate, seed, seed-test, security-audit, load-test, test-playwright, test-s3, warm-cache"

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

test-playwright:
	@echo "Testing Playwright browser setup..."
	@docker-compose exec api python -c "from dealbrain_api.tasks.card_images import test_playwright; import json; print(json.dumps(test_playwright(), indent=2))"

test-s3:
	@echo "Testing S3 connectivity..."
	@docker-compose exec api python -c "import boto3; from dealbrain_api.settings import get_settings; s = get_settings(); c = boto3.client('s3', region_name=s.s3.region, endpoint_url=s.s3.endpoint_url); c.put_object(Bucket=s.s3.bucket_name, Key='card-images/test.txt', Body=b'test', ContentType='text/plain'); print('✓ Upload successful'); c.delete_object(Bucket=s.s3.bucket_name, Key='card-images/test.txt'); print('✓ Cleanup successful')"

warm-cache:
	@echo "Triggering cache warm-up for top 100 listings..."
	@docker-compose exec api python -c "from dealbrain_api.tasks.card_images import warm_cache_top_listings; import json; print(json.dumps(warm_cache_top_listings(limit=100), indent=2))"

