# Fix Script Execution Issue

## Problem
When running `python -m scripts.init_registry_db`, you get "No module named scripts.init_registry_db"

## Solution

Run the script directly instead of as a module:

```bash
# Instead of:
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.init_registry_db

# Use:
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/init_registry_db.py
```

## Alternative: Set Working Directory

Or ensure you're in the right directory:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend sh -c "cd /app && python -m scripts.init_registry_db"
```

## Updated Commands

### Initialize Registry
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/init_registry_db.py
```

### Create School
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/create_school.py --name "School Name" --code "SCHOOL001"
```

### Create Admin User
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python scripts/create_admin_user.py --school-code SCHOOL001 --email admin@school.com --password password
```

