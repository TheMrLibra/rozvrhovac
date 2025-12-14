"""
Script to verify if a user exists in a school database.
"""
import asyncio
import sys
from app.core.database_manager import get_registry_db, get_school_db
from app.repositories.registry_repository import RegistryRepository
from app.repositories.user_repository import UserRepository

async def verify_user(email: str, school_code: str = None):
    """Verify if a user exists in the database."""
    async for registry_db in get_registry_db():
        try:
            registry_repo = RegistryRepository(registry_db)
            
            if school_code:
                registry_entry = await registry_repo.get_by_code(school_code)
                if not registry_entry:
                    print(f"❌ School '{school_code}' not found in registry")
                    return
                schools = [registry_entry]
            else:
                schools = await registry_repo.get_all_active()
            
            print(f"🔍 Searching for user: {email}")
            print(f"📚 Checking {len(schools)} school(s)...\n")
            
            found = False
            for registry_entry in schools:
                print(f"  Checking school: {registry_entry.code} ({registry_entry.database_name})")
                try:
                    async for db in get_school_db(
                        database_name=registry_entry.database_name,
                        host=registry_entry.database_host,
                        port=registry_entry.database_port,
                        user=registry_entry.database_user
                    ):
                        try:
                            user_repo = UserRepository(db)
                            user = await user_repo.get_by_email(email)
                            if user:
                                found = True
                                print(f"  ✅ User found!")
                                print(f"     ID: {user.id}")
                                print(f"     Email: {user.email}")
                                print(f"     Role: {user.role}")
                                print(f"     School ID: {user.school_id}")
                                print(f"     Active: {user.is_active}")
                                return
                            else:
                                print(f"  ❌ User not found in this school")
                        finally:
                            break
                except Exception as e:
                    print(f"  ⚠️  Error checking school: {e}")
                    continue
            
            if not found:
                print(f"\n❌ User '{email}' not found in any school database")
        finally:
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.verify_user <email> [school_code]")
        sys.exit(1)
    
    email = sys.argv[1]
    school_code = sys.argv[2] if len(sys.argv) > 2 else None
    
    asyncio.run(verify_user(email, school_code))

