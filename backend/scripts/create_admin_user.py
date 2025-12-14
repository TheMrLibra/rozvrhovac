"""
Script to create an admin user for a tenant.
Usage: python -m scripts.create_admin_user --tenant-slug default-school --email admin@school.local --password securepassword --school-code SCHOOL001
"""
import asyncio
import argparse
import sys
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import UserRole
from app.models.school import School
from app.repositories.tenant_repository import TenantRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

async def create_admin_user(
    tenant_slug: str,
    email: str,
    password: str,
    school_code: str = "SCHOOL001"
):
    """Create an admin user for a tenant."""
    print(f"\n🚀 Creating admin user")
    print(f"   Tenant: {tenant_slug}")
    print(f"   Email: {email}")
    print(f"   School Code: {school_code}")
    
    async with AsyncSessionLocal() as db:
        # Step 1: Get tenant
        tenant_repo = TenantRepository(db)
        tenant = await tenant_repo.get_by_slug(tenant_slug)
        
        if not tenant:
            print(f"❌ Error: Tenant with slug '{tenant_slug}' not found.")
            print(f"   Available tenants:")
            tenants = await tenant_repo.get_all()
            for t in tenants:
                print(f"     - {t.slug} ({t.name})")
            return False
        
        print(f"✅ Found tenant: {tenant.name} (ID: {tenant.id})")
        
        # Step 2: Get or create school
        school_repo = SchoolRepository(db)
        school = await school_repo.get_by_code(school_code, tenant_id=tenant.id)
        
        if not school:
            print(f"Creating school with code '{school_code}'...")
            school = School(
                tenant_id=tenant.id,
                name=f"School {school_code}",
                code=school_code
            )
            school = await school_repo.create(school, tenant_id=tenant.id)
            await db.commit()
            await db.refresh(school)
            print(f"✅ Created school: {school.name} (ID: {school.id})")
        else:
            print(f"✅ Using existing school: {school.name} (ID: {school.id})")
        
        # Step 3: Create admin user
        user_repo = UserRepository(db)
        user_service = UserService(db)
        
        # Check if user already exists
        existing_user = await user_repo.get_by_email(email, tenant_id=tenant.id)
        if existing_user:
            print(f"⚠️  User with email '{email}' already exists.")
            # Non-interactive: update password automatically
            from app.core.security import get_password_hash
            existing_user.password_hash = get_password_hash(password)
            await db.commit()
            await db.refresh(existing_user)
            print(f"✅ Updated password for user: {email}")
            print(f"\nUser details:")
            print(f"  Email: {existing_user.email}")
            print(f"  Role: {existing_user.role.value}")
            print(f"  Tenant ID: {existing_user.tenant_id}")
            print(f"  School ID: {existing_user.school_id}")
            print(f"  User ID: {existing_user.id}")
            return True
        
        # Create admin user
        print(f"Creating admin user...")
        admin_user = await user_service.create_user(
            email=email,
            password=password,
            tenant_id=tenant.id,
            school_id=school.id,
            role=UserRole.ADMIN
        )
        await db.commit()
        await db.refresh(admin_user)
        print(f"✅ Admin user created successfully!")
        print(f"\nUser details:")
        print(f"  Email: {admin_user.email}")
        print(f"  Role: {admin_user.role.value}")
        print(f"  Tenant ID: {admin_user.tenant_id}")
        print(f"  School ID: {admin_user.school_id}")
        print(f"  User ID: {admin_user.id}")
        print(f"\n⚠️  Please save these credentials securely!")
        print(f"\nTo login, use:")
        print(f"  curl -X POST http://localhost:8000/api/v1/auth/login \\")
        print(f"    -H 'Content-Type: application/json' \\")
        print(f"    -H 'X-Tenant: {tenant_slug}' \\")
        print(f"    -d '{{\"email\": \"{email}\", \"password\": \"{password}\"}}'")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Create an admin user for a tenant")
    parser.add_argument("--tenant-slug", required=True, help="Tenant slug (e.g., 'default-school')")
    parser.add_argument("--email", required=True, help="Admin user email")
    parser.add_argument("--password", required=True, help="Admin user password")
    parser.add_argument("--school-code", default="SCHOOL001", help="School code (default: SCHOOL001)")
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(create_admin_user(
            tenant_slug=args.tenant_slug,
            email=args.email,
            password=args.password,
            school_code=args.school_code
        ))
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
