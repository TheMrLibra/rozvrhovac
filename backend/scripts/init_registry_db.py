"""
Script to initialize the registry database.
This creates the registry database and the school_registry table.
Usage: python -m scripts.init_registry_db
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.database_manager import RegistrySessionLocal, build_database_url
from app.models.registry import SchoolRegistry, RegistryBase

async def create_registry_database():
    """Create the registry database if it doesn't exist."""
    # Extract database name from REGISTRY_DATABASE_URL
    db_url = settings.REGISTRY_DATABASE_URL
    # Parse database name (assuming format: postgresql+asyncpg://user:pass@host:port/dbname)
    parts = db_url.split("/")
    database_name = parts[-1]
    
    # Get connection details
    connection_part = parts[-2]  # user:pass@host:port
    if "@" in connection_part:
        auth_part, host_part = connection_part.split("@")
        if ":" in host_part:
            host, port = host_part.split(":")
            port = int(port)
        else:
            host = host_part
            port = 5432
        if ":" in auth_part:
            user, password = auth_part.split(":")
        else:
            user = auth_part
            password = ""
    else:
        host = "localhost"
        port = 5432
        user = "postgres"
        password = ""
    
    # Connect to postgres database to create the registry database
    admin_url = build_database_url("postgres", host, port, user, password)
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    async with engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'")
        )
        exists = result.scalar_one_or_none()
        
        if exists:
            print(f"Registry database '{database_name}' already exists.")
        else:
            # Create database
            await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
            print(f"✅ Created registry database: {database_name}")
    
    await engine.dispose()

async def create_registry_tables():
    """Create tables in the registry database."""
    engine = create_async_engine(
        settings.REGISTRY_DATABASE_URL,
        echo=True
    )
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(RegistryBase.metadata.create_all)
        print("✅ Created registry tables")
    
    await engine.dispose()

async def init_registry():
    """Initialize the registry database."""
    print("🚀 Initializing registry database...")
    
    try:
        # Step 1: Create database
        await create_registry_database()
        
        # Step 2: Create tables
        await create_registry_tables()
        
        print("\n✅ Registry database initialized successfully!")
        print("\nNext steps:")
        print("  1. Create a school: python -m scripts.create_school --name 'School Name' --code SCHOOL001")
        print("  2. Create an admin user: python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.local --password <password>")
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(init_registry())

