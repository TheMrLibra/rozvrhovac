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

create-school: ## Create a new school (usage: make create-school TENANT_SLUG="default-school" NAME="School Name" CODE="SCHOOL002" [CREATE_ADMIN=--create-admin])
	docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_school --tenant-slug "$(TENANT_SLUG)" --name "$(NAME)" --code "$(CODE)" $(CREATE_ADMIN) $(if $(ADMIN_EMAIL),--admin-email "$(ADMIN_EMAIL)") $(if $(ADMIN_PASSWORD),--admin-password "$(ADMIN_PASSWORD)")

list-tenants: ## List all tenants and their schools
	docker-compose -f docker-compose.dev.yml exec backend python -m scripts.list_tenants

migrate-dev: ## Run database migrations in dev (requires MIGRATION_DEFAULT_TENANT_ID)
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

migrate-prod: ## Run database migrations in prod (requires MIGRATION_DEFAULT_TENANT_ID)
	@echo "Creating database if it doesn't exist..."
	@docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='rozvrhovac'" | grep -q 1 || docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -c "CREATE DATABASE rozvrhovac;"
	docker compose -f docker-compose.prod.yml exec -w /app backend alembic upgrade head

migrate-prod-to-tenants: ## Run migrations up to tenants table creation (before creating first tenant)
	@echo "Creating database if it doesn't exist..."
	@docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='rozvrhovac'" | grep -q 1 || docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -c "CREATE DATABASE rozvrhovac;"
	docker compose -f docker-compose.prod.yml exec -w /app backend alembic upgrade 316b16895072

prod-create-db: ## Create the database in production
	docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -c "CREATE DATABASE rozvrhovac;" || echo "Database may already exist"

dev-up: ## Start development services and run complete setup
	@./scripts/dev-setup.sh

dev-down: ## Stop development services
	docker-compose -f docker-compose.dev.yml down

rebuild-backend: ## Rebuild backend container (dev)
	docker compose -f docker-compose.dev.yml build backend
	docker compose -f docker-compose.dev.yml up -d backend
	@echo "Backend rebuilt and restarted."

rebuild-backend-no-cache: ## Rebuild backend container without cache (dev)
	docker compose -f docker-compose.dev.yml build --no-cache backend
	docker compose -f docker-compose.dev.yml up -d backend
	@echo "Backend rebuilt (no cache) and restarted."

rebuild-backend-prod: ## Rebuild backend container in production
	docker compose -f docker-compose.prod.yml build backend
	docker compose -f docker-compose.prod.yml up -d backend
	@echo "Backend rebuilt and restarted in production."

rebuild-frontend-prod: ## Rebuild frontend container in production
	docker compose -f docker-compose.prod.yml build frontend
	docker compose -f docker-compose.prod.yml up -d frontend
	@echo "Frontend rebuilt and restarted in production."

rebuild-all-prod: ## Rebuild all containers in production
	docker compose -f docker-compose.prod.yml build
	docker compose -f docker-compose.prod.yml up -d
	@echo "All services rebuilt and restarted in production."

recreate-backend-prod: ## Recreate backend container to reload .env.prod
	docker compose -f docker-compose.prod.yml up -d --force-recreate backend
	@echo "Backend container recreated. Environment variables reloaded."

prod-up: ## Start production services
	docker compose -f docker-compose.prod.yml up -d
	@echo "Production services started."

prod-down: ## Stop production services
	docker compose -f docker-compose.prod.yml down

prod-create-tenant: ## Create a tenant in production (usage: make prod-create-tenant NAME="Tenant Name" SLUG="tenant-slug")
	docker compose -f docker-compose.prod.yml exec -w /app backend python -m scripts.seed_tenant --name "$(NAME)" --slug "$(SLUG)"

prod-create-school: ## Create a school in production (usage: make prod-create-school TENANT_SLUG="slug" NAME="School Name" CODE="SCHOOL001" [CREATE_ADMIN=--create-admin] [ADMIN_EMAIL="email"] [ADMIN_PASSWORD="pass"])
	docker compose -f docker-compose.prod.yml exec -w /app backend python -m scripts.create_school --tenant-slug "$(TENANT_SLUG)" --name "$(NAME)" --code "$(CODE)" $(CREATE_ADMIN) $(if $(ADMIN_EMAIL),--admin-email "$(ADMIN_EMAIL)") $(if $(ADMIN_PASSWORD),--admin-password "$(ADMIN_PASSWORD)")

prod-create-admin: ## Create admin user in production (usage: make prod-create-admin TENANT_SLUG="slug" EMAIL="email" PASSWORD="pass" SCHOOL_CODE="SCHOOL001")
	docker compose -f docker-compose.prod.yml exec -w /app backend python -m scripts.create_admin_user --tenant-slug "$(TENANT_SLUG)" --email "$(EMAIL)" --password "$(PASSWORD)" --school-code "$(SCHOOL_CODE)"

prod-list-tenants: ## List tenants in production
	docker compose -f docker-compose.prod.yml exec -w /app backend python -m scripts.list_tenants

prod-create-test-data: ## Create test data in production (usage: make prod-create-test-data TENANT_SLUG="slug" SCHOOL_CODE="SCHOOL001" [FORCE=--force])
	docker compose -f docker-compose.prod.yml exec -w /app backend python -m scripts.create_test_data --tenant-slug "$(TENANT_SLUG)" --school-code "$(SCHOOL_CODE)" $(FORCE)

prod-check-db: ## Check database connection in production
	docker compose -f docker-compose.prod.yml exec -w /app backend python -c "import asyncio; from app.core.database import AsyncSessionLocal; async def test(): async with AsyncSessionLocal() as db: await db.execute('SELECT 1'); print('✅ Database connection OK'); asyncio.run(test())"

prod-check-env: ## Check environment variables in production backend
	docker compose -f docker-compose.prod.yml exec backend printenv | grep -E "MIGRATION_DEFAULT_TENANT_ID|ENV|DB_"

prod-migration-status: ## Check migration status in production
	docker compose -f docker-compose.prod.yml exec -w /app backend alembic current

prod-migration-history: ## Show migration history in production
	docker compose -f docker-compose.prod.yml exec -w /app backend alembic history

prod-logs-backend: ## View backend logs in production
	docker compose -f docker-compose.prod.yml logs backend --tail=50 -f

prod-logs-postgres: ## View PostgreSQL logs in production
	docker compose -f docker-compose.prod.yml logs postgres --tail=50 -f

