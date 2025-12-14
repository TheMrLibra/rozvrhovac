# Local Development Setup

## Quick Start - One Command! 🚀

```bash
make dev-up
```

That's it! This single command will:
- ✅ Start Docker services (PostgreSQL, Backend, pgAdmin)
- ✅ Run all database migrations
- ✅ Create default tenant ("default-school")
- ✅ Create default school ("SCHOOL001")
- ✅ Create admin user (admin@school.example / admin123)

### Start Frontend

After `make dev-up` completes, start the frontend:

```bash
cd frontend

# Switch to Node.js 18+ (required)
nvm use  # or: nvm install 18 && nvm use 18

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Note**: The project requires Node.js >=18.0.0. If you see `crypto.getRandomValues is not a function`, upgrade Node.js.

## Access Points

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **pgAdmin**: http://localhost:5050 (admin@rozvrhovac.dev / admin)

## Login Credentials

- **Email**: `admin@school.example`
- **Password**: `admin123`
- **Header**: `X-Tenant: default-school`

## Access Points

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **pgAdmin**: http://localhost:5050 (admin@rozvrhovac.dev / admin)

## Testing the API

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant: default-school" \
  -d '{"email": "admin@school.local", "password": "admin123"}'
```

### Authenticated Request
```bash
curl -H "Authorization: Bearer <token>" \
     -H "X-Tenant: default-school" \
     http://localhost:8000/api/v1/auth/me
```

## Troubleshooting

**Migration fails?** Make sure you set `MIGRATION_DEFAULT_TENANT_ID` with the UUID from step 2.

**Tenant not found?** Run `make seed-tenant` again and check the slug matches.

**Backend not starting?** Check logs: `docker-compose -f docker-compose.dev.yml logs backend`

For more details, see [QUICK_START.md](./QUICK_START.md)

