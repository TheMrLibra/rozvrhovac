"""
Script to create a default tenant for development/testing.
Usage: python -m scripts.seed_tenant --name "Default School" --slug "default-school"
"""
import asyncio
import argparse
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.repositories.tenant_repository import TenantRepository
import uuid


async def create_tenant(
    name: str,
    slug: str
):
    """Create a tenant."""
    print(f"\n🚀 Creating tenant: {name}")
    print(f"   Slug: {slug}")
    
    async with AsyncSessionLocal() as db:
        tenant_repo = TenantRepository(db)
        
        # Check if tenant with slug already exists
        existing = await tenant_repo.get_by_slug(slug)
        if existing:
            print(f"⚠️  Tenant with slug '{slug}' already exists.")
            print(f"\nTenant details:")
            print(f"  ID: {existing.id}")
            print(f"  Name: {existing.name}")
            print(f"  Slug: {existing.slug}")
            return existing
        
        # Create tenant
        tenant = Tenant(
            id=uuid.uuid4(),
            name=name,
            slug=slug
        )
        
        try:
            created_tenant = await tenant_repo.create(tenant)
            await db.commit()
            print(f"\n✅ Tenant created successfully!")
            print(f"\nTenant details:")
            print(f"  ID: {created_tenant.id}")
            print(f"  Name: {created_tenant.name}")
            print(f"  Slug: {created_tenant.slug}")
            print(f"\n⚠️  Set this UUID as MIGRATION_DEFAULT_TENANT_ID for migrations:")
            print(f"  export MIGRATION_DEFAULT_TENANT_ID={created_tenant.id}")
            return created_tenant
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


def main():
    parser = argparse.ArgumentParser(description="Create a tenant")
    parser.add_argument("--name", required=True, help="Tenant name")
    parser.add_argument("--slug", required=True, help="Tenant slug (unique identifier)")
    
    args = parser.parse_args()
    
    try:
        tenant = asyncio.run(create_tenant(
            name=args.name,
            slug=args.slug
        ))
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

