from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
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
    
    async def get_by_id_with_primary_teacher(self, id: int):
        result = await self.db.execute(
            select(ClassSubjectAllocation)
            .options(selectinload(ClassSubjectAllocation.primary_teacher))
            .where(ClassSubjectAllocation.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_class_group_id(self, class_group_id: int) -> List[ClassSubjectAllocation]:
        result = await self.db.execute(
            select(ClassSubjectAllocation)
            .options(selectinload(ClassSubjectAllocation.primary_teacher))
            .where(ClassSubjectAllocation.class_group_id == class_group_id)
        )
        return list(result.scalars().all())
    
    async def get_by_subject_id(self, subject_id: int) -> List[ClassSubjectAllocation]:
        result = await self.db.execute(
            select(ClassSubjectAllocation)
            .options(selectinload(ClassSubjectAllocation.primary_teacher))
            .where(ClassSubjectAllocation.subject_id == subject_id)
        )
        return list(result.scalars().all())
    
    async def update(self, id: int, **kwargs):
        """Override update to eagerly load primary_teacher after update"""
        await self.db.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        await self.db.commit()
        return await self.get_by_id_with_primary_teacher(id)

