from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.class_group import ClassGroup
from app.repositories.base_repository import BaseRepository

class ClassGroupRepository(BaseRepository[ClassGroup]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ClassGroup)
    
    async def get_by_school_id(self, school_id: int, tenant_id: Optional[UUID] = None) -> List[ClassGroup]:
        stmt = (
            select(ClassGroup)
            .where(ClassGroup.school_id == school_id)
            .options(selectinload(ClassGroup.subject_allocations))
        )
        if tenant_id:
            stmt = stmt.where(ClassGroup.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

