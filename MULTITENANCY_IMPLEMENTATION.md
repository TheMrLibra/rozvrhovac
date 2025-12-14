# Multi-Tenancy Implementation Summary

## ✅ Completed Tasks

### A) Architecture Documentation
- Created `docs/multitenancy.md` with comprehensive documentation of:
  - Current architecture (SQLAlchemy async, JWT auth)
  - Refactored architecture (tenant model, tenant resolution, RLS preparation)
  - Migration strategy
  - Operational notes

### B) Tenant Model
- ✅ Created `Tenant` model with UUID primary key
- ✅ Fields: `id` (UUID), `name`, `slug` (unique), `created_at`, `updated_at`
- ✅ Migration created: `316b16895072_add_tenant_table.py`

### C) Tenant Resolution
- ✅ Created `TenantContext` Pydantic model
- ✅ Implemented `get_tenant_context()` dependency with priority:
  1. From authenticated user's `tenant_id`
  2. From `X-Tenant` header (UUID or slug)
  3. From `DEFAULT_TENANT_SLUG` (dev only)
  4. Raise 400 error if cannot resolve (prod)
- ✅ Created `get_tenant_context_optional()` for optional tenant resolution
- ✅ Created `TenantRepository` for tenant CRUD operations

### D) Tenant ID in All Tables
- ✅ Added `tenant_id` UUID FK to all tenant-owned tables:
  - Users, Schools, SchoolSettings
  - Teachers, Subjects, ClassGroups, Classrooms, GradeLevels
  - Timetables, TimetableEntries
  - TeacherAbsences, Substitutions
- ✅ Updated unique constraints to include `tenant_id`:
  - `users`: `(tenant_id, email)` unique
  - `schools`: `(tenant_id, code)` unique
- ✅ Created migration: `3e765b7e2d53_add_tenant_id_to_all_tables.py`
- ✅ Migration includes data backfill with `MIGRATION_DEFAULT_TENANT_ID` env var

### E) Repository Tenant Filtering
- ✅ Updated `BaseRepository` to require `tenant_id` in all methods:
  - `get_by_id(id, tenant_id)`
  - `get_all(tenant_id, skip, limit)`
  - `create(obj, tenant_id)` - ensures tenant_id is set server-side
  - `update(id, tenant_id, **kwargs)` - verifies tenant ownership
  - `delete(id, tenant_id)` - verifies tenant ownership
- ✅ Updated `UserRepository` with tenant-aware `get_by_email(email, tenant_id)`
- ✅ Added `get_by_id_for_auth()` for authentication (no tenant filtering)

### F) API Endpoints (Partial)
- ✅ Updated `auth_router.py`:
  - Login endpoint accepts `X-Tenant` header (optional)
  - User authentication scoped to tenant when provided
- ⚠️ **Remaining**: Other endpoints need to be updated to use `get_tenant_context()` dependency
  - This is a large task that can be done incrementally
  - Infrastructure is in place - endpoints just need to add the dependency

### G) RLS Preparation
- ✅ Created `app/db/rls.py` with:
  - `set_tenant_context()` function for setting session-local tenant
  - `get_rls_policy_sql()` for generating RLS policies
  - `get_all_rls_setup_sql()` for enabling RLS on all tables
  - List of tenant-owned tables
  - Documentation on how to enable RLS in the future

### H) Docker Compose
- ✅ Updated `docker-compose.dev.yml`:
  - Added `ENV=dev`
  - Added `DEFAULT_TENANT_SLUG=default-school`
  - Added `env_file: .env.dev`
- ✅ Updated `docker-compose.prod.yml`:
  - Removed registry database (single database approach)
  - Added `ENV=prod`
  - Added `MIGRATION_DEFAULT_TENANT_ID` support
  - Added `env_file: .env.prod`
- ✅ Created example env files:
  - `.env.example`
  - `.env.dev.example`
  - `.env.prod.example`

### I) Configuration
- ✅ Updated `app/core/config.py` with:
  - `ENV` (dev/prod)
  - `DEFAULT_TENANT_SLUG` (optional, dev only)
  - `MIGRATION_DEFAULT_TENANT_ID` (for migrations)
  - `is_dev` property

### J) Seed Scripts
- ✅ Created `scripts/seed_tenant.py`:
  - Creates a tenant with name and slug
  - Checks for existing tenant
  - Outputs UUID for use in migrations

### K) Tests
- ✅ Created test infrastructure:
  - `tests/conftest.py` with fixtures for:
    - Database session
    - Two test tenants (tenant_a, tenant_b)
    - Users and teachers for each tenant
  - `tests/test_tenant_isolation.py` with tests for:
    - Tenant isolation in repositories (teachers, users)
    - Email uniqueness per tenant
    - Create/update/delete prevention across tenants
    - Data leakage prevention

### L) Makefile Updates
- ✅ Added commands:
  - `make seed-tenant` - Create a tenant
  - `make migrate-dev` - Run migrations in dev
  - `make migrate-prod` - Run migrations in prod
  - `make dev-up` / `make dev-down` - Development services
  - `make prod-up` / `make prod-down` - Production services

## 📋 Remaining Tasks

### F) Update All API Endpoints (Incremental)
Each endpoint that accesses tenant-owned data needs to:
1. Add `tenant: TenantContext = Depends(get_tenant_context)` dependency
2. Pass `tenant.tenant_id` to all repository/service calls
3. Ensure `tenant_id` is set server-side on create operations

**Example pattern:**
```python
@router.get("/teachers")
async def list_teachers(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    repo = TeacherRepository(db)
    teachers = await repo.get_all(tenant_id=tenant.tenant_id)
    return teachers
```

**Endpoints to update:**
- `schools_router.py`
- `teachers_router.py`
- `subjects_router.py`
- `class_groups_router.py`
- `classrooms_router.py`
- `timetable_router.py`
- `substitution_router.py`
- `absence_router.py`

## 🚀 Usage Guide

### Development Setup

1. **Start services:**
   ```bash
   make dev-up
   ```

2. **Create default tenant:**
   ```bash
   make seed-tenant NAME="Default School" SLUG="default-school"
   ```
   Note the UUID output.

3. **Set migration tenant ID and run migrations:**
   ```bash
   export MIGRATION_DEFAULT_TENANT_ID=<uuid-from-step-2>
   make migrate-dev
   ```

4. **Create admin user (if needed):**
   ```bash
   docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_admin_user \
     --school-code SCHOOL001 \
     --email admin@school.local \
     --password securepassword
   ```

### Production Setup

1. **Set environment variables in `.env.prod`:**
   ```
   ENV=prod
   DATABASE_URL=postgresql+asyncpg://...
   MIGRATION_DEFAULT_TENANT_ID=<uuid-of-default-tenant>
   ```

2. **Start services:**
   ```bash
   make prod-up
   ```

3. **Run migrations:**
   ```bash
   make migrate-prod
   ```

### Using the API

**Development:**
- Tenant is resolved from `DEFAULT_TENANT_SLUG` if no header provided
- Can override with `X-Tenant` header (slug or UUID)

**Production:**
- Must provide `X-Tenant` header with tenant slug or UUID
- Example: `X-Tenant: default-school` or `X-Tenant: 123e4567-e89b-12d3-a456-426614174000`

### Running Tests

```bash
cd backend
pytest tests/test_tenant_isolation.py -v
```

## 🔒 Security Notes

1. **Tenant ID is NEVER accepted from request body** - always set server-side from context
2. **All queries are filtered by tenant_id** - repositories enforce this
3. **Update/Delete operations verify tenant ownership** - prevents cross-tenant modifications
4. **Email uniqueness is per-tenant** - same email can exist in different tenants
5. **Future RLS will add database-level enforcement** - defense in depth

## 📝 Migration Notes

When running the `add_tenant_id_to_all_tables` migration:
- **REQUIRED**: Set `MIGRATION_DEFAULT_TENANT_ID` environment variable
- All existing rows will be assigned to this tenant
- Migration will fail with clear error if variable is not set
- After migration, ensure all new data includes proper `tenant_id`

## 🔮 Future: Enabling RLS

When ready to enable PostgreSQL Row Level Security:

1. Review `app/db/rls.py` for SQL templates
2. Update `get_db()` dependency to call `set_tenant_context()`
3. Run RLS setup SQL on database
4. Remove manual tenant filtering from repositories (RLS handles it)
5. Test thoroughly

See `docs/multitenancy.md` for detailed RLS instructions.

