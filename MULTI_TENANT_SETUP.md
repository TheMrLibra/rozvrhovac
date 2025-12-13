# Multi-Tenant Database Setup Summary

This document summarizes the changes made to support multi-tenant deployment with one backend and multiple databases (one per school).

## Changes Made

### 1. Registry Database System

**New Files:**
- `backend/app/models/registry.py` - Registry model for storing school metadata
- `backend/app/core/database_manager.py` - Multi-tenant database connection manager
- `backend/app/repositories/registry_repository.py` - Repository for registry operations

**Purpose:**
- The registry database stores metadata about each school and their database connection information
- Each school has its own isolated database
- The backend routes requests to the correct database based on school context

### 2. Database Routing

**Modified Files:**
- `backend/app/core/dependencies.py` - Added `get_school_context()` and `get_db_for_school()`
- `backend/app/core/config.py` - Added registry database configuration

**How it works:**
- School context is extracted from:
  1. `X-School-Code` header (priority)
  2. JWT token `school_id` (fallback)
- Database connection is routed to the school's database based on registry lookup
- Falls back to default database if no school context is found

### 3. Authentication Updates

**Modified Files:**
- `backend/app/api/v1/auth_router.py` - Updated login to require `school_code`
- `backend/app/schemas/auth.py` - Added `school_code` to `LoginRequest`

**Changes:**
- Login now requires `school_code` in the request body
- Backend looks up school in registry and connects to school's database
- JWT tokens include `school_id` for subsequent requests

### 4. API Router Updates

**Modified Files:**
- All API routers updated to use `get_db_for_school` instead of `get_db`
- This ensures all endpoints route to the correct school database

### 5. Management Scripts

**New Scripts:**
- `backend/scripts/init_registry_db.py` - Initialize registry database
- `backend/scripts/create_school.py` - Create a new school and its database
- `backend/scripts/create_admin_user.py` - Create admin user for a school

## Usage

### Initial Setup

1. **Initialize Registry Database:**
   ```bash
   cd backend
   python -m scripts.init_registry_db
   ```

2. **Create a School:**
   ```bash
   python -m scripts.create_school \
     --name "School Name" \
     --code "SCHOOL001"
   ```

3. **Create Admin User:**
   ```bash
   python -m scripts.create_admin_user \
     --school-code SCHOOL001 \
     --email admin@school.local \
     --password securepassword
   ```

### API Usage

**Login:**
```json
POST /api/v1/auth/login
{
  "email": "admin@school.local",
  "password": "password",
  "school_code": "SCHOOL001"
}
```

**Subsequent Requests:**
Include JWT token in Authorization header:
```
Authorization: Bearer <token>
```

The backend automatically routes to the correct database based on `school_id` in the token.

## Database Structure

### Registry Database (`rozvrhovac_registry`)
- `school_registry` table - Stores school metadata and database connection info

### School Databases (`rozvrhovac_<school_code>`)
- Each school has its own database with all application tables
- Complete data isolation between schools
- Same schema across all school databases

## Environment Variables

Required environment variables:

```bash
# Registry Database
REGISTRY_DATABASE_URL=postgresql+asyncpg://user:pass@host:port/rozvrhovac_registry

# Default Database Settings (for creating new school databases)
DEFAULT_DB_HOST=localhost
DEFAULT_DB_PORT=5432
DEFAULT_DB_USER=postgres
DEFAULT_DB_PASSWORD=postgres

# JWT
SECRET_KEY=your-secret-key

# CORS
CORS_ORIGINS=http://localhost:5173
```

## Migration Path

### For Existing Deployments

1. Backup existing database
2. Initialize registry database
3. Create registry entry for existing school:
   ```sql
   INSERT INTO school_registry (school_id, name, code, database_name, ...)
   VALUES (1, 'Existing School', 'EXISTING001', 'rozvrhovac', ...);
   ```
4. Update environment variables
5. Restart backend

### For New Deployments

Follow the "Initial Setup" steps above.

## Security Considerations

1. **Database Isolation:** Each school's data is completely isolated
2. **Connection Security:** Use SSL/TLS for database connections in production
3. **Password Storage:** Store database passwords securely (use secrets manager)
4. **JWT Security:** Use strong, random secret keys
5. **Access Control:** Verify `school_id` matches user's school in all endpoints

## Troubleshooting

### School Not Found
- Verify school exists in registry database
- Check `school_registry` table
- Verify database connection settings

### Database Connection Errors
- Check database server is running
- Verify credentials in registry
- Check network connectivity
- Review PostgreSQL logs

### Migration Issues
- Ensure migrations run on each school database
- Check Alembic configuration
- Verify model imports

## Future Enhancements

Potential improvements:
1. Database connection pooling per school
2. Automatic database creation via API
3. School database backup automation
4. Database migration management UI
5. Cross-school analytics (if needed)

