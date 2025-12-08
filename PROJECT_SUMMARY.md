# Rozvrhovac - Project Summary

## Overview
A complete multi-tenant school timetable management system with automatic substitution capabilities, built using FastAPI (backend) and Vue 3 (frontend).

## What Has Been Implemented

### Backend (Python + FastAPI)

#### ✅ Domain Models (SQLAlchemy)
- **School** - Multi-tenant root entity
- **SchoolSettings** - Time windows, lesson duration, breaks, lunch settings
- **GradeLevel** - Grade levels (1st, 2nd, 3rd, etc.)
- **ClassGroup** - Individual classes (e.g., "1.A")
- **Subject** - Subjects with constraints (consecutive hours, multiple per day, etc.)
- **ClassSubjectAllocation** - Weekly hour requirements per class-subject
- **Teacher** - Teachers with availability and max hours
- **TeacherSubjectCapability** - What subjects/grade levels teachers can teach
- **Classroom** - Classrooms with specializations and restrictions
- **User** - Authentication with roles (ADMIN, TEACHER, SCHOLAR)
- **Timetable** - Generated timetables
- **TimetableEntry** - Individual lesson placements
- **TeacherAbsence** - Absence records
- **Substitution** - Substitution records

#### ✅ Architecture (3-Layer)
- **Routers** (`app/api/v1/`): API endpoints
  - `auth_router.py` - Login, user info
  - `schools_router.py` - School management
  - `timetable_router.py` - Timetable generation, validation, retrieval
  - `teachers_router.py` - Teacher management, timetable views
  - `substitution_router.py` - Substitution generation and management

- **Services** (`app/services/`): Business logic
  - `user_service.py` - Authentication, token generation
  - `timetable_service.py` - Timetable generation algorithm (heuristic)
  - `timetable_validation_service.py` - Comprehensive constraint validation
  - `substitution_service.py` - Automatic substitution generation

- **Repositories** (`app/repositories/`): Data access
  - Base repository with CRUD operations
  - Specialized repositories for each entity
  - Multi-tenant filtering (school_id)

#### ✅ Features Implemented
1. **JWT Authentication**
   - Access tokens + Refresh tokens
   - Role-based access control (ADMIN, TEACHER, SCHOLAR)
   - Secure password hashing (bcrypt)

2. **Timetable Generation**
   - Heuristic algorithm that:
     - Distributes weekly hours across the week
     - Respects teacher availability
     - Checks teacher max weekly hours
     - Validates subject constraints
     - Assigns suitable classrooms
     - Prioritizes hard-to-place subjects

3. **Timetable Validation**
   - No teacher/class/classroom conflicts
   - Teacher weekly hours limits
   - Subject constraint validation:
     - Consecutive hours rules
     - Max consecutive hours
     - Multiple per day restrictions
     - Required block lengths

4. **Substitution System**
   - Automatic substitute teacher finding
   - Capability matching
   - Availability checking
   - Weekly hours validation

5. **Multi-Tenant Support**
   - Row-level separation by `school_id`
   - All queries filtered by school
   - User access restricted to their school

#### ✅ Database
- PostgreSQL with async SQLAlchemy
- Alembic migrations configured
- All relationships properly defined

### Frontend (Vue 3 + TypeScript)

#### ✅ Structure
- **Vite** build tool
- **Vue Router** for navigation
- **Pinia** for state management
- **SCSS with BEM** methodology
- **TypeScript** throughout

#### ✅ Views Implemented
- `LoginView.vue` - User authentication
- `DashboardView.vue` - Role-based dashboard
- `TimetableView.vue` - Timetable visualization
- `AdminDashboard.vue` - Admin panel with timetable generation
- `SchoolSettingsView.vue` - Settings management (placeholder)

#### ✅ Components
- `TimetableGrid.vue` - Main timetable grid display
- `TimetableCell.vue` - Individual lesson cell

#### ✅ Features
- JWT token management
- API service with interceptors
- Role-based route protection
- Responsive design

### Deployment

#### ✅ Docker
- Backend Dockerfile (Python 3.11, uvicorn)
- Frontend Dockerfile (multi-stage: Node build + Nginx)
- Docker Compose for local development

#### ✅ Kubernetes
- Backend deployment + service
- Frontend deployment + service
- ConfigMap for configuration
- Secret example for sensitive data

## Project Structure

```
rozvrhovac/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routers
│   │   ├── core/            # Config, database, security, dependencies
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic DTOs
│   │   └── services/        # Business logic
│   ├── alembic/             # Migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/
│   │   ├── services/
│   │   └── router/
│   ├── package.json
│   └── Dockerfile
├── k8s/                     # Kubernetes manifests
├── docker-compose.yml
└── README.md
```

## Next Steps / Improvements

### Backend
1. **Enhanced Timetable Generation**
   - Implement backtracking algorithm for better solutions
   - Add genetic algorithm option
   - Improve constraint satisfaction

2. **Additional Features**
   - CRUD endpoints for all entities (currently basic)
   - Bulk operations
   - Timetable export (PDF, Excel)
   - Historical timetable versions

3. **Testing**
   - Unit tests for services (pytest)
   - Integration tests for API
   - Test coverage reporting

4. **Performance**
   - Caching layer (Redis)
   - Database query optimization
   - Background job processing (Celery)

### Frontend
1. **Enhanced UI**
   - Complete CRUD forms for all entities
   - Better timetable visualization (drag & drop)
   - Calendar view
   - Print-friendly views

2. **Features**
   - Real-time updates (WebSockets)
   - Advanced filtering and search
   - Export functionality
   - Mobile responsive design

3. **Testing**
   - Unit tests (Vitest)
   - E2E tests (Playwright/Cypress)

### Infrastructure
1. **Helm Chart**
   - Complete Helm chart with values
   - Ingress configuration
   - Horizontal Pod Autoscaling

2. **CI/CD**
   - GitHub Actions / GitLab CI
   - Automated testing
   - Deployment pipelines

3. **Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Logging (ELK stack)

## Running the Project

### Local Development

1. **Backend:**
```bash
cd backend
pip install -r requirements.txt
# Set up .env file
alembic upgrade head
uvicorn app.main:app --reload
```

2. **Frontend:**
```bash
cd frontend
npm install
npm run dev
```

3. **Docker Compose:**
```bash
docker-compose up
```

### Production

1. Build images:
```bash
docker build -t rozvrhovac-backend ./backend
docker build -t rozvrhovac-frontend ./frontend
```

2. Deploy to Kubernetes:
```bash
kubectl apply -f k8s/
```

## Notes

- The timetable generation algorithm is a basic heuristic. For production, consider implementing more sophisticated algorithms (constraint satisfaction, genetic algorithms, etc.).
- Date-to-day-of-week mapping in substitution service needs implementation for proper absence handling.
- Some CRUD operations are basic and can be expanded.
- Frontend forms for entity management are placeholders and need full implementation.

## License

MIT

