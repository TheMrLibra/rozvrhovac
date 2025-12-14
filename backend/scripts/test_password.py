"""
Test password verification for a user.
"""
import asyncio
import sys
from app.core.database_manager import get_registry_db, get_school_db
from app.repositories.registry_repository import RegistryRepository
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, get_password_hash

async def test_password(email: str, password: str, school_code: str):
    """Test password verification."""
    async for registry_db in get_registry_db():
        try:
            registry_repo = RegistryRepository(registry_db)
            registry_entry = await registry_repo.get_by_code(school_code)
            
            if not registry_entry:
                print(f"❌ School '{school_code}' not found")
                return
            
            async for db in get_school_db(
                database_name=registry_entry.database_name,
                host=registry_entry.database_host,
                port=registry_entry.database_port,
                user=registry_entry.database_user
            ):
                try:
                    user_repo = UserRepository(db)
                    user = await user_repo.get_by_email(email)
                    
                    if not user:
                        print(f"❌ User '{email}' not found")
                        return
                    
                    print(f"✅ User found: {email}")
                    print(f"   Password hash: {user.password_hash}")
                    print(f"   Is active: {user.is_active}")
                    print(f"   Role: {user.role}")
                    
                    # Test password verification
                    print(f"\n🔐 Testing password verification...")
                    print(f"   Input password: {password}")
                    
                    is_valid = verify_password(password, user.password_hash)
                    print(f"   Verification result: {is_valid}")
                    
                    if not is_valid:
                        print(f"\n⚠️  Password verification failed!")
                        print(f"   Generating new hash for comparison...")
                        new_hash = get_password_hash(password)
                        print(f"   New hash: {new_hash}")
                        print(f"   Old hash: {user.password_hash}")
                        print(f"   Hashes match: {new_hash == user.password_hash}")
                        
                        # Test if new hash verifies
                        test_new = verify_password(password, new_hash)
                        print(f"   New hash verifies: {test_new}")
                    
                finally:
                    break
        finally:
            break

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m scripts.test_password <email> <password> <school_code>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    school_code = sys.argv[3]
    
    asyncio.run(test_password(email, password, school_code))

