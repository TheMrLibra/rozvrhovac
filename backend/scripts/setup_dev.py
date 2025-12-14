"""
One-command development setup script.
Creates tenant, runs migrations, and creates admin user.
Usage: python -m scripts.setup_dev
"""
import asyncio
import sys
import os
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.school import School
from app.models.user import UserRole
from app.repositories.tenant_repository import TenantRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.core.security import get_password_hash


async def setup_dev():
    """Complete development setup."""
    print("\n🚀 Starting development setup...\n")
    
    async with AsyncSessionLocal() as db:
        # Step 1: Create tenant if it doesn't exist
        tenant_slug = os.getenv("DEFAULT_TENANT_SLUG", "default-school")
        tenant_name = os.getenv("DEFAULT_TENANT_NAME", "Default School")
        
        tenant_repo = TenantRepository(db)
        tenant = await tenant_repo.get_by_slug(tenant_slug)
        
        if tenant:
            print(f"✅ Tenant '{tenant_slug}' already exists (ID: {tenant.id})")
        else:
            print(f"📦 Creating tenant: {tenant_name} (slug: {tenant_slug})...")
            tenant = Tenant(
                id=uuid4(),
                name=tenant_name,
                slug=tenant_slug
            )
            tenant = await tenant_repo.create(tenant)
            await db.commit()
            await db.refresh(tenant)
            print(f"✅ Tenant created (ID: {tenant.id})")
        
        tenant_id = tenant.id
        
        # Step 2: Create school if it doesn't exist
        school_code = os.getenv("DEFAULT_SCHOOL_CODE", "SCHOOL001")
        school_repo = SchoolRepository(db)
        school = await school_repo.get_by_code(school_code, tenant_id=tenant_id)
        
        if school:
            print(f"✅ School '{school_code}' already exists (ID: {school.id})")
        else:
            print(f"📦 Creating school: {school_code}...")
            school = School(
                tenant_id=tenant_id,
                name=f"School {school_code}",
                code=school_code
            )
            school = await school_repo.create(school, tenant_id=tenant_id)
            await db.commit()
            await db.refresh(school)
            print(f"✅ School created (ID: {school.id})")
        
        # Step 3: Create admin user if it doesn't exist
        admin_email = os.getenv("ADMIN_EMAIL", "admin@school.example")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        user_repo = UserRepository(db)
        user_service = UserService(db)
        
        existing_user = await user_repo.get_by_email(admin_email, tenant_id=tenant_id)
        if existing_user:
            print(f"✅ Admin user '{admin_email}' already exists")
            # Update password
            existing_user.password_hash = get_password_hash(admin_password)
            await db.commit()
            print(f"✅ Password updated for admin user")
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
        print("✅ Development setup complete!")
        print("="*60)
        print(f"\n📋 Summary:")
        print(f"   Tenant: {tenant.name} ({tenant.slug})")
        print(f"   Tenant ID: {tenant.id}")
        print(f"   School: {school.name} ({school.code})")
        print(f"   Admin Email: {admin_email}")
        print(f"   Admin Password: {admin_password}")
        print(f"\n🔗 Access Points:")
        print(f"   Backend API: http://localhost:8000")
        print(f"   API Docs: http://localhost:8000/docs")
        print(f"   Frontend: http://localhost:5173 (run: cd frontend && npm run dev)")
        print(f"\n🔐 Login Example:")
        print(f"   curl -X POST http://localhost:8000/api/v1/auth/login \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -H 'X-Tenant: {tenant_slug}' \\")
        print(f"     -d '{{\"email\": \"{admin_email}\", \"password\": \"{admin_password}\"}}'")
        print("\n")
        
        return True


def main():
    try:
        success = asyncio.run(setup_dev())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

