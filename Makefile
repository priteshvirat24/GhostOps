.PHONY: help dev build test db-init migrate seed clean lint api web

help:
	@echo "GhostOps Monorepo Commands:"
	@echo "  make dev         - Start all services with Docker Compose"
	@echo "  make api         - Run FastAPI backend locally"
	@echo "  make web         - Run Next.js frontend locally"
	@echo "  make db-init     - Initialize CockroachDB database schema"
	@echo "  make migrate     - Run database migrations using Alembic"
	@echo "  make seed        - Populate test seed data"
	@echo "  make test        - Run backend unit & integration tests"
	@echo "  make lint        - Run linters across packages"
	@echo "  make clean       - Clean temporary build & cache files"

dev:
	docker-compose up --build

api:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

db-init:
	python scripts/seed_db.py --init-only

migrate:
	alembic upgrade head

seed:
	python scripts/seed_db.py

test:
	cd apps/api && pytest -v

lint:
	cd apps/api && ruff check . || flake8 . || true

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
