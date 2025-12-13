from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.school import School, SchoolSettings
from app.repositories.school_repository import SchoolRepository, SchoolSettingsRepository
from app.schemas.school import SchoolSettingsUpdate

class SchoolService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.school_repo = SchoolRepository(db)
        self.settings_repo = SchoolSettingsRepository(db)
    
    async def get_school(self, school_id: int) -> Optional[School]:
        """Get a school by ID"""
        return await self.school_repo.get_by_id(school_id)
    
    async def get_school_settings(self, school_id: int) -> Optional[SchoolSettings]:
        """Get school settings by school ID"""
        return await self.settings_repo.get_by_school_id(school_id)
    
    async def update_school_settings(
        self,
        school_id: int,
        settings_data: SchoolSettingsUpdate
    ) -> Optional[SchoolSettings]:
        """Update school settings"""
        settings = await self.settings_repo.get_by_school_id(school_id)
        if not settings:
            return None
        
        update_data = {k: v for k, v in settings_data.model_dump().items() if v is not None}
        return await self.settings_repo.update(settings.id, **update_data)

