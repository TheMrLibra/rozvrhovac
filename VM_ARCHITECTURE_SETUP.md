# VM Architecture Setup Guide

This guide covers deployment with:
- **VM 1**: Nginx Reverse Proxy
- **VM 2**: Application (Backend, Frontend, Databases)

## Architecture Overview

```
Internet
   │
   ▼
[VM 1: Nginx Reverse Proxy]
   │
   ├───► [VM 2: Frontend Container] (port 80)
   └───► [VM 2: Backend Container] (port 8000)
   │
   └───► [VM 2: Databases] (internal only)
```

## VM 2: Application VM Setup

### 1. Clone and Setup

```bash
cd /opt/rozvrhovac
sudo git pull
sudo git checkout Deployment  # or your branch
```

### 2. Create Environment File

```bash
sudo cp env.prod.example .env.prod
sudo nano .env.prod
```

**Important settings:**
```bash
# Set strong passwords
REGISTRY_DB_PASSWORD=strong-password-here
DB_PASSWORD=strong-password-here

# Set JWT secret (generate with: openssl rand -hex 32)
SECRET_KEY=your-generated-secret-key-here

# Set CORS to your frontend domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Set API URL for frontend
VITE_API_URL=https://api.yourdomain.com
```

### 3. Start Services

```bash
# Use the VM-specific compose file (no nginx services)
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod up -d
```

### 4. Initialize Registry

```bash
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod exec backend python -m scripts.init_registry_db
```

### 5. Create School and Admin

```bash
# Create school
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod exec backend \
  python -m scripts.create_school --name "Your School" --code "SCHOOL001"

# Create admin
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod exec backend \
  python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.com --password password
```

### 6. Get Application VM IP

```bash
# Find the IP address of this VM
ip addr show | grep "inet " | grep -v 127.0.0.1
# Or
hostname -I
```

**Note this IP** - you'll need it for the nginx configuration on VM 1.

## VM 1: Nginx Reverse Proxy Setup

### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 2. Configure Backend Proxy

```bash
# Copy backend config
sudo nano /etc/nginx/sites-available/rozvrhovac-backend
```

Paste the content from `nginx/vm-reverse-proxy-backend.conf` and update:
- Replace `<APPLICATION_VM_IP>` with VM 2's IP address
- Replace `api.yourdomain.com` with your backend domain
- Update SSL certificate paths if using HTTPS

### 3. Configure Frontend Proxy

```bash
# Copy frontend config
sudo nano /etc/nginx/sites-available/rozvrhovac-frontend
```

Paste the content from `nginx/vm-reverse-proxy-frontend.conf` and update:
- Replace `<APPLICATION_VM_IP>` with VM 2's IP address
- Replace `yourdomain.com` with your frontend domain
- Update SSL certificate paths if using HTTPS

### 4. Enable Sites

```bash
# Enable backend
sudo ln -s /etc/nginx/sites-available/rozvrhovac-backend /etc/nginx/sites-enabled/

# Enable frontend
sudo ln -s /etc/nginx/sites-available/rozvrhovac-frontend /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 5. Configure Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if needed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### 6. Configure SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal is set up automatically
```

## Network Configuration

### VM 2 (Application VM) Firewall

```bash
# Allow connections from VM 1 (nginx) only
# Replace VM1_IP with your nginx VM's IP

# Allow backend port from nginx VM
sudo ufw allow from <VM1_IP> to any port 8000

# Allow frontend port from nginx VM
sudo ufw allow from <VM1_IP> to any port 80

# Deny direct access from internet
sudo ufw deny 8000
sudo ufw deny 80

# Enable firewall
sudo ufw enable
```

### VM 1 (Nginx VM) Firewall

```bash
# Allow HTTP/HTTPS from internet
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

## DNS Configuration

Configure your DNS records:

```
A     yourdomain.com        → VM1_IP
A     www.yourdomain.com    → VM1_IP
A     api.yourdomain.com    → VM1_IP
```

## Health Checks

### Check Backend Health

```bash
# From VM 1 (nginx)
curl http://<VM2_IP>:8000/health

# From internet
curl https://api.yourdomain.com/health
```

### Check Frontend Health

```bash
# From VM 1 (nginx)
curl http://<VM2_IP>:80/health

# From internet
curl https://yourdomain.com/health
```

## Monitoring

### Application VM Logs

```bash
# Backend logs
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod logs -f backend

# Frontend logs
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod logs -f frontend

# All logs
docker compose -f docker-compose.prod.vm.yml --env-file .env.prod logs -f
```

### Nginx VM Logs

```bash
# Backend access logs
sudo tail -f /var/log/nginx/rozvrhovac_backend_access.log

# Frontend access logs
sudo tail -f /var/log/nginx/rozvrhovac_frontend_access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Backend Not Reachable

1. Check VM 2 firewall allows VM 1 IP
2. Check backend container is running: `docker compose ps`
3. Test from VM 1: `curl http://<VM2_IP>:8000/health`
4. Check backend logs: `docker compose logs backend`

### Frontend Not Loading

1. Check VM 2 firewall allows VM 1 IP
2. Check frontend container is running: `docker compose ps`
3. Test from VM 1: `curl http://<VM2_IP>:80`
4. Check frontend logs: `docker compose logs frontend`

### Nginx Errors

1. Test configuration: `sudo nginx -t`
2. Check error logs: `sudo tail -f /var/log/nginx/error.log`
3. Verify upstream servers are reachable
4. Check DNS resolution

## Security Checklist

- [ ] Strong passwords in `.env.prod`
- [ ] JWT secret key is random and secure
- [ ] SSL certificates configured
- [ ] Firewall rules restrict database access
- [ ] Only nginx VM can access application ports
- [ ] Regular security updates applied
- [ ] Database backups configured
- [ ] Log rotation configured

## Backup Strategy

### Application VM

```bash
# Backup registry database
docker compose -f docker-compose.prod.vm.yml exec postgres-registry \
  pg_dump -U postgres rozvrhovac_registry > registry_backup.sql

# Backup school databases
docker compose -f docker-compose.prod.vm.yml exec postgres \
  pg_dump -U postgres rozvrhovac_school001 > school001_backup.sql
```

### Nginx VM

```bash
# Backup nginx configs
sudo tar -czf nginx-configs-backup.tar.gz /etc/nginx/sites-available/
```

