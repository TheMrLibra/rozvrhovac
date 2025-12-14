"""
Script to create a new school and its database.
Usage: python -m scripts.create_school --name "School Name" --code "SCHOOL001" [--db-host localhost] [--db-port 5432] [--db-user postgres] [--db-password postgres]
"""
import asyncio
import argparse
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, create_engine
from datetime import time
from app.core.config import settings
from app.core.database_manager import RegistrySessionLocal, build_database_url
from app.models.registry import SchoolRegistry
from app.models.school import School, SchoolSettings
from app.repositories.registry_repository import RegistryRepository
from app.repositories.school_repository import SchoolRepository, SchoolSettingsRepository

async def create_database(database_name: str, host: str, port: int, user: str, password: str):
    """Create a new PostgreSQL database."""
    # Connect to postgres database to create the new database
    admin_url = build_database_url("postgres", host, port, user, password)
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    async with engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'")
        )
        exists = result.scalar_one_or_none()
        
        if exists:
            print(f"Database '{database_name}' already exists.")
            await engine.dispose()
            return False
        
        # Create database
        await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
        print(f"✅ Created database: {database_name}")
    
    await engine.dispose()
    return True

async def run_migrations(database_url: str):
    """Run Alembic migrations on a database."""
    import os
    import subprocess
    
    # Change to backend directory to find alembic.ini
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    original_dir = os.getcwd()
    
    try:
        os.chdir(backend_dir)
        # Use sync URL for alembic (remove +asyncpg)
        sync_url = database_url.replace("+asyncpg", "")
        
        # Set ALEMBIC_DATABASE_URL for alembic (keep DATABASE_URL as async for app imports)
        env = os.environ.copy()
        env['ALEMBIC_DATABASE_URL'] = sync_url
        # Keep original DATABASE_URL so database.py imports work correctly
        if 'DATABASE_URL' not in env:
            env['DATABASE_URL'] = database_url
        
        # Run migrations using subprocess to avoid asyncio.run() nesting
        print(f"Running migrations on database...")
        print(f"Database URL: {sync_url}")
        
        # Check if database has tables but no alembic_version (inconsistent state)
        from sqlalchemy import create_engine as create_sync_engine
        from sqlalchemy import inspect as sql_inspect
        sync_engine_check = create_sync_engine(sync_url)
        inspector_check = sql_inspect(sync_engine_check)
        existing_tables = inspector_check.get_table_names()
        sync_engine_check.dispose()
        
        # Check current revision
        check_result = subprocess.run(
            ['python', '-m', 'alembic', 'current'],
            env=env,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        current_rev = check_result.stdout.strip() if check_result.stdout else None
        print(f"Current revision: {current_rev if current_rev else 'None (fresh database)'}")
        
        # If database has tables but no alembic_version, stamp it to head
        if not current_rev and existing_tables:
            print(f"⚠️  Database has tables but no Alembic version tracking.")
            print(f"   Found tables: {existing_tables}")
            print(f"   Stamping database to current head revision...")
            
            # Get the head revision
            heads_result = subprocess.run(
                ['python', '-m', 'alembic', 'heads'],
                env=env,
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            head_rev = heads_result.stdout.strip().split()[0] if heads_result.stdout else None
            
            if head_rev:
                stamp_result = subprocess.run(
                    ['python', '-m', 'alembic', 'stamp', head_rev],
                    env=env,
                    cwd=backend_dir,
                    capture_output=True,
                    text=True
                )
                if stamp_result.returncode != 0:
                    print(f"⚠️  Warning: Could not stamp database: {stamp_result.stderr}")
                else:
                    print(f"✅ Stamped database to revision: {head_rev}")
            else:
                print(f"⚠️  Could not determine head revision, continuing anyway...")
        
        # Run migrations (will be a no-op if already at head)
        result = subprocess.run(
            ['python', '-m', 'alembic', 'upgrade', 'head'],
            env=env,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Check if error is just about duplicate tables (tables exist but migration tried to create them)
            if 'DuplicateTable' in result.stderr or 'already exists' in result.stderr:
                print(f"⚠️  Migration error due to existing tables. Stamping database to head...")
                # Try to stamp to head
                heads_result = subprocess.run(
                    ['python', '-m', 'alembic', 'heads'],
                    env=env,
                    cwd=backend_dir,
                    capture_output=True,
                    text=True
                )
                head_rev = heads_result.stdout.strip().split()[0] if heads_result.stdout else None
                if head_rev:
                    stamp_result = subprocess.run(
                        ['python', '-m', 'alembic', 'stamp', head_rev],
                        env=env,
                        cwd=backend_dir,
                        capture_output=True,
                        text=True
                    )
                    if stamp_result.returncode == 0:
                        print(f"✅ Stamped database to revision: {head_rev}")
                        print(f"✅ Migrations completed (database was already up to date)")
                    else:
                        print(f"❌ Migration error: {result.stderr}")
                        raise RuntimeError(f"Migration failed: {result.stderr}")
                else:
                    print(f"❌ Migration error: {result.stderr}")
                    raise RuntimeError(f"Migration failed: {result.stderr}")
            else:
                print(f"❌ Migration error: {result.stderr}")
                raise RuntimeError(f"Migration failed: {result.stderr}")
        else:
            print(f"✅ Migrations completed")
            if result.stdout:
                print(result.stdout)
        
        # Verify migrations actually ran by checking revision again
        verify_result = subprocess.run(
            ['python', '-m', 'alembic', 'current'],
            env=env,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        print(f"Revision after migration: {verify_result.stdout.strip() if verify_result.stdout else 'None'}")
        
        # Verify tables were created by checking if schools table exists
        from sqlalchemy import create_engine as create_sync_engine
        from sqlalchemy import inspect as sql_inspect
        sync_engine = create_sync_engine(sync_url)
        inspector = sql_inspect(sync_engine)
        tables = inspector.get_table_names()
        sync_engine.dispose()
        
        # Check for missing critical tables and create them
        missing_tables = []
        if 'schools' not in tables:
            missing_tables.append('schools')
        if 'school_settings' not in tables:
            missing_tables.append('school_settings')
        if 'users' not in tables:
            missing_tables.append('users')
        
        if missing_tables:
            print(f"⚠️  Warning: Missing tables after migrations: {missing_tables}")
            print(f"   Found tables: {tables}")
            print(f"   Database appears to be in inconsistent state.")
            print(f"   Creating missing tables manually...")
            
            from sqlalchemy import MetaData, Table, Column, Integer, String, Time, JSON, ForeignKey, Index
            sync_engine = create_engine(sync_url)
            metadata = MetaData()
            
            # Create schools table if missing
            if 'schools' in missing_tables:
                schools_table = Table(
                    'schools',
                    metadata,
                    Column('id', Integer, primary_key=True),
                    Column('name', String, nullable=False),
                    Column('code', String, nullable=False),
                    Index('ix_schools_id', 'id'),
                    Index('ix_schools_code', 'code', unique=True)
                )
                try:
                    schools_table.create(sync_engine, checkfirst=True)
                    print(f"✅ Created 'schools' table")
                except Exception as e:
                    print(f"⚠️  Could not create schools table: {e}")
            
            # Create school_settings table if missing (depends on schools)
            if 'school_settings' in missing_tables:
                # Verify schools exists (should be created above if it was missing)
                inspector_check = sql_inspect(sync_engine)
                tables_check = inspector_check.get_table_names()
                if 'schools' not in tables_check:
                    print(f"⚠️  Cannot create school_settings: schools table still missing")
                else:
                    # Use raw SQL to create the table (avoids MetaData reflection issues)
                    from sqlalchemy import text
                    create_sql = """
                    CREATE TABLE IF NOT EXISTS school_settings (
                        id SERIAL PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        class_hour_length_minutes INTEGER NOT NULL,
                        break_duration_minutes INTEGER NOT NULL,
                        break_durations JSON,
                        possible_lunch_hours JSON,
                        lunch_duration_minutes INTEGER NOT NULL,
                        CONSTRAINT fk_school_settings_school_id FOREIGN KEY (school_id) REFERENCES schools(id)
                    );
                    CREATE INDEX IF NOT EXISTS ix_school_settings_id ON school_settings(id);
                    CREATE UNIQUE INDEX IF NOT EXISTS ix_school_settings_school_id ON school_settings(school_id);
                    """
                    try:
                        with sync_engine.connect() as conn:
                            conn.execute(text(create_sql))
                            conn.commit()
                        print(f"✅ Created 'school_settings' table")
                    except Exception as e:
                        print(f"⚠️  Could not create school_settings table: {e}")
                        raise
            
            # Create users table if missing (depends on schools)
            if 'users' in missing_tables:
                # Verify schools exists
                inspector_check = sql_inspect(sync_engine)
                tables_check = inspector_check.get_table_names()
                if 'schools' not in tables_check:
                    print(f"⚠️  Cannot create users: schools table still missing")
                else:
                    # Use raw SQL to create the table
                    from sqlalchemy import text
                    create_users_sql = """
                    -- Create ENUM type if it doesn't exist
                    DO $$ BEGIN
                        CREATE TYPE userrole AS ENUM ('ADMIN', 'TEACHER', 'SCHOLAR');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                    
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        email VARCHAR NOT NULL,
                        password_hash VARCHAR NOT NULL,
                        role userrole NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        teacher_id INTEGER,
                        class_group_id INTEGER,
                        CONSTRAINT fk_users_school_id FOREIGN KEY (school_id) REFERENCES schools(id)
                    );
                    CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);
                    CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);
                    CREATE INDEX IF NOT EXISTS ix_users_school_id ON users(school_id);
                    """
                    try:
                        with sync_engine.connect() as conn:
                            conn.execute(text(create_users_sql))
                            conn.commit()
                        print(f"✅ Created 'users' table")
                    except Exception as e:
                        print(f"⚠️  Could not create users table: {e}")
                        raise
            
            sync_engine.dispose()
            
            # Verify tables exist now
            sync_engine = create_engine(sync_url)
            inspector = sql_inspect(sync_engine)
            tables_after = inspector.get_table_names()
            sync_engine.dispose()
            
            # Check if critical tables exist
            if 'schools' not in tables_after:
                raise RuntimeError("Failed to create 'schools' table. Database is in inconsistent state.")
            if 'school_settings' not in tables_after:
                raise RuntimeError("Failed to create 'school_settings' table. Database is in inconsistent state.")
            if 'users' not in tables_after:
                raise RuntimeError("Failed to create 'users' table. Database is in inconsistent state.")
            print(f"✅ Verified: Required tables exist")
        else:
            print(f"✅ Verified: Required tables exist")
    finally:
        os.chdir(original_dir)

async def create_school(
    name: str,
    code: str,
    db_host: str = None,
    db_port: int = None,
    db_user: str = None,
    db_password: str = None
):
    """Create a new school with its own database."""
    db_host = db_host or settings.DEFAULT_DB_HOST
    db_port = db_port or settings.DEFAULT_DB_PORT
    db_user = db_user or settings.DEFAULT_DB_USER
    db_password = db_password or settings.DEFAULT_DB_PASSWORD
    
    # Generate database name
    database_name = f"rozvrhovac_{code.lower()}"
    
    print(f"\n🚀 Creating school: {name}")
    print(f"   Code: {code}")
    print(f"   Database: {database_name}")
    print(f"   Host: {db_host}:{db_port}")
    
    # Step 1: Create database
    db_created = await create_database(database_name, db_host, db_port, db_user, db_password)
    if not db_created:
        response = input(f"Database '{database_name}' already exists. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return None
    
    # Step 2: Run migrations on the new database
    database_url = build_database_url(database_name, db_host, db_port, db_user, db_password)
    await run_migrations(database_url)
    
    # Step 3: Create school in the school database
    school_db_url = database_url
    school_engine = create_async_engine(school_db_url, echo=False)
    SchoolSessionLocal = async_sessionmaker(school_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SchoolSessionLocal() as school_db:
        school_repo = SchoolRepository(school_db)
        settings_repo = SchoolSettingsRepository(school_db)
        
        # Check if school already exists
        existing_school = await school_repo.get_by_code(code)
        if existing_school:
            print(f"⚠️  School with code '{code}' already exists in database.")
            school_id = existing_school.id
            school = existing_school
        else:
            # Create school
            school = School(name=name, code=code)
            school = await school_repo.create(school)
            await school_db.commit()
            school_id = school.id
            print(f"✅ Created school in database (ID: {school_id})")
        
        # Create default school settings if they don't exist
        existing_settings = await settings_repo.get_by_school_id(school_id)
        if not existing_settings:
            school_settings = SchoolSettings(
                school_id=school_id,
                start_time=time(8, 0),
                end_time=time(16, 0),
                class_hour_length_minutes=45,
                break_duration_minutes=10,
                break_durations=[5, 20, 10, 10, 10],
                possible_lunch_hours=[3, 4, 5],
                lunch_duration_minutes=30
            )
            await settings_repo.create(school_settings)
            await school_db.commit()
            print(f"✅ Created default school settings")
    
    await school_engine.dispose()
    
    # Step 4: Create registry entry
    async with RegistrySessionLocal() as registry_db:
        registry_repo = RegistryRepository(registry_db)
        
        # Check if registry entry already exists
        existing_registry = await registry_repo.get_by_code(code)
        if existing_registry:
            print(f"⚠️  Registry entry for code '{code}' already exists.")
            registry = existing_registry
        else:
            registry = SchoolRegistry(
                school_id=school_id,
                name=name,
                code=code,
                database_name=database_name,
                database_host=db_host,
                database_port=db_port,
                database_user=db_user,
                is_active=True
            )
            registry = await registry_repo.create(registry)
            await registry_db.commit()
            print(f"✅ Created registry entry (Registry ID: {registry.id})")
    
    print(f"\n✅ School '{name}' created successfully!")
    print(f"\nSummary:")
    print(f"  School ID: {school_id}")
    print(f"  School Code: {code}")
    print(f"  Database: {database_name}")
    print(f"  Registry ID: {registry.id}")
    print(f"\nNext step: Create an admin user with:")
    print(f"  python -m scripts.create_admin_user --school-code {code} --email admin@{code.lower()}.local --password <password>")
    
    return {
        "school_id": school_id,
        "code": code,
        "database_name": database_name,
        "registry_id": registry.id
    }

def main():
    parser = argparse.ArgumentParser(description="Create a new school and its database")
    parser.add_argument("--name", required=True, help="School name")
    parser.add_argument("--code", required=True, help="School code (unique identifier)")
    parser.add_argument("--db-host", default=None, help="Database host (default: from config)")
    parser.add_argument("--db-port", type=int, default=None, help="Database port (default: from config)")
    parser.add_argument("--db-user", default=None, help="Database user (default: from config)")
    parser.add_argument("--db-password", default=None, help="Database password (default: from config)")
    
    args = parser.parse_args()
    
    try:
        result = asyncio.run(create_school(
            name=args.name,
            code=args.code,
            db_host=args.db_host,
            db_port=args.db_port,
            db_user=args.db_user,
            db_password=args.db_password
        ))
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

