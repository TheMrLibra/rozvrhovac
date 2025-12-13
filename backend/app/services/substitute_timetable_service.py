from typing import List, Optional, Dict, Tuple
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.timetable import Timetable, TimetableEntry
from app.models.absence import TeacherAbsence
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.class_group import ClassGroup
from app.models.classroom import Classroom
from app.repositories.timetable_repository import TimetableRepository, TimetableEntryRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.absence_repository import TeacherAbsenceRepository
from app.repositories.class_group_repository import ClassGroupRepository
from app.repositories.subject_repository import SubjectRepository

class SubstituteTimetableService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.timetable_repo = TimetableRepository(db)
        self.entry_repo = TimetableEntryRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.classroom_repo = ClassroomRepository(db)
        self.absence_repo = TeacherAbsenceRepository(db)
        self.class_repo = ClassGroupRepository(db)
        self.subject_repo = SubjectRepository(db)
    
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
        
        # Reload with entries for return
        substitute_timetable = await self.timetable_repo.get_by_id_with_entries(substitute_timetable.id)
        
        # Get all classes and subjects for constraint checking
        classes = await self.class_repo.get_by_school_id(school_id)
        classes_dict = {c.id: c for c in classes}
        subjects = await self.subject_repo.get_by_school_id(school_id)
        subjects_dict = {s.id: s for s in subjects}
        
        # Track teacher hours for weekly limit checking
        teacher_hours: Dict[int, int] = {}
        for teacher in teachers:
            teacher_hours[teacher.id] = 0
        
        # Copy entries from base timetable, replacing teachers/classrooms where needed
        entries: List[TimetableEntry] = []
        
        for base_entry in base_timetable.entries:
            # Only process entries for the day of week that matches the substitute date
            if base_entry.day_of_week != day_of_week:
                continue
            
            # Get subject and class for constraint checking
            subject = subjects_dict.get(base_entry.subject_id)
            class_group = classes_dict.get(base_entry.class_group_id)
            if not subject or not class_group:
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
                    base_entry, absent_teacher_id, teachers, substitute_date, entries, teacher_hours
                )
                if substitute_teacher:
                    teacher_id = substitute_teacher.id
                    teacher_hours[teacher_id] += 1
                else:
                    # No substitute found, skip this entry (admin can fix manually)
                    continue
            
            # Check subject constraints (consecutive hours, multiple in day, etc.)
            if not self._check_subject_constraints(
                subject, class_group.id, day_of_week, base_entry.lesson_index, entries
            ):
                # Skip entry if constraints violated
                continue
            
            # Find suitable classroom (check availability, capacity, specializations)
            # Always check classroom availability, even if teacher is not absent
            classroom = await self._find_suitable_classroom(
                subject, class_group, day_of_week, base_entry.lesson_index, classrooms, entries
            )
            if classroom:
                classroom_id = classroom.id
            elif base_entry.classroom_id:
                # Check if original classroom is still available
                original_classroom = next((c for c in classrooms if c.id == base_entry.classroom_id), None)
                if original_classroom:
                    # Check if classroom is free at this time
                    original_classroom_available = not any(
                        e.classroom_id == base_entry.classroom_id and 
                        e.day_of_week == day_of_week and 
                        e.lesson_index == base_entry.lesson_index 
                        for e in entries
                    )
                    if original_classroom_available:
                        # Check if classroom still fits capacity and specializations
                        class_size = class_group.number_of_students
                        capacity_ok = True
                        if class_size is not None and original_classroom.capacity is not None:
                            capacity_ok = class_size <= original_classroom.capacity
                        
                        specialization_ok = True
                        if (subject.requires_specialized_classroom or subject.is_laboratory) and original_classroom.specializations:
                            specialization_ok = subject.id in original_classroom.specializations
                        
                        if capacity_ok and specialization_ok:
                            classroom_id = base_entry.classroom_id
                        else:
                            classroom_id = None  # Classroom doesn't meet requirements
                    else:
                        classroom_id = None  # Classroom is occupied
                else:
                    classroom_id = None  # Original classroom not found
            
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
        
        # Reload with entries for return
        substitute_timetable = await self.timetable_repo.get_by_id_with_entries(substitute_timetable.id)
        
        return substitute_timetable
    
    async def get_substitute_timetable_with_lunch_hours(
        self,
        school_id: int,
        timetable_id: int
    ) -> Tuple[Timetable, Dict[int, Dict[int, List[int]]]]:
        """Get a substitute timetable with entries and calculate lunch hours"""
        from app.services.timetable_service import TimetableService
        
        timetable = await self.timetable_repo.get_by_id_with_entries(timetable_id)
        if not timetable:
            return None, {}
        
        # Use TimetableService to calculate lunch hours
        timetable_service = TimetableService(self.db)
        lunch_hours = await timetable_service.calculate_class_lunch_hours(school_id, timetable_id)
        return timetable, lunch_hours
    
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
        existing_entries: List[TimetableEntry],
        teacher_hours: Dict[int, int]
    ) -> Optional[Teacher]:
        """Find a substitute teacher for an entry, following all rules except primary teacher assignment"""
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
            
            # Check weekly hours limit
            current_hours = teacher_hours.get(teacher.id, 0)
            if current_hours >= teacher.max_weekly_hours:
                continue
            
            return teacher
        
        return None
    
    async def _find_suitable_classroom(
        self,
        subject: Subject,
        class_group: ClassGroup,
        day: int,
        lesson_index: int,
        classrooms: List[Classroom],
        placed_entries: List[TimetableEntry]
    ) -> Optional[Classroom]:
        """Find a suitable classroom, preferring ones where the class fits"""
        # Classroom is optional, so return None if no classrooms available
        if not classrooms:
            return None
        
        # Get class size for capacity checking
        class_size = class_group.number_of_students
        
        # Separate classrooms into those that fit and those that don't
        fitting_classrooms = []
        other_classrooms = []
        
        for classroom in classrooms:
            # Check if available (across ALL classes)
            if any(e.classroom_id == classroom.id and e.day_of_week == day 
                  and e.lesson_index == lesson_index for e in placed_entries):
                continue  # Skip occupied classrooms
            
            # Check if class fits (if both capacity and class_size are set)
            fits = True
            if class_size is not None and classroom.capacity is not None:
                fits = class_size <= classroom.capacity
            
            if fits:
                fitting_classrooms.append(classroom)
            else:
                other_classrooms.append(classroom)
        
        # If subject requires specialized classroom
        if subject.requires_specialized_classroom or subject.is_laboratory:
            # First try specialized classrooms that fit
            for classroom in fitting_classrooms:
                if classroom.specializations:
                    # Check if this classroom specializes in this subject (subject ID in specializations list)
                    if subject.id in classroom.specializations:
                        return classroom
            
            # Then try specialized classrooms that don't fit (as fallback)
            for classroom in other_classrooms:
                if classroom.specializations:
                    if subject.id in classroom.specializations:
                        return classroom
        
        # Prefer classrooms where class fits
        if fitting_classrooms:
            return fitting_classrooms[0]
        
        # Fallback to any available classroom
        if other_classrooms:
            return other_classrooms[0]
        
        return None
    
    def _check_subject_constraints(
        self,
        subject: Subject,
        class_group_id: int,
        day: int,
        lesson_index: int,
        placed_entries: List[TimetableEntry]
    ) -> bool:
        """Check if placing subject at this position violates constraints"""
        class_entries = [e for e in placed_entries 
                        if e.class_group_id == class_group_id and e.day_of_week == day]
        
        # Check consecutive hours
        if not subject.allow_consecutive_hours:
            if any(abs(e.lesson_index - lesson_index) == 1 and e.subject_id == subject.id 
                   for e in class_entries):
                return False
        
        # Check multiple in day
        if not subject.allow_multiple_in_one_day:
            if any(e.subject_id == subject.id for e in class_entries):
                return False
        
        # Check max consecutive hours
        if subject.max_consecutive_hours:
            # Count consecutive hours for this subject on this day
            same_day_subject_entries = sorted(
                [e for e in class_entries if e.subject_id == subject.id],
                key=lambda e: e.lesson_index
            )
            if same_day_subject_entries:
                # Check if adding this would exceed max consecutive
                # This is simplified - would need more complex logic for full validation
                pass
        
        # Check required block length (simplified)
        if subject.required_block_length:
            # This would need more complex logic to ensure blocks are placed correctly
            pass
        
        return True

