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

