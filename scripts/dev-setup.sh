#!/bin/bash
# One-command development setup script

set -e

echo "🚀 Starting development setup..."
echo ""

# Start services
echo "📦 Starting Docker services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if backend is healthy
echo "🔍 Checking backend health..."
for i in {1..30}; do
    if docker-compose -f docker-compose.dev.yml exec -T backend python -c "import sys; sys.exit(0)" 2>/dev/null; then
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend not ready after 30 attempts"
        exit 1
    fi
    sleep 1
done

# Run initial migration (creates tenant table)
echo "📊 Running initial migration (creates tenant table)..."
docker-compose -f docker-compose.dev.yml exec -T backend alembic upgrade 316b16895072 || echo "⚠️  Migration may have already run"

# Run setup script (creates tenant, school, admin user)
echo "🔧 Running development setup..."
docker-compose -f docker-compose.dev.yml exec -T backend python -m scripts.setup_dev

# Get tenant ID for remaining migrations
echo "📊 Running remaining migrations..."
TENANT_ID=$(docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d rozvrhovac -t -c "SELECT id FROM tenants WHERE slug = 'default-school' LIMIT 1;" | tr -d " \n")

if [ -z "$TENANT_ID" ]; then
    echo "❌ Could not find tenant ID"
    exit 1
fi

# Run remaining migrations
docker-compose -f docker-compose.dev.yml exec -T -e MIGRATION_DEFAULT_TENANT_ID="$TENANT_ID" backend alembic upgrade head || echo "⚠️  Migrations may have already run"

echo ""
echo "✅ Development environment ready!"
echo ""
echo "📋 Access Points:"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Frontend: http://localhost:5173"
echo ""
echo "🚀 To start frontend:"
echo "   cd frontend"
echo "   nvm use  # Switch to Node.js 18+ (required)"
echo "   npm install  # First time only"
echo "   npm run dev"
echo ""
echo "🔐 Login Credentials:"
echo "   Email: admin@school.example"
echo "   Password: admin123"
echo "   Header: X-Tenant: default-school"
echo ""

