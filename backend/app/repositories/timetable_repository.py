from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.timetable import Timetable, TimetableEntry
from app.repositories.base_repository import BaseRepository

class TimetableRepository(BaseRepository[Timetable]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Timetable)
    
    async def get_by_school_id(self, school_id: int, tenant_id: Optional[UUID] = None) -> List[Timetable]:
        stmt = (
            select(Timetable)
            .where(Timetable.school_id == school_id)
            .options(
                selectinload(Timetable.entries).selectinload(TimetableEntry.class_group),
                selectinload(Timetable.entries).selectinload(TimetableEntry.subject),
                selectinload(Timetable.entries).selectinload(TimetableEntry.teacher),
                selectinload(Timetable.entries).selectinload(TimetableEntry.classroom),
            )
        )
        if tenant_id:
            stmt = stmt.where(Timetable.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_id_with_entries(self, id: int, tenant_id: Optional[UUID] = None) -> Optional[Timetable]:
        stmt = (
            select(Timetable)
            .where(Timetable.id == id)
            .options(
                selectinload(Timetable.entries).selectinload(TimetableEntry.class_group),
                selectinload(Timetable.entries).selectinload(TimetableEntry.subject),
                selectinload(Timetable.entries).selectinload(TimetableEntry.teacher),
                selectinload(Timetable.entries).selectinload(TimetableEntry.classroom),
            )
        )
        if tenant_id:
            stmt = stmt.where(Timetable.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

class TimetableEntryRepository(BaseRepository[TimetableEntry]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TimetableEntry)
    
    async def get_by_timetable_id(self, timetable_id: int, tenant_id: Optional[UUID] = None) -> List[TimetableEntry]:
        stmt = (
            select(TimetableEntry)
            .where(TimetableEntry.timetable_id == timetable_id)
            .options(
                # Don't load timetable relationship to avoid circular references
                selectinload(TimetableEntry.class_group),
                selectinload(TimetableEntry.subject),
                selectinload(TimetableEntry.teacher),
                selectinload(TimetableEntry.classroom),
            )
        )
        if tenant_id:
            stmt = stmt.where(TimetableEntry.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_teacher_and_date_range(
        self, teacher_id: int, date_from, date_to
    ) -> List[TimetableEntry]:
        # This would need to be implemented based on how we map day_of_week to actual dates
        # For now, returning entries by teacher_id
        result = await self.db.execute(
            select(TimetableEntry).where(TimetableEntry.teacher_id == teacher_id)
        )
        return list(result.scalars().all())

