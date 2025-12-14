# Troubleshooting Guide

## Database Authentication Errors

### Error: `password authentication failed for user "postgres"`

This means the database password in your `.env.prod` file doesn't match what PostgreSQL was initialized with.

#### Solution 1: Check Environment Variables

```bash
# Check if .env.prod exists and has DB_PASSWORD
cat .env.prod | grep DB_PASSWORD

# Check what password PostgreSQL container is using
docker-compose -f docker-compose.prod.yml exec postgres env | grep POSTGRES_PASSWORD
```

#### Solution 2: Fix Password Mismatch

**Option A: Update .env.prod to match existing PostgreSQL password**

If PostgreSQL was already initialized with a password, update `.env.prod`:

```bash
# Find the actual password PostgreSQL is using
docker-compose -f docker-compose.prod.yml exec postgres printenv POSTGRES_PASSWORD

# Update .env.prod with the correct password
# Edit .env.prod and set:
DB_PASSWORD=<actual-password>
```

**Option B: Reset PostgreSQL password (⚠️ WARNING: Deletes all data)**

If you can lose existing data:

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Remove PostgreSQL volume
docker volume rm rozvrhovac_postgres_data

# Update .env.prod with new password
# DB_PASSWORD=<new-strong-password>

# Start services (will initialize with new password)
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for PostgreSQL to be ready, then run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**Option C: Change PostgreSQL password without losing data**

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres

# Change password
ALTER USER postgres WITH PASSWORD 'new-password';

# Exit psql
\q

# Update .env.prod
# DB_PASSWORD=new-password

# Restart backend to pick up new password
docker-compose -f docker-compose.prod.yml restart backend
```

#### Solution 3: Verify Database Connection

```bash
# Test connection from backend container
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.config import settings
print(f'DATABASE_URL: {settings.DATABASE_URL}')
"

# Test PostgreSQL connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
async def test():
    async with AsyncSessionLocal() as db:
        result = await db.execute('SELECT 1')
        print('✅ Database connection successful!')
asyncio.run(test())
"
```

### Error: `database "rozvrhovac" does not exist`

The database hasn't been created yet.

#### Solution: Create Database

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres

# Create database
CREATE DATABASE rozvrhovac;

# Exit
\q

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Migration Errors

### Error: `MIGRATION_DEFAULT_TENANT_ID must be set`

This happens when running migrations that need to backfill tenant_id for existing data.

#### Solution:

1. **Create a tenant first:**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.seed_tenant \
  --name "Default Tenant" \
  --slug "default-tenant"
```

2. **Copy the tenant UUID from output**

3. **Add to .env.prod:**
```bash
MIGRATION_DEFAULT_TENANT_ID=<tenant-uuid>
```

4. **Restart backend to pick up env var:**
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

5. **Run migrations again:**
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Container Issues

### Backend container won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check if database is ready
docker-compose -f docker-compose.prod.yml ps postgres

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend
```

### PostgreSQL container won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs postgres

# Check volume permissions
docker volume inspect rozvrhovac_postgres_data

# Remove and recreate volume (⚠️ loses data)
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d postgres
```

## Environment Variable Issues

### Variables not being picked up

1. **Check .env.prod exists:**
```bash
ls -la .env.prod
```

2. **Verify format (no spaces around =):**
```bash
# Correct:
DB_PASSWORD=mypassword

# Wrong:
DB_PASSWORD = mypassword
```

3. **Restart containers after changing .env.prod:**
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

4. **Check variables in container:**
```bash
docker-compose -f docker-compose.prod.yml exec backend env | grep DB_PASSWORD
```

## Quick Diagnostic Commands

```bash
# Check all services status
docker-compose -f docker-compose.prod.yml ps

# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend --tail=50

# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres --tail=50

# Test database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
async def test():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute('SELECT 1')
        print('✅ Database connection OK')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
asyncio.run(test())
"

# Check environment variables
docker-compose -f docker-compose.prod.yml exec backend env | grep -E "DB_|DATABASE_|ENV"
```

## Common Issues Summary

| Issue | Solution |
|-------|----------|
| Password auth failed | Check `.env.prod` has correct `DB_PASSWORD`, restart containers |
| Database doesn't exist | Create database: `CREATE DATABASE rozvrhovac;` |
| Migration needs tenant ID | Create tenant first, add UUID to `.env.prod` |
| Container won't start | Check logs, verify environment variables |
| Variables not loaded | Restart containers after changing `.env.prod` |

