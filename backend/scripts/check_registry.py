"""
Script to check registry entries.
"""
import asyncio
from app.core.database_manager import get_registry_db
from app.repositories.registry_repository import RegistryRepository

async def check_registry():
    """Check all registry entries."""
    async for registry_db in get_registry_db():
        try:
            registry_repo = RegistryRepository(registry_db)
            all_schools = await registry_repo.get_all_active()
            
            print(f"📚 Found {len(all_schools)} active school(s) in registry:\n")
            for school in all_schools:
                print(f"  Registry ID: {school.id}")
                print(f"  School ID: {school.school_id}")
                print(f"  Code: {school.code}")
                print(f"  Name: {school.name}")
                print(f"  Database: {school.database_name}")
                print(f"  Host: {school.database_host}:{school.database_port}")
                print(f"  Active: {school.is_active}")
                print()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(check_registry())

