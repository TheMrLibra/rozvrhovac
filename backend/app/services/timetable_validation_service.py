from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.timetable import TimetableEntry
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.class_group import ClassGroup
from app.models.school import SchoolSettings
from app.repositories.timetable_repository import TimetableEntryRepository
from app.repositories.school_repository import SchoolSettingsRepository

class ValidationError:
    def __init__(self, type: str, message: str, entry_id: int = None):
        self.type = type
        self.message = message
        self.entry_id = entry_id

class TimetableValidationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.entry_repo = TimetableEntryRepository(db)
        self.settings_repo = SchoolSettingsRepository(db)
    
    async def validate_timetable(self, timetable_id: int) -> List[ValidationError]:
        """Validate all constraints for a timetable"""
        errors: List[ValidationError] = []
        entries = await self.entry_repo.get_by_timetable_id(timetable_id)
        
        if not entries:
            return errors
        
        # Get school_id from timetable directly
        from sqlalchemy import select
        from app.models.timetable import Timetable
        result = await self.db.execute(select(Timetable).where(Timetable.id == timetable_id))
        timetable = result.scalar_one_or_none()
        if not timetable:
            return errors
        
        school_id = timetable.school_id
        settings = await self.settings_repo.get_by_school_id(school_id)
        
        # Group entries by various dimensions for validation
        teacher_entries: Dict[int, List[TimetableEntry]] = {}
        class_entries: Dict[int, List[TimetableEntry]] = {}
        classroom_entries: Dict[int, List[TimetableEntry]] = {}
        teacher_hours: Dict[int, int] = {}
        class_subject_hours: Dict[tuple, int] = {}  # (class_id, subject_id) -> hours
        
        for entry in entries:
            # Group by teacher
            if entry.teacher_id not in teacher_entries:
                teacher_entries[entry.teacher_id] = []
            teacher_entries[entry.teacher_id].append(entry)
            
            # Group by class
            if entry.class_group_id not in class_entries:
                class_entries[entry.class_group_id] = []
            class_entries[entry.class_group_id].append(entry)
            
            # Group by classroom
            if entry.classroom_id:
                if entry.classroom_id not in classroom_entries:
                    classroom_entries[entry.classroom_id] = []
                classroom_entries[entry.classroom_id].append(entry)
            
            # Count teacher hours
            teacher_hours[entry.teacher_id] = teacher_hours.get(entry.teacher_id, 0) + 1
            
            # Count class-subject hours
            key = (entry.class_group_id, entry.subject_id)
            class_subject_hours[key] = class_subject_hours.get(key, 0) + 1
        
        # Validate: No teacher has two lessons simultaneously
        for teacher_id, teacher_entries_list in teacher_entries.items():
            for i, entry1 in enumerate(teacher_entries_list):
                for entry2 in teacher_entries_list[i+1:]:
                    if (entry1.day_of_week == entry2.day_of_week and 
                        entry1.lesson_index == entry2.lesson_index):
                        errors.append(ValidationError(
                            "teacher_conflict",
                            f"Teacher {entry1.teacher.full_name} has two lessons at the same time",
                            entry1.id
                        ))
        
        # Validate: No class has two lessons simultaneously
        for class_id, class_entries_list in class_entries.items():
            for i, entry1 in enumerate(class_entries_list):
                for entry2 in class_entries_list[i+1:]:
                    if (entry1.day_of_week == entry2.day_of_week and 
                        entry1.lesson_index == entry2.lesson_index):
                        errors.append(ValidationError(
                            "class_conflict",
                            f"Class {entry1.class_group.name} has two lessons at the same time",
                            entry1.id
                        ))
        
        # Validate: No classroom has two lessons simultaneously
        for classroom_id, classroom_entries_list in classroom_entries.items():
            for i, entry1 in enumerate(classroom_entries_list):
                for entry2 in classroom_entries_list[i+1:]:
                    if (entry1.day_of_week == entry2.day_of_week and 
                        entry1.lesson_index == entry2.lesson_index):
                        errors.append(ValidationError(
                            "classroom_conflict",
                            f"Classroom {entry1.classroom.name} has two lessons at the same time",
                            entry1.id
                        ))
        
        # Validate: Teacher max weekly hours
        for teacher_id, hours in teacher_hours.items():
            from sqlalchemy import select
            result = await self.db.execute(select(Teacher).where(Teacher.id == teacher_id))
            teacher = result.scalar_one_or_none()
            if teacher and hours > teacher.max_weekly_hours:
                errors.append(ValidationError(
                    "teacher_hours_exceeded",
                    f"Teacher {teacher.full_name} exceeds max weekly hours ({hours} > {teacher.max_weekly_hours})"
                ))
        
        # Validate: ClassSubjectAllocation weekly hours fulfilled
        # This would need to check against ClassSubjectAllocation records
        # For now, we'll skip this as it requires loading allocations
        
        # Validate: Subject constraints (consecutive hours, multiple in day, etc.)
        for entry in entries:
            from sqlalchemy import select
            result = await self.db.execute(select(Subject).where(Subject.id == entry.subject_id))
            subject = result.scalar_one_or_none()
            if subject:
                # Check consecutive hours
                if not subject.allow_consecutive_hours:
                    # Check if this entry is consecutive with another
                    same_day_entries = [e for e in entries 
                                      if e.class_group_id == entry.class_group_id 
                                      and e.day_of_week == entry.day_of_week
                                      and e.subject_id == entry.subject_id
                                      and abs(e.lesson_index - entry.lesson_index) == 1]
                    if same_day_entries:
                        errors.append(ValidationError(
                            "consecutive_hours_violation",
                            f"Subject {subject.name} does not allow consecutive hours",
                            entry.id
                        ))
                
                # Check max consecutive hours
                if subject.max_consecutive_hours:
                    # Count consecutive hours for this subject on this day
                    same_day_subject_entries = sorted(
                        [e for e in entries 
                         if e.class_group_id == entry.class_group_id 
                         and e.day_of_week == entry.day_of_week
                         and e.subject_id == entry.subject_id],
                        key=lambda e: e.lesson_index
                    )
                    max_consecutive = 1
                    current_consecutive = 1
                    for i in range(1, len(same_day_subject_entries)):
                        if same_day_subject_entries[i].lesson_index == same_day_subject_entries[i-1].lesson_index + 1:
                            current_consecutive += 1
                            max_consecutive = max(max_consecutive, current_consecutive)
                        else:
                            current_consecutive = 1
                    
                    if max_consecutive > subject.max_consecutive_hours:
                        errors.append(ValidationError(
                            "max_consecutive_hours_violation",
                            f"Subject {subject.name} exceeds max consecutive hours ({max_consecutive} > {subject.max_consecutive_hours})"
                        ))
                
                # Check allow_multiple_in_one_day
                if not subject.allow_multiple_in_one_day:
                    same_day_count = len([e for e in entries 
                                         if e.class_group_id == entry.class_group_id 
                                         and e.day_of_week == entry.day_of_week
                                         and e.subject_id == entry.subject_id])
                    if same_day_count > 1:
                        errors.append(ValidationError(
                            "multiple_in_day_violation",
                            f"Subject {subject.name} cannot occur multiple times in one day",
                            entry.id
                        ))
        
        return errors

