"""
Script to create a new school for a tenant.
Usage: python -m scripts.create_school --tenant-slug <slug> --name <name> --code <code> [--create-admin]
"""
import asyncio
import sys
import os
import argparse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.school import School, SchoolSettings
from app.models.user import UserRole
from app.repositories.tenant_repository import TenantRepository
from app.repositories.school_repository import SchoolRepository, SchoolSettingsRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.core.config import settings
from datetime import time


async def create_school(
    tenant_slug: str,
    school_name: str,
    school_code: str,
    create_admin: bool = False,
    admin_email: str = None,
    admin_password: str = None
):
    """Create a new school for a tenant."""
    print("\n🏫 Creating new school...\n")
    
    async with AsyncSessionLocal() as db:
        # Step 1: Get tenant
        tenant_repo = TenantRepository(db)
        tenant = await tenant_repo.get_by_slug(tenant_slug)
        
        if not tenant:
            print(f"❌ Tenant with slug '{tenant_slug}' not found.")
            print(f"   Available tenants can be listed with: make list-tenants")
            return False
        
        print(f"✅ Found tenant: {tenant.name} ({tenant.slug})")
        tenant_id = tenant.id
        
        # Step 2: Check if school already exists
        school_repo = SchoolRepository(db)
        existing_school = await school_repo.get_by_code(school_code, tenant_id=tenant_id)
        
        if existing_school:
            print(f"❌ School with code '{school_code}' already exists for tenant '{tenant_slug}'")
            print(f"   School ID: {existing_school.id}")
            print(f"   School Name: {existing_school.name}")
            return False
        
        # Step 3: Create school
        print(f"📦 Creating school: {school_name} (code: {school_code})...")
        school = School(
            tenant_id=tenant_id,
            name=school_name,
            code=school_code
        )
        school = await school_repo.create(school, tenant_id=tenant_id)
        await db.commit()
        await db.refresh(school)
        print(f"✅ School created (ID: {school.id})")
        
        # Step 4: Create default school settings
        settings_repo = SchoolSettingsRepository(db)
        existing_settings = await settings_repo.get_by_school_id(school.id, tenant_id=tenant_id)
        
        if existing_settings:
            print(f"✅ School settings already exist")
        else:
            print(f"📦 Creating default school settings...")
            default_settings = SchoolSettings(
                tenant_id=tenant_id,
                school_id=school.id,
                start_time=time(8, 0),  # 08:00
                end_time=time(16, 0),   # 16:00
                class_hour_length_minutes=45,
                break_duration_minutes=10,
                break_durations=[5, 10, 10, 10, 10],  # 5 min after 1st lesson, 10 min after others
                possible_lunch_hours=[3, 4, 5],  # Lunch can be at lesson 3, 4, or 5
                lunch_duration_minutes=30
            )
            default_settings = await settings_repo.create(default_settings, tenant_id=tenant_id)
            await db.commit()
            print(f"✅ Default school settings created")
        
        # Step 5: Create admin user if requested
        if create_admin:
            if not admin_email:
                admin_email = f"admin@{school_code.lower()}.example"
            if not admin_password:
                admin_password = "admin123"
            
            user_repo = UserRepository(db)
            user_service = UserService(db)
            
            existing_user = await user_repo.get_by_email(admin_email, tenant_id=tenant_id)
            if existing_user:
                print(f"⚠️  User with email '{admin_email}' already exists")
            else:
                print(f"📦 Creating admin user: {admin_email}...")
                admin_user = await user_service.create_user(
                    email=admin_email,
                    password=admin_password,
                    tenant_id=tenant_id,
                    school_id=school.id,
                    role=UserRole.ADMIN
                )
                await db.commit()
                await db.refresh(admin_user)
                print(f"✅ Admin user created (ID: {admin_user.id})")
        
        print("\n" + "="*60)
        print("✅ School creation complete!")
        print("="*60)
        print(f"\n📋 Summary:")
        print(f"   Tenant: {tenant.name} ({tenant.slug})")
        print(f"   School: {school.name} ({school.code})")
        print(f"   School ID: {school.id}")
        if create_admin:
            print(f"   Admin Email: {admin_email}")
            print(f"   Admin Password: {admin_password}")
        print(f"\n🔗 Next Steps:")
        print(f"   - Create test data: make create-test-data TENANT_SLUG={tenant_slug} SCHOOL_CODE={school_code}")
        print(f"   - Login with X-Tenant header: {tenant_slug}")
        print("\n")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Create a new school for a tenant")
    parser.add_argument(
        "--tenant-slug",
        type=str,
        default=os.getenv("DEFAULT_TENANT_SLUG", "default-school"),
        help="Slug of the tenant (default: from DEFAULT_TENANT_SLUG env or 'default-school')"
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Name of the school"
    )
    parser.add_argument(
        "--code",
        type=str,
        required=True,
        help="Unique code for the school (must be unique per tenant)"
    )
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create an admin user for this school"
    )
    parser.add_argument(
        "--admin-email",
        type=str,
        default=None,
        help="Email for admin user (default: admin@<school-code>.example)"
    )
    parser.add_argument(
        "--admin-password",
        type=str,
        default=None,
        help="Password for admin user (default: admin123)"
    )
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(create_school(
            tenant_slug=args.tenant_slug,
            school_name=args.name,
            school_code=args.code,
            create_admin=args.create_admin,
            admin_email=args.admin_email,
            admin_password=args.admin_password
        ))
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
