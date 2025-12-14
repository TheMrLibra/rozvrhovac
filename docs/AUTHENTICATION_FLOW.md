# Authentication Flow - Automatic Tenant Detection

## Overview

Users can now log in from a single page without needing to specify their tenant. The system automatically determines the tenant and school from the user's email address and stores this information for all subsequent requests.

## Flow Diagram

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │
       │ 1. POST /api/v1/auth/login
       │    Body: {email, password}
       │    (NO X-Tenant header needed)
       │
       ▼
┌─────────────────┐
│   Backend API   │
└──────┬──────────┘
       │
       │ 2. Search user by email across all tenants
       │    SELECT * FROM users WHERE email = ?
       │
       │ 3. Verify password
       │
       │ 4. Get tenant and school information
       │    - tenant_id, tenant_slug
       │    - school_id, school_name
       │
       │ 5. Generate JWT tokens
       │
       │ 6. Return response:
       │    {
       │      access_token: "...",
       │      refresh_token: "...",
       │      tenant_id: "...",
       │      tenant_slug: "school-slug",
       │      school_id: 4,
       │      school_name: "School Name"
       │    }
       │
       ▼
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       │ 7. Store in localStorage:
       │    - access_token
       │    - refresh_token
       │    - tenant_slug  ← Used for X-Tenant header
       │    - school_id
       │    - school_name
       │
       │ 8. All subsequent API requests:
       │    Headers:
       │      Authorization: Bearer <token>
       │      X-Tenant: <tenant_slug>  ← Auto-added
       │
       ▼
```

## Backend Changes

### Login Endpoint (`/api/v1/auth/login`)

**Before:**
- Required `X-Tenant` header
- Searched user only in specified tenant

**After:**
- No `X-Tenant` header required
- Searches user across all tenants
- Returns tenant and school information in response

**Response Schema:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "tenant_id": "uuid-here",
  "tenant_slug": "school-slug",
  "school_id": 4,
  "school_name": "School Name"
}
```

### User Repository

Added `get_by_email_any_tenant()` method:
- Searches across all tenants when `tenant_id` is not provided
- Used for login without tenant context

### User Service

Updated `authenticate_user()`:
- If `tenant_id` is `None`, searches across all tenants
- If `tenant_id` is provided, searches only in that tenant (for backward compatibility)

## Frontend Changes

### Auth Store (`stores/auth.ts`)

**New State:**
- `tenantSlug` - Tenant slug from login response
- `schoolId` - School ID from login response
- `schoolName` - School name from login response

**Login Flow:**
1. Call `/auth/login` without `X-Tenant` header
2. Receive tenant and school information in response
3. Store in localStorage and reactive state
4. All subsequent requests use stored `tenant_slug`

**Logout:**
- Clears all tenant and school information from localStorage

### API Client (`services/api.ts`)

**Request Interceptor:**
- Automatically adds `X-Tenant` header from localStorage
- Excludes `/auth/login` endpoint (doesn't need tenant header)
- Uses `tenant_slug` stored during login

## Usage Examples

### Login

```typescript
// Frontend - No tenant needed!
await authStore.login('user@example.com', 'password')

// Backend automatically:
// 1. Finds user by email across all tenants
// 2. Returns tenant_slug, school_id, school_name
// 3. Frontend stores in localStorage
```

### Subsequent Requests

```typescript
// All API requests automatically include X-Tenant header
await api.get('/teachers')  // X-Tenant: school-slug (auto-added)
await api.get('/subjects')  // X-Tenant: school-slug (auto-added)
```

### Multiple Subdomains

If you have multiple subdomains (e.g., `school1.app.com`, `school2.app.com`):

**Option 1: Same login page for all**
- Users log in from `app.com/login` or any subdomain
- System determines tenant from email
- Works seamlessly across subdomains

**Option 2: Subdomain-specific login**
- Each subdomain can have its own login page
- Still works the same way - no tenant selection needed
- Tenant determined from user email

## Benefits

1. **Better UX**: Users don't need to know their tenant/school
2. **Simpler Frontend**: No tenant selection UI needed
3. **Flexible**: Works with single domain or multiple subdomains
4. **Backward Compatible**: Still supports X-Tenant header if needed
5. **Automatic**: Tenant context automatically maintained across requests

## Security Considerations

1. **Email Uniqueness**: Emails are unique per tenant, not globally
   - If same email exists in multiple tenants, first match is returned
   - Consider enforcing global email uniqueness if needed

2. **Tenant Isolation**: Still enforced at application level
   - All queries filtered by `tenant_id`
   - Users can only access their tenant's data

3. **Token Security**: JWT tokens don't contain tenant_id
   - Tenant determined from user record or X-Tenant header
   - Prevents token reuse across tenants

## Migration Notes

### Existing Users

- No changes needed for existing users
- Login flow automatically works with new system
- Tenant information stored on first login after update

### API Compatibility

- Login endpoint still accepts `X-Tenant` header (optional)
- If provided, searches only in that tenant (backward compatibility)
- If not provided, searches across all tenants (new behavior)

### Frontend Migration

- Update auth store to handle new login response format
- Update API client to add X-Tenant header automatically
- Clear localStorage on logout to remove old tenant data

## Testing

### Test Cases

1. **Login without tenant**
   ```bash
   curl -X POST /api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password"}'
   ```
   Should return tenant and school information.

2. **Login with tenant (backward compatibility)**
   ```bash
   curl -X POST /api/v1/auth/login \
     -H "Content-Type: application/json" \
     -H "X-Tenant: school-slug" \
     -d '{"email": "user@example.com", "password": "password"}'
   ```
   Should work as before.

3. **Subsequent requests**
   - Verify X-Tenant header is automatically added
   - Verify tenant context is correctly resolved

## Summary

The authentication flow now automatically determines tenant and school from the user's email, eliminating the need for users to specify their tenant during login. The system stores this information and automatically includes it in all subsequent API requests, providing a seamless multi-tenant experience.

