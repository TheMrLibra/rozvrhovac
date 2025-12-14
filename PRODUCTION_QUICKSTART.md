# Production Quick Start Guide

Quick reference for deploying Rozvrhovac in production.

## 1. Setup Environment

```bash
# Copy example environment file
cp env.prod.example .env.prod

# Edit .env.prod with your values
nano .env.prod
```

**Important:** Set strong passwords and JWT secret!

## 2. Start Services

```bash
# Using Makefile
make up-prod

# Or directly
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## 3. Initialize Registry Database

```bash
# Using Makefile
make init-registry

# Or directly
docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.init_registry_db
```

## 4. Create Your First School

```bash
# Using Makefile
make create-school NAME="Your School" CODE="SCHOOL001"

# Or directly
docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend \
  python -m scripts.create_school --name "Your School" --code "SCHOOL001"
```

## 5. Create Admin User

```bash
# Using Makefile
make create-admin CODE="SCHOOL001" EMAIL="admin@school.com" PASSWORD="securepassword"

# Or directly
docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend \
  python -m scripts.create_admin_user \
    --school-code SCHOOL001 \
    --email admin@school.com \
    --password securepassword
```

## 6. Verify Deployment

```bash
# Check service status
make status-prod

# View logs
make logs-prod

# Test health endpoint
curl http://localhost:8000/health
```

## Common Commands

```bash
# View logs
make logs-prod

# Restart services
docker-compose -f docker-compose.prod.yml --env-file .env.prod restart

# Stop services
make down-prod

# Rebuild after code changes
make rebuild-prod
```

## Next Steps

1. Configure SSL/TLS certificates
2. Set up domain DNS
3. Configure automated backups
4. Set up monitoring
5. Review security settings

See `docker-compose.prod.README.md` for detailed documentation.

