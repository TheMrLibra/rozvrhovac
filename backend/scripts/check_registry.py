#!/usr/bin/env python3
"""
Script to check registry entries and verify school_id mappings.
"""
import asyncio
import sys
from app.core.database_manager import RegistrySessionLocal
from app.repositories.registry_repository import RegistryRepository

async def main():
    """Check registry entries."""
    print("🔍 Checking registry entries...\n")
    
    async with RegistrySessionLocal() as registry_db:
        registry_repo = RegistryRepository(registry_db)
        
        # Get all active schools
        all_schools = await registry_repo.get_all_active()
        
        if not all_schools:
            print("❌ No active schools found in registry!")
            return
        
        print(f"✅ Found {len(all_schools)} active school(s) in registry:\n")
        
        for school in all_schools:
            print(f"  Registry ID: {school.id}")
            print(f"  School ID: {school.school_id}")
            print(f"  Code: {school.code}")
            print(f"  Name: {school.name}")
            print(f"  Database: {school.database_name}")
            print(f"  Host: {school.database_host}:{school.database_port}")
            print(f"  Active: {school.is_active}")
            print()
        
        # Check specific school_id
        if len(sys.argv) > 1:
            school_id = int(sys.argv[1])
            print(f"\n🔎 Looking up school_id: {school_id}")
            entry = await registry_repo.get_by_school_id(school_id)
            if entry:
                print(f"✅ Found registry entry for school_id {school_id}:")
                print(f"   Code: {entry.code}")
                print(f"   Database: {entry.database_name}")
            else:
                print(f"❌ No registry entry found for school_id {school_id}")

if __name__ == "__main__":
    asyncio.run(main())
