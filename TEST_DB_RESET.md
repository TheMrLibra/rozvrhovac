# Testing Database Reset Guide

## Quick Reset Command

To completely reset the testing database (deletes all data and recreates everything):

```bash
# Option 1: Using Makefile (recommended)
make reset-test-db

# Option 2: Using script directly
./scripts/reset-test-db.sh

# Option 3: Without confirmation prompt (for CI/automation)
./scripts/reset-test-db.sh --no-confirm
```

## What Gets Reset

The reset process:

1. **Stops all services** and removes database volumes (deletes all data)
2. **Starts services** (database, backend)
3. **Runs migrations** (creates all tables)
4. **Creates tenant** (`test-school`)
5. **Creates school** (`SCHOOL001`)
6. **Creates admin user** (`admin@school.example` / `admin123`)
7. **Creates comprehensive test data**:
   - 4 Grade Levels (1st-4th Grade)
   - 10 Class Groups (1.A, 1.B, 1.C, 2.A, 2.B, 2.C, 3.A, 3.B, 4.A, 4.B)
   - 10 Subjects (Mathematics, Physics, Chemistry, Biology, Computer Science, English, History, Geography, Physical Education, Art)
   - 18 Teachers with capabilities
   - 17 Classrooms (including specialized labs)
   - 66 Class Subject Allocations

## Step-by-Step Manual Reset

If you prefer to do it manually:

```bash
# 1. Stop and remove volumes (deletes all data)
docker-compose -f docker-compose.dev.yml down -v

# 2. Start services
docker-compose -f docker-compose.dev.yml up -d

# 3. Wait for services
sleep 5

# 4. Run initial migration (creates tenant table)
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade 316b16895072

# 5. Setup tenant, school, admin
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.setup_dev

# 6. Get tenant ID and run remaining migrations
TENANT_ID=$(docker-compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d rozvrhovac -t -c "SELECT id FROM tenants WHERE slug = 'test-school' LIMIT 1;" | tr -d " \n")
docker-compose -f docker-compose.dev.yml exec -T -e MIGRATION_DEFAULT_TENANT_ID="$TENANT_ID" backend alembic upgrade head

# 7. Create test data
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_test_data --tenant-slug "test-school" --school-code "SCHOOL001" --force
```

## Verify Database is Correct

After reset, verify the database:

```bash
# Check tenant exists
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d rozvrhovac -c "SELECT name, slug FROM tenants;"

# Check school exists
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d rozvrhovac -c "SELECT name, code FROM schools;"

# Check admin user exists
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d rozvrhovac -c "SELECT email, role FROM users WHERE role = 'admin';"

# Check test data counts
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d rozvrhovac -c "
SELECT 
    'Grade Levels' as type, COUNT(*) as count FROM grade_levels
UNION ALL
SELECT 'Class Groups', COUNT(*) FROM class_groups
UNION ALL
SELECT 'Subjects', COUNT(*) FROM subjects
UNION ALL
SELECT 'Teachers', COUNT(*) FROM teachers
UNION ALL
SELECT 'Classrooms', COUNT(*) FROM classrooms
UNION ALL
SELECT 'Class Subject Allocations', COUNT(*) FROM class_subject_allocations
UNION ALL
SELECT 'Teacher Capabilities', COUNT(*) FROM teacher_subject_capabilities;
"
```

Expected counts:
- Grade Levels: 4
- Class Groups: 10
- Subjects: 10
- Teachers: 18
- Classrooms: 17
- Class Subject Allocations: 66
- Teacher Capabilities: ~50+ (general + primary assignments)

## Troubleshooting

### Database connection errors
```bash
# Check if database is running
docker-compose -f docker-compose.dev.yml ps postgres

# Check database logs
docker-compose -f docker-compose.dev.yml logs postgres
```

### Migration errors
```bash
# Check migration status
docker-compose -f docker-compose.dev.yml exec backend alembic current

# Check migration history
docker-compose -f docker-compose.dev.yml exec backend alembic history
```

### Test data not created
```bash
# Check if tenant/school exist first
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.list_tenants

# Manually create test data
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_test_data --tenant-slug "test-school" --school-code "SCHOOL001" --force
```

## Alternative: Reset Only Test Data (Keep Tenant/School)

If you only want to reset test data but keep tenant, school, and admin:

```bash
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_test_data --tenant-slug "test-school" --school-code "SCHOOL001" --force
```

This will:
- Delete existing test data (teachers, subjects, classes, etc.)
- Recreate all test data
- Keep tenant, school, and admin user intact

