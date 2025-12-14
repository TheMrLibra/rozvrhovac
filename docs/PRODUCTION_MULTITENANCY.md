# Multi-Tenancy in Production

## Overview

The application uses a **single-database, application-level multi-tenancy** architecture. All tenant-owned data is stored in the same PostgreSQL database, with tenant isolation enforced at the application layer through `tenant_id` filtering.

## Architecture

### Tenant Resolution Flow

In production, tenant context is resolved in the following priority order:

1. **From authenticated user** (if user has `tenant_id`)
2. **From `X-Tenant` header** (UUID or slug) - **REQUIRED in production**
3. **Error** - If tenant cannot be resolved, returns 400 Bad Request

**Important**: Production does NOT use `DEFAULT_TENANT_SLUG` fallback. The `X-Tenant` header must be provided for all requests.

### Authentication Flow

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ 1. POST /api/v1/auth/login
       │    Headers: X-Tenant: <tenant-slug>
       │    Body: {email, password}
       │
       ▼
┌─────────────────┐
│   Backend API   │
└──────┬──────────┘
       │
       │ 2. Resolve tenant from X-Tenant header
       │    Lookup tenant by slug → tenant_id
       │
       │ 3. Authenticate user (scoped to tenant)
       │    SELECT * FROM users 
       │    WHERE email = ? AND tenant_id = ?
       │
       │ 4. Generate JWT token
       │    Token contains: {user_id, role, school_id}
       │    Token does NOT contain tenant_id
       │
       ▼
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
       │ 5. Store token + tenant context
       │
       │ 6. All subsequent requests:
       │    Headers: 
       │      Authorization: Bearer <token>
       │      X-Tenant: <tenant-slug>
       │
       ▼
┌─────────────────┐
│   Backend API   │
└──────┬──────────┘
       │
       │ 7. Extract user from token
       │    User object has tenant_id from DB
       │
       │ 8. Resolve tenant context:
       │    Priority: user.tenant_id > X-Tenant header
       │
       │ 9. All queries filtered by tenant_id
       │    SELECT * FROM teachers 
       │    WHERE tenant_id = ? AND ...
       │
       ▼
```

## Frontend Integration

### Setting Tenant Context

The frontend must send the `X-Tenant` header with every API request. This can be done in several ways:

#### Option 1: Store tenant in localStorage/sessionStorage

```typescript
// After login, store tenant slug
localStorage.setItem('tenant_slug', tenantSlug);

// In API client (axios/fetch)
const api = axios.create({
  baseURL: 'https://api.yourdomain.com',
  headers: {
    'X-Tenant': localStorage.getItem('tenant_slug') || ''
  }
});
```

#### Option 2: Subdomain-based tenant resolution

If using subdomains (e.g., `school1.yourdomain.com`, `school2.yourdomain.com`):

```typescript
// Extract tenant from subdomain
const subdomain = window.location.hostname.split('.')[0];
const tenantSlug = subdomain; // or map subdomain → tenant slug

// Set in API client
const api = axios.create({
  baseURL: 'https://api.yourdomain.com',
  headers: {
    'X-Tenant': tenantSlug
  }
});
```

#### Option 3: Tenant selection UI

Allow users to select their tenant/school:

```typescript
// After login, show tenant selection
const selectedTenant = await selectTenant(); // User selects from list
localStorage.setItem('tenant_slug', selectedTenant.slug);

// Use in all API requests
headers: {
  'X-Tenant': localStorage.getItem('tenant_slug')
}
```

### Frontend Tenant Management

For applications with multiple schools per tenant:

1. **After login**: Fetch user's tenant_id from `/api/v1/auth/me`
2. **Load tenant info**: Fetch tenant details using tenant_id
3. **Store tenant slug**: Save tenant slug for X-Tenant header
4. **Optional**: Allow switching between schools within the same tenant

## Production Configuration

### Environment Variables

```bash
# .env.prod
ENV=prod
# DEFAULT_TENANT_SLUG not set - requires X-Tenant header

DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/rozvrhovac
SECRET_KEY=<strong-random-secret-key>
CORS_ORIGINS=https://app.yourdomain.com,https://api.yourdomain.com
```

### Docker Compose Production

The production setup (`docker-compose.prod.yml`) is configured with:
- `ENV=prod` - Disables default tenant fallback
- No `DEFAULT_TENANT_SLUG` - Requires X-Tenant header
- Database with proper credentials
- Health checks and restart policies

### Reverse Proxy Configuration

If using Nginx as reverse proxy, ensure `X-Tenant` header is passed through:

```nginx
location /api/ {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # IMPORTANT: Pass through X-Tenant header
    proxy_set_header X-Tenant $http_x_tenant;
    
    # Or set tenant from subdomain
    # set $tenant_slug $host;
    # proxy_set_header X-Tenant $tenant_slug;
}
```

### Subdomain-based Tenant Resolution (Optional)

For subdomain-based tenant resolution (e.g., `school1.app.com`, `school2.app.com`):

1. **DNS**: Configure wildcard DNS: `*.app.com` → your server IP
2. **Nginx**: Extract subdomain and set X-Tenant header:

```nginx
server {
    server_name *.app.com;
    
    # Extract subdomain
    set $tenant_slug $host;
    if ($host ~* "^([^.]+)\.app\.com$") {
        set $tenant_slug $1;
    }
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header X-Tenant $tenant_slug;
        # ... other proxy settings
    }
}
```

3. **Frontend**: Use current subdomain automatically:

```typescript
const tenantSlug = window.location.hostname.split('.')[0];
```

## Security Considerations

### Tenant Isolation

- ✅ **Application-level filtering**: All queries include `tenant_id` filter
- ✅ **User tenant_id**: Users can only access their own tenant's data
- ✅ **Header validation**: X-Tenant header is validated against database
- ⚠️ **Future**: PostgreSQL RLS (Row Level Security) can be enabled for defense-in-depth

### Authentication Security

- ✅ **JWT tokens**: Signed with secret key, include expiration
- ✅ **HTTPS required**: All production traffic should use HTTPS
- ✅ **CORS**: Configured to allow only trusted origins
- ✅ **Password hashing**: Uses bcrypt with salt

### Best Practices

1. **Never trust client**: Always validate tenant_id server-side
2. **Use HTTPS**: Encrypt all traffic in production
3. **Rate limiting**: Implement rate limiting per tenant
4. **Audit logging**: Log tenant access for security monitoring
5. **Regular backups**: Backup database regularly (tenant data isolation)

## Database Schema

### Tenant-Owned Tables

All these tables have `tenant_id` UUID column:

- `users` - Users belong to a tenant
- `schools` - Schools belong to a tenant (can have multiple per tenant)
- `teachers` - Teachers belong to a school (which belongs to a tenant)
- `subjects` - Subjects belong to a school
- `class_groups` - Classes belong to a school
- `grade_levels` - Grade levels belong to a school
- `classrooms` - Classrooms belong to a school
- `timetables` - Timetables belong to a school
- `timetable_entries` - Entries belong to a timetable
- `teacher_absences` - Absences belong to a teacher
- `substitutions` - Substitutions belong to a school
- `school_settings` - Settings belong to a school

### Unique Constraints

Unique constraints include `tenant_id`:

```sql
-- Example: School codes are unique per tenant
CREATE UNIQUE INDEX ix_schools_tenant_code ON schools(tenant_id, code);

-- Example: User emails are unique per tenant
CREATE UNIQUE INDEX ix_users_tenant_email ON users(tenant_id, email);
```

## API Usage Examples

### Login

```bash
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant: school-slug" \
  -d '{
    "email": "admin@school.example",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Authenticated Request

```bash
curl -X GET https://api.yourdomain.com/api/v1/teachers \
  -H "Authorization: Bearer eyJ..." \
  -H "X-Tenant: school-slug"
```

### Multiple Schools Per Tenant

If a tenant has multiple schools, users can switch between them:

```bash
# List schools for tenant
curl -X GET https://api.yourdomain.com/api/v1/schools \
  -H "Authorization: Bearer eyJ..." \
  -H "X-Tenant: tenant-slug"

# Access specific school's data
curl -X GET https://api.yourdomain.com/api/v1/schools/4/teachers \
  -H "Authorization: Bearer eyJ..." \
  -H "X-Tenant: tenant-slug"
```

## Deployment Checklist

- [ ] Set `ENV=prod` in environment variables
- [ ] Remove or don't set `DEFAULT_TENANT_SLUG`
- [ ] Configure strong `SECRET_KEY` for JWT signing
- [ ] Set up HTTPS (SSL/TLS certificates)
- [ ] Configure CORS origins (production domains only)
- [ ] Set up database backups
- [ ] Configure reverse proxy to pass `X-Tenant` header
- [ ] Update frontend to send `X-Tenant` header
- [ ] Test tenant isolation (verify data separation)
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting per tenant
- [ ] Document tenant onboarding process

## Monitoring and Operations

### Tenant Management

```bash
# List all tenants
make list-tenants

# Create new tenant
make seed-tenant NAME="New School" SLUG="new-school"

# Create new school for tenant
make create-school TENANT_SLUG="new-school" NAME="School Name" CODE="SCHOOL001"

# Create test data
make create-test-data TENANT_SLUG="new-school" SCHOOL_CODE="SCHOOL001"
```

### Database Queries

```sql
-- List all tenants
SELECT id, name, slug, created_at FROM tenants;

-- List schools for a tenant
SELECT id, name, code FROM schools WHERE tenant_id = '<tenant-uuid>';

-- Count users per tenant
SELECT t.name, COUNT(u.id) as user_count
FROM tenants t
LEFT JOIN users u ON u.tenant_id = t.id
GROUP BY t.id, t.name;
```

### Troubleshooting

**Issue**: 400 Bad Request - "Tenant must be specified via X-Tenant header"
- **Solution**: Ensure frontend sends `X-Tenant` header with every request

**Issue**: 404 Not Found - "Tenant with slug 'xxx' not found"
- **Solution**: Verify tenant slug exists: `make list-tenants`

**Issue**: User can't access data
- **Solution**: Verify user's `tenant_id` matches X-Tenant header value

**Issue**: Cross-tenant data leakage
- **Solution**: Verify all repository queries include `tenant_id` filter

## Future Enhancements

### PostgreSQL RLS (Row Level Security)

When ready, enable RLS for additional security:

1. Enable RLS on all tenant-owned tables
2. Create policies that filter by `tenant_id`
3. Set tenant context in database session
4. Remove application-level filtering (optional, for performance)

See `docs/multitenancy.md` for RLS preparation details.

### Tenant-specific Configuration

Future enhancements could include:
- Tenant-specific feature flags
- Custom branding per tenant
- Tenant-specific rate limits
- Tenant-specific storage quotas

## Summary

**Production multi-tenancy works by:**

1. **Tenant Resolution**: Via `X-Tenant` header (required in prod)
2. **Data Isolation**: All queries filtered by `tenant_id` at application level
3. **Authentication**: Users belong to tenants, tokens don't include tenant_id
4. **Frontend**: Must send `X-Tenant` header with all requests
5. **Security**: Server-side validation, HTTPS required, CORS configured

The system is designed to scale horizontally while maintaining strict tenant isolation through application-level filtering.

