from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.school import School, SchoolSettings
from app.repositories.base_repository import BaseRepository

class SchoolRepository(BaseRepository[School]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, School)
    
    async def get_by_code(self, code: str, tenant_id: UUID) -> Optional[School]:
        """Get school by code, filtered by tenant."""
        result = await self.db.execute(
            select(School)
            .where(School.code == code)
            .where(School.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

class SchoolSettingsRepository(BaseRepository[SchoolSettings]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SchoolSettings)
    
    async def get_by_school_id(self, school_id: int, tenant_id: UUID) -> Optional[SchoolSettings]:
        """Get school settings by school ID, filtered by tenant."""
        result = await self.db.execute(
            select(SchoolSettings)
            .where(SchoolSettings.school_id == school_id)
            .where(SchoolSettings.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

