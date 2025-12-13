# Rebuild Container to Include Scripts

## Problem
The scripts don't exist in the container because it was built before the scripts were added.

## Solution: Rebuild the Backend Container

### Option 1: Rebuild just the backend service

```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod build backend
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod up -d backend
```

### Option 2: Rebuild all services

```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### Option 3: Using Makefile (if available)

```bash
make rebuild-prod
```

## After Rebuilding

Then run the script:

```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/init_registry_db.py
```

## Verify Scripts Are in Container

Check if scripts exist:

```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend ls -la /app/scripts/
```

You should see `init_registry_db.py` in the output.

