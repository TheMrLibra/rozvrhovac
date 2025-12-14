#!/bin/bash
# Script to diagnose and fix database password mismatch

set -e

echo "🔍 Diagnosing database password issue..."
echo ""

# Check if PostgreSQL container is running
if ! docker compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL container is not running!"
    echo "   Start it with: docker compose -f docker-compose.prod.yml up -d postgres"
    exit 1
fi

echo "✅ PostgreSQL container is running"
echo ""

# Check what password PostgreSQL container expects
echo "📋 Checking PostgreSQL environment variables..."
POSTGRES_PASSWORD=$(docker compose -f docker-compose.prod.yml exec -T postgres printenv POSTGRES_PASSWORD 2>/dev/null || echo "")
echo "   POSTGRES_PASSWORD in container: ${POSTGRES_PASSWORD:-<not set>}"
echo ""

# Check what password backend is trying to use
echo "📋 Checking backend environment variables..."
BACKEND_DB_PASSWORD=$(docker compose -f docker-compose.prod.yml exec -T backend printenv DB_PASSWORD 2>/dev/null || echo "")
echo "   DB_PASSWORD in backend: ${BACKEND_DB_PASSWORD:-<not set>}"
echo ""

# Check .env.prod
if [ -f .env.prod ]; then
    echo "📋 Checking .env.prod file..."
    ENV_DB_PASSWORD=$(grep "^DB_PASSWORD=" .env.prod | cut -d'=' -f2 | tr -d ' ' || echo "")
    echo "   DB_PASSWORD in .env.prod: ${ENV_DB_PASSWORD:-<not set>}"
    echo ""
else
    echo "⚠️  .env.prod file not found!"
    echo ""
fi

# Try to connect with current password
echo "🔐 Testing database connection..."
if docker compose -f docker-compose.prod.yml exec -T backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
async def test():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute('SELECT 1')
        print('✅ Database connection successful!')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False
result = asyncio.run(test())
exit(0 if result else 1)
" 2>&1; then
    echo ""
    echo "✅ Database connection is working!"
    exit 0
else
    echo ""
    echo "❌ Database connection failed!"
    echo ""
fi

# Provide solutions
echo "💡 Solutions:"
echo ""
echo "Option 1: Update PostgreSQL password to match .env.prod"
echo "   Run these commands:"
echo ""
echo "   docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -c \"ALTER USER postgres WITH PASSWORD 'postgres';\""
echo "   docker compose -f docker-compose.prod.yml restart backend"
echo ""
echo "Option 2: Update .env.prod to match PostgreSQL password"
echo "   First, find the actual password PostgreSQL is using:"
echo "   docker compose -f docker-compose.prod.yml exec postgres printenv POSTGRES_PASSWORD"
echo "   Then update .env.prod and restart backend:"
echo "   docker compose -f docker-compose.prod.yml restart backend"
echo ""
echo "Option 3: Fresh start (⚠️  DELETES ALL DATA)"
echo "   docker compose -f docker-compose.prod.yml down"
echo "   docker volume rm rozvrhovac_postgres_data"
echo "   docker compose -f docker-compose.prod.yml up -d postgres"
echo "   # Wait a few seconds, then run migrations"
echo ""

exit 1

