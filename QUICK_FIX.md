# Quick Fix for Your Current Issue

## Step 1: Resolve the Merge Conflict

```bash
# Use the new multi-tenant version (recommended)
sudo git checkout --ours docker-compose.prod.yml

# Mark as resolved
sudo git add docker-compose.prod.yml

# Verify
sudo git status
```

## Step 2: Install Docker Compose (if needed)

Check which command is available:

```bash
# Check for docker-compose standalone
which docker-compose

# Check for docker compose plugin
docker compose version
```

If neither works, install docker-compose:

```bash
sudo apt update
sudo apt install docker-compose
```

Or if you have Docker 20.10+, the plugin should be available. Try:

```bash
docker compose version
```

## Step 3: Pull Latest Changes

```bash
sudo git pull
```

## Step 4: Create .env.prod File

```bash
# Copy example
sudo cp env.prod.example .env.prod

# Edit with your values
sudo nano .env.prod
```

**Important:** Set strong passwords and JWT secret!

## Step 5: Start Production Services

```bash
# Using Makefile (now supports both docker-compose and docker compose)
make up-prod

# Or manually
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
# OR
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Troubleshooting

### If "docker-compose: No such file or directory"

The Makefile now auto-detects which command to use. If it still fails:

1. Check if `docker compose` works:
   ```bash
   docker compose version
   ```

2. If that works, the Makefile should use it automatically

3. If neither works, install docker-compose:
   ```bash
   sudo apt install docker-compose
   ```

### If conflict persists

```bash
# View the conflict
sudo git diff docker-compose.prod.yml

# Use our version
sudo git checkout --ours docker-compose.prod.yml
sudo git add docker-compose.prod.yml
```

