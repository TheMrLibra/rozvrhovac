.PHONY: help up down logs migrate shell-db shell-backend clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services (database, backend, frontend)
	docker-compose up -d
	@echo "Services started. Run 'make migrate' to set up the database."

up-dev: ## Start database and backend only (for local frontend development)
	docker-compose -f docker-compose.dev.yml up -d postgres backend
	@echo "Database and backend started. Run frontend locally with: cd frontend && npm run dev"

down: ## Stop all services
	docker-compose down

down-dev: ## Stop development services
	docker-compose -f docker-compose.dev.yml down

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-db: ## View database logs
	docker-compose logs -f postgres

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create NAME=description)
	docker-compose exec backend alembic revision --autogenerate -m "$(NAME)"

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d rozvrhovac

shell-backend: ## Open backend container shell
	docker-compose exec backend /bin/bash

clean: ## Stop services and remove volumes (WARNING: deletes database data)
	docker-compose down -v
	@echo "All services stopped and volumes removed."

rebuild: ## Rebuild and restart all services
	docker-compose up --build -d

status: ## Show status of all services
	docker-compose ps

seed: ## Seed initial data (school, users)
	docker-compose -f docker-compose.dev.yml exec backend python -m scripts.seed_data

seed-tenant: ## Create a default tenant (usage: make seed-tenant NAME="Default School" SLUG="default-school")
	docker-compose -f docker-compose.dev.yml exec backend python -m scripts.seed_tenant --name "$(NAME)" --slug "$(SLUG)"

create-test-data: ## Create comprehensive test data (usage: make create-test-data TENANT_SLUG="default-school" SCHOOL_CODE="SCHOOL001" [FORCE=--force])
	docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_test_data --tenant-slug "$(TENANT_SLUG)" --school-code "$(SCHOOL_CODE)" $(FORCE)

migrate-dev: ## Run database migrations in dev (requires MIGRATION_DEFAULT_TENANT_ID)
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

migrate-prod: ## Run database migrations in prod (requires MIGRATION_DEFAULT_TENANT_ID)
	docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

dev-up: ## Start development services and run complete setup
	@./scripts/dev-setup.sh

dev-down: ## Stop development services
	docker-compose -f docker-compose.dev.yml down

rebuild-backend: ## Rebuild backend container (dev)
	docker-compose -f docker-compose.dev.yml build backend
	docker-compose -f docker-compose.dev.yml up -d backend
	@echo "Backend rebuilt and restarted."

rebuild-backend-no-cache: ## Rebuild backend container without cache (dev)
	docker-compose -f docker-compose.dev.yml build --no-cache backend
	docker-compose -f docker-compose.dev.yml up -d backend
	@echo "Backend rebuilt (no cache) and restarted."

prod-up: ## Start production services
	docker-compose -f docker-compose.prod.yml up -d
	@echo "Production services started."

prod-down: ## Stop production services
	docker-compose -f docker-compose.prod.yml down

