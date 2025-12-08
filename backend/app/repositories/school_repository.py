from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.school import School, SchoolSettings
from app.repositories.base_repository import BaseRepository

class SchoolRepository(BaseRepository[School]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, School)
    
    async def get_by_code(self, code: str) -> Optional[School]:
        result = await self.db.execute(select(School).where(School.code == code))
        return result.scalar_one_or_none()

class SchoolSettingsRepository(BaseRepository[SchoolSettings]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, SchoolSettings)
    
    async def get_by_school_id(self, school_id: int) -> Optional[SchoolSettings]:
        result = await self.db.execute(select(SchoolSettings).where(SchoolSettings.school_id == school_id))
        return result.scalar_one_or_none()

