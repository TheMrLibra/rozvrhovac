"""
Script to create a new school and its database.
Usage: python -m scripts.create_school --name "School Name" --code "SCHOOL001" [--db-host localhost] [--db-port 5432] [--db-user postgres] [--db-password postgres]
"""
import asyncio
import argparse
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from datetime import time
from app.core.config import settings
from app.core.database_manager import RegistrySessionLocal, build_database_url
from app.models.registry import SchoolRegistry
from app.models.school import School, SchoolSettings
from app.repositories.registry_repository import RegistryRepository
from app.repositories.school_repository import SchoolRepository, SchoolSettingsRepository
from alembic.config import Config
from alembic import command

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
    import sys
    
    # Change to backend directory to find alembic.ini
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    original_dir = os.getcwd()
    
    try:
        os.chdir(backend_dir)
        alembic_cfg = Config("alembic.ini")
        # Use sync URL for alembic (remove +asyncpg)
        sync_url = database_url.replace("+asyncpg", "")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        
        # Run migrations
        print(f"Running migrations on database...")
        command.upgrade(alembic_cfg, "head")
        print(f"✅ Migrations completed")
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
            settings = SchoolSettings(
                school_id=school_id,
                start_time=time(8, 0),
                end_time=time(16, 0),
                class_hour_length_minutes=45,
                break_duration_minutes=10,
                break_durations=[5, 20, 10, 10, 10],
                possible_lunch_hours=[3, 4, 5],
                lunch_duration_minutes=30
            )
            await settings_repo.create(settings)
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

