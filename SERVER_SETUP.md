# Server Setup Instructions

## Quick Fix for Docker Compose Issue

On your server, run these commands:

### Step 1: Check which command works

```bash
# Try docker compose (plugin - modern Docker)
docker compose version

# If that doesn't work, try docker-compose (standalone)
docker-compose --version
```

### Step 2: Use the working command directly

**If `docker compose` works (recommended):**

```bash
# Start production services
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Initialize registry
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.init_registry_db

# Create school
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_school --name "School Name" --code "SCHOOL001"

# Create admin
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.com --password password
```

**If `docker-compose` works:**

Replace `docker compose` with `docker-compose` in all commands above.

### Step 3: Make Makefile work (Optional)

**Option A: Create alias**

```bash
echo 'alias docker-compose="docker compose"' >> ~/.bashrc
source ~/.bashrc
```

**Option B: Use the wrapper script**

```bash
# The wrapper script should work automatically
make up-prod
```

**Option C: Install docker-compose standalone**

```bash
sudo apt update
sudo apt install docker-compose
```

## Complete Setup Sequence

```bash
# 1. Resolve merge conflict (if not done)
sudo git checkout --ours docker-compose.prod.yml
sudo git add docker-compose.prod.yml

# 2. Pull latest changes
sudo git pull

# 3. Create .env.prod (if not done)
sudo cp env.prod.example .env.prod
sudo nano .env.prod  # Edit with your values

# 4. Start services
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 5. Initialize registry
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.init_registry_db

# 6. Create your first school
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_school --name "Your School" --code "SCHOOL001"

# 7. Create admin user
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.com --password yourpassword
```

## Verify Everything Works

```bash
# Check service status
docker compose -f docker-compose.prod.yml --env-file .env.prod ps

# View logs
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f

# Test health endpoint
curl http://localhost:8000/health
```

## Troubleshooting

### "docker-compose: No such file or directory"

This means `docker-compose` standalone is not installed. Use `docker compose` (with space) instead - it's the modern Docker Compose plugin.

### Makefile still doesn't work

Just use `docker compose` commands directly. The Makefile is just a convenience wrapper.

### Permission denied

Make sure you're using `sudo` where needed, or add your user to the docker group:

```bash
sudo usermod -aG docker $USER
# Then logout and login again
```

