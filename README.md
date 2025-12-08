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

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables (create `.env` file):
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rozvrhovac
SECRET_KEY=your-secret-key-change-in-production
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run development server:
```bash
npm run dev
```

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

## Deployment

### Docker

Build and run with Docker Compose (create `docker-compose.yml`):

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: rozvrhovac
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/rozvrhovac
    depends_on:
      - postgres
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

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

