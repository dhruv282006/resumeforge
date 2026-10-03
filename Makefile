# =============================================================================
# ResumeForge – Makefile
# =============================================================================
# Usage:  make <target>
# Run `make help` (or just `make`) for a full list of available targets.
#
# Requirements: GNU Make, Docker, Docker Compose v2, Python 3.11+, Node.js 20+
# =============================================================================

.DEFAULT_GOAL := help

# Colours for terminal output
CYAN  := \033[0;36m
GREEN := \033[0;32m
YELLOW:= \033[0;33m
RESET := \033[0m

DOCKER_COMPOSE := docker compose
BACKEND_DIR    := apps/backend
FRONTEND_DIR   := apps/frontend
SCRIPTS_DIR    := scripts

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
## Show this help message (default target)
help:
	@echo ""
	@echo "$(CYAN)ResumeForge – Available Make Targets$(RESET)"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*##"; printf ""} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  $(GREEN)%-22s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
##@ Setup & Infrastructure
# =============================================================================

.PHONY: setup
## First-time project setup: copy .env.example → .env, pull Docker images
setup:
	@echo "$(CYAN)Running first-time setup...$(RESET)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✔ Created .env from .env.example — edit it with your values.$(RESET)"; \
	else \
		echo "$(YELLOW)⚠ .env already exists — skipping copy.$(RESET)"; \
	fi
	$(DOCKER_COMPOSE) pull postgres redis mailhog
	@echo "$(GREEN)✔ Setup complete. Run 'make up-infra' to start infrastructure.$(RESET)"

.PHONY: up
## Start ALL Docker services (infra + backend + frontend)
up:
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✔ All services started. Run 'make health' to verify.$(RESET)"

.PHONY: up-infra
## Start infrastructure only (postgres, redis, mailhog)
up-infra:
	$(DOCKER_COMPOSE) up -d postgres redis mailhog
	@echo "$(GREEN)✔ Infrastructure services started.$(RESET)"

.PHONY: down
## Stop all running services (preserves volumes)
down:
	$(DOCKER_COMPOSE) down

.PHONY: down-volumes
## Stop all services and remove volumes — WARNING: destroys all data!
down-volumes:
	@echo "$(YELLOW)WARNING: This will permanently delete all database data!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) down -v

.PHONY: logs
## Tail logs for all services
logs:
	$(DOCKER_COMPOSE) logs -f

.PHONY: logs-backend
## Tail backend (FastAPI) logs
logs-backend:
	$(DOCKER_COMPOSE) logs -f backend

.PHONY: logs-worker
## Tail Celery worker logs
logs-worker:
	$(DOCKER_COMPOSE) logs -f celery_worker

.PHONY: ps
## Show status of all Docker Compose services
ps:
	$(DOCKER_COMPOSE) ps

# =============================================================================
##@ Database
# =============================================================================

.PHONY: migrate
## Run all pending Alembic migrations
migrate:
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

.PHONY: migrate-create
## Create a new Alembic migration (usage: make migrate-create name="add_users_table")
migrate-create:
	@if [ -z "$(name)" ]; then \
		echo "$(YELLOW)Usage: make migrate-create name=\"your_migration_name\"$(RESET)"; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec backend alembic revision --autogenerate -m "$(name)"

.PHONY: db-reset
## Drop and recreate the database (development only — destroys data!)
db-reset:
	@echo "$(YELLOW)WARNING: This will DROP and recreate the '$(POSTGRES_DB)' database!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(DOCKER_COMPOSE) exec postgres psql -U $${POSTGRES_USER:-resumeforge} -c "DROP DATABASE IF EXISTS $${POSTGRES_DB:-resumeforge};"
	$(DOCKER_COMPOSE) exec postgres psql -U $${POSTGRES_USER:-resumeforge} -c "CREATE DATABASE $${POSTGRES_DB:-resumeforge};"
	@echo "$(GREEN)✔ Database recreated. Run 'make migrate' to apply migrations.$(RESET)"

.PHONY: db-seed
## Seed the database with development data
db-seed:
	$(DOCKER_COMPOSE) exec backend python /app/$(SCRIPTS_DIR)/seed_db.py

# =============================================================================
##@ Backend
# =============================================================================

.PHONY: backend-dev
## Run the FastAPI backend locally (outside Docker) with hot-reload
backend-dev:
	cd $(BACKEND_DIR) && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: backend-test
## Run backend test suite
backend-test:
	cd $(BACKEND_DIR) && pytest tests/ -v

.PHONY: backend-lint
## Run ruff linter on backend source code
backend-lint:
	cd $(BACKEND_DIR) && ruff check app/ tests/

.PHONY: backend-format
## Auto-format backend code with ruff
backend-format:
	cd $(BACKEND_DIR) && ruff format app/ tests/

.PHONY: backend-shell
## Open an interactive shell inside the running backend container
backend-shell:
	$(DOCKER_COMPOSE) exec backend bash

# =============================================================================
##@ Frontend
# =============================================================================

.PHONY: frontend-dev
## Run the Next.js frontend locally (outside Docker)
frontend-dev:
	cd $(FRONTEND_DIR) && npm run dev

.PHONY: frontend-install
## Install frontend npm dependencies
frontend-install:
	cd $(FRONTEND_DIR) && npm install

.PHONY: frontend-build
## Build the Next.js frontend for production
frontend-build:
	cd $(FRONTEND_DIR) && npm run build

.PHONY: frontend-lint
## Run ESLint on the frontend source code
frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

.PHONY: frontend-shell
## Open an interactive shell inside the running frontend container
frontend-shell:
	$(DOCKER_COMPOSE) exec frontend sh

# =============================================================================
##@ Workers
# =============================================================================

.PHONY: worker-dev
## Run the Celery worker locally (outside Docker)
worker-dev:
	cd $(BACKEND_DIR) && celery -A app.workers.celery_app:celery_app worker --loglevel=info --concurrency=2

.PHONY: worker-shell
## Open an interactive shell inside the running Celery worker container
worker-shell:
	$(DOCKER_COMPOSE) exec celery_worker bash

# =============================================================================
##@ Testing
# =============================================================================

.PHONY: test
## Run all tests (backend + frontend)
test: test-backend frontend-lint

.PHONY: test-backend
## Run backend tests with coverage report
test-backend:
	cd $(BACKEND_DIR) && pytest tests/ --cov=app --cov-report=term-missing --cov-report=html -v

.PHONY: test-verbose
## Run backend tests with maximum verbosity
test-verbose:
	cd $(BACKEND_DIR) && pytest tests/ -vvv --tb=long

# =============================================================================
##@ Utilities
# =============================================================================

.PHONY: health
## Check health of all services (runs scripts/check_services.py)
health:
	python $(SCRIPTS_DIR)/check_services.py

.PHONY: seed
## Seed the database with development fixtures
seed:
	python $(SCRIPTS_DIR)/seed_db.py

.PHONY: clean
## Remove Python cache files, build artifacts, and test output
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✔ Cleanup complete.$(RESET)"

.PHONY: build
## Build all Docker images without using cache
build:
	$(DOCKER_COMPOSE) build --no-cache

.PHONY: rebuild
## Rebuild and restart all services
rebuild: down build up
