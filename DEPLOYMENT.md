# Production Deployment Steps

## After Git Pull on Production Server

When you pull new code changes on the production server, follow these steps:

### 1. Pull the latest code
```bash
git pull origin main  # or your main branch name
```

### 2. Rebuild and restart the backend container
```bash
# Option A: Using Makefile (recommended)
make rebuild-backend-prod

# Option B: Manual commands
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d backend
```

### 3. Verify the deployment
```bash
# Check backend logs for any errors
make prod-logs-backend

# Or manually:
docker compose -f docker-compose.prod.yml logs backend --tail=50 -f

# Check if backend is healthy
curl http://localhost:8000/health
```

### 4. (Optional) Rebuild frontend if frontend code changed
```bash
make rebuild-frontend-prod
```

## Quick Deployment Checklist

- [ ] `git pull` - Pull latest code
- [ ] `make rebuild-backend-prod` - Rebuild backend container
- [ ] `make prod-logs-backend` - Check for errors
- [ ] Test the API endpoint that was changed
- [ ] (If frontend changed) `make rebuild-frontend-prod`

## Troubleshooting

### Backend not picking up changes?
- Make sure you rebuilt the container: `make rebuild-backend-prod`
- Check if the code is actually in the container:
  ```bash
  docker compose -f docker-compose.prod.yml exec backend cat /app/app/api/v1/teachers_router.py | grep -A 5 "NULL-aware"
  ```

### Still getting errors?
- Check backend logs: `make prod-logs-backend`
- Verify the container is running: `docker compose -f docker-compose.prod.yml ps`
- Restart the backend: `docker compose -f docker-compose.prod.yml restart backend`

### Need to see actual error details?
```bash
# View real-time logs
docker compose -f docker-compose.prod.yml logs backend -f

# View last 100 lines
docker compose -f docker-compose.prod.yml logs backend --tail=100
```

