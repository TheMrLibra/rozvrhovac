# Resolving Merge Conflict in docker-compose.prod.yml

You have a merge conflict in `docker-compose.prod.yml`. Here's how to resolve it:

## Option 1: Use the New Multi-Tenant Version (Recommended)

The new version includes multi-tenant database support. To use it:

```bash
# Use the current branch version (the new multi-tenant one)
sudo git checkout --ours docker-compose.prod.yml

# Mark as resolved
sudo git add docker-compose.prod.yml

# Verify the conflict is resolved
sudo git status
```

## Option 2: Use the Stashed Version

If you want to keep the version from the Deployment branch:

```bash
# Use the stashed version
sudo git checkout --theirs docker-compose.prod.yml

# Mark as resolved
sudo git add docker-compose.prod.yml

# Verify the conflict is resolved
sudo git status
```

## Option 3: Manual Resolution

If you want to manually merge both versions:

1. Open the file and look for conflict markers:
   ```
   <<<<<<< Updated upstream
   (content from Deployment branch)
   =======
   (content from your stashed changes)
   >>>>>>> Stashed changes
   ```

2. Edit the file to combine both versions as needed
3. Remove the conflict markers
4. Save the file
5. Mark as resolved:
   ```bash
   sudo git add docker-compose.prod.yml
   ```

## After Resolving

Once the conflict is resolved:

```bash
# Verify status
sudo git status

# The file should show as resolved
# You can now continue with your work
```

## Installing Docker Compose

If you're getting "docker-compose: No such file or directory", you have two options:

### Option A: Install docker-compose standalone

```bash
sudo apt update
sudo apt install docker-compose
```

### Option B: Use Docker Compose Plugin (Recommended)

Modern Docker installations include `docker compose` (with a space) as a plugin:

```bash
# Check if docker compose plugin is available
docker compose version

# If available, the Makefile will automatically use it
# The Makefile has been updated to detect both commands
```

The Makefile has been updated to automatically detect and use whichever command is available (`docker-compose` or `docker compose`).

