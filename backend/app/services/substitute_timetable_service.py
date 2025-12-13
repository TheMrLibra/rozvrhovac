from typing import List, Optional, Dict, Tuple, Set
from datetime import date, datetime
import math
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
from app.repositories.school_repository import SchoolSettingsRepository

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
        self.settings_repo = SchoolSettingsRepository(db)
    
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
        """Generate a substitute timetable for a specific date based on absences.
        First tries to rearrange lessons within the day, then adjusts the rest of the week if needed."""
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
        
        # Get school settings
        settings = await self.settings_repo.get_by_school_id(school_id)
        if not settings:
            raise ValueError("School settings not found")
        
        # Calculate max lessons per day
        total_minutes = (settings.end_time.hour * 60 + settings.end_time.minute) - \
                       (settings.start_time.hour * 60 + settings.start_time.minute)
        if settings.break_durations and len(settings.break_durations) > 0:
            avg_break_duration = sum(settings.break_durations) / len(settings.break_durations)
            lesson_duration = settings.class_hour_length_minutes + int(avg_break_duration)
        else:
            lesson_duration = settings.class_hour_length_minutes + settings.break_duration_minutes
        
        lunch_hours_count = 0
        if settings.possible_lunch_hours and settings.lunch_duration_minutes > 0:
            lunch_hours_count = math.ceil(settings.lunch_duration_minutes / settings.class_hour_length_minutes)
        
        lunch_duration_minutes = lunch_hours_count * settings.class_hour_length_minutes if settings.possible_lunch_hours else 0
        available_minutes = total_minutes - lunch_duration_minutes
        max_lessons_per_day = int(available_minutes // lesson_duration)
        
        # Get all absences for this date
        day_of_week = self._date_to_day_of_week(substitute_date)
        absences = await self._get_absences_for_date(school_id, substitute_date)
        
        # Get all teachers and classrooms
        teachers = await self.teacher_repo.get_by_school_id(school_id)
        classrooms = await self.classroom_repo.get_by_school_id(school_id)
        
        # Get all classes and subjects
        classes = await self.class_repo.get_by_school_id(school_id)
        classes_dict = {c.id: c for c in classes}
        subjects = await self.subject_repo.get_by_school_id(school_id)
        subjects_dict = {s.id: s for s in subjects}
        
        # Create substitute timetable
        substitute_timetable = Timetable(
            school_id=school_id,
            name=f"Substitute for {substitute_date.strftime('%Y-%m-%d')}",
            valid_from=substitute_date,
            valid_to=substitute_date,
            is_primary=0,
            substitute_for_date=substitute_date,
            base_timetable_id=base_timetable_id
        )
        substitute_timetable = await self.timetable_repo.create(substitute_timetable)
        
        # Get entries for the target day from base timetable
        day_entries = [e for e in base_timetable.entries if e.day_of_week == day_of_week]
        
        # Group entries by class
        class_entries: Dict[int, List[TimetableEntry]] = {}
        for entry in day_entries:
            if entry.class_group_id not in class_entries:
                class_entries[entry.class_group_id] = []
            class_entries[entry.class_group_id].append(entry)
        
        # Track teacher hours
        teacher_hours: Dict[int, int] = {t.id: 0 for t in teachers}
        
        # Get lunch hours for the day (from base timetable calculation)
        from app.services.timetable_service import TimetableService
        timetable_service = TimetableService(self.db)
        lunch_hours = await timetable_service.calculate_class_lunch_hours(school_id, base_timetable_id)
        
        # Try to rearrange lessons within the day first
        all_entries: List[TimetableEntry] = []
        failed_classes: Set[int] = set()
        
        for class_id, class_day_entries in class_entries.items():
            class_group = classes_dict.get(class_id)
            if not class_group:
                continue
            
            # Get lunch hours for this class on this day
            class_lunch_slots = set(lunch_hours.get(class_id, {}).get(day_of_week, []))
            
            # Try to rearrange lessons within the day
            rearranged = await self._try_rearrange_class_day(
                class_group, class_day_entries, subjects_dict, teachers, classrooms,
                absences, substitute_date, day_of_week, max_lessons_per_day,
                class_lunch_slots, teacher_hours, all_entries, substitute_timetable.id
            )
            
            if rearranged:
                all_entries.extend(rearranged)
            else:
                # Mark class as failed - will try moving to other days
                failed_classes.add(class_id)
                # Still add original entries as fallback (will be adjusted later)
                for entry in class_day_entries:
                    all_entries.append(entry)
        
        # If some classes failed, try moving their lessons to other days
        if failed_classes:
            # Get available days (exclude past days and the target day)
            today = date.today()
            available_days = []
            for day in range(5):  # Monday-Friday
                if day == day_of_week:
                    continue  # Skip target day
                # Calculate date for this day of week in the same week
                days_diff = day - day_of_week
                check_date = date(
                    substitute_date.year,
                    substitute_date.month,
                    substitute_date.day
                )
                from datetime import timedelta
                check_date = check_date + timedelta(days=days_diff)
                if check_date >= today:  # Only future days
                    available_days.append((day, check_date))
            
            # Try to move failed classes' lessons to other days
            for class_id in failed_classes:
                class_group = classes_dict.get(class_id)
                if not class_group:
                    continue
                
                class_day_entries = class_entries[class_id]
                
                # Try moving lessons to other days
                moved = await self._try_move_class_to_other_days(
                    class_group, class_day_entries, subjects_dict, teachers, classrooms,
                    absences, available_days, max_lessons_per_day, lunch_hours,
                    teacher_hours, all_entries, substitute_timetable.id, base_timetable.entries
                )
                
                if moved:
                    # Remove original entries for this class from the target day
                    all_entries = [e for e in all_entries 
                                 if not (e.class_group_id == class_id and e.day_of_week == day_of_week)]
                    all_entries.extend(moved)
        
        # Save all entries
        for entry in all_entries:
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
    
    async def _try_rearrange_class_day(
        self,
        class_group: ClassGroup,
        class_entries: List[TimetableEntry],
        subjects_dict: Dict[int, Subject],
        teachers: List[Teacher],
        classrooms: List[Classroom],
        absences: List[TeacherAbsence],
        substitute_date: date,
        day_of_week: int,
        max_lessons_per_day: int,
        lunch_slots: Set[int],
        teacher_hours: Dict[int, int],
        existing_entries: List[TimetableEntry],
        timetable_id: int
    ) -> Optional[List[TimetableEntry]]:
        """Try to rearrange lessons within a day for a class, ensuring all subjects are still taught"""
        from itertools import permutations
        
        # Get available lesson indices (excluding lunch slots)
        available_indices = [i for i in range(1, max_lessons_per_day + 1) if i not in lunch_slots]
        
        if len(class_entries) > len(available_indices):
            return None  # Not enough slots
        
        # Create a list of lessons to place (subject_id, original_entry)
        lessons_to_place = []
        for entry in class_entries:
            subject = subjects_dict.get(entry.subject_id)
            if subject:
                lessons_to_place.append((entry, subject))
        
        # Try different arrangements using async backtracking
        async def can_place_lesson(entry: TimetableEntry, subject: Subject, lesson_index: int, 
                           placed: List[Tuple[TimetableEntry, int]]) -> Tuple[bool, Optional[Teacher], Optional[Classroom]]:
            """Check if a lesson can be placed at a specific index and return teacher/classroom"""
            # Check if slot is already taken
            if any(li == lesson_index for _, li in placed):
                return False, None, None
            
            # Check subject constraints
            placed_indices = [li for _, li in placed]
            if not self._check_subject_constraints_for_rearrangement(
                subject, class_group.id, lesson_index, placed_indices
            ):
                return False, None, None
            
            # Check if original teacher is absent
            absent_teacher_id = None
            for absence in absences:
                if absence.teacher_id == entry.teacher_id:
                    absent_teacher_id = absence.teacher_id
                    break
            
            # Find teacher
            teacher_id = entry.teacher_id
            if absent_teacher_id:
                # Need substitute teacher
                # Create a temporary entry for checking
                temp_entry = TimetableEntry(
                    timetable_id=timetable_id,
                    class_group_id=entry.class_group_id,
                    subject_id=entry.subject_id,
                    teacher_id=entry.teacher_id,
                    classroom_id=entry.classroom_id,
                    day_of_week=day_of_week,
                    lesson_index=lesson_index
                )
                substitute_teacher = await self._find_substitute_teacher(
                    temp_entry, absent_teacher_id, teachers, substitute_date,
                    existing_entries + [TimetableEntry(
                        timetable_id=timetable_id,
                        class_group_id=e.class_group_id,
                        subject_id=e.subject_id,
                        teacher_id=e.teacher_id,
                        classroom_id=e.classroom_id,
                        day_of_week=day_of_week,
                        lesson_index=li
                    ) for e, li in placed],
                    teacher_hours
                )
                if not substitute_teacher:
                    return False, None, None
                teacher_id = substitute_teacher.id
            else:
                # Check if original teacher is available at this time
                if any(e.teacher_id == teacher_id and e.day_of_week == day_of_week 
                      and e.lesson_index == lesson_index for e in existing_entries):
                    return False, None, None
                
                # Check teacher availability
                day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
                day_name = day_names[day_of_week]
                teacher = next((t for t in teachers if t.id == teacher_id), None)
                if teacher and teacher.availability:
                    available_hours = teacher.availability.get(day_name, [])
                    if available_hours and lesson_index not in available_hours:
                        return False, None, None
            
            # Find classroom
            placed_entries_for_check = existing_entries + [
                TimetableEntry(
                    timetable_id=timetable_id,
                    class_group_id=e.class_group_id,
                    subject_id=e.subject_id,
                    teacher_id=e.teacher_id,
                    classroom_id=e.classroom_id,
                    day_of_week=day_of_week,
                    lesson_index=li
                ) for e, li in placed
            ]
            classroom = await self._find_suitable_classroom(
                subject, class_group, day_of_week, lesson_index, classrooms, placed_entries_for_check
            )
            
            return True, next((t for t in teachers if t.id == teacher_id), None), classroom
        
        # Async backtracking to find valid arrangement
        async def backtrack(remaining: List[Tuple[TimetableEntry, Subject]], 
                     placed: List[Tuple[TimetableEntry, int]]) -> Optional[List[Tuple[TimetableEntry, int, Teacher, Optional[Classroom]]]]:
            if not remaining:
                return [(e, li, next((t for t in teachers if t.id == e.teacher_id), None), None) 
                        for e, li in placed]
            
            entry, subject = remaining[0]
            for lesson_index in available_indices:
                if any(li == lesson_index for _, li in placed):
                    continue
                
                can_place, teacher, classroom = await can_place_lesson(entry, subject, lesson_index, placed)
                if can_place:
                    new_placed = placed + [(entry, lesson_index)]
                    result = await backtrack(remaining[1:], new_placed)
                    if result:
                        # Update teacher and classroom in result
                        for i, (e, li, t, c) in enumerate(result):
                            if e.id == entry.id:
                                result[i] = (e, li, teacher, classroom)
                                break
                        return result
            
            return None
        
        result = await backtrack(lessons_to_place, [])
        if not result:
            return None
        
        # Create entries from result
        entries = []
        for entry, lesson_index, teacher, classroom in result:
            if not teacher:
                return None  # Should not happen
            
            new_entry = TimetableEntry(
                timetable_id=timetable_id,
                class_group_id=entry.class_group_id,
                subject_id=entry.subject_id,
                teacher_id=teacher.id,
                classroom_id=classroom.id if classroom else None,
                day_of_week=day_of_week,
                lesson_index=lesson_index
            )
            entries.append(new_entry)
            teacher_hours[teacher.id] += 1
        
        return entries
    
    def _check_subject_constraints_for_rearrangement(
        self,
        subject: Subject,
        class_group_id: int,
        lesson_index: int,
        placed_indices: List[int]
    ) -> bool:
        """Check subject constraints for rearrangement (simplified - no day context needed)"""
        # Check consecutive hours
        if not subject.allow_consecutive_hours:
            if any(abs(li - lesson_index) == 1 for li in placed_indices):
                return False
        
        # Check multiple in day - we're rearranging within a day, so this is OK
        # (subject can appear multiple times if allowed)
        
        return True
    
    async def _try_move_class_to_other_days(
        self,
        class_group: ClassGroup,
        class_entries: List[TimetableEntry],
        subjects_dict: Dict[int, Subject],
        teachers: List[Teacher],
        classrooms: List[Classroom],
        absences: List[TeacherAbsence],
        available_days: List[Tuple[int, date]],
        max_lessons_per_day: int,
        lunch_hours: Dict[int, Dict[int, List[int]]],
        teacher_hours: Dict[int, int],
        existing_entries: List[TimetableEntry],
        timetable_id: int,
        base_entries: List[TimetableEntry]
    ) -> Optional[List[TimetableEntry]]:
        """Try to move a class's lessons to other days in the week"""
        if not available_days:
            return None
        
        moved_entries = []
        school_id = class_group.school_id
        
        for entry in class_entries:
            subject = subjects_dict.get(entry.subject_id)
            if not subject:
                continue
            
            # Try to place this lesson on an available day
            placed = False
            for day, check_date in available_days:
                # Get lunch slots for this class on this day
                class_lunch_slots = set(lunch_hours.get(class_group.id, {}).get(day, []))
                available_indices = [i for i in range(1, max_lessons_per_day + 1) if i not in class_lunch_slots]
                
                # Check if original teacher is absent on this day
                day_absences = await self._get_absences_for_date(school_id, check_date)
                absent_teacher_id = None
                for absence in day_absences:
                    if absence.teacher_id == entry.teacher_id:
                        absent_teacher_id = absence.teacher_id
                        break
                
                # Try to find a slot for this lesson
                for lesson_index in available_indices:
                    # Check if slot conflicts with existing entries
                    if any(e.class_group_id == class_group.id and e.day_of_week == day 
                          and e.lesson_index == lesson_index for e in existing_entries + moved_entries):
                        continue
                    
                    # Find teacher
                    teacher_id = entry.teacher_id
                    if absent_teacher_id:
                        temp_entry = TimetableEntry(
                            timetable_id=timetable_id,
                            class_group_id=entry.class_group_id,
                            subject_id=entry.subject_id,
                            teacher_id=entry.teacher_id,
                            classroom_id=entry.classroom_id,
                            day_of_week=day,
                            lesson_index=lesson_index
                        )
                        substitute_teacher = await self._find_substitute_teacher(
                            temp_entry, absent_teacher_id, teachers, check_date,
                            existing_entries + moved_entries, teacher_hours
                        )
                        if not substitute_teacher:
                            continue
                        teacher_id = substitute_teacher.id
                    else:
                        # Check if teacher is available
                        if any(e.teacher_id == teacher_id and e.day_of_week == day 
                              and e.lesson_index == lesson_index for e in existing_entries + moved_entries):
                            continue
                        
                        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
                        day_name = day_names[day]
                        teacher = next((t for t in teachers if t.id == teacher_id), None)
                        if teacher and teacher.availability:
                            available_hours = teacher.availability.get(day_name, [])
                            if available_hours and lesson_index not in available_hours:
                                continue
                    
                    # Find classroom
                    classroom = await self._find_suitable_classroom(
                        subject, class_group, day, lesson_index, classrooms,
                        existing_entries + moved_entries
                    )
                    
                    # Check subject constraints
                    day_placed = [e for e in moved_entries if e.class_group_id == class_group.id and e.day_of_week == day]
                    placed_indices = [e.lesson_index for e in day_placed]
                    if not self._check_subject_constraints_for_rearrangement(
                        subject, class_group.id, lesson_index, placed_indices
                    ):
                        continue
                    
                    # Create entry
                    new_entry = TimetableEntry(
                        timetable_id=timetable_id,
                        class_group_id=entry.class_group_id,
                        subject_id=entry.subject_id,
                        teacher_id=teacher_id,
                        classroom_id=classroom.id if classroom else None,
                        day_of_week=day,
                        lesson_index=lesson_index
                    )
                    moved_entries.append(new_entry)
                    teacher_hours[teacher_id] += 1
                    placed = True
                    break
                
                if placed:
                    break
            
            if not placed:
                # Could not place this lesson anywhere
                return None
        
        return moved_entries

