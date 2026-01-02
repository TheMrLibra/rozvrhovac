# Rozvrhovac - Multi-Tenant School Timetable Management System

A production-ready multi-tenant web application for schools that generates permanent timetables and handles automatic substitutions.

## Table of Contents

- [Architecture](#architecture)
- [Quick Start (Local Development)](#quick-start-local-development)
- [Production Deployment](#production-deployment)
- [Useful Commands](#useful-commands)
- [Features](#features)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## Architecture

### Technology Stack

**Backend:**
- **Framework**: FastAPI (Python 3.11+)
- **Architecture**: 3-layer (Routers → Services → Repositories)
- **Database**: PostgreSQL 15+ with SQLAlchemy (async)
- **Migrations**: Alembic
- **Authentication**: JWT (Access + Refresh tokens)
- **Multi-tenancy**: Single database with tenant-scoped data isolation

**Frontend:**
- **Framework**: Vue 3 + TypeScript
- **Build Tool**: Vite
- **State Management**: Pinia
- **Styling**: SCSS with BEM methodology
- **HTTP Client**: Axios with automatic tenant header injection

**Deployment:**
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx (production)
- **Orchestration**: Kubernetes-ready (manifests included)

### Multi-Tenancy Architecture

The application uses a **single PostgreSQL database** with tenant-scoped data isolation:

- **Tenant Model**: Each tenant represents an organization (e.g., a school district)
- **School Model**: Each tenant can have multiple schools
- **Data Isolation**: All tenant-owned tables include `tenant_id` UUID column
- **Automatic Tenant Resolution**: Tenant determined from user email during login
- **Tenant Filtering**: All queries automatically filtered by `tenant_id` at the repository level

**Tenant Resolution Priority:**
1. From authenticated user's `tenant_id`
2. From `X-Tenant` header (UUID or slug)
3. From `DEFAULT_TENANT_SLUG` environment variable (dev only)
4. Raise 400 error if tenant cannot be resolved (production)

**Tenant-Owned Entities:**
- Users, Schools, Teachers, Subjects, ClassGroups, Classrooms, GradeLevels
- Timetables, TimetableEntries, TeacherAbsences, Substitutions, SchoolSettings

### Authentication Flow

Users log in from a single page without specifying tenant. The system automatically:

1. Searches user by email across all tenants
2. Verifies password
3. Returns tenant and school information in login response
4. Stores tenant/school info in localStorage
5. Automatically includes `X-Tenant` header in all subsequent requests

**Login Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "tenant_id": "uuid",
  "tenant_slug": "school-slug",
  "school_id": 4,
  "school_name": "School Name"
}
```

## Quick Start (Local Development)

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Make (optional, but recommended)

### One-Command Setup

```bash
# This single command does everything:
# - Starts Docker services (database, backend)
# - Runs migrations
# - Creates default tenant
# - Creates school and admin user
make dev-up
```

**Default Credentials:**
- Email: `admin@school.example`
- Password: `admin123`

### Start Frontend

```bash
cd frontend

# Switch to correct Node.js version (if using nvm)
nvm use

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Access Points:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: `localhost:5432` (user: `postgres`, password: `postgres`)

### Create Test Data

```bash
# Generate comprehensive test data (grade levels, classes, subjects, teachers, etc.)
make create-test-data TENANT_SLUG="default-school" SCHOOL_CODE="SCHOOL001"
```

This creates:
- 4 Grade Levels (1st-4th Grade)
- 10 Class Groups
- 10 Subjects
- 18 Teachers with capabilities
- 17 Classrooms
- 66 Class Subject Allocations

## Production Deployment

### Prerequisites

- Docker and Docker Compose installed on server
- Domain name configured (optional, for subdomains)
- SSL certificates (for HTTPS)

### Step 1: Environment Setup

Create `.env.prod` file:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=<strong-password>
DATABASE_URL=postgresql+asyncpg://postgres:<password>@postgres:5432/rozvrhovac

# Application
ENV=prod
PROJECT_NAME=Rozvrhovac
API_V1_STR=/api/v1

# JWT Security
SECRET_KEY=<generate-strong-random-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (comma-separated list of allowed origins)
CORS_ORIGINS=https://app.yourdomain.com,https://api.yourdomain.com

# Multi-tenancy
MIGRATION_DEFAULT_TENANT_ID=<uuid-of-first-tenant-for-migrations>
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Deploy Services

```bash
# Start production services
make prod-up

# Or manually:
docker compose -f docker-compose.prod.yml up -d
```

### Step 3: Create First Tenant

```bash
# Create a tenant
make prod-create-tenant NAME="First School" SLUG="first-school"

# Note the tenant UUID from output, add to .env.prod:
# MIGRATION_DEFAULT_TENANT_ID=<tenant-uuid>

# Recreate backend to reload environment variables
make recreate-backend-prod
```

### Step 4: Run Database Migrations

```bash
# Run migrations (will use MIGRATION_DEFAULT_TENANT_ID from .env.prod)
make migrate-prod
```

### Step 5: Create School with Admin

```bash
# Create school with admin user in one command
make prod-create-school \
  TENANT_SLUG="first-school" \
  NAME="My School" \
  CODE="SCHOOL001" \
  CREATE_ADMIN=--create-admin \
  ADMIN_EMAIL="admin@myschool.example" \
  ADMIN_PASSWORD="SecurePassword123!"
```

### Step 6: Build Frontend

```bash
# Rebuild frontend with production API URL
make rebuild-frontend-prod

# Or manually (set VITE_API_URL in docker-compose.prod.yml):
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Step 7: Verify Deployment

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# Check backend logs
make prod-logs-backend

# Test health endpoint
curl http://localhost:8000/health

# List tenants
make prod-list-tenants
```

### Complete Onboarding Workflow

For a new customer/school:

```bash
# 1. Create tenant (if new organization)
make prod-create-tenant NAME="Customer Name" SLUG="customer-slug"

# 2. Create school with admin
make prod-create-school \
  TENANT_SLUG="customer-slug" \
  NAME="School Name" \
  CODE="SCHOOL001" \
  CREATE_ADMIN=--create-admin \
  ADMIN_EMAIL="admin@school.example" \
  ADMIN_PASSWORD="SecurePassword123!"

# 3. (Optional) Create test data
make prod-create-test-data TENANT_SLUG="customer-slug" SCHOOL_CODE="SCHOOL001"
```

The user can now log in - the system automatically determines their tenant and school from their email!

## Useful Commands

### Development Commands

```bash
# Start development environment (one command setup)
make dev-up

# Stop development services
make dev-down

# Run database migrations
make migrate-dev

# Rebuild backend container
make rebuild-backend

# Create test data
make create-test-data TENANT_SLUG="default-school" SCHOOL_CODE="SCHOOL001"

# Create a new school
make create-school TENANT_SLUG="default-school" NAME="School Name" CODE="SCHOOL002"

# List all tenants and schools
make list-tenants

# View logs
make logs-backend
make logs-db

# Open database shell
make shell-db

# Open backend container shell
make shell-backend
```

### Production Commands

```bash
# Start/stop production services
make prod-up
make prod-down

# Run migrations
make migrate-prod

# Create tenant
make prod-create-tenant NAME="Tenant Name" SLUG="tenant-slug"

# Create school with admin
make prod-create-school \
  TENANT_SLUG="slug" \
  NAME="School Name" \
  CODE="SCHOOL001" \
  CREATE_ADMIN=--create-admin \
  ADMIN_EMAIL="email" \
  ADMIN_PASSWORD="password"

# Create admin user
make prod-create-admin \
  TENANT_SLUG="slug" \
  EMAIL="email" \
  PASSWORD="password" \
  SCHOOL_CODE="SCHOOL001"

# List tenants
make prod-list-tenants

# Rebuild containers
make rebuild-backend-prod
make rebuild-frontend-prod
make rebuild-all-prod

# Check environment variables
make prod-check-env

# Check migration status
make prod-migration-status

# View logs
make prod-logs-backend
make prod-logs-postgres
```

### Database Commands

```bash
# Create migration
make migrate-create NAME="description"

# Run migrations
make migrate-dev          # Development
make migrate-prod         # Production

# Check migration status
make prod-migration-status
```

### Utility Commands

```bash
# Show all available commands
make help

# Clean everything (removes database data)
make clean

# Check service status
make status
```

## Features

### Core Features

- ✅ **Multi-tenant architecture** with automatic tenant detection
- ✅ **JWT authentication** with role-based access control
- ✅ **Timetable generation** using heuristic algorithm
- ✅ **Timetable validation** (constraints checking)
- ✅ **Automatic substitution generation** for teacher absences
- ✅ **CRUD operations** for all entities
- ✅ **Multiple schools per tenant** support
- ✅ **Teacher capabilities** by grade level
- ✅ **Class-subject allocations** with weekly hour requirements

### User Roles

- **ADMIN**: Full access to all features (create/edit/delete)
- **TEACHER**: View own timetable, report absences
- **SCHOLAR**: View class timetable

## Project Structure

```
rozvrhovac/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routers
│   │   ├── core/             # Core configuration (database, security, tenant context)
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer (tenant-aware)
│   │   ├── schemas/          # Pydantic DTOs
│   │   └── services/         # Business logic
│   ├── alembic/              # Database migrations
│   ├── scripts/               # Utility scripts (create_admin_user, seed_tenant, etc.)
│   ├── tests/                 # Test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # Vue components
│   │   ├── views/            # Vue views/pages
│   │   ├── stores/           # Pinia stores (auth, alert, i18n)
│   │   ├── services/         # API services
│   │   ├── composables/      # Reusable composables (useAlert, etc.)
│   │   └── router/           # Vue Router
│   ├── package.json
│   └── Dockerfile
├── nginx/                     # Nginx configuration
├── k8s/                       # Kubernetes manifests
├── scripts/                   # Setup scripts
├── docker-compose.dev.yml     # Development Docker Compose
├── docker-compose.prod.yml    # Production Docker Compose
└── Makefile                   # Convenience commands
```

## API Documentation

### Authentication

- `POST /api/v1/auth/login` - Login (no tenant header needed)
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

### Timetables

- `POST /api/v1/timetables/schools/{school_id}/timetables/generate` - Generate timetable
- `POST /api/v1/timetables/schools/{school_id}/timetables/{timetable_id}/validate` - Validate timetable
- `GET /api/v1/timetables/schools/{school_id}/timetables` - List timetables
- `GET /api/v1/timetables/schools/{school_id}/timetables/{timetable_id}` - Get timetable
- `DELETE /api/v1/timetables/schools/{school_id}/timetables/{timetable_id}` - Delete timetable

### Substitutions

- `POST /api/v1/timetables/schools/{school_id}/timetables/{timetable_id}/generate-substitute` - Generate substitute timetable

### Entities

- `GET /api/v1/teachers/schools/{school_id}/teachers` - List teachers
- `GET /api/v1/subjects/class-subject-allocations` - List class-subject allocations
- `GET /api/v1/class-groups/schools/{school_id}/class-groups` - List class groups
- `GET /api/v1/schools/{school_id}/settings` - Get school settings

**Interactive API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Backend Issues

**Backend not responding:**
```bash
# Check status
docker compose -f docker-compose.dev.yml ps

# View logs
make logs-backend

# Restart
docker compose -f docker-compose.dev.yml restart backend
```

**Migration fails with "MIGRATION_DEFAULT_TENANT_ID must be set":**
1. Create a tenant: `make seed-tenant NAME="Default School" SLUG="default-school"`
2. Copy UUID from output
3. Set in environment: `export MIGRATION_DEFAULT_TENANT_ID=<uuid>`
4. Run migrations again: `make migrate-dev`

**Tenant not found errors:**
- Verify tenant exists: `make list-tenants`
- Create tenant if missing: `make seed-tenant NAME="Name" SLUG="slug"`

### Frontend Issues

**Frontend not accessible:**
1. Check Node.js version (requires 18+):
   ```bash
   node --version
   ```

2. Switch to correct version (if using nvm):
   ```bash
   cd frontend
   nvm use
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Check port availability:
   ```bash
   lsof -i :5173
   ```

**"crypto.getRandomValues is not a function" error:**
- Upgrade Node.js to version 18 or higher

### Database Issues

**Connection errors:**
```bash
# Check PostgreSQL is running
docker compose -f docker-compose.dev.yml ps postgres

# Test connection
docker compose -f docker-compose.dev.yml exec postgres psql -U postgres -d rozvrhovac -c "SELECT 1;"
```

**Can't login / No users:**
```bash
# Create admin user
docker compose -f docker-compose.dev.yml exec backend python -m scripts.create_admin_user \
  --tenant-slug default-school \
  --email admin@school.example \
  --password admin123 \
  --school-code SCHOOL001
```

### Production Issues

**Environment variables not loading:**
```bash
# Recreate backend container to reload .env.prod
make recreate-backend-prod

# Verify environment variables
make prod-check-env
```

**Frontend build fails:**
- Check npm authentication: Remove any `.npmrc` files
- Verify `VITE_API_URL` is set correctly in `docker-compose.prod.yml`
- Check build logs: `docker compose -f docker-compose.prod.yml logs frontend`

**Database password authentication failed:**
- Verify `DB_PASSWORD` in `.env.prod` matches PostgreSQL container password
- Reset PostgreSQL password if needed:
  ```bash
  docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -c "ALTER USER postgres WITH PASSWORD 'your-password';"
  ```

## License

MIT
