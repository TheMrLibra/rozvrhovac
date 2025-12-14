# Deployment and Onboarding Guide

## Production Deployment

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL database (or use Docker Compose)
- Domain name configured (optional, for subdomains)
- SSL certificates (for HTTPS)

### Step 1: Environment Setup

Create `.env.prod` file:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=<strong-password>
DATABASE_URL=postgresql+asyncpg://postgres:<password>@postgres:5432/rozvrhovac

# Application
ENV=prod
PROJECT_NAME=Rozvrhovac
API_V1_STR=/api/v1

# JWT Security
SECRET_KEY=<generate-strong-random-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (comma-separated list of allowed origins)
CORS_ORIGINS=https://app.yourdomain.com,https://api.yourdomain.com

# Logging
LOG_LEVEL=INFO

# Multi-tenancy
# DEFAULT_TENANT_SLUG not set in prod - tenant determined from user email
MIGRATION_DEFAULT_TENANT_ID=<uuid-of-first-tenant-for-migrations>
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Deploy Services

```bash
# Start production services
make prod-up

# Or manually:
docker-compose -f docker-compose.prod.yml up -d
```

### Step 3: Run Database Migrations

```bash
# First, create a tenant (see Step 4)
# Then set MIGRATION_DEFAULT_TENANT_ID in .env.prod
# Run migrations
make migrate-prod

# Or manually:
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 4: Create First Tenant

```bash
# Create a tenant
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.seed_tenant \
  --name "First School" \
  --slug "first-school"

# Note the tenant UUID from output, add to .env.prod:
# MIGRATION_DEFAULT_TENANT_ID=<tenant-uuid>
```

### Step 5: Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Test health endpoint
curl http://localhost:8000/health
```

## Creating a New School and Admin

### Option 1: Create School with Admin (Recommended)

This creates both the school and admin user in one command:

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_school \
  --tenant-slug "first-school" \
  --name "My School" \
  --code "SCHOOL001" \
  --create-admin \
  --admin-email "admin@myschool.example" \
  --admin-password "SecurePassword123!"
```

**Output:**
```
🏫 Creating new school...

✅ Found tenant: First School (first-school)
📦 Creating school: My School (code: SCHOOL001)...
✅ School created (ID: 4)
📦 Creating default school settings...
✅ Default school settings created
📦 Creating admin user: admin@myschool.example...
✅ Admin user created (ID: 1)

============================================================
✅ School creation complete!
============================================================

📋 Summary:
   Tenant: First School (first-school)
   School: My School (SCHOOL001)
   School ID: 4
   Admin Email: admin@myschool.example
   Admin Password: SecurePassword123!
```

### Option 2: Create School and Admin Separately

**Step 1: Create the school**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_school \
  --tenant-slug "first-school" \
  --name "My School" \
  --code "SCHOOL001"
```

**Step 2: Create admin user**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_admin_user \
  --tenant-slug "first-school" \
  --email "admin@myschool.example" \
  --password "SecurePassword123!" \
  --school-code "SCHOOL001"
```

### Option 3: Using Make Commands (Development)

For development environment:

```bash
# Create school with admin
make create-school \
  TENANT_SLUG="first-school" \
  NAME="My School" \
  CODE="SCHOOL001" \
  CREATE_ADMIN=--create-admin \
  ADMIN_EMAIL="admin@myschool.example" \
  ADMIN_PASSWORD="SecurePassword123!"

# Create admin separately
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.create_admin_user \
  --tenant-slug "first-school" \
  --email "admin@myschool.example" \
  --password "SecurePassword123!" \
  --school-code "SCHOOL001"
```

## Complete Onboarding Workflow

### For a New Customer/School

**1. Create Tenant (if new organization)**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.seed_tenant \
  --name "Customer Name" \
  --slug "customer-slug"
```

**2. Create School with Admin**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_school \
  --tenant-slug "customer-slug" \
  --name "School Name" \
  --code "SCHOOL001" \
  --create-admin \
  --admin-email "admin@school.example" \
  --admin-password "SecurePassword123!"
```

**3. (Optional) Create Test Data**
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_test_data \
  --tenant-slug "customer-slug" \
  --school-code "SCHOOL001"
```

**4. Provide Login Credentials**
- Email: `admin@school.example`
- Password: `SecurePassword123!`
- Login URL: `https://app.yourdomain.com/login`

The user can now log in - the system will automatically determine their tenant and school from their email!

## Management Commands

### List All Tenants and Schools

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.list_tenants
```

**Output:**
```
📋 Tenants and Schools
============================================================

🏢 Tenant: First School
   Slug: first-school
   ID: 550e8400-e29b-41d4-a716-446655440000
   Created: 2024-01-15 10:30:00
   Schools (2):
      • My School (SCHOOL001) - ID: 4
      • Another School (SCHOOL002) - ID: 5

🏢 Tenant: Second School
   Slug: second-school
   ID: 660e8400-e29b-41d4-a716-446655440001
   Created: 2024-01-16 14:20:00
   Schools (1):
      • Their School (SCHOOL001) - ID: 6

============================================================
Total: 2 tenant(s)
```

### Create Additional Schools for Existing Tenant

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_school \
  --tenant-slug "first-school" \
  --name "Second School Location" \
  --code "SCHOOL002" \
  --create-admin \
  --admin-email "admin2@myschool.example" \
  --admin-password "SecurePassword123!"
```

### Create Additional Admin Users

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_admin_user \
  --tenant-slug "first-school" \
  --email "admin2@myschool.example" \
  --password "SecurePassword123!" \
  --school-code "SCHOOL001"
```

## Production Make Commands

Add these to your `Makefile` for easier production management:

```makefile
# Production commands
prod-create-tenant: ## Create a tenant in production
	docker-compose -f docker-compose.prod.yml exec backend python -m scripts.seed_tenant --name "$(NAME)" --slug "$(SLUG)"

prod-create-school: ## Create a school in production
	docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_school --tenant-slug "$(TENANT_SLUG)" --name "$(NAME)" --code "$(CODE)" $(CREATE_ADMIN) $(if $(ADMIN_EMAIL),--admin-email "$(ADMIN_EMAIL)") $(if $(ADMIN_PASSWORD),--admin-password "$(ADMIN_PASSWORD)")

prod-create-admin: ## Create admin user in production
	docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_admin_user --tenant-slug "$(TENANT_SLUG)" --email "$(EMAIL)" --password "$(PASSWORD)" --school-code "$(SCHOOL_CODE)"

prod-list-tenants: ## List tenants in production
	docker-compose -f docker-compose.prod.yml exec backend python -m scripts.list_tenants

prod-create-test-data: ## Create test data in production
	docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_test_data --tenant-slug "$(TENANT_SLUG)" --school-code "$(SCHOOL_CODE)" $(FORCE)
```

## Verification Steps

### 1. Verify Tenant Created

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.list_tenants
```

### 2. Test Login

```bash
curl -X POST https://api.yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@myschool.example",
    "password": "SecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_slug": "first-school",
  "school_id": 4,
  "school_name": "My School"
}
```

### 3. Test Authenticated Request

```bash
curl -X GET https://api.yourdomain.com/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Troubleshooting

### Issue: "Tenant not found"

**Solution:** List tenants to verify slug:
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.list_tenants
```

### Issue: "School code already exists"

**Solution:** School codes must be unique per tenant. Use a different code:
```bash
--code "SCHOOL002"  # Instead of SCHOOL001
```

### Issue: "User already exists"

**Solution:** The script will update the password automatically. Or use a different email.

### Issue: Migration fails

**Solution:** Ensure `MIGRATION_DEFAULT_TENANT_ID` is set in `.env.prod`:
1. Create a tenant first
2. Copy the tenant UUID from output
3. Add to `.env.prod`: `MIGRATION_DEFAULT_TENANT_ID=<uuid>`
4. Run migrations again

## Security Best Practices

1. **Strong Passwords**: Use strong, randomly generated passwords for admin users
2. **SECRET_KEY**: Generate a strong, random SECRET_KEY for JWT signing
3. **HTTPS**: Always use HTTPS in production
4. **Database Backups**: Set up regular database backups
5. **Environment Variables**: Never commit `.env.prod` to version control
6. **Access Control**: Limit who can run these scripts (use SSH keys, etc.)

## Quick Reference

```bash
# Deploy
make prod-up
make migrate-prod

# Create tenant
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.seed_tenant \
  --name "Name" --slug "slug"

# Create school with admin
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.create_school \
  --tenant-slug "slug" --name "School" --code "SCHOOL001" \
  --create-admin --admin-email "admin@example.com" --admin-password "pass"

# List tenants
docker-compose -f docker-compose.prod.yml exec backend python -m scripts.list_tenants
```

## Summary

The deployment process is straightforward:

1. **Deploy** services with `make prod-up`
2. **Create tenant** for new organization
3. **Create school** with admin user in one command
4. **Provide credentials** to customer
5. **Customer logs in** - system automatically determines tenant/school from email

No manual tenant selection needed - the system handles it automatically! 🎉

