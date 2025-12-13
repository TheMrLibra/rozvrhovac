# Detect docker-compose command (supports both docker-compose and docker compose)
# Use wrapper script for reliable detection
DOCKER_COMPOSE := $(shell if [ -f ./docker-compose-wrapper.sh ]; then echo "./docker-compose-wrapper.sh"; elif docker compose version >/dev/null 2>&1; then echo "docker compose"; elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

.PHONY: help up up-prod up-prod-vm down down-prod logs logs-prod migrate shell-db shell-backend clean init-registry init-registry-vm create-school create-school-vm create-admin create-admin-vm

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services (database, backend, frontend)
	$(DOCKER_COMPOSE) up -d
	@echo "Services started. Run 'make migrate' to set up the database."

up-dev: ## Start database and backend only (for local frontend development)
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d postgres backend
	@echo "Database and backend started. Run frontend locally with: cd frontend && npm run dev"

down: ## Stop all services
	$(DOCKER_COMPOSE) down

down-dev: ## Stop development services
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

logs: ## View logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-backend: ## View backend logs
	$(DOCKER_COMPOSE) logs -f backend

logs-db: ## View database logs
	$(DOCKER_COMPOSE) logs -f postgres

migrate: ## Run database migrations
	$(DOCKER_COMPOSE) exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create NAME=description)
	$(DOCKER_COMPOSE) exec backend alembic revision --autogenerate -m "$(NAME)"

shell-db: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d rozvrhovac

shell-backend: ## Open backend container shell
	$(DOCKER_COMPOSE) exec backend /bin/bash

clean: ## Stop services and remove volumes (WARNING: deletes database data)
	$(DOCKER_COMPOSE) down -v
	@echo "All services stopped and volumes removed."

rebuild: ## Rebuild and restart all services
	$(DOCKER_COMPOSE) up --build -d

status: ## Show status of all services
	$(DOCKER_COMPOSE) ps

seed: ## Seed initial data (school, users)
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml exec backend python -m scripts.seed_data

# Production targets
up-prod: ## Start production services (with nginx)
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod up -d
	@echo "Production services started."
	@echo "Run 'make init-registry' to initialize registry database."

up-prod-vm: ## Start production services (VM architecture - no nginx)
	$(DOCKER_COMPOSE) -f docker-compose.prod.vm.yml --env-file .env.prod up -d
	@echo "Production services started (VM architecture)."
	@echo "Run 'make init-registry-vm' to initialize registry database."

down-prod: ## Stop production services
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod down

logs-prod: ## View production logs
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod logs -f

rebuild-prod: ## Rebuild and restart production services
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod up -d --build

status-prod: ## Show production services status
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod ps

# Multi-tenant setup targets
init-registry: ## Initialize registry database
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/init_registry_db.py

init-registry-vm: ## Initialize registry database (VM architecture)
	$(DOCKER_COMPOSE) -f docker-compose.prod.vm.yml --env-file .env.prod exec backend python scripts/init_registry_db.py

create-school: ## Create a new school (usage: make create-school NAME="School Name" CODE="SCHOOL001")
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/create_school.py --name "$(NAME)" --code "$(CODE)"

create-school-vm: ## Create a new school (VM architecture) (usage: make create-school-vm NAME="School Name" CODE="SCHOOL001")
	$(DOCKER_COMPOSE) -f docker-compose.prod.vm.yml --env-file .env.prod exec backend python scripts/create_school.py --name "$(NAME)" --code "$(CODE)"

create-admin: ## Create admin user (usage: make create-admin CODE="SCHOOL001" EMAIL="admin@school.local" PASSWORD="password")
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/create_admin_user.py --school-code "$(CODE)" --email "$(EMAIL)" --password "$(PASSWORD)"

create-admin-vm: ## Create admin user (VM architecture) (usage: make create-admin-vm CODE="SCHOOL001" EMAIL="admin@school.local" PASSWORD="password")
	$(DOCKER_COMPOSE) -f docker-compose.prod.vm.yml --env-file .env.prod exec backend python scripts/create_admin_user.py --school-code "$(CODE)" --email "$(EMAIL)" --password "$(PASSWORD)"

