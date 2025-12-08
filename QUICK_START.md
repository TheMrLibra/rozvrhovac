# Quick Start Guide

## Access Points

### Backend API
- **URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Frontend
- **URL**: http://localhost:5173 (when running locally)
- **Note**: Frontend runs locally in development mode for better hot reload

### Database Tools
- **pgAdmin**: http://localhost:5050
  - Email: `admin@rozvrhovac.dev`
  - Password: `admin`
- **PostgreSQL**: `localhost:5432`
  - Database: `rozvrhovac`
  - User: `postgres`
  - Password: `postgres`

## Quick Start Commands

```bash
# Start database and backend
make up-dev

# Run database migrations
make migrate

# Seed initial data (creates demo school and users)
make seed

# Start frontend (in a separate terminal)
cd frontend
npm run dev
```

## Login Credentials

After running the seed script, you can login with:

### Admin User
- **Email**: `admin@rozvrhovac.dev`
- **Password**: `admin123`
- **Access**: Full access to all features

### Teacher User
- **Email**: `teacher@rozvrhovac.dev`
- **Password**: `teacher123`
- **Access**: View own timetable, report absences

### Scholar User
- **Email**: `scholar@rozvrhovac.dev`
- **Password**: `scholar123`
- **Access**: View class timetable

## Troubleshooting

### Backend not responding at http://localhost:8000

1. Check if backend is running:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

2. Check backend logs:
   ```bash
   docker-compose -f docker-compose.dev.yml logs backend
   ```

3. Restart backend:
   ```bash
   docker-compose -f docker-compose.dev.yml restart backend
   ```

### Frontend not accessible

1. **Check Node.js version** (requires 18+):
   ```bash
   node --version
   # Should be v18.x.x or v20.x.x
   ```

2. **Switch to correct Node.js version** (if using nvm):
   ```bash
   cd frontend
   nvm use  # Uses .nvmrc file
   ```

3. Make sure you've installed dependencies:
   ```bash
   cd frontend
   npm install
   ```

4. Start the dev server:
   ```bash
   npm run dev
   ```

5. Check if port 5173 is available:
   ```bash
   lsof -i :5173
   ```

### Frontend Error: `crypto.getRandomValues is not a function`

This means you're using Node.js < 18. Upgrade to Node.js 18 or 20:
```bash
nvm install 20
nvm use 20
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database connection issues

1. Check if PostgreSQL is running:
   ```bash
   docker-compose -f docker-compose.dev.yml ps postgres
   ```

2. Test connection:
   ```bash
   docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d rozvrhovac -c "SELECT 1;"
   ```

### No users in database / Can't login

Run the seed script to create initial users:
```bash
make seed
# Or manually:
docker-compose -f docker-compose.dev.yml exec backend python -m scripts.seed_data
```
