# Deployment Guide

This guide explains how to deploy the Rozvrhovac application with multi-tenant database support.

## Architecture

The application uses a multi-tenant architecture where:
- **One backend instance** serves all schools
- **Each school has its own database** for data isolation
- **Registry database** stores metadata about schools and their database connections

## Prerequisites

- PostgreSQL database server
- Python 3.9+ (for backend)
- Node.js 18+ (for frontend)
- Docker and Docker Compose (optional, for containerized deployment)

## Database Setup

### 1. Initialize Registry Database

The registry database stores metadata about all schools. Initialize it first:

```bash
cd backend
python -m scripts.init_registry_db
```

This will:
- Create the registry database (default: `rozvrhovac_registry`)
- Create the `school_registry` table

### 2. Environment Variables

Set the following environment variables for the backend:

```bash
# Registry Database (stores school metadata)
REGISTRY_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac_registry

# Default database connection settings (used when creating new school databases)
DEFAULT_DB_HOST=localhost
DEFAULT_DB_PORT=5432
DEFAULT_DB_USER=postgres
DEFAULT_DB_PASSWORD=postgres  # Change in production!

# JWT Secret (change in production!)
SECRET_KEY=your-secret-key-change-in-production

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Creating Schools

### Create a New School

To create a new school and its database:

```bash
cd backend
python -m scripts.create_school \
  --name "School Name" \
  --code "SCHOOL001" \
  [--db-host localhost] \
  [--db-port 5432] \
  [--db-user postgres] \
  [--db-password postgres]
```

This script will:
1. Create a new PostgreSQL database (named `rozvrhovac_school001`)
2. Run migrations on the new database
3. Create the school record in the school database
4. Create default school settings
5. Register the school in the registry database

### Create Admin User for a School

After creating a school, create an admin user:

```bash
cd backend
python -m scripts.create_admin_user \
  --school-code SCHOOL001 \
  --email admin@school.local \
  --password securepassword
```

## API Usage

### Login

The login endpoint now requires a `school_code` in the request body:

```json
POST /api/v1/auth/login
{
  "email": "admin@school.local",
  "password": "securepassword",
  "school_code": "SCHOOL001"
}
```

The backend will:
1. Look up the school in the registry database
2. Connect to the school's database
3. Authenticate the user
4. Return JWT tokens with `school_id` included

### Subsequent Requests

After login, include the JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

The backend extracts `school_id` from the JWT token and routes to the correct database automatically.

Alternatively, you can use the `X-School-Code` header:

```
X-School-Code: SCHOOL001
```

## Docker Deployment

### Using Docker Compose

1. Update environment variables in `docker-compose.yml` or use `.env` file
2. Build and start services:

```bash
docker-compose up -d
```

3. Initialize registry database:

```bash
docker-compose exec backend python -m scripts.init_registry_db
```

4. Create schools and admin users as described above

### Kubernetes Deployment

1. Update `k8s/configmap.yaml` with your configuration
2. Create secrets in `k8s/secret.yaml` (use `secret.yaml.example` as template)
3. Apply configurations:

```bash
kubectl apply -f k8s/
```

4. Initialize registry database in the backend pod:

```bash
kubectl exec -it <backend-pod-name> -- python -m scripts.init_registry_db
```

## Database Migrations

### School Databases

Each school database needs migrations run separately. The `create_school` script automatically runs migrations when creating a new school.

To run migrations on an existing school database:

```bash
# Set DATABASE_URL to the school's database
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac_school001
alembic upgrade head
```

### Registry Database

The registry database uses a simple table structure. If you need to modify it, create a migration manually or update the `init_registry_db.py` script.

## Security Considerations

1. **Database Passwords**: Store database passwords securely (use secrets manager in production)
2. **JWT Secret**: Use a strong, random secret key in production
3. **Database Access**: Restrict database access to only the backend application
4. **Network Security**: Use SSL/TLS for database connections in production
5. **CORS**: Configure CORS origins appropriately for your frontend domain

## Monitoring

Monitor:
- Registry database connections
- School database connections (per school)
- Database sizes and performance
- Failed login attempts
- School creation/deletion events

## Troubleshooting

### School Not Found

If you get "School not found" errors:
1. Verify the school exists in the registry: Check `school_registry` table
2. Verify the school database exists
3. Check database connection settings

### Database Connection Errors

1. Verify database server is running
2. Check connection credentials
3. Verify network connectivity
4. Check PostgreSQL logs

### Migration Errors

1. Ensure Alembic is configured correctly
2. Check that all models are imported
3. Verify database permissions
4. Check migration history

## Backup Strategy

1. **Registry Database**: Backup regularly (contains school metadata)
2. **School Databases**: Backup each school database separately
3. **Backup Frequency**: Consider daily backups for production
4. **Backup Retention**: Keep backups for at least 30 days

## Scaling Considerations

- **Database Connections**: Each school database maintains its own connection pool
- **Backend Scaling**: Backend can be scaled horizontally (stateless)
- **Database Scaling**: Each school database can be scaled independently if needed
- **Load Balancing**: Use sticky sessions or ensure school context is in every request

