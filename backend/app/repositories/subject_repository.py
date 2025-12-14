from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models.subject import Subject, ClassSubjectAllocation
from app.models.class_group import ClassGroup
from app.repositories.base_repository import BaseRepository

class SubjectRepository(BaseRepository[Subject]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Subject)
    
    async def get_by_school_id(self, school_id: int, tenant_id: Optional[UUID] = None) -> List[Subject]:
        stmt = select(Subject).where(Subject.school_id == school_id)
        if tenant_id:
            stmt = stmt.where(Subject.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class ClassSubjectAllocationRepository(BaseRepository[ClassSubjectAllocation]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ClassSubjectAllocation)
    
    async def get_by_id_with_primary_teacher(self, id: int, tenant_id: Optional[UUID] = None):
        """Get allocation by ID with primary teacher loaded, optionally filtered by tenant."""
        stmt = (
            select(ClassSubjectAllocation)
            .options(selectinload(ClassSubjectAllocation.primary_teacher))
            .where(ClassSubjectAllocation.id == id)
        )
        if tenant_id:
            # Filter through class_group relationship
            stmt = stmt.join(ClassGroup).where(ClassGroup.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_class_group_id(self, class_group_id: int, tenant_id: Optional[UUID] = None) -> List[ClassSubjectAllocation]:
        """Get allocations by class_group_id, optionally filtered by tenant."""
        stmt = (
            select(ClassSubjectAllocation)
            .options(selectinload(ClassSubjectAllocation.primary_teacher))
            .where(ClassSubjectAllocation.class_group_id == class_group_id)
        )
        if tenant_id:
            # Filter through class_group relationship
            stmt = stmt.join(ClassGroup).where(ClassGroup.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_subject_id(self, subject_id: int, tenant_id: Optional[UUID] = None) -> List[ClassSubjectAllocation]:
        """Get allocations by subject_id, optionally filtered by tenant."""
        stmt = (
            select(ClassSubjectAllocation)
            .options(selectinload(ClassSubjectAllocation.primary_teacher))
            .where(ClassSubjectAllocation.subject_id == subject_id)
        )
        if tenant_id:
            # Filter through class_group relationship
            stmt = stmt.join(ClassGroup).where(ClassGroup.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, id: int, tenant_id: UUID, **kwargs):
        """Override update to eagerly load primary_teacher after update, with tenant filtering."""
        await self.db.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        await self.db.commit()
        return await self.get_by_id_with_primary_teacher(id, tenant_id=tenant_id)

