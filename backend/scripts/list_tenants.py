"""
Script to list all tenants and their schools.
Usage: python -m scripts.list_tenants
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.school import School
from app.repositories.tenant_repository import TenantRepository
from app.repositories.school_repository import SchoolRepository


async def list_tenants():
    """List all tenants and their schools."""
    print("\n📋 Tenants and Schools\n")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        tenant_repo = TenantRepository(db)
        school_repo = SchoolRepository(db)
        
        # Get all tenants
        result = await db.execute(select(Tenant).order_by(Tenant.name))
        tenants = result.scalars().all()
        
        if not tenants:
            print("No tenants found.")
            return
        
        for tenant in tenants:
            print(f"\n🏢 Tenant: {tenant.name}")
            print(f"   Slug: {tenant.slug}")
            print(f"   ID: {tenant.id}")
            print(f"   Created: {tenant.created_at}")
            
            # Get schools for this tenant
            result = await db.execute(
                select(School)
                .where(School.tenant_id == tenant.id)
                .order_by(School.name)
            )
            schools = result.scalars().all()
            
            if schools:
                print(f"   Schools ({len(schools)}):")
                for school in schools:
                    print(f"      • {school.name} ({school.code}) - ID: {school.id}")
            else:
                print(f"   Schools: None")
        
        print("\n" + "=" * 60)
        print(f"\nTotal: {len(tenants)} tenant(s)")


def main():
    try:
        asyncio.run(list_tenants())
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

