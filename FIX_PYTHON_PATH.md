# Fix Python Module Path Issue

## Problem
When running scripts, Python can't find the `app` module because it's not in the Python path.

## Solution

Run scripts from `/app` directory using `python -m`:

```bash
# Instead of:
docker compose exec backend python scripts/init_registry_db.py

# Use:
docker compose exec backend sh -c "cd /app && python -m scripts.init_registry_db"
```

## Correct Commands

### Initialize Registry
```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend sh -c "cd /app && python -m scripts.init_registry_db"
```

### Create School
```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend sh -c "cd /app && python -m scripts.create_school --name 'School Name' --code 'SCHOOL001'"
```

### Create Admin User
```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend sh -c "cd /app && python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.com --password password"
```

## Alternative: Set PYTHONPATH

You can also set PYTHONPATH:

```bash
sudo docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend sh -c "PYTHONPATH=/app python scripts/init_registry_db.py"
```

But using `cd /app && python -m scripts.*` is cleaner and matches the script's intended usage.

