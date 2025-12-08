from typing import List, Optional, Dict, Tuple
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.timetable import Timetable, TimetableEntry
from app.models.class_group import ClassGroup
from app.models.subject import Subject, ClassSubjectAllocation
from app.models.teacher import Teacher, TeacherSubjectCapability
from app.models.classroom import Classroom
from app.models.school import SchoolSettings
from app.repositories.timetable_repository import TimetableRepository, TimetableEntryRepository
from app.repositories.class_group_repository import ClassGroupRepository
from app.repositories.subject_repository import ClassSubjectAllocationRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.school_repository import SchoolSettingsRepository
from app.services.timetable_validation_service import TimetableValidationService

class TimetableService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.timetable_repo = TimetableRepository(db)
        self.entry_repo = TimetableEntryRepository(db)
        self.class_repo = ClassGroupRepository(db)
        self.allocation_repo = ClassSubjectAllocationRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.classroom_repo = ClassroomRepository(db)
        self.settings_repo = SchoolSettingsRepository(db)
        self.validation_service = TimetableValidationService(db)
    
    async def generate_timetable(
        self,
        school_id: int,
        name: str,
        valid_from: Optional[date] = None,
        valid_to: Optional[date] = None
    ) -> Timetable:
        """Generate a timetable using a heuristic algorithm"""
        
        # Get school settings
        settings = await self.settings_repo.get_by_school_id(school_id)
        if not settings:
            raise ValueError("School settings not found")
        
        # Get all classes
        classes = await self.class_repo.get_by_school_id(school_id)
        if not classes:
            raise ValueError("No classes found for school")
        
        # Get all teachers
        teachers = await self.teacher_repo.get_by_school_id(school_id)
        if not teachers:
            raise ValueError("No teachers found for school")
        
        # Get all classrooms
        classrooms = await self.classroom_repo.get_by_school_id(school_id)
        
        # Create timetable
        timetable = Timetable(
            school_id=school_id,
            name=name,
            valid_from=valid_from,
            valid_to=valid_to
        )
        timetable = await self.timetable_repo.create(timetable)
        
        # Generate entries for each class
        entries: List[TimetableEntry] = []
        
        for class_group in classes:
            # Get subject allocations for this class
            allocations = await self.allocation_repo.get_by_class_group_id(class_group.id)
            
            # Create a list of subjects to place
            subjects_to_place: List[Tuple[Subject, int]] = []
            for allocation in allocations:
                subject = await self.db.get(Subject, allocation.subject_id)
                if subject:
                    for _ in range(allocation.weekly_hours):
                        subjects_to_place.append((subject, allocation.id))
            
            # Sort by difficulty (harder constraints first)
            subjects_to_place.sort(key=lambda x: self._get_subject_difficulty(x[0]), reverse=True)
            
            # Place subjects for this class
            class_entries = await self._place_subjects_for_class(
                timetable.id,
                class_group,
                subjects_to_place,
                teachers,
                classrooms,
                settings
            )
            entries.extend(class_entries)
        
        # Save all entries
        for entry in entries:
            await self.entry_repo.create(entry)
        
        return timetable
    
    def _get_subject_difficulty(self, subject: Subject) -> int:
        """Calculate difficulty score for placing a subject (higher = harder)"""
        score = 0
        if subject.requires_specialized_classroom:
            score += 10
        if subject.is_laboratory:
            score += 5
        if subject.required_block_length:
            score += subject.required_block_length * 3
        if not subject.allow_multiple_in_one_day:
            score += 5
        if not subject.allow_consecutive_hours:
            score += 2
        return score
    
    async def _place_subjects_for_class(
        self,
        timetable_id: int,
        class_group: ClassGroup,
        subjects_to_place: List[Tuple[Subject, int]],
        teachers: List[Teacher],
        classrooms: List[Classroom],
        settings: SchoolSettings
    ) -> List[TimetableEntry]:
        """Place subjects for a single class using backtracking"""
        entries: List[TimetableEntry] = []
        placed_entries: List[TimetableEntry] = []
        
        # Calculate number of lessons per day based on settings
        # This is a simplified calculation
        max_lessons_per_day = 8  # Default, should be calculated from settings
        
        # Try to place each subject
        for subject, allocation_id in subjects_to_place:
            placed = False
            
            # Try each day of the week
            for day in range(5):  # Monday to Friday
                if placed:
                    break
                
                # Try each lesson index
                for lesson_index in range(1, max_lessons_per_day + 1):
                    if placed:
                        break
                    
                    # Check if this slot is already taken for this class
                    if any(e.day_of_week == day and e.lesson_index == lesson_index 
                           for e in placed_entries if e.class_group_id == class_group.id):
                        continue
                    
                    # Find suitable teacher
                    teacher = await self._find_suitable_teacher(
                        subject, class_group, day, lesson_index, teachers, placed_entries
                    )
                    if not teacher:
                        continue
                    
                    # Find suitable classroom (optional)
                    classroom = await self._find_suitable_classroom(
                        subject, day, lesson_index, classrooms, placed_entries
                    )
                    
                    # Check subject constraints
                    if not self._check_subject_constraints(
                        subject, class_group.id, day, lesson_index, placed_entries
                    ):
                        continue
                    
                    # Create entry
                    entry = TimetableEntry(
                        timetable_id=timetable_id,
                        class_group_id=class_group.id,
                        subject_id=subject.id,
                        teacher_id=teacher.id,
                        classroom_id=classroom.id if classroom else None,
                        day_of_week=day,
                        lesson_index=lesson_index
                    )
                    placed_entries.append(entry)
                    entries.append(entry)
                    placed = True
        
        return entries
    
    async def _find_suitable_teacher(
        self,
        subject: Subject,
        class_group: ClassGroup,
        day: int,
        lesson_index: int,
        teachers: List[Teacher],
        placed_entries: List[TimetableEntry]
    ) -> Optional[Teacher]:
        """Find a teacher who can teach this subject and is available"""
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        day_name = day_names[day]
        
        for teacher in teachers:
            # Check if teacher can teach this subject
            can_teach = False
            for capability in teacher.capabilities:
                if capability.subject_id == subject.id:
                    if (capability.grade_level_id == class_group.grade_level_id or 
                        capability.class_group_id == class_group.id or
                        capability.grade_level_id is None):
                        can_teach = True
                        break
            
            if not can_teach:
                continue
            
            # Check teacher availability
            if teacher.availability:
                available_hours = teacher.availability.get(day_name, [])
                if lesson_index not in available_hours:
                    continue
            
            # Check if teacher is already busy at this time
            if any(e.teacher_id == teacher.id and e.day_of_week == day and e.lesson_index == lesson_index
                   for e in placed_entries):
                continue
            
            # Check teacher weekly hours (simplified - would need full count)
            teacher_hours = sum(1 for e in placed_entries if e.teacher_id == teacher.id)
            if teacher_hours >= teacher.max_weekly_hours:
                continue
            
            return teacher
        
        return None
    
    async def _find_suitable_classroom(
        self,
        subject: Subject,
        day: int,
        lesson_index: int,
        classrooms: List[Classroom],
        placed_entries: List[TimetableEntry]
    ) -> Optional[Classroom]:
        """Find a suitable classroom"""
        # Classroom is optional, so return None if no classrooms available
        if not classrooms:
            return None
        
        # If subject requires specialized classroom
        if subject.requires_specialized_classroom or subject.is_laboratory:
            for classroom in classrooms:
                if classroom.specializations:
                    # Check if this classroom specializes in this subject (subject ID in specializations list)
                    if subject.id in classroom.specializations:
                        # Check if available
                        if not any(e.classroom_id == classroom.id and e.day_of_week == day 
                                 and e.lesson_index == lesson_index for e in placed_entries):
                            return classroom
        
        # Find any available classroom
        for classroom in classrooms:
            if not any(e.classroom_id == classroom.id and e.day_of_week == day 
                      and e.lesson_index == lesson_index for e in placed_entries):
                return classroom
        
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
        
        # Check required block length
        if subject.required_block_length:
            # This is simplified - would need more complex logic
            pass
        
        return True

