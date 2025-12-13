.PHONY: help up up-prod down down-prod logs logs-prod migrate shell-db shell-backend clean init-registry create-school create-admin

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

# Production targets
up-prod: ## Start production services
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo "Production services started."
	@echo "Run 'make init-registry' to initialize registry database."

down-prod: ## Stop production services
	docker-compose -f docker-compose.prod.yml --env-file .env.prod down

logs-prod: ## View production logs
	docker-compose -f docker-compose.prod.yml --env-file .env.prod logs -f

rebuild-prod: ## Rebuild and restart production services
	docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

status-prod: ## Show production services status
	docker-compose -f docker-compose.prod.yml --env-file .env.prod ps

# Multi-tenant setup targets
init-registry: ## Initialize registry database
	docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.init_registry_db

create-school: ## Create a new school (usage: make create-school NAME="School Name" CODE="SCHOOL001")
	docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_school --name "$(NAME)" --code "$(CODE)"

create-admin: ## Create admin user (usage: make create-admin CODE="SCHOOL001" EMAIL="admin@school.local" PASSWORD="password")
	docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_admin_user --school-code "$(CODE)" --email "$(EMAIL)" --password "$(PASSWORD)"

