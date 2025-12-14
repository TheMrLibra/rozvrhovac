# Multi-Tenancy Architecture

## Current Architecture Summary

### Technology Stack
- **ORM**: SQLAlchemy (async) with `AsyncSession`
- **Database**: PostgreSQL (single database, no RLS yet)
- **Authentication**: JWT tokens with OAuth2PasswordBearer
- **Migrations**: Alembic
- **Session Management**: FastAPI dependency injection via `get_db()`

### Current State (Before Refactoring)
- The application previously used a multi-database architecture where each school had its own database
- Models used `school_id` (Integer) as foreign key to `schools` table
- Manual school_id checks in endpoints: `if current_user.school_id != school_id: raise 403`
- No centralized tenant filtering in repositories

### Authentication Flow
1. User logs in via `/api/v1/auth/login` with email/password
2. JWT token is generated containing user_id in `sub` claim
3. Protected endpoints use `get_current_user` dependency which:
   - Extracts token from Authorization header
   - Decodes JWT to get user_id
   - Fetches User from database
   - Returns User object with `school_id` attribute

## Refactored Architecture

### Tenant Model
- **Table**: `tenants`
- **Primary Key**: `id` (UUID)
- **Fields**:
  - `id`: UUID primary key
  - `name`: String (display name)
  - `slug`: String (unique, for future subdomain mapping)
  - `created_at`: Timestamp
  - `updated_at`: Timestamp

### Tenant Resolution Strategy

The tenant is resolved in the following priority order:

1. **From authenticated user**: If user has `tenant_id`, use it
2. **From request header**: `X-Tenant` header (supports both UUID and slug)
3. **Default tenant (dev only)**: `DEFAULT_TENANT_SLUG` environment variable
4. **Production**: Raise 400 error if tenant cannot be resolved

**Implementation**: `get_tenant_context()` FastAPI dependency

### Tenant Scoping

All tenant-owned tables now include:
- `tenant_id` UUID NOT NULL column
- Foreign key to `tenants(id)`
- Composite index: `(tenant_id, <commonly-filtered-columns>)`
- Updated unique constraints to include `tenant_id`

**Tenant-owned entities**:
- Users
- Schools (renamed concept - now represents tenant-specific school data)
- Teachers
- Subjects
- ClassGroups
- Classrooms
- GradeLevels
- Timetables
- TimetableEntries
- TeacherAbsences
- Substitutions
- SchoolSettings

**Global entities** (no tenant_id):
- Tenants (obviously)

### Data Access Layer

**Repository Pattern**:
- Base repository includes `tenant_id` parameter in all queries
- Helper function `tenant_query(stmt, tenant_id)` ensures all queries are filtered
- Create operations automatically set `tenant_id` from context (never from client)
- Update/Delete operations verify tenant ownership in WHERE clause

**Example**:
```python
async def get_by_id(self, id: int, tenant_id: UUID) -> Optional[ModelType]:
    result = await self.db.execute(
        select(self.model)
        .where(self.model.id == id)
        .where(self.model.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()
```

### API Endpoints

All tenant-scoped endpoints:
1. Accept `tenant: TenantContext = Depends(get_tenant_context)`
2. Pass `tenant.tenant_id` to all repository/service calls
3. Never accept `tenant_id` from request body (set server-side)

**Example**:
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

## Future PostgreSQL RLS Integration

### Preparation Module: `app/db/rls.py`

This module contains functions that will be used when RLS is enabled:

1. **`set_tenant_context(connection, tenant_id: UUID)`**
   - Sets `SET LOCAL app.tenant_id = '<tenant_id>'` on connection
   - Called before each request's database operations

2. **RLS Policy Templates**
   - SQL strings for policies (not executed automatically)
   - Example: `CREATE POLICY tenant_isolation ON teachers USING (tenant_id = current_setting('app.tenant_id')::uuid)`

### Enabling RLS (Future Steps)

1. Enable RLS on all tenant-owned tables:
   ```sql
   ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
   ```

2. Create policies for each table:
   ```sql
   CREATE POLICY tenant_isolation ON teachers
     USING (tenant_id = current_setting('app.tenant_id')::uuid);
   ```

3. Update application code to set tenant context:
   - Modify `get_db()` dependency to call `set_tenant_context()`
   - Ensure tenant is resolved before database session creation

4. Remove manual tenant filtering from repositories (RLS handles it)

### Benefits of RLS
- Defense in depth: Even if application code has bugs, database enforces isolation
- Reduced code complexity: No need for manual tenant filtering
- Performance: Database-level filtering is optimized

## Migrations

### Data Backfill Strategy

When adding `tenant_id` to existing tables:

1. Migration requires `MIGRATION_DEFAULT_TENANT_ID` environment variable
2. All existing rows are assigned to this default tenant
3. Migration fails with clear error if variable is not set

**Example migration**:
```python
def upgrade():
    # Add tenant_id column (nullable first)
    op.add_column('users', sa.Column('tenant_id', UUID(), nullable=True))
    
    # Backfill with default tenant
    default_tenant_id = os.getenv('MIGRATION_DEFAULT_TENANT_ID')
    if not default_tenant_id:
        raise ValueError("MIGRATION_DEFAULT_TENANT_ID must be set")
    
    op.execute(f"UPDATE users SET tenant_id = '{default_tenant_id}'")
    
    # Make NOT NULL
    op.alter_column('users', 'tenant_id', nullable=False)
```

## Environment Variables

### Required Variables

- `DATABASE_URL`: PostgreSQL connection string
- `ENV`: `dev` or `prod`
- `DEFAULT_TENANT_SLUG`: Default tenant slug for dev (optional in dev, required in prod if no header)
- `MIGRATION_DEFAULT_TENANT_ID`: UUID of default tenant for data backfill during migrations

### Example `.env.dev`
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac
ENV=dev
DEFAULT_TENANT_SLUG=default-school
SECRET_KEY=dev-secret-key
```

### Example `.env.prod`
```
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/rozvrhovac
ENV=prod
SECRET_KEY=<strong-production-secret>
# DEFAULT_TENANT_SLUG not set - requires X-Tenant header
```

## Operational Notes

### Running Migrations

1. **Development**:
   ```bash
   export MIGRATION_DEFAULT_TENANT_ID=$(uuidgen)  # or use existing tenant UUID
   alembic upgrade head
   ```

2. **Production**:
   ```bash
   export MIGRATION_DEFAULT_TENANT_ID=<existing-tenant-uuid>
   alembic upgrade head
   ```

### Creating Default Tenant

Use seed script:
```bash
python -m scripts.seed_tenant --name "Default School" --slug "default-school"
```

### Testing Tenant Isolation

Run test suite:
```bash
pytest tests/test_tenant_isolation.py
```

Tests verify:
- Data created under Tenant A is not visible to Tenant B
- Cross-tenant access attempts return 404
- Tenant filtering is enforced in all CRUD operations

