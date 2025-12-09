from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.timetable import Timetable, TimetableEntry
from app.models.absence import TeacherAbsence
from app.models.teacher import Teacher
from app.repositories.timetable_repository import TimetableRepository, TimetableEntryRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.absence_repository import TeacherAbsenceRepository

class SubstituteTimetableService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.timetable_repo = TimetableRepository(db)
        self.entry_repo = TimetableEntryRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.classroom_repo = ClassroomRepository(db)
        self.absence_repo = TeacherAbsenceRepository(db)
    
    def _date_to_day_of_week(self, target_date: date) -> int:
        """Convert a date to day of week (0=Monday, 4=Friday)"""
        # weekday() returns 0=Monday, 6=Sunday
        return target_date.weekday()
    
    async def generate_substitute_timetable(
        self,
        school_id: int,
        base_timetable_id: int,
        substitute_date: date
    ) -> Timetable:
        """Generate a substitute timetable for a specific date based on absences"""
        # Get the primary timetable
        base_timetable = await self.timetable_repo.get_by_id_with_entries(base_timetable_id)
        if not base_timetable or base_timetable.school_id != school_id:
            raise ValueError("Base timetable not found")
        if base_timetable.is_primary != 1:
            raise ValueError("Base timetable must be a primary timetable")
        
        # Check if substitute timetable already exists for this date
        existing = await self._find_existing_substitute(school_id, base_timetable_id, substitute_date)
        if existing:
            # Delete existing substitute timetable and recreate
            await self._delete_substitute_timetable(existing.id)
        
        # Get all absences for this date
        day_of_week = self._date_to_day_of_week(substitute_date)
        absences = await self._get_absences_for_date(school_id, substitute_date)
        
        # Get all teachers and classrooms
        teachers = await self.teacher_repo.get_by_school_id(school_id)
        classrooms = await self.classroom_repo.get_by_school_id(school_id)
        
        # Create substitute timetable
        substitute_timetable = Timetable(
            school_id=school_id,
            name=f"Substitute for {substitute_date.strftime('%Y-%m-%d')}",
            valid_from=substitute_date,
            valid_to=substitute_date,
            is_primary=0,  # This is a substitute timetable
            substitute_for_date=substitute_date,
            base_timetable_id=base_timetable_id
        )
        substitute_timetable = await self.timetable_repo.create(substitute_timetable)
        
        # Copy entries from base timetable, replacing teachers/classrooms where needed
        entries: List[TimetableEntry] = []
        
        for base_entry in base_timetable.entries:
            # Only process entries for the day of week that matches the substitute date
            if base_entry.day_of_week != day_of_week:
                continue
            
            # Check if the original teacher is absent
            absent_teacher_id = None
            for absence in absences:
                if absence.teacher_id == base_entry.teacher_id:
                    absent_teacher_id = absence.teacher_id
                    break
            
            # Find substitute teacher if original is absent
            teacher_id = base_entry.teacher_id
            classroom_id = base_entry.classroom_id
            
            if absent_teacher_id:
                substitute_teacher = await self._find_substitute_teacher(
                    base_entry, absent_teacher_id, teachers, substitute_date, entries
                )
                if substitute_teacher:
                    teacher_id = substitute_teacher.id
                else:
                    # No substitute found, skip this entry or keep original (admin can fix manually)
                    teacher_id = base_entry.teacher_id
            
            # Create entry for substitute timetable
            entry = TimetableEntry(
                timetable_id=substitute_timetable.id,
                class_group_id=base_entry.class_group_id,
                subject_id=base_entry.subject_id,
                teacher_id=teacher_id,
                classroom_id=classroom_id,
                day_of_week=day_of_week,
                lesson_index=base_entry.lesson_index
            )
            entries.append(entry)
        
        # Save all entries
        for entry in entries:
            await self.entry_repo.create(entry)
        
        return substitute_timetable
    
    async def _find_existing_substitute(
        self,
        school_id: int,
        base_timetable_id: int,
        substitute_date: date
    ) -> Optional[Timetable]:
        """Find existing substitute timetable for a date"""
        result = await self.db.execute(
            select(Timetable).where(
                Timetable.school_id == school_id,
                Timetable.base_timetable_id == base_timetable_id,
                Timetable.substitute_for_date == substitute_date,
                Timetable.is_primary == 0
            )
        )
        return result.scalar_one_or_none()
    
    async def _delete_substitute_timetable(self, timetable_id: int):
        """Delete a substitute timetable and its entries"""
        # Delete entries first
        result = await self.db.execute(
            select(TimetableEntry).where(TimetableEntry.timetable_id == timetable_id)
        )
        entries = result.scalars().all()
        for entry in entries:
            await self.entry_repo.delete(entry.id)
        
        # Delete timetable
        await self.timetable_repo.delete(timetable_id)
    
    async def _get_absences_for_date(self, school_id: int, target_date: date) -> List[TeacherAbsence]:
        """Get all teacher absences that cover the target date"""
        from app.models.absence import TeacherAbsence
        result = await self.db.execute(
            select(TeacherAbsence).where(
                TeacherAbsence.school_id == school_id,
                TeacherAbsence.date_from <= target_date,
                TeacherAbsence.date_to >= target_date
            )
        )
        return list(result.scalars().all())
    
    async def _find_substitute_teacher(
        self,
        entry: TimetableEntry,
        absent_teacher_id: int,
        teachers: List[Teacher],
        target_date: date,
        existing_entries: List[TimetableEntry]
    ) -> Optional[Teacher]:
        """Find a substitute teacher for an entry"""
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        day_name = day_names[entry.day_of_week]
        
        for teacher in teachers:
            if teacher.id == absent_teacher_id:
                continue
            
            # Check if teacher can teach this subject
            can_teach = False
            for capability in teacher.capabilities:
                if capability.subject_id == entry.subject_id:
                    can_teach = True
                    break
            
            if not can_teach:
                continue
            
            # Check availability
            if teacher.availability:
                available_hours = teacher.availability.get(day_name, [])
                if available_hours and entry.lesson_index not in available_hours:
                    continue
            
            # Check if teacher is already busy at this time
            if any(e.teacher_id == teacher.id and e.day_of_week == entry.day_of_week 
                   and e.lesson_index == entry.lesson_index for e in existing_entries):
                continue
            
            # Check if teacher is absent on this date
            teacher_absences = await self._get_absences_for_date(teacher.school_id, target_date)
            if any(a.teacher_id == teacher.id for a in teacher_absences):
                continue
            
            return teacher
        
        return None

