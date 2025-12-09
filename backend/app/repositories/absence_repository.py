from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.absence import TeacherAbsence, Substitution
from app.repositories.base_repository import BaseRepository

class TeacherAbsenceRepository(BaseRepository[TeacherAbsence]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TeacherAbsence)
    
    async def get_by_school_id(self, school_id: int) -> List[TeacherAbsence]:
        result = await self.db.execute(
            select(TeacherAbsence)
            .options(selectinload(TeacherAbsence.teacher))
            .where(TeacherAbsence.school_id == school_id)
        )
        return list(result.scalars().all())
    
    async def get_by_teacher_id(self, teacher_id: int) -> List[TeacherAbsence]:
        result = await self.db.execute(
            select(TeacherAbsence)
            .options(selectinload(TeacherAbsence.teacher))
            .where(TeacherAbsence.teacher_id == teacher_id)
        )
        return list(result.scalars().all())

class SubstitutionRepository(BaseRepository[Substitution]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Substitution)
    
    async def get_by_school_id(self, school_id: int) -> List[Substitution]:
        result = await self.db.execute(
            select(Substitution).where(Substitution.school_id == school_id)
        )
        return list(result.scalars().all())

