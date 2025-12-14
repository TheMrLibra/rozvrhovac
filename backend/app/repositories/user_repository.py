from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_email(self, email: str, tenant_id: Optional[UUID] = None) -> Optional[User]:
        """
        Get user by email. If tenant_id is provided, filter by tenant.
        If tenant_id is None, searches across all tenants (for login without tenant context).
        """
        stmt = select(User).where(User.email == email)
        if tenant_id:
            stmt = stmt.where(User.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email_any_tenant(self, email: str) -> Optional[User]:
        """
        Get user by email across all tenants (for login without tenant context).
        Returns the first matching user. If same email exists in multiple tenants,
        this will return one of them (typically the first found).
        """
        result = await self.db.execute(
            select(User).where(User.email == email).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_school_id(self, school_id: int, tenant_id: UUID) -> list[User]:
        """Get users by school_id, filtered by tenant."""
        result = await self.db.execute(
            select(User)
            .where(User.school_id == school_id)
            .where(User.tenant_id == tenant_id)
        )
        return list(result.scalars().all())
    
    # Override get_by_id to not require tenant_id for auth (user lookup by ID doesn't need tenant)
    # But we'll keep the base implementation that requires tenant_id for safety
    async def get_by_id_for_auth(self, user_id: int) -> Optional[User]:
        """Get user by ID for authentication (no tenant filtering)."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

