from typing import Optional
from uuid import UUID
from datetime import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.school import School, SchoolSettings
from app.repositories.school_repository import SchoolRepository, SchoolSettingsRepository
from app.schemas.school import SchoolSettingsUpdate

class SchoolService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.school_repo = SchoolRepository(db)
        self.settings_repo = SchoolSettingsRepository(db)
    
    async def get_school(self, school_id: int, tenant_id: UUID) -> Optional[School]:
        """Get a school by ID, filtered by tenant."""
        return await self.school_repo.get_by_id(school_id, tenant_id=tenant_id)
    
    async def get_school_settings(self, school_id: int, tenant_id: UUID) -> Optional[SchoolSettings]:
        """Get school settings by school ID, filtered by tenant."""
        return await self.settings_repo.get_by_school_id(school_id, tenant_id=tenant_id)
    
    async def get_or_create_school_settings(
        self,
        school_id: int,
        tenant_id: UUID
    ) -> SchoolSettings:
        """Get school settings, creating default ones if they don't exist."""
        settings = await self.settings_repo.get_by_school_id(school_id, tenant_id=tenant_id)
        if not settings:
            # Create default settings
            settings = SchoolSettings(
                tenant_id=tenant_id,
                school_id=school_id,
                start_time=time(8, 0),  # 08:00
                end_time=time(16, 0),  # 16:00
                class_hour_length_minutes=45,
                break_duration_minutes=10,
                break_durations=[10, 20, 10, 10, 10],  # Default break durations
                possible_lunch_hours=[3, 4, 5],
                lunch_duration_minutes=30
            )
            settings = await self.settings_repo.create(settings, tenant_id=tenant_id)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings
    
    async def update_school_settings(
        self,
        school_id: int,
        settings_data: SchoolSettingsUpdate,
        tenant_id: UUID
    ) -> Optional[SchoolSettings]:
        """Update school settings, filtered by tenant."""
        settings = await self.settings_repo.get_by_school_id(school_id, tenant_id=tenant_id)
        if not settings:
            return None
        
        update_data = {k: v for k, v in settings_data.model_dump().items() if v is not None}
        return await self.settings_repo.update(settings.id, tenant_id=tenant_id, **update_data)

