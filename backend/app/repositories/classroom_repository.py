from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.classroom import Classroom
from app.repositories.base_repository import BaseRepository

class ClassroomRepository(BaseRepository[Classroom]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Classroom)
    
    async def get_by_school_id(self, school_id: int) -> List[Classroom]:
        result = await self.db.execute(select(Classroom).where(Classroom.school_id == school_id))
        return list(result.scalars().all())

