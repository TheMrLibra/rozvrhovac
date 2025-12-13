# Production Docker Compose Setup

This document explains how to deploy Rozvrhovac in production using Docker Compose with multi-tenant database support.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Sufficient disk space for databases
- Domain name and SSL certificates (for HTTPS)

## Quick Start

1. **Copy environment file:**
   ```bash
   cp env.prod.example .env.prod
   ```

2. **Edit `.env.prod` with your production values:**
   - Set strong passwords for databases
   - Set a strong JWT secret key (minimum 32 characters)
   - Configure CORS origins for your domain
   - Update API URL if needed

3. **Build and start services:**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

4. **Initialize registry database:**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.init_registry_db
   ```

5. **Create your first school:**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_school \
     --name "Your School Name" \
     --code "SCHOOL001"
   ```

6. **Create admin user:**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env-file .env.prod exec backend python -m scripts.create_admin_user \
     --school-code SCHOOL001 \
     --email admin@yourschool.com \
     --password securepassword
   ```

## Architecture

### Services

1. **postgres-registry**: Registry database storing school metadata
2. **postgres**: Main PostgreSQL instance for school databases
3. **backend**: FastAPI backend application
4. **nginx-backend**: Reverse proxy for backend API
5. **frontend**: Vue.js frontend application
6. **nginx-frontend**: Reverse proxy for frontend

### Network

All services are on a private bridge network (`rozvrhovac-network`) for security.

### Volumes

- `registry_db_data`: Registry database data
- `postgres_data`: School databases data

## Production Considerations

### Security

1. **Change all default passwords** in `.env.prod`
2. **Use strong JWT secret** (generate with `openssl rand -hex 32`)
3. **Don't expose database ports** publicly (ports are commented out)
4. **Use HTTPS** - configure SSL certificates in nginx configs
5. **Restrict CORS origins** to your actual domains
6. **Regular security updates** - keep images updated

### SSL/TLS Setup

To enable HTTPS, you'll need to:

1. Obtain SSL certificates (Let's Encrypt recommended)
2. Update nginx configs to use SSL
3. Add certificate volumes to docker-compose
4. Configure certificate renewal

Example nginx SSL configuration:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    # ... rest of config
}
```

### Database Backups

Set up regular backups:

```bash
# Backup registry database
docker-compose -f docker-compose.prod.yml exec postgres-registry pg_dump -U postgres rozvrhovac_registry > registry_backup.sql

# Backup a school database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres rozvrhovac_school001 > school001_backup.sql
```

Automate backups with cron or a backup service.

### Monitoring

Consider adding:
- **Prometheus** for metrics
- **Grafana** for dashboards
- **ELK Stack** for logging
- **Health check endpoints** monitoring

### Scaling

- **Backend**: Can be scaled horizontally (stateless)
- **Frontend**: Can be scaled horizontally (stateless)
- **Databases**: Each school database can be scaled independently if needed

Example scaling backend:
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --scale backend=3
```

### Resource Limits

Add resource limits to docker-compose for production:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Environment Variables

See `.env.prod.example` for all available environment variables.

### Required Variables

- `REGISTRY_DB_PASSWORD`: Registry database password
- `DB_PASSWORD`: Main database password
- `SECRET_KEY`: JWT secret key
- `CORS_ORIGINS`: Allowed CORS origins

### Optional Variables

- `BACKEND_PORT`: Backend port (default: 8000)
- `FRONTEND_PORT`: Frontend port (default: 3000)
- `LOG_LEVEL`: Logging level (default: INFO)

## Maintenance

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Restart Services

```bash
docker-compose -f docker-compose.prod.yml restart backend
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### Database Migrations

Run migrations on a school database:

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Note: Migrations are automatically run when creating a new school.

## Troubleshooting

### Services Won't Start

1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify environment variables are set correctly
3. Check disk space: `df -h`
4. Verify ports aren't in use: `netstat -tulpn | grep <port>`

### Database Connection Errors

1. Verify database containers are healthy: `docker-compose ps`
2. Check database logs: `docker-compose logs postgres`
3. Verify credentials in `.env.prod`
4. Test connection: `docker-compose exec backend python -c "from app.core.database_manager import get_registry_db; import asyncio; asyncio.run(list(get_registry_db()))"`

### Registry Not Found

1. Ensure registry database is initialized: `python -m scripts.init_registry_db`
2. Check registry database exists: `docker-compose exec postgres-registry psql -U postgres -l`
3. Verify REGISTRY_DATABASE_URL in backend logs

## Backup and Restore

### Backup Script

Create a backup script:

```bash
#!/bin/bash
BACKUP_DIR="/backups/rozvrhovac"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup registry
docker-compose -f docker-compose.prod.yml exec -T postgres-registry pg_dump -U postgres rozvrhovac_registry > "$BACKUP_DIR/registry_$DATE.sql"

# Backup all school databases (list them first)
# docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres rozvrhovac_school001 > "$BACKUP_DIR/school001_$DATE.sql"
```

### Restore

```bash
# Restore registry
docker-compose -f docker-compose.prod.yml exec -T postgres-registry psql -U postgres rozvrhovac_registry < registry_backup.sql

# Restore school database
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres rozvrhovac_school001 < school001_backup.sql
```

## Next Steps

1. Set up SSL/TLS certificates
2. Configure domain DNS to point to your server
3. Set up automated backups
4. Configure monitoring and alerting
5. Review and harden security settings
6. Set up CI/CD pipeline for deployments

