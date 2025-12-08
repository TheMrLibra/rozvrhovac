# Rozvrhovac - School Timetable Management System

A multi-tenant web application for schools that generates permanent timetables and handles automatic substitutions.

## Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Architecture**: 3-layer (Routers → Services → Repositories)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Migrations**: Alembic
- **Authentication**: JWT (Access + Refresh tokens)

### Frontend
- **Framework**: Vue 3 + TypeScript
- **Build Tool**: Vite
- **State Management**: Pinia
- **Styling**: SCSS with BEM methodology

### Deployment
- **Containerization**: Docker
- **Orchestration**: Kubernetes (with basic manifests)

## Project Structure

```
rozvrhovac/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routers
│   │   ├── core/             # Core configuration
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   ├── schemas/          # Pydantic DTOs
│   │   └── services/         # Business logic
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # Vue components
│   │   ├── views/            # Vue views/pages
│   │   ├── stores/           # Pinia stores
│   │   ├── services/         # API services
│   │   └── router/           # Vue Router
│   ├── package.json
│   └── Dockerfile
└── k8s/                      # Kubernetes manifests
```

## Setup

### Quick Start with Docker Compose (Recommended)

The easiest way to get started is using Docker Compose, which will set up the database, backend, and frontend:

```bash
# Start all services (database, backend, frontend)
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Database Connection Details:**
- Host: `localhost` (from your machine) or `postgres` (from other containers)
- Port: `5432`
- Database: `rozvrhovac`
- User: `postgres`
- Password: `postgres`

**Optional: Use development compose file** (includes pgAdmin for database management):
```bash
docker-compose -f docker-compose.dev.yml up -d
# pgAdmin will be available at http://localhost:5050
```

### Manual Setup (Without Docker)

#### Database Setup

**Option 1: Use Docker for database only**
```bash
# Start just the database
docker-compose up -d postgres

# The database will be available at localhost:5432
```

**Option 2: Install PostgreSQL locally**
- Install PostgreSQL 15+
- Create database: `createdb rozvrhovac`
- Update `DATABASE_URL` in your `.env.local` file

#### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Copy the example file
cp .env.local.example .env.local
```

Update the `.env.local` file with your local values:
- If using Docker Compose database: `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac`
- If using local PostgreSQL: Update with your local connection string
- Set a secure `SECRET_KEY`

3. Run migrations:
```bash
alembic upgrade head
```

4. Run the server:
```bash
uvicorn app.main:app --reload
# Or use the run script:
python run.py
```

### Frontend Setup

**Prerequisites:** Node.js 18+ (20+ recommended). The project includes a `.nvmrc` file for automatic version switching with nvm.

1. **Switch to correct Node.js version** (if using nvm):
```bash
cd frontend
nvm use  # Automatically uses version from .nvmrc
# Or manually: nvm use 20
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables (optional):
```bash
# Copy the example file
cp .env.local.example .env.local
# Update .env.local with your values if needed
```

4. Run development server:
```bash
npm run dev
```

The frontend will be available at **http://localhost:5173**

**Note:** 
- In development mode (`docker-compose.dev.yml`), the frontend is meant to run locally (not in Docker) for better hot reload.
- The backend API is available at http://localhost:8000 and will be automatically proxied by Vite.
- If you get `crypto.getRandomValues is not a function` error, make sure you're using Node.js 18+.

## Features

### Core Features
- ✅ Multi-tenant architecture (row-level separation by school_id)
- ✅ JWT authentication with role-based access control
- ✅ Timetable generation using heuristic algorithm
- ✅ Timetable validation (constraints checking)
- ✅ Automatic substitution generation
- ✅ CRUD operations for all entities

### User Roles
- **ADMIN**: Full access to all features
- **TEACHER**: View own timetable, report absences
- **SCHOLAR**: View class timetable

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Timetables
- `POST /api/v1/timetables/schools/{school_id}/timetables/generate` - Generate timetable
- `POST /api/v1/timetables/schools/{school_id}/timetables/{timetable_id}/validate` - Validate timetable
- `GET /api/v1/timetables/schools/{school_id}/timetables` - List timetables
- `GET /api/v1/timetables/schools/{school_id}/timetables/{timetable_id}` - Get timetable

### Substitutions
- `POST /api/v1/substitutions/schools/{school_id}/substitutions/generate` - Generate substitutions
- `GET /api/v1/substitutions/schools/{school_id}/substitutions` - List substitutions

## Development with Docker Compose

The project includes Docker Compose configurations for easy local development:

### Quick Commands (using Makefile)

```bash
# Start all services (database, backend, frontend)
make up

# Start only database and backend (run frontend locally)
make up-dev

# Run database migrations
make migrate

# View logs
make logs

# Stop services
make down

# Clean everything (removes database data)
make clean

# See all available commands
make help
```

### Manual Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# Start database and backend only (for local frontend dev)
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f [service_name]

# Stop services
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v

# Rebuild services after code changes
docker-compose up --build -d
```

**Services:**
- `postgres` - PostgreSQL 15 database (port 5432)
- `backend` - FastAPI backend (port 8000) 
- `frontend` - Vue.js frontend (port 80) - *optional in dev mode*
- `pgadmin` - Database management UI (port 5050) - *only in docker-compose.dev.yml*

**Database Access:**
- Host: `localhost` (from your machine) or `postgres` (from other containers)
- Port: `5432`
- Database: `rozvrhovac`
- User: `postgres`
- Password: `postgres`

**Development Workflow:**
1. Start database and backend: `make up-dev` or `docker-compose -f docker-compose.dev.yml up -d`
2. Run migrations: `make migrate`
3. Run frontend locally: `cd frontend && npm run dev` (better hot reload)
4. Access:
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:5173
   - pgAdmin (if using dev compose): http://localhost:5050

**Note:** Database data persists in a Docker volume (`postgres_data`). Use `make clean` or `docker-compose down -v` to clear it.

## Deployment

### Docker

The `docker-compose.yml` file is configured for development. For production:

1. Use environment-specific compose files
2. Set secure passwords and secrets
3. Configure proper networking
4. Use production-ready images

### Kubernetes

1. Create secrets:
```bash
kubectl create secret generic rozvrhovac-secrets \
  --from-literal=database-url="postgresql+asyncpg://..." \
  --from-literal=secret-key="your-secret-key"
```

2. Apply manifests:
```bash
kubectl apply -f k8s/
```

## Development

### Running Tests
```bash
cd backend
pytest
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## License

MIT

