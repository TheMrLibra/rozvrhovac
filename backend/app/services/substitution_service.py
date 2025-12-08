from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.absence import TeacherAbsence, Substitution, SubstitutionStatus
from app.models.timetable import TimetableEntry
from app.models.teacher import Teacher
from app.repositories.absence_repository import TeacherAbsenceRepository, SubstitutionRepository
from app.repositories.timetable_repository import TimetableEntryRepository
from app.repositories.teacher_repository import TeacherRepository
from app.services.timetable_validation_service import TimetableValidationService

class SubstitutionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.absence_repo = TeacherAbsenceRepository(db)
        self.substitution_repo = SubstitutionRepository(db)
        self.entry_repo = TimetableEntryRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.validation_service = TimetableValidationService(db)
    
    async def generate_substitutions(
        self,
        school_id: int,
        absence_id: int
    ) -> List[Substitution]:
        """Generate substitutions for a teacher absence"""
        absence = await self.absence_repo.get_by_id(absence_id)
        if not absence or absence.school_id != school_id:
            raise ValueError("Absence not found")
        
        # Find affected timetable entries
        affected_entries = await self._find_affected_entries(absence)
        
        substitutions: List[Substitution] = []
        
        for entry in affected_entries:
            # Try to find a substitute teacher
            substitute_teacher = await self._find_substitute_teacher(entry, absence)
            
            substitution = Substitution(
                school_id=school_id,
                timetable_entry_id=entry.id,
                original_teacher_id=absence.teacher_id,
                substitute_teacher_id=substitute_teacher.id if substitute_teacher else None,
                status=SubstitutionStatus.AUTO_GENERATED if substitute_teacher else SubstitutionStatus.AUTO_GENERATED
            )
            substitution = await self.substitution_repo.create(substitution)
            substitutions.append(substitution)
        
        return substitutions
    
    async def _find_affected_entries(self, absence: TeacherAbsence) -> List[TimetableEntry]:
        """Find timetable entries affected by the absence"""
        # Get all entries for this teacher
        all_entries = await self.entry_repo.get_by_teacher_and_date_range(
            absence.teacher_id, absence.date_from, absence.date_to
        )
        
        # Filter entries that fall within the absence period
        # This is simplified - would need proper date-to-day-of-week mapping
        # In a real implementation, we'd:
        # 1. Get all timetables for the school
        # 2. Map absence dates to day_of_week
        # 3. Filter entries by matching day_of_week and date range
        affected = []
        for entry in all_entries:
            # For now, return all entries for this teacher
            # TODO: Implement proper date-to-day-of-week mapping
            affected.append(entry)
        
        return affected
    
    async def _find_substitute_teacher(
        self,
        entry: TimetableEntry,
        absence: TeacherAbsence
    ) -> Optional[Teacher]:
        """Find a suitable substitute teacher"""
        # Get all teachers for this school
        teachers = await self.teacher_repo.get_by_school_id(entry.timetable.school_id)
        
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        day_name = day_names[entry.day_of_week]
        
        for teacher in teachers:
            if teacher.id == absence.teacher_id:
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
                if entry.lesson_index not in available_hours:
                    continue
            
            # Check if already busy
            existing_entries = await self.entry_repo.get_by_timetable_id(entry.timetable_id)
            if any(e.teacher_id == teacher.id and e.day_of_week == entry.day_of_week 
                   and e.lesson_index == entry.lesson_index for e in existing_entries):
                continue
            
            # Check weekly hours
            teacher_hours = sum(1 for e in existing_entries if e.teacher_id == teacher.id)
            if teacher_hours >= teacher.max_weekly_hours:
                continue
            
            return teacher
        
        return None

