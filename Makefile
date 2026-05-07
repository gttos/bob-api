.PHONY: help up down build restart logs shell test test-unit test-integration test-properties migrate migration logs-api logs-worker ps

# Default target
help:
	@echo ""
	@echo "Interior AI Backend — Available commands:"
	@echo ""
	@echo "  STACK"
	@echo "  make up           Start all services (build if needed)"
	@echo "  make build        Rebuild all images"
	@echo "  make down         Stop and remove containers"
	@echo "  make restart      Restart all services"
	@echo "  make ps           Show running containers"
	@echo ""
	@echo "  LOGS"
	@echo "  make logs         Tail all logs"
	@echo "  make logs-api     Tail API logs only"
	@echo "  make logs-worker  Tail Celery worker logs only"
	@echo ""
	@echo "  DATABASE"
	@echo "  make migrate      Run pending migrations"
	@echo "  make migration m='description'  Create new migration"
	@echo "  make db-refresh   Drop all tables and re-run migrations (fresh DB)"
	@echo ""
	@echo "  TESTING"
	@echo "  make test         Run all tests"
	@echo "  make test-unit    Run unit tests only"
	@echo "  make test-int     Run integration tests only"
	@echo "  make test-props   Run property-based tests only"
	@echo ""
	@echo "  SHELL"
	@echo "  make shell        Open bash shell in API container"
	@echo ""

# ─── Stack ────────────────────────────────────────────────────────────────────

up:
	docker compose up

build:
	docker compose up --build

down:
	docker compose down

down-v:
	docker compose down -v

restart:
	docker compose restart

ps:
	docker compose ps

# ─── Logs ─────────────────────────────────────────────────────────────────────

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f celery-worker

# ─── Database ─────────────────────────────────────────────────────────────────

migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

migrate-down:
	docker compose exec api alembic downgrade -1

db-refresh:
	docker compose exec db psql -U interiorai -d interiorai_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker compose exec api alembic upgrade head

# ─── Testing ──────────────────────────────────────────────────────────────────

test:
	docker compose exec api pytest tests/ -v

test-unit:
	docker compose exec api pytest tests/unit/ -v

test-int:
	docker compose exec api pytest tests/integration/ -v

test-props:
	docker compose exec api pytest tests/properties/ -v

test-e2e:
	docker compose exec api pytest tests/integration/test_e2e_flows.py -v

test-cov:
	docker compose exec api pytest tests/ --cov=app --cov-report=term-missing

# ─── Shell ────────────────────────────────────────────────────────────────────

shell:
	docker compose exec api bash

# ─── Redis / Queue ────────────────────────────────────────────────────────────

queue:
	docker compose exec redis redis-cli LLEN celery

queue-list:
	docker compose exec redis redis-cli LRANGE celery 0 -1

queue-flush:
	docker compose exec redis redis-cli DEL celery
