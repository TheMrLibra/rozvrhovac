from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.class_group import ClassGroup
from app.repositories.base_repository import BaseRepository

class ClassGroupRepository(BaseRepository[ClassGroup]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ClassGroup)
    
    async def get_by_school_id(self, school_id: int) -> List[ClassGroup]:
        result = await self.db.execute(
            select(ClassGroup)
            .where(ClassGroup.school_id == school_id)
            .options(selectinload(ClassGroup.subject_allocations))
        )
        return list(result.scalars().all())

