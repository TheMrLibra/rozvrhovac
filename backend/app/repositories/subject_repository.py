from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subject import Subject, ClassSubjectAllocation
from app.repositories.base_repository import BaseRepository

class SubjectRepository(BaseRepository[Subject]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Subject)
    
    async def get_by_school_id(self, school_id: int) -> List[Subject]:
        result = await self.db.execute(select(Subject).where(Subject.school_id == school_id))
        return list(result.scalars().all())

class ClassSubjectAllocationRepository(BaseRepository[ClassSubjectAllocation]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ClassSubjectAllocation)
    
    async def get_by_class_group_id(self, class_group_id: int) -> List[ClassSubjectAllocation]:
        result = await self.db.execute(
            select(ClassSubjectAllocation).where(ClassSubjectAllocation.class_group_id == class_group_id)
        )
        return list(result.scalars().all())
    
    async def get_by_subject_id(self, subject_id: int) -> List[ClassSubjectAllocation]:
        result = await self.db.execute(
            select(ClassSubjectAllocation).where(ClassSubjectAllocation.subject_id == subject_id)
        )
        return list(result.scalars().all())

