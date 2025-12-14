#!/usr/bin/env python3
"""
Script to fix registry entry by checking the actual school_id in the school database
and updating the registry entry if needed.
"""
import asyncio
import sys
from app.core.database_manager import RegistrySessionLocal, get_school_db
from app.repositories.registry_repository import RegistryRepository
from app.repositories.school_repository import SchoolRepository

async def main():
    """Fix registry entry for a school code."""
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.fix_registry <school_code>")
        sys.exit(1)
    
    school_code = sys.argv[1]
    print(f"🔧 Fixing registry entry for school code: {school_code}\n")
    
    async with RegistrySessionLocal() as registry_db:
        registry_repo = RegistryRepository(registry_db)
        
        # Get registry entry by code
        registry_entry = await registry_repo.get_by_code(school_code)
        if not registry_entry:
            print(f"❌ No registry entry found for code: {school_code}")
            sys.exit(1)
        
        print(f"📋 Current registry entry:")
        print(f"   Registry ID: {registry_entry.id}")
        print(f"   School ID: {registry_entry.school_id}")
        print(f"   Code: {registry_entry.code}")
        print(f"   Database: {registry_entry.database_name}\n")
        
        # Connect to school database and check actual school_id
        async for school_db in get_school_db(
            database_name=registry_entry.database_name,
            host=registry_entry.database_host,
            port=registry_entry.database_port,
            user=registry_entry.database_user
        ):
            school_repo = SchoolRepository(school_db)
            school = await school_repo.get_by_code(school_code)
            
            if not school:
                print(f"❌ School not found in database {registry_entry.database_name}")
                sys.exit(1)
            
            print(f"📋 School in database:")
            print(f"   School ID: {school.id}")
            print(f"   Code: {school.code}\n")
            
            # Check if school_id matches
            if registry_entry.school_id != school.id:
                print(f"⚠️  Mismatch detected!")
                print(f"   Registry school_id: {registry_entry.school_id}")
                print(f"   Database school_id: {school.id}\n")
                
                # Update registry entry
                registry_entry.school_id = school.id
                await registry_db.commit()
                print(f"✅ Updated registry entry school_id to {school.id}")
            else:
                print(f"✅ Registry entry school_id matches database school_id ({school.id})")
            
            break

if __name__ == "__main__":
    asyncio.run(main())

