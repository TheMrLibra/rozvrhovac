from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.teacher import Teacher
from app.repositories.base_repository import BaseRepository

class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Teacher)
    
    async def get_by_school_id(self, school_id: int) -> List[Teacher]:
        result = await self.db.execute(
            select(Teacher)
            .where(Teacher.school_id == school_id)
            .options(selectinload(Teacher.capabilities))
        )
        return list(result.scalars().all())
    
    async def get_by_id_with_capabilities(self, id: int) -> Teacher:
        result = await self.db.execute(
            select(Teacher)
            .where(Teacher.id == id)
            .options(selectinload(Teacher.capabilities))
        )
        return result.scalar_one_or_none()

