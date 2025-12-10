from typing import List, Optional, Dict, Tuple
from datetime import date
import random
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
        
        # Create timetable (mark as primary)
        timetable = Timetable(
            school_id=school_id,
            name=name,
            valid_from=valid_from,
            valid_to=valid_to,
            is_primary=1  # This is a primary timetable
        )
        timetable = await self.timetable_repo.create(timetable)
        
        # Calculate max lessons per day from settings
        total_minutes = (settings.end_time.hour * 60 + settings.end_time.minute) - \
                       (settings.start_time.hour * 60 + settings.start_time.minute)
        
        # Helper function to get break duration for a specific break index
        def get_break_duration(break_index: int) -> int:
            """Get break duration after lesson (break_index + 1). break_index 0 = after lesson 1"""
            if settings.break_durations and len(settings.break_durations) > 0:
                if break_index < len(settings.break_durations):
                    return settings.break_durations[break_index]
                else:
                    # Use last value as default for remaining breaks
                    return settings.break_durations[-1]
            else:
                # Fallback to single break_duration_minutes
                return settings.break_duration_minutes
        
        # For max lessons calculation, use average break duration
        if settings.break_durations and len(settings.break_durations) > 0:
            avg_break_duration = sum(settings.break_durations) / len(settings.break_durations)
            lesson_duration = settings.class_hour_length_minutes + int(avg_break_duration)
        else:
            lesson_duration = settings.class_hour_length_minutes + settings.break_duration_minutes
        
        # Calculate lunch break in class hours (round up)
        lunch_hours_count = 0
        lunch_hour_slots = []  # Consecutive lesson indices blocked for lunch
        if settings.possible_lunch_hours and settings.lunch_duration_minutes > 0:
            # Calculate how many class hours needed (round up)
            import math
            lunch_hours_count = math.ceil(settings.lunch_duration_minutes / settings.class_hour_length_minutes)
            
            # Find consecutive hours in possible_lunch_hours that can accommodate lunch
            possible_hours = sorted(settings.possible_lunch_hours)
            for i in range(len(possible_hours) - lunch_hours_count + 1):
                # Check if we can get consecutive hours starting from this position
                consecutive = possible_hours[i:i+lunch_hours_count]
                # Check if they are consecutive (each is one more than the previous)
                is_consecutive = all(consecutive[j] == consecutive[0] + j for j in range(len(consecutive)))
                if is_consecutive:
                    lunch_hour_slots = consecutive
                    break
            
            # If no consecutive hours found, use the first N hours from possible_lunch_hours
            if not lunch_hour_slots:
                lunch_hour_slots = possible_hours[:lunch_hours_count]
        
        # Calculate available minutes (subtract lunch duration)
        lunch_duration_minutes = lunch_hours_count * settings.class_hour_length_minutes if lunch_hour_slots else 0
        available_minutes = total_minutes - lunch_duration_minutes
        max_lessons_per_day = int(available_minutes // lesson_duration)
        
        # Group subjects by class for even distribution
        class_subjects: Dict[int, List[Tuple[Subject, ClassSubjectAllocation]]] = {}  # class_id -> [(subject, allocation), ...]
        for class_group in classes:
            allocations = await self.allocation_repo.get_by_class_group_id(class_group.id)
            class_subjects[class_group.id] = []
            for allocation in allocations:
                subject = await self.db.get(Subject, allocation.subject_id)
                if subject:
                    for _ in range(allocation.weekly_hours):
                        class_subjects[class_group.id].append((subject, allocation))
            
            # Sort by difficulty (harder constraints first) for each class
            class_subjects[class_group.id].sort(key=lambda x: self._get_subject_difficulty(x[0]), reverse=True)
        
        # Generate entries for all classes together to avoid conflicts
        entries: List[TimetableEntry] = []
        
        # Place subjects for each class with even distribution
        for class_group in classes:
            if class_group.id not in class_subjects:
                continue
            
            class_entries = await self._place_subjects_for_class_evenly(
                timetable.id,
                class_group,
                class_subjects[class_group.id],
                teachers,
                classrooms,
                settings,
                max_lessons_per_day,
                entries,  # Pass all existing entries to check conflicts
                lunch_hour_slots,  # Pass lunch hour slots to block
                is_primary_timetable=True  # This is a primary timetable
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
    
    async def _place_subjects_for_class_evenly(
        self,
        timetable_id: int,
        class_group: ClassGroup,
        subjects_to_place: List[Tuple[Subject, ClassSubjectAllocation]],
        teachers: List[Teacher],
        classrooms: List[Classroom],
        settings: SchoolSettings,
        max_lessons_per_day: int,
        existing_entries: List[TimetableEntry],
        lunch_hour_slots: List[int] = None,
        is_primary_timetable: bool = True
    ) -> List[TimetableEntry]:
        """Place subjects for a class ensuring every day has at least one lesson, with even distribution"""
        entries: List[TimetableEntry] = []
        
        # Track teacher hours across all classes
        teacher_hours: Dict[int, int] = {
            t.id: sum(1 for e in existing_entries if e.teacher_id == t.id) 
            for t in teachers
        }
        
        # Track hours per day for even distribution
        hours_per_day: Dict[int, int] = {day: 0 for day in range(5)}
        
        # Get lunch break hours (block only the consecutive slots used for lunch)
        # Other possible lunch hours can still have classes
        lunch_hours = set(lunch_hour_slots or [])
        
        # Create a list of available slots (day, lesson_index) excluding lunch breaks
        available_slots = []
        for day in range(5):
            for lesson_index in range(1, max_lessons_per_day + 1):
                if lesson_index not in lunch_hours:
                    available_slots.append((day, lesson_index))
        
        # Track which teacher is assigned to each class-subject combination
        # For primary timetables, we'll only use the primary teacher for each class-subject
        class_subject_teacher: Dict[Tuple[int, int], int] = {}  # (class_group_id, subject_id) -> teacher_id
        
        # Pre-find primary teachers for all class-subject combinations (for primary timetables)
        if is_primary_timetable:
            for subject, allocation in subjects_to_place:
                if allocation.primary_teacher_id:
                    # Use the primary teacher from the allocation
                    primary_teacher = next((t for t in teachers if t.id == allocation.primary_teacher_id), None)
                    if primary_teacher:
                        class_subject_teacher[(class_group.id, subject.id)] = primary_teacher.id
        
        # First, ensure at least one lesson per day
        # Place one subject on each day first
        days_with_lessons = set()
        subjects_remaining = list(subjects_to_place)
        
        # Place one lesson on each day (Monday-Friday)
        for day in range(5):
            if not subjects_remaining:
                break
            
            # Find a subject that can be placed on this day
            for idx, (subject, allocation) in enumerate(subjects_remaining):
                placed = False
                
                # Try each lesson index for this day
                for lesson_index in range(1, max_lessons_per_day + 1):
                    if lesson_index in lunch_hours:
                        continue
                    
                    # Check if this slot is already taken for this class
                    if any(e.day_of_week == day and e.lesson_index == lesson_index 
                           and e.class_group_id == class_group.id for e in existing_entries + entries):
                        continue
                    
                    # Check if we already have a teacher assigned for this class-subject
                    class_subject_key = (class_group.id, subject.id)
                    assigned_teacher_id = class_subject_teacher.get(class_subject_key)
                    
                    # Find suitable teacher (checking availability at this specific time slot)
                    teacher = await self._find_suitable_teacher(
                        subject, class_group, day, lesson_index, teachers, existing_entries + entries, teacher_hours, is_primary_timetable, assigned_teacher_id
                    )
                    if not teacher:
                        continue
                    
                    # If we didn't have an assigned teacher yet, store it now
                    if not assigned_teacher_id:
                        class_subject_teacher[class_subject_key] = teacher.id
                    
                    # Find suitable classroom
                    classroom = await self._find_suitable_classroom(
                        subject, class_group, day, lesson_index, classrooms, existing_entries + entries
                    )
                    
                    # Check subject constraints
                    if not self._check_subject_constraints(
                        subject, class_group.id, day, lesson_index, existing_entries + entries
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
                    entries.append(entry)
                    teacher_hours[teacher.id] += 1
                    hours_per_day[day] += 1
                    days_with_lessons.add(day)
                    placed = True
                    
                    # Remove this subject from remaining list
                    subjects_remaining.pop(idx)
                    break
                
                if placed:
                    break
        
        # Now place remaining subjects with even distribution
        # Sort slots to prioritize days with fewer hours (for even distribution)
        def slot_priority(slot):
            day, lesson_index = slot
            # Prioritize days with fewer hours, but ensure all days have at least one
            if day not in days_with_lessons:
                return (-1, day, lesson_index)  # Days without lessons get highest priority
            return (hours_per_day[day], day, lesson_index)
        
        # Place remaining subjects
        for subject, allocation in subjects_remaining:
            placed = False
            
            # Sort available slots by priority (days with fewer hours first)
            available_slots_sorted = sorted(available_slots, key=slot_priority)
            
            for day, lesson_index in available_slots_sorted:
                if placed:
                    break
                
                # Check if this slot is already taken for this class
                if any(e.day_of_week == day and e.lesson_index == lesson_index 
                       and e.class_group_id == class_group.id for e in existing_entries + entries):
                    continue
                
                # Check if we already have a teacher assigned for this class-subject
                class_subject_key = (class_group.id, subject.id)
                assigned_teacher_id = class_subject_teacher.get(class_subject_key)
                
                # Find suitable teacher (checking availability at this specific time slot)
                teacher = await self._find_suitable_teacher(
                    subject, class_group, day, lesson_index, teachers, existing_entries + entries, teacher_hours, is_primary_timetable, assigned_teacher_id
                )
                if not teacher:
                    continue
                
                # If we didn't have an assigned teacher yet, store it now
                if not assigned_teacher_id:
                    class_subject_teacher[class_subject_key] = teacher.id
                
                # Find suitable classroom
                classroom = await self._find_suitable_classroom(
                    subject, class_group, day, lesson_index, classrooms, existing_entries + entries
                )
                
                # Check subject constraints
                if not self._check_subject_constraints(
                    subject, class_group.id, day, lesson_index, existing_entries + entries
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
                entries.append(entry)
                teacher_hours[teacher.id] += 1
                hours_per_day[day] += 1
                days_with_lessons.add(day)
                placed = True
        
        return entries
    
    async def _find_primary_teacher_for_class_subject(
        self,
        subject: Subject,
        class_group: ClassGroup,
        teachers: List[Teacher],
        allocation: Optional[ClassSubjectAllocation] = None
    ) -> Optional[Teacher]:
        """Find the primary teacher for a class-subject combination (without checking availability)
        Now uses primary_teacher_id from ClassSubjectAllocation if available"""
        if allocation and allocation.primary_teacher_id:
            return next((t for t in teachers if t.id == allocation.primary_teacher_id), None)
        # Fallback to old method if allocation doesn't have primary_teacher_id
        for teacher in teachers:
            for capability in teacher.capabilities:
                if capability.subject_id == subject.id:
                    # Check if this is the primary teacher for this specific class-subject
                    if capability.is_primary == 1 and capability.class_group_id == class_group.id:
                        return teacher
        return None
    
    async def _find_suitable_teacher(
        self,
        subject: Subject,
        class_group: ClassGroup,
        day: int,
        lesson_index: int,
        teachers: List[Teacher],
        placed_entries: List[TimetableEntry],
        teacher_hours: Dict[int, int],
        is_primary_timetable: bool = True,
        assigned_teacher_id: Optional[int] = None
    ) -> Optional[Teacher]:
        """Find a teacher who can teach this subject and is available at this specific time slot.
        For primary timetables, if assigned_teacher_id is provided, only checks that teacher.
        For substitute timetables, can return any suitable teacher."""
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        day_name = day_names[day]
        
        # If we have an assigned teacher (for primary timetables), only check that teacher
        if assigned_teacher_id is not None:
            teacher = next((t for t in teachers if t.id == assigned_teacher_id), None)
            if not teacher:
                return None
            
            # Check teacher availability
            if teacher.availability:
                available_hours = teacher.availability.get(day_name, [])
                if available_hours and lesson_index not in available_hours:
                    return None
            
            # Check if teacher is already busy at this time (across ALL classes)
            if any(e.teacher_id == teacher.id and e.day_of_week == day and e.lesson_index == lesson_index
                   for e in placed_entries):
                return None
            
            # Check teacher weekly hours
            if teacher_hours.get(teacher.id, 0) >= teacher.max_weekly_hours:
                return None
            
            return teacher
        
        # For primary timetables without assigned teacher, this shouldn't happen
        # because we pre-find primary teachers. But if it does, return None
        # (we don't want to fall back to TeacherSubjectCapability anymore)
        if is_primary_timetable:
            return None
            
            # Check if primary teacher is available at this time
            if primary_teacher.availability:
                available_hours = primary_teacher.availability.get(day_name, [])
                if available_hours and lesson_index not in available_hours:
                    return None
            
            # Check if teacher is already busy at this time
            if any(e.teacher_id == primary_teacher.id and e.day_of_week == day and e.lesson_index == lesson_index
                   for e in placed_entries):
                return None
            
            # Check teacher weekly hours
            if teacher_hours.get(primary_teacher.id, 0) >= primary_teacher.max_weekly_hours:
                return None
            
            return primary_teacher
        
        # For substitute timetables, find any suitable teacher
        primary_teacher = None
        other_teachers = []
        
        for teacher in teachers:
            # Check if teacher can teach this subject
            can_teach = False
            is_primary = False
            for capability in teacher.capabilities:
                if capability.subject_id == subject.id:
                    # Check if this capability matches the class
                    matches_class = (
                        capability.class_group_id == class_group.id or
                        (capability.grade_level_id == class_group.grade_level_id and capability.class_group_id is None) or
                        (capability.grade_level_id is None and capability.class_group_id is None)
                    )
                    if matches_class:
                        can_teach = True
                        # Check if this is the primary teacher for this class-subject
                        if capability.is_primary == 1 and capability.class_group_id == class_group.id:
                            is_primary = True
                        break
            
            if not can_teach:
                continue
            
            # Check teacher availability
            if teacher.availability:
                available_hours = teacher.availability.get(day_name, [])
                if available_hours and lesson_index not in available_hours:
                    continue
            
            # Check if teacher is already busy at this time (across ALL classes)
            if any(e.teacher_id == teacher.id and e.day_of_week == day and e.lesson_index == lesson_index
                   for e in placed_entries):
                continue
            
            # Check teacher weekly hours
            if teacher_hours.get(teacher.id, 0) >= teacher.max_weekly_hours:
                continue
            
            if is_primary:
                primary_teacher = teacher
            else:
                other_teachers.append(teacher)
        
        # For substitute timetables, return primary teacher if found, otherwise any suitable teacher
        if primary_teacher:
            return primary_teacher
        
        # If no primary teacher, return first available teacher (shuffle for load balancing)
        if other_teachers:
            random.shuffle(other_teachers)
            return other_teachers[0]
        
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

