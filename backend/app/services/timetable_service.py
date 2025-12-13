from typing import List, Optional, Dict, Tuple
from datetime import date
import random
import math
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
        possible_hours = []
        if settings.possible_lunch_hours and settings.lunch_duration_minutes > 0:
            # Calculate how many class hours needed (round up)
            import math
            lunch_hours_count = math.ceil(settings.lunch_duration_minutes / settings.class_hour_length_minutes)
            possible_hours = sorted(settings.possible_lunch_hours)
        
        # Calculate available minutes (subtract lunch duration)
        # We'll calculate this per class since each class has its own lunch hour
        lunch_duration_minutes = lunch_hours_count * settings.class_hour_length_minutes if possible_hours else 0
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
        
        # Assign lunch hours to classes per day
        # Structure: class_lunch_hours[class_id][day] = list of lunch hour lesson indices
        # IMPORTANT: Never assign lunch to lesson_index 1 (first lesson must be at school start time)
        # Lunch can be assigned to any possible lunch hour (no even distribution requirement)
        class_lunch_hours: Dict[int, Dict[int, List[int]]] = {}  # class_id -> {day: [lunch_hours]}
        if settings.possible_lunch_hours and len(settings.possible_lunch_hours) > 0:
            possible_hours = sorted(settings.possible_lunch_hours)
            # Filter out lesson_index 1 from possible lunch hours (first lesson must be at school start)
            possible_hours_filtered = [h for h in possible_hours if h > 1]
            if not possible_hours_filtered:
                # If all possible hours are 1 or less, use original list but warn
                possible_hours_filtered = possible_hours
            
            # For each class, assign lunch hours per day
            for idx, class_group in enumerate(classes):
                class_lunch_hours[class_group.id] = {}
                
                # For each day (0-4 = Monday-Friday), assign a lunch hour
                for day in range(5):
                    # Simply pick from possible hours (no even distribution requirement)
                    # Use class index and day for some variation
                    assigned_lunch_hour = possible_hours_filtered[(idx + day) % len(possible_hours_filtered)] if possible_hours_filtered else possible_hours[0] if possible_hours else None
                    
                    if not assigned_lunch_hour:
                        continue
                    
                    # Calculate consecutive lunch slots starting from assigned lunch hour
                    # Ensure none of the slots are lesson_index 1
                    class_lunch_slots = []
                    for hour_offset in range(lunch_hours_count):
                        check_hour = assigned_lunch_hour + hour_offset
                        if check_hour in possible_hours and check_hour != 1:
                            class_lunch_slots.append(check_hour)
                        elif check_hour == 1:
                            # Skip lesson_index 1 - can't have lunch at first lesson
                            break
                    
                    # If we couldn't get enough consecutive hours, just use the assigned hour (if not 1)
                    if len(class_lunch_slots) < lunch_hours_count:
                        if assigned_lunch_hour != 1:
                            class_lunch_slots = [assigned_lunch_hour]
                        else:
                            # If assigned hour is 1, use next available hour
                            next_hour = next((h for h in possible_hours_filtered if h > 1), None)
                            if next_hour:
                                class_lunch_slots = [next_hour]
                            else:
                                class_lunch_slots = []
                    
                    class_lunch_hours[class_group.id][day] = class_lunch_slots
        
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
                class_lunch_hours.get(class_group.id, {}),  # Pass lunch hours per day for this class
                is_primary_timetable=True,  # This is a primary timetable
                lunch_hours_count=lunch_hours_count  # Pass lunch hours count for adjustment
            )
            entries.extend(class_entries)
        
        # After all lessons are placed, adjust lunch breaks for all classes
        # Check each day for each class: if there are no lessons after lunch, and there's a gap,
        # move lunch directly after the last lesson
        for class_group in classes:
            if class_group.id not in class_subjects:
                continue
            
            # Get all entries for this class
            class_entries = [e for e in entries if e.class_group_id == class_group.id]
            
            for day in range(5):
                day_class_entries = [e for e in class_entries if e.day_of_week == day]
                if not day_class_entries:
                    continue
                
                # Get the last lesson index for this day and class
                last_lesson_index = max(e.lesson_index for e in day_class_entries)
                
                # Get lunch hours for this day
                lunch_slots = class_lunch_hours.get(class_group.id, {}).get(day, [])
                if not lunch_slots:
                    continue
                
                lunch_start = min(lunch_slots)
                lunch_end = max(lunch_slots)
                
                # Check if there are any teaching hours (lessons) after the lunch break
                lessons_after_lunch = [e for e in day_class_entries if e.lesson_index > lunch_end]
                
                # If there are no lessons after lunch, check if there's a gap between last lesson and lunch
                if not lessons_after_lunch:
                    # Check if there's a gap (lunch starts after the last lesson)
                    if lunch_start > last_lesson_index:
                        # There's a gap - move lunch to be directly after the last lesson
                        new_lunch_start = last_lesson_index + 1
                        new_lunch_slots = []
                        for i in range(lunch_hours_count):
                            new_lunch_slots.append(new_lunch_start + i)
                        
                        # Update the lunch hours for this day
                        class_lunch_hours[class_group.id][day] = new_lunch_slots
        
        # Save all entries
        for entry in entries:
            await self.entry_repo.create(entry)
        
        # Reload timetable with entries for return
        timetable = await self.timetable_repo.get_by_id_with_entries(timetable.id)
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
        lunch_hours_per_day: Dict[int, List[int]] = None,  # day -> list of lunch hour lesson indices
        is_primary_timetable: bool = True,
        lunch_hours_count: int = 0  # Number of consecutive hours needed for lunch
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
        
        # Get lunch break hours per day (block only the consecutive slots used for lunch on each day)
        lunch_hours_per_day_dict = lunch_hours_per_day or {}
        
        # Create a list of available slots (day, lesson_index) excluding lunch breaks
        # Lunch breaks vary by day for each class
        available_slots = []
        for day in range(5):
            lunch_hours_for_day_set = set(lunch_hours_per_day_dict.get(day, []))
            for lesson_index in range(1, max_lessons_per_day + 1):
                if lesson_index not in lunch_hours_for_day_set:
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
        # CRITICAL: First lesson of each day MUST be at lesson_index 1 (school start time)
        for day in range(5):
            if not subjects_remaining:
                break
            
            # Get lunch hours for this day
            lunch_hours_for_day_set = set(lunch_hours_per_day_dict.get(day, []))
            
            # Get existing lesson indices for this day to try placing adjacent
            day_entries = [e for e in entries if e.day_of_week == day]
            day_lesson_indices = {e.lesson_index for e in day_entries}
            
            # If this is the first lesson for this day, MUST place at lesson_index 1
            # Try ALL subjects until we find one that can be placed at lesson_index 1
            if not day_lesson_indices:
                lesson_index = 1
                # lesson_index 1 should never be a lunch break, but check anyway
                if lesson_index not in lunch_hours_for_day_set:
                    # Try each subject until we find one that can be placed at lesson_index 1
                    for idx, (subject, allocation) in enumerate(subjects_remaining):
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
                        if teacher:
                            # If we didn't have an assigned teacher yet, store it now
                            if not assigned_teacher_id:
                                class_subject_teacher[class_subject_key] = teacher.id
                            
                            # Find suitable classroom
                            classroom = await self._find_suitable_classroom(
                                subject, class_group, day, lesson_index, classrooms, existing_entries + entries
                            )
                            
                            # Check subject constraints
                            if self._check_subject_constraints(
                                subject, class_group.id, day, lesson_index, existing_entries + entries, allocation
                            ):
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
                                subjects_remaining.pop(idx)
                                break  # Move to next day
            
            # Find a subject that can be placed on this day (for remaining subjects)
            for idx, (subject, allocation) in enumerate(subjects_remaining):
                placed = False
                
                # If first lesson wasn't placed at index 1, try other slots (but still prioritize lesson_index 1)
                candidate_slots = []
                for lesson_index in range(1, max_lessons_per_day + 1):
                    if lesson_index in lunch_hours_for_day_set:
                        continue
                    if any(e.day_of_week == day and e.lesson_index == lesson_index 
                           and e.class_group_id == class_group.id for e in existing_entries + entries):
                        continue
                    
                    # Prioritize lesson_index 1 for first lesson of day
                    is_first = (lesson_index == 1) if not day_lesson_indices else False
                    # Prioritize slots adjacent to existing lessons
                    is_adjacent = False
                    if day_lesson_indices:
                        if (lesson_index - 1 in day_lesson_indices) or (lesson_index + 1 in day_lesson_indices):
                            is_adjacent = True
                    
                    candidate_slots.append((is_first, is_adjacent, lesson_index))
                
                # Sort: first lesson (index 1) first, then adjacent slots, then by lesson index
                candidate_slots.sort(key=lambda x: (not x[0], not x[1], x[2]))
                
                # Try each candidate slot
                for is_first, is_adjacent, lesson_index in candidate_slots:
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
                        subject, class_group.id, day, lesson_index, existing_entries + entries, allocation
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
        
        # Now place remaining subjects with even distribution and minimal gaps
        # Sort slots to prioritize:
        # 1. Days with fewer hours (for even distribution)
        # 2. Slots adjacent to existing lessons (to minimize gaps)
        def slot_priority(slot):
            day, lesson_index = slot
            # Get existing lesson indices for this day and class
            day_entries = [e for e in entries if e.day_of_week == day]
            day_lesson_indices = {e.lesson_index for e in day_entries}
            
            # Check if this slot is adjacent to an existing lesson (minimize gaps)
            is_adjacent = False
            if day_lesson_indices:
                # Check if adjacent to any existing lesson (before or after)
                if (lesson_index - 1 in day_lesson_indices) or (lesson_index + 1 in day_lesson_indices):
                    is_adjacent = True
            
            # Prioritize days without lessons first, then adjacent slots, then by hours per day
            if day not in days_with_lessons:
                return (-1, 0, day, lesson_index)  # Days without lessons get highest priority
            # Prioritize adjacent slots (to minimize gaps), then by hours per day
            return (0 if is_adjacent else 1, hours_per_day[day], day, lesson_index)
        
        # Place remaining subjects
        # Track how many hours have been placed for each subject
        subject_hours_placed: Dict[Tuple[int, int], int] = {}  # (class_group_id, subject_id) -> hours placed
        
        for subject, allocation in subjects_remaining:
            class_subject_key = (class_group.id, subject.id)
            hours_placed = subject_hours_placed.get(class_subject_key, 0)
            hours_to_place = allocation.weekly_hours if allocation else 1
            hours_remaining = hours_to_place - hours_placed
            
            if hours_remaining <= 0:
                continue  # All hours for this subject are already placed
            
            placed = False
            
            # Check if this subject requires consecutive hours
            required_consecutive = allocation.required_consecutive_hours if allocation else None
            
            # If required_consecutive_hours is set, try to place consecutive blocks first
            if required_consecutive and required_consecutive > 1 and hours_remaining >= required_consecutive:
                # Try to place consecutive blocks
                blocks_placed = 0
                while hours_remaining >= required_consecutive and blocks_placed < 10:  # Limit iterations
                    block_placed = await self._place_consecutive_block(
                        timetable_id, class_group, subject, allocation, teachers, classrooms,
                        required_consecutive, existing_entries, entries, lunch_hours_per_day_dict,
                        max_lessons_per_day, teacher_hours, class_subject_teacher,
                        hours_per_day, days_with_lessons, is_primary_timetable
                    )
                    if block_placed:
                        hours_remaining -= required_consecutive
                        hours_placed += required_consecutive
                        subject_hours_placed[class_subject_key] = hours_placed
                        blocks_placed += 1
                    else:
                        # If we can't place a consecutive block, break and try individual placement
                        break
                
                if hours_remaining == 0:
                    placed = True
                    continue
            
            # If not placed yet (no consecutive requirement or consecutive placement failed), place individually
            if not placed:
                # Sort available slots by priority (adjacent slots first, then by hours per day)
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
                        subject, class_group.id, day, lesson_index, existing_entries + entries, allocation
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
    
    async def _place_consecutive_block(
        self,
        timetable_id: int,
        class_group: ClassGroup,
        subject: Subject,
        allocation: ClassSubjectAllocation,
        teachers: List[Teacher],
        classrooms: List[Classroom],
        block_size: int,
        existing_entries: List[TimetableEntry],
        entries: List[TimetableEntry],
        lunch_hours_per_day: Dict[int, List[int]],
        max_lessons_per_day: int,
        teacher_hours: Dict[int, int],
        class_subject_teacher: Dict[Tuple[int, int], int],
        hours_per_day: Dict[int, int],
        days_with_lessons: set,
        is_primary_timetable: bool
    ) -> bool:
        """Place a consecutive block of lessons for a subject. Returns True if successful."""
        # Get lunch hours per day
        lunch_hours_per_day_dict = lunch_hours_per_day or {}
        
        # Try each day
        for day in range(5):
            lunch_hours_for_day_set = set(lunch_hours_per_day_dict.get(day, []))
            
            # Try each starting lesson index
            for start_index in range(1, max_lessons_per_day + 1 - block_size + 1):
                # Check if all consecutive slots are available
                consecutive_slots = list(range(start_index, start_index + block_size))
                
                # Check if any slot is a lunch break or already taken
                if any(slot in lunch_hours_for_day_set for slot in consecutive_slots):
                    continue
                if any(e.day_of_week == day and e.lesson_index in consecutive_slots 
                       and e.class_group_id == class_group.id for e in existing_entries + entries):
                    continue
                
                # Check if we already have a teacher assigned for this class-subject
                class_subject_key = (class_group.id, subject.id)
                assigned_teacher_id = class_subject_teacher.get(class_subject_key)
                
                # Check if teacher is available for all slots
                teacher = None
                for slot_index in consecutive_slots:
                    candidate_teacher = await self._find_suitable_teacher(
                        subject, class_group, day, slot_index, teachers, existing_entries + entries, 
                        teacher_hours, is_primary_timetable, assigned_teacher_id
                    )
                    if not candidate_teacher:
                        break
                    if teacher is None:
                        teacher = candidate_teacher
                    elif teacher.id != candidate_teacher.id:
                        # Teacher must be the same for all slots
                        break
                else:
                    # All slots have the same teacher available
                    if teacher:
                        # If we didn't have an assigned teacher yet, store it now
                        if not assigned_teacher_id:
                            class_subject_teacher[class_subject_key] = teacher.id
                        
                        # Check subject constraints for the first slot
                        if not self._check_subject_constraints(
                            subject, class_group.id, day, start_index, existing_entries + entries, allocation
                        ):
                            continue
                        
                        # Place all consecutive entries
                        for slot_index in consecutive_slots:
                            classroom = await self._find_suitable_classroom(
                                subject, class_group, day, slot_index, classrooms, existing_entries + entries
                            )
                            entry = TimetableEntry(
                                timetable_id=timetable_id,
                                class_group_id=class_group.id,
                                subject_id=subject.id,
                                teacher_id=teacher.id,
                                classroom_id=classroom.id if classroom else None,
                                day_of_week=day,
                                lesson_index=slot_index
                            )
                            entries.append(entry)
                            teacher_hours[teacher.id] += 1
                            hours_per_day[day] += 1
                            days_with_lessons.add(day)
                        
                        return True
        
        return False
    
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
        placed_entries: List[TimetableEntry],
        allocation: Optional[ClassSubjectAllocation] = None
    ) -> bool:
        """Check if placing subject at this position violates constraints"""
        class_entries = [e for e in placed_entries 
                        if e.class_group_id == class_group_id and e.day_of_week == day]
        
        # Check consecutive hours
        if not subject.allow_consecutive_hours:
            if any(abs(e.lesson_index - lesson_index) == 1 and e.subject_id == subject.id 
                   for e in class_entries):
                return False
        
        # Check multiple in day - use allocation setting if available, otherwise use subject setting
        allow_multiple = subject.allow_multiple_in_one_day
        if allocation and allocation.allow_multiple_in_one_day is not None:
            allow_multiple = allocation.allow_multiple_in_one_day
        
        if not allow_multiple:
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
    
    async def calculate_class_lunch_hours(
        self,
        school_id: int,
        timetable_id: int
    ) -> Dict[int, Dict[int, List[int]]]:
        """Calculate lunch hours for each class per day in a timetable, matching the generation logic
        and applying adjustments: if there are no lessons after lunch and there's a gap, move lunch after last lesson"""
        
        settings = await self.settings_repo.get_by_school_id(school_id)
        if not settings or not settings.possible_lunch_hours or settings.lunch_duration_minutes <= 0:
            return {}
        
        classes = await self.class_repo.get_by_school_id(school_id)
        if not classes:
            return {}
        
        # Get all entries for this timetable
        entries = await self.entry_repo.get_by_timetable_id(timetable_id)
        
        # Calculate lunch hours count
        lunch_hours_count = math.ceil(settings.lunch_duration_minutes / settings.class_hour_length_minutes)
        possible_hours = sorted(settings.possible_lunch_hours)
        
        # Distribute classes evenly across possible lunch hours per day (same logic as generation)
        # Structure: class_lunch_hours[class_id][day] = list of lunch hour lesson indices
        class_lunch_hours: Dict[int, Dict[int, List[int]]] = {}
        sorted_classes = sorted(classes, key=lambda c: c.id)
        
        for idx, class_group in enumerate(sorted_classes):
            class_lunch_hours[class_group.id] = {}
            # Filter out lesson_index 1 from possible lunch hours (first lesson must be at school start)
            possible_hours_filtered = [h for h in possible_hours if h > 1]
            if not possible_hours_filtered:
                possible_hours_filtered = possible_hours
            
            # For each day (0-4 = Monday-Friday), assign a lunch hour
            # Simply pick from possible hours (no even distribution requirement)
            for day in range(5):
                # Simply pick from possible hours
                assigned_lunch_hour = possible_hours_filtered[(idx + day) % len(possible_hours_filtered)] if possible_hours_filtered else possible_hours[0] if possible_hours else None
                
                if not assigned_lunch_hour:
                    continue
                
                # Calculate consecutive lunch slots starting from assigned lunch hour
                # Ensure none of the slots are lesson_index 1
                class_lunch_slots: List[int] = []
                for hour_offset in range(lunch_hours_count):
                    check_hour = assigned_lunch_hour + hour_offset
                    if check_hour in possible_hours and check_hour != 1:
                        class_lunch_slots.append(check_hour)
                    elif check_hour == 1:
                        # Skip lesson_index 1 - can't have lunch at first lesson
                        break
                
                # If we couldn't get enough consecutive hours, just use the assigned hour (if not 1)
                if len(class_lunch_slots) < lunch_hours_count:
                    if assigned_lunch_hour != 1:
                        class_lunch_slots = [assigned_lunch_hour]
                    else:
                        # If assigned hour is 1, use next available hour
                        next_hour = next((h for h in possible_hours_filtered if h > 1), None)
                        if next_hour:
                            class_lunch_slots = [next_hour]
                        else:
                            class_lunch_slots = []
                
                class_lunch_hours[class_group.id][day] = class_lunch_slots
        
        # After calculating initial lunch hours, apply adjustments based on actual entries
        # Check each day for each class: if there are no lessons after lunch and there's a gap,
        # move lunch directly after the last lesson
        for class_group in sorted_classes:
            # Get all entries for this class
            class_entries = [e for e in entries if e.class_group_id == class_group.id]
            
            for day in range(5):
                day_class_entries = [e for e in class_entries if e.day_of_week == day]
                if not day_class_entries:
                    continue
                
                # Get the last lesson index for this day and class
                last_lesson_index = max(e.lesson_index for e in day_class_entries)
                
                # Get lunch hours for this day
                lunch_slots = class_lunch_hours.get(class_group.id, {}).get(day, [])
                if not lunch_slots:
                    continue
                
                lunch_start = min(lunch_slots)
                lunch_end = max(lunch_slots)
                
                # Check if there are any teaching hours (lessons) after the lunch break
                lessons_after_lunch = [e for e in day_class_entries if e.lesson_index > lunch_end]
                
                # If there are no lessons after lunch, check if there's a gap between last lesson and lunch
                if not lessons_after_lunch:
                    # Check if there's a gap (lunch starts after the last lesson)
                    if lunch_start > last_lesson_index:
                        # There's a gap - move lunch to be directly after the last lesson
                        new_lunch_start = last_lesson_index + 1
                        new_lunch_slots = []
                        for i in range(lunch_hours_count):
                            new_lunch_slots.append(new_lunch_start + i)
                        
                        # Update the lunch hours for this day
                        class_lunch_hours[class_group.id][day] = new_lunch_slots
        
        return class_lunch_hours
    
    async def get_timetable_with_lunch_hours(
        self,
        school_id: int,
        timetable_id: int
    ) -> Tuple[Timetable, Dict[int, Dict[int, List[int]]]]:
        """Get a timetable with entries and calculate lunch hours"""
        timetable = await self.timetable_repo.get_by_id_with_entries(timetable_id)
        if not timetable:
            return None, {}
        
        lunch_hours = await self.calculate_class_lunch_hours(school_id, timetable_id)
        return timetable, lunch_hours
    
    async def delete_timetable(
        self,
        school_id: int,
        timetable_id: int
    ) -> bool:
        """Delete a timetable and all its entries, including substitute timetables"""
        from sqlalchemy import select
        from app.models.timetable import Timetable
        
        # Verify timetable exists and belongs to school
        timetable = await self.timetable_repo.get_by_id(timetable_id)
        if not timetable:
            raise ValueError("Timetable not found")
        if timetable.school_id != school_id:
            raise ValueError("Timetable does not belong to this school")
        
        try:
            # First, find and delete all substitute timetables that reference this timetable as their base
            substitute_result = await self.db.execute(
                select(Timetable).where(Timetable.base_timetable_id == timetable_id)
            )
            substitute_timetables = substitute_result.scalars().all()
            
            # Delete entries and timetables for each substitute timetable
            for substitute_timetable in substitute_timetables:
                # Delete substitutions that reference entries in this substitute timetable
                from app.models.absence import Substitution
                substitute_entries_result = await self.db.execute(
                    select(TimetableEntry).where(TimetableEntry.timetable_id == substitute_timetable.id)
                )
                substitute_entries = substitute_entries_result.scalars().all()
                
                # Delete substitutions for each entry
                for entry in substitute_entries:
                    substitutions_result = await self.db.execute(
                        select(Substitution).where(Substitution.timetable_entry_id == entry.id)
                    )
                    substitutions = substitutions_result.scalars().all()
                    for substitution in substitutions:
                        from app.repositories.absence_repository import SubstitutionRepository
                        sub_repo = SubstitutionRepository(self.db)
                        await sub_repo.delete(substitution.id)
                    
                    await self.entry_repo.delete(entry.id)
                
                # Delete the substitute timetable
                await self.timetable_repo.delete(substitute_timetable.id)
            
            # Delete all timetable entries for the base timetable
            result = await self.db.execute(
                select(TimetableEntry).where(TimetableEntry.timetable_id == timetable_id)
            )
            entries = result.scalars().all()
            
            # Delete substitutions for each entry
            from app.models.absence import Substitution
            for entry in entries:
                substitutions_result = await self.db.execute(
                    select(Substitution).where(Substitution.timetable_entry_id == entry.id)
                )
                substitutions = substitutions_result.scalars().all()
                for substitution in substitutions:
                    from app.repositories.absence_repository import SubstitutionRepository
                    sub_repo = SubstitutionRepository(self.db)
                    await sub_repo.delete(substitution.id)
                
                await self.entry_repo.delete(entry.id)
            
            # Now delete the base timetable
            await self.timetable_repo.delete(timetable_id)
            
            # Commit the transaction
            await self.db.commit()
            
            return True
        except Exception as e:
            # Rollback on error
            await self.db.rollback()
            raise ValueError(f"Failed to delete timetable: {str(e)}")

