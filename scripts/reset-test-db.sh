#!/bin/bash
# Reset testing database - completely recreates database with fresh test data
# Usage: ./scripts/reset-test-db.sh [--no-confirm]

set -e

CONFIRM=true
if [ "$1" == "--no-confirm" ]; then
    CONFIRM=false
fi

echo "🔄 Resetting Testing Database"
echo "=============================="
echo ""

if [ "$CONFIRM" = true ]; then
    echo "⚠️  WARNING: This will DELETE ALL DATA in the database!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Cancelled."
        exit 1
    fi
    echo ""
fi

# Step 1: Stop services and remove volumes (deletes all data)
echo "📦 Step 1/6: Stopping services and removing database volumes..."
docker-compose -f docker-compose.dev.yml down -v

# Step 2: Start services
echo ""
echo "🚀 Step 2/6: Starting services..."
docker-compose -f docker-compose.dev.yml up -d

# Step 3: Wait for services to be ready
echo ""
echo "⏳ Step 3/6: Waiting for services to be ready..."
sleep 5

# Check if backend is healthy
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

# Step 4: Run initial migration (creates tenant table)
echo ""
echo "📊 Step 4/6: Running initial migration (creates tenant table)..."
docker-compose -f docker-compose.dev.yml exec -T backend alembic upgrade 316b16895072 || echo "⚠️  Initial migration may have already run"

# Step 5: Setup tenant, school, and admin user
echo ""
echo "🔧 Step 5/6: Setting up tenant, school, and admin user..."
docker-compose -f docker-compose.dev.yml exec -T backend python -m scripts.setup_dev

# Get tenant ID for remaining migrations
TENANT_ID=$(docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d rozvrhovac -t -c "SELECT id FROM tenants WHERE slug = 'test-school' LIMIT 1;" | tr -d " \n")

if [ -z "$TENANT_ID" ]; then
    echo "❌ Could not find tenant ID"
    exit 1
fi

# Run remaining migrations
echo ""
echo "📊 Running remaining migrations..."
docker-compose -f docker-compose.dev.yml exec -T -e MIGRATION_DEFAULT_TENANT_ID="$TENANT_ID" backend alembic upgrade head || echo "⚠️  Migrations may have already run"

# Step 6: Create test data
echo ""
echo "📚 Step 6/6: Creating comprehensive test data..."
docker-compose -f docker-compose.dev.yml exec -T backend python -m scripts.create_test_data --tenant-slug "test-school" --school-code "SCHOOL001" --force

echo ""
echo "=============================="
echo "✅ Testing Database Reset Complete!"
echo "=============================="
echo ""
echo "📋 Summary:"
echo "   • Database recreated (all old data deleted)"
echo "   • All migrations applied"
echo "   • Tenant: test-school"
echo "   • School: SCHOOL001"
echo "   • Admin User: admin@school.example"
echo "   • Admin Password: admin123"
echo "   • Test data created:"
echo "     - 4 Grade Levels"
echo "     - 10 Class Groups"
echo "     - 10 Subjects"
echo "     - 18 Teachers with capabilities"
echo "     - 17 Classrooms"
echo "     - 66 Class Subject Allocations"
echo ""
echo "🔗 Access Points:"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Frontend: http://localhost:5173"
echo ""
echo "🔐 Login Credentials:"
echo "   Email: admin@school.example"
echo "   Password: admin123"
echo "   Header: X-Tenant: test-school"
echo ""
echo "💡 Quick Test:"
echo "   curl -X POST http://localhost:8000/api/v1/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'X-Tenant: test-school' \\"
echo "     -d '{\"email\": \"admin@school.example\", \"password\": \"admin123\"}'"
echo ""

