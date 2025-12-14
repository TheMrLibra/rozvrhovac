from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.classroom import Classroom
from app.repositories.base_repository import BaseRepository

class ClassroomRepository(BaseRepository[Classroom]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Classroom)
    
    async def get_by_school_id(self, school_id: int, tenant_id: Optional[UUID] = None) -> List[Classroom]:
        stmt = select(Classroom).where(Classroom.school_id == school_id)
        if tenant_id:
            stmt = stmt.where(Classroom.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

