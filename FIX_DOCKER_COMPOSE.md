# Fix Docker Compose Command Issue

## Quick Fix

The Makefile should auto-detect, but if it's not working, try this:

### Option 1: Use docker compose directly (Recommended)

```bash
# Check if docker compose plugin works
docker compose version

# If it works, use it directly:
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Option 2: Install docker-compose standalone

```bash
sudo apt update
sudo apt install docker-compose
```

### Option 3: Create an alias

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias docker-compose='docker compose'
```

Then reload:
```bash
source ~/.bashrc
```

## Test Which Command Works

Run this script:

```bash
chmod +x check-docker-compose.sh
./check-docker-compose.sh
```

## Manual Commands (No Makefile)

If Makefile still doesn't work, use these commands directly:

```bash
# Start production
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Or if docker-compose is installed:
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Initialize registry
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.init_registry_db

# Create school
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_school --name "School Name" --code "SCHOOL001"

# Create admin
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.com --password password

# View logs
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f

# Stop
docker compose -f docker-compose.prod.yml --env-file .env.prod down
```

