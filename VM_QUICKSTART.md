# VM Architecture Quick Start

## Application VM (VM 2) - Quick Setup

```bash
# 1. Use VM-specific compose file
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod up -d

# 2. Initialize registry
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod exec backend python -m scripts.init_registry_db

# 3. Create school
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod exec backend \
  python -m scripts.create_school --name "School Name" --code "SCHOOL001"

# 4. Create admin
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod exec backend \
  python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.com --password password

# 5. Get VM IP (needed for nginx config)
hostname -I
```

## Nginx VM (VM 1) - Quick Setup

```bash
# 1. Install nginx
sudo apt update && sudo apt install nginx

# 2. Copy configs (from project)
# Edit nginx/vm-reverse-proxy-backend.conf
# Edit nginx/vm-reverse-proxy-frontend.conf
# Replace <APPLICATION_VM_IP> with VM 2's IP

# 3. Enable sites
sudo cp nginx/vm-reverse-proxy-backend.conf /etc/nginx/sites-available/rozvrhovac-backend
sudo cp nginx/vm-reverse-proxy-frontend.conf /etc/nginx/sites-available/rozvrhovac-frontend
sudo ln -s /etc/nginx/sites-available/rozvrhovac-backend /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/rozvrhovac-frontend /etc/nginx/sites-enabled/

# 4. Test and reload
sudo nginx -t
sudo systemctl reload nginx

# 5. Configure SSL (optional)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

## Using Makefile (if available)

```bash
# On Application VM
make up-prod-vm
make init-registry-vm
make create-school-vm NAME="School" CODE="SCHOOL001"
make create-admin-vm CODE="SCHOOL001" EMAIL="admin@school.com" PASSWORD="password"
```

## Key Differences

- **docker-compose.prod.yml**: Includes nginx services (single VM setup)
- **docker-compose.prod.vm.yml**: No nginx services (separate nginx VM)

Use `docker-compose.prod.vm.yml` when nginx runs on a separate VM.

