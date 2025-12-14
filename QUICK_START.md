# Quick Start Guide

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend)
- Make (optional, but recommended)

## Access Points

### Backend API
- **URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Frontend
- **URL**: http://localhost:5173 (when running locally)
- **Note**: Frontend runs locally in development mode for better hot reload

### Database Tools
- **pgAdmin**: http://localhost:5050
  - Email: `admin@rozvrhovac.dev`
  - Password: `admin`
- **PostgreSQL**: `localhost:5432`
  - Database: `rozvrhovac`
  - User: `postgres`
  - Password: `postgres`

## Quick Start - One Command Setup

### Complete Development Setup

```bash
# This single command does everything:
# - Starts Docker services
# - Runs migrations
# - Creates default tenant
# - Creates school and admin user
make dev-up
```

That's it! After running `make dev-up`, your development environment is ready.

**Default Credentials:**
- Email: `admin@school.example`
- Password: `admin123`
- Tenant Header: `X-Tenant: default-school`

### Manual Setup (if needed)

If you prefer to run steps manually or customize the setup:

<details>
<summary>Click to expand manual setup steps</summary>

### 1. Start Development Services

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Run Initial Migration (Creates Tenant Table)

```bash
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade 316b16895072
```

### 3. Create Default Tenant

```bash
make seed-tenant NAME="Default School" SLUG="default-school"
```

### 4. Run Remaining Migrations

```bash
# Get tenant UUID first
TENANT_ID=$(docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d rozvrhovac -t -c "SELECT id FROM tenants WHERE slug = 'default-school';" | tr -d " \n")
docker-compose -f docker-compose.dev.yml exec -e MIGRATION_DEFAULT_TENANT_ID=$TENANT_ID backend alembic upgrade head
```

### 5. Create Admin User

```bash
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_admin_user \
  --tenant-slug default-school \
  --email admin@school.example \
  --password admin123 \
  --school-code SCHOOL001
```

</details>

### Start Frontend

**Prerequisites**: Node.js 18+ is required. If you have nvm installed, it will automatically use the version specified in `.nvmrc`.

```bash
cd frontend

# If using nvm, switch to Node.js 18+
nvm use  # or: nvm install 18 && nvm use 18

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Note**: If you see `crypto.getRandomValues is not a function`, you need to upgrade Node.js to version 18 or higher.

## Using the API

### Development Mode

In development, the tenant is automatically resolved from `DEFAULT_TENANT_SLUG` (set to `default-school`).

You can also override by sending the `X-Tenant` header:
```bash
curl -H "X-Tenant: default-school" http://localhost:8000/api/v1/...
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant: default-school" \
  -d '{
    "email": "admin@school.local",
    "password": "securepassword"
  }'
```

### Authenticated Requests

Include the JWT token in the Authorization header:
```bash
curl -H "Authorization: Bearer <token>" \
     -H "X-Tenant: default-school" \
     http://localhost:8000/api/v1/...
```

## Creating Test Data

To populate your database with comprehensive test data (grade levels, classes, subjects, teachers, classrooms, etc.), use the test data generation script:

```bash
# Using Makefile (recommended)
make create-test-data TENANT_SLUG="default-school" SCHOOL_CODE="SCHOOL001"

# Or with force flag to automatically delete existing data
make create-test-data TENANT_SLUG="default-school" SCHOOL_CODE="SCHOOL001" FORCE=--force

# Or directly with Python
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_test_data \
  --tenant-slug default-school \
  --school-code SCHOOL001 \
  --force
```

This will create:
- **4 Grade Levels** (1st-4th Grade)
- **10 Class Groups** (1.A, 1.B, 1.C, 2.A, 2.B, 2.C, 3.A, 3.B, 4.A, 4.B)
- **10 Subjects** (Mathematics, Physics, Chemistry, Biology, Computer Science, English, History, Geography, Physical Education, Art)
- **18 Teachers** with capabilities and primary assignments
- **17 Classrooms** (regular rooms + specialized labs)
- **66 Class Subject Allocations** with weekly hour requirements

**Note**: If test data already exists, the script will prompt you to delete it first (unless you use `--force`).

## Environment Variables

Create `.env.dev` file (optional, defaults are set in docker-compose.dev.yml):

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/rozvrhovac
ENV=dev
DEFAULT_TENANT_SLUG=default-school
SECRET_KEY=dev-secret-key-change-in-production
```

## Troubleshooting

### Backend not responding at http://localhost:8000

1. Check if backend is running:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

2. Check backend logs:
   ```bash
   docker-compose -f docker-compose.dev.yml logs backend
   ```

3. Restart backend:
   ```bash
   docker-compose -f docker-compose.dev.yml restart backend
   ```

### Migration fails with "MIGRATION_DEFAULT_TENANT_ID must be set"

1. Create a tenant first:
   ```bash
   make seed-tenant NAME="Default School" SLUG="default-school"
   ```

2. Copy the UUID from the output

3. Set it as environment variable:
   ```bash
   export MIGRATION_DEFAULT_TENANT_ID=<uuid>
   ```

4. Run migrations again:
   ```bash
   make migrate-dev
   ```

### Tenant not found errors

- Make sure you've created a tenant: `make seed-tenant`
- Check tenant exists: `docker-compose -f docker-compose.dev.yml exec backend python -c "from app.repositories.tenant_repository import TenantRepository; from app.core.database import AsyncSessionLocal; import asyncio; async def check(): async with AsyncSessionLocal() as db: repo = TenantRepository(db); tenants = await repo.get_all(); print([t.slug for t in tenants])"`

### Frontend not accessible

1. **Check Node.js version** (requires 18+):
   ```bash
   node --version
   # Should be v18.x.x or v20.x.x
   ```

2. **Switch to correct Node.js version** (if using nvm):
   ```bash
   cd frontend
   nvm use  # Uses .nvmrc file
   ```

3. Make sure you've installed dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Start the dev server:
   ```bash
   npm run dev
   ```

5. Check if port 5173 is available:
   ```bash
   lsof -i :5173
   ```

### Database connection issues

1. Check if PostgreSQL is running:
   ```bash
   docker-compose -f docker-compose.dev.yml ps postgres
   ```

2. Test connection:
   ```bash
   docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d rozvrhovac -c "SELECT 1;"
   ```

### Can't login / No users

Create an admin user:
```bash
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_admin_user \
  --tenant-slug default-school \
  --email admin@school.example \
  --password admin123 \
  --school-code SCHOOL001
```

Then login with the `X-Tenant` header set to your tenant slug.

### Local
1. make dev-up
2. cd frontend && nvm use && npm install && npm run dev
3. Test data: make create-test-data TENANT_SLUG="default-school" SCHOOL_CODE="SCHOOL001"
4. Rebuild BE - make rebuild-backend