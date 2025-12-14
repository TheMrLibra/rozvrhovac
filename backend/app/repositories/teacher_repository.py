from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.teacher import Teacher
from app.repositories.base_repository import BaseRepository

class TeacherRepository(BaseRepository[Teacher]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Teacher)
    
    async def get_by_school_id(self, school_id: int, tenant_id: Optional[UUID] = None) -> List[Teacher]:
        stmt = (
            select(Teacher)
            .where(Teacher.school_id == school_id)
            .options(selectinload(Teacher.capabilities))
        )
        if tenant_id:
            stmt = stmt.where(Teacher.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_id_with_capabilities(self, id: int) -> Teacher:
        result = await self.db.execute(
            select(Teacher)
            .where(Teacher.id == id)
            .options(selectinload(Teacher.capabilities))
        )
        return result.scalar_one_or_none()

