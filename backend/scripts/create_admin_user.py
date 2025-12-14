"""
Script to create an admin user for a given school.
Usage: python -m scripts.create_admin_user --school-code SCHOOL001 --email admin@school.local --password securepassword
"""
import asyncio
import argparse
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database_manager import RegistrySessionLocal, get_school_db
from app.models.user import UserRole
from app.repositories.registry_repository import RegistryRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

async def create_admin_user(
    school_code: str,
    email: str,
    password: str
):
    """Create an admin user for a school."""
    print(f"\n🚀 Creating admin user for school: {school_code}")
    print(f"   Email: {email}")
    
    # Step 1: Get school registry entry
    async with RegistrySessionLocal() as registry_db:
        registry_repo = RegistryRepository(registry_db)
        registry_entry = await registry_repo.get_by_code(school_code)
        
        if not registry_entry:
            print(f"❌ Error: School with code '{school_code}' not found in registry.")
            return False
        
        if not registry_entry.is_active:
            print(f"❌ Error: School '{school_code}' is not active.")
            return False
        
        print(f"✅ Found school: {registry_entry.name}")
        print(f"   Database: {registry_entry.database_name}")
        
        # Step 2: Connect to school database and create user
        async for school_db in get_school_db(
            database_name=registry_entry.database_name,
            host=registry_entry.database_host,
            port=registry_entry.database_port,
            user=registry_entry.database_user
        ):
            try:
                user_repo = UserRepository(school_db)
                user_service = UserService(school_db)
                
                # Check if user already exists
                existing_user = await user_repo.get_by_email(email)
                if existing_user:
                    print(f"⚠️  User with email '{email}' already exists.")
                    # Non-interactive: update password automatically
                    from app.core.security import get_password_hash
                    existing_user.password_hash = get_password_hash(password)
                    await school_db.commit()
                    print(f"✅ Updated password for user: {email}")
                    print(f"\nUser details:")
                    print(f"  Email: {existing_user.email}")
                    print(f"  Role: {existing_user.role.value}")
                    print(f"  School ID: {existing_user.school_id}")
                    print(f"  User ID: {existing_user.id}")
                    return True
                
                # Create admin user
                try:
                    admin_user = await user_service.create_user(
                        email=email,
                        password=password,
                        school_id=registry_entry.school_id,
                        role=UserRole.ADMIN
                    )
                    await school_db.commit()
                    
                    print(f"\n✅ Admin user created successfully!")
                    print(f"\nUser details:")
                    print(f"  Email: {admin_user.email}")
                    print(f"  Role: {admin_user.role.value}")
                    print(f"  School ID: {admin_user.school_id}")
                    print(f"  User ID: {admin_user.id}")
                    print(f"\n⚠️  Please save these credentials securely!")
                    
                    return True
                except Exception as e:
                    print(f"❌ Error creating user: {e}")
                    import traceback
                    traceback.print_exc()
                    await school_db.rollback()
                    raise
            finally:
                break
    
    return False

def main():
    parser = argparse.ArgumentParser(description="Create an admin user for a school")
    parser.add_argument("--school-code", required=True, help="School code")
    parser.add_argument("--email", required=True, help="Admin user email")
    parser.add_argument("--password", required=True, help="Admin user password")
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(create_admin_user(
            school_code=args.school_code,
            email=args.email,
            password=args.password
        ))
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

