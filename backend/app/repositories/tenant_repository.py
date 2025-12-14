from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tenant import Tenant
from app.repositories.base_repository import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, Tenant)
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        result = await self.db.execute(
            select(self.model).where(self.model.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, id: UUID) -> Optional[Tenant]:
        """Get tenant by UUID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

