# Database Structure Analysis

## Overview
Multi-tenant architecture with:
- **Registry Database**: Stores metadata about schools and their database connections
- **School Databases**: One database per school, containing all school-specific data

## Registry Database (`rozvrhovac_registry`)

### Table: `school_registry`
Stores metadata about each school and connection information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Indexed | Registry entry ID |
| `school_id` | Integer | Unique, Indexed | Maps to `School.id` in school database |
| `name` | String | Not Null | School name |
| `code` | String | Unique, Indexed | School code (e.g., "GJR") |
| `database_name` | String | Unique, Indexed | Database name (e.g., "rozvrhovac_gjr") |
| `database_host` | String | Not Null | Database host |
| `database_port` | Integer | Not Null | Database port |
| `database_user` | String | Not Null | Database user |
| `is_active` | Boolean | Not Null, Default True | Whether school is active |

**✅ Structure is correct** - Properly indexes `school_id` for fast lookups.

## School Databases (e.g., `rozvrhovac_gjr`)

### Core Tables

#### `schools`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Indexed | School ID (maps to registry.school_id) |
| `name` | String | Not Null | School name |
| `code` | String | Unique, Indexed | School code |

**✅ Structure is correct** - `id` maps to `school_registry.school_id`.

#### `users`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Indexed | User ID |
| `school_id` | Integer | FK → schools.id, Indexed | School ID |
| `email` | String | Unique, Indexed | Email address |
| `password_hash` | String | Not Null | Bcrypt hash |
| `role` | Enum | Not Null | ADMIN, TEACHER, SCHOLAR |
| `is_active` | Boolean | Default True | Active status |
| `teacher_id` | Integer | FK → teachers.id, Nullable | Teacher reference |
| `class_group_id` | Integer | FK → class_groups.id, Nullable | Class group reference |

**✅ Structure is correct**:
- `email` is unique per database (correct for multi-tenant)
- `school_id` foreign key ensures data isolation
- Proper indexes for performance

#### `school_settings`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, Indexed | Settings ID |
| `school_id` | Integer | FK → schools.id, Unique | School ID (one-to-one) |
| `start_time` | Time | Not Null | School start time |
| `end_time` | Time | Not Null | School end time |
| `class_hour_length_minutes` | Integer | Not Null | Lesson duration |
| `break_duration_minutes` | Integer | Not Null | Default break duration |
| `break_durations` | JSON | Nullable | Array of break durations |
| `possible_lunch_hours` | JSON | Nullable | Array of lunch hour options |
| `lunch_duration_minutes` | Integer | Not Null | Lunch duration |

**✅ Structure is correct** - One-to-one relationship with schools.

### Other Tables
- `teachers` - Teacher information
- `subjects` - Subject catalog
- `class_groups` - Class groups
- `classrooms` - Classroom information
- `timetables` - Timetable definitions
- `timetable_entries` - Individual timetable entries
- `teacher_absences` - Teacher absence records
- `substitutions` - Substitution records
- `grade_levels` - Grade level definitions

All tables properly reference `school_id` for data isolation.

## Key Relationships

### Registry ↔ School Database
```
school_registry.school_id → schools.id (in school database)
```
This mapping allows the system to:
1. Look up school registry entry by `school_id` from JWT token
2. Connect to the correct school database
3. Ensure data isolation between schools

### User ↔ School
```
users.school_id → schools.id
```
Ensures users belong to a specific school.

### User ↔ Teacher (Optional)
```
users.teacher_id → teachers.id
users.id ← teachers.user_id
```
Bidirectional relationship for teacher users.

## Indexes

### Registry Database
- ✅ `school_registry.school_id` - Unique index (for JWT lookup)
- ✅ `school_registry.code` - Unique index (for header lookup)
- ✅ `school_registry.database_name` - Unique index

### School Databases
- ✅ `users.email` - Unique index (per database)
- ✅ `users.school_id` - Index (for filtering)
- ✅ `schools.code` - Unique index
- ✅ All foreign keys properly indexed

## Security Considerations

### ✅ Password Storage
- Passwords are hashed using bcrypt
- Never stored in plain text

### ✅ Data Isolation
- Each school has its own database
- Foreign keys ensure referential integrity
- No cross-school data access possible

### ✅ Email Uniqueness
- Email is unique per school database
- Same email can exist in different schools (correct behavior)
- Prevents email conflicts within a school

## Potential Improvements

### 1. Composite Index for User Lookups
Consider adding a composite index on `(school_id, email)` for faster lookups:
```sql
CREATE INDEX ix_users_school_email ON users(school_id, email);
```
**Status**: Not critical, current indexes are sufficient.

### 2. Registry Entry Validation
Ensure `school_id` in registry matches actual `School.id` in school database.
**Status**: Handled by `fix_registry.py` script.

### 3. Database Connection Pooling
Current implementation caches engines per school.
**Status**: ✅ Already implemented in `database_manager.py`.

## Conclusion

**✅ Database structure is correct and well-designed for multi-tenant architecture.**

Key strengths:
- Proper data isolation via separate databases
- Correct foreign key relationships
- Appropriate indexes for performance
- Secure password storage
- Clean separation between registry and school data

The structure supports:
- Multi-tenant authentication
- School-specific data isolation
- Efficient lookups via indexes
- Scalability (each school is independent)

