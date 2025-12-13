from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.timetable import TimetableCreate, TimetableResponse, ValidationResponse, ValidationErrorResponse
from pydantic import BaseModel
from app.services.timetable_service import TimetableService
from app.services.timetable_validation_service import TimetableValidationService, ValidationError
from app.services.substitute_timetable_service import SubstituteTimetableService
from datetime import date
from typing import Dict, List
import math

router = APIRouter()

async def calculate_class_lunch_hours(
    db: AsyncSession,
    school_id: int,
    timetable_id: int
) -> Dict[int, Dict[int, List[int]]]:
    """Calculate lunch hours for each class per day in a timetable, matching the generation logic"""
    from app.repositories.school_repository import SchoolSettingsRepository
    from app.repositories.class_group_repository import ClassGroupRepository
    
    settings_repo = SchoolSettingsRepository(db)
    class_repo = ClassGroupRepository(db)
    
    settings = await settings_repo.get_by_school_id(school_id)
    if not settings or not settings.possible_lunch_hours or settings.lunch_duration_minutes <= 0:
        return {}
    
    classes = await class_repo.get_by_school_id(school_id)
    if not classes:
        return {}
    
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
    
    return class_lunch_hours

@router.post("/schools/{school_id}/timetables/generate", response_model=TimetableResponse)
async def generate_timetable(
    school_id: int,
    timetable_data: TimetableCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    timetable_service = TimetableService(db)
    try:
        timetable = await timetable_service.generate_timetable(
            school_id=school_id,
            name=timetable_data.name,
            valid_from=timetable_data.valid_from,
            valid_to=timetable_data.valid_to
        )
        
        # Get full timetable with entries
        from app.repositories.timetable_repository import TimetableRepository
        repo = TimetableRepository(db)
        full_timetable = await repo.get_by_id_with_entries(timetable.id)
        if not full_timetable:
            raise HTTPException(status_code=404, detail="Timetable not found after creation")
        
        # Calculate and add lunch hours
        lunch_hours = await calculate_class_lunch_hours(db, school_id, full_timetable.id)
        timetable_dict = {
            "id": full_timetable.id,
            "school_id": full_timetable.school_id,
            "name": full_timetable.name,
            "valid_from": full_timetable.valid_from,
            "valid_to": full_timetable.valid_to,
            "is_primary": full_timetable.is_primary,
            "substitute_for_date": full_timetable.substitute_for_date,
            "base_timetable_id": full_timetable.base_timetable_id,
            "entries": full_timetable.entries,
            "class_lunch_hours": lunch_hours
        }
        return TimetableResponse(**timetable_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/schools/{school_id}/timetables/{timetable_id}/validate", response_model=ValidationResponse)
async def validate_timetable(
    school_id: int,
    timetable_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    validation_service = TimetableValidationService(db)
    errors = await validation_service.validate_timetable(timetable_id)
    
    return ValidationResponse(
        is_valid=len(errors) == 0,
        errors=[ValidationErrorResponse(type=e.type, message=e.message, entry_id=e.entry_id) for e in errors]
    )

@router.get("/schools/{school_id}/timetables", response_model=list[TimetableResponse])
async def list_timetables(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.repositories.timetable_repository import TimetableRepository
    repo = TimetableRepository(db)
    timetables = await repo.get_by_school_id(school_id)
    
    # Add lunch hours for each timetable
    result = []
    for timetable in timetables:
        lunch_hours = await calculate_class_lunch_hours(db, school_id, timetable.id)
        # Convert to dict response
        timetable_dict = {
            "id": timetable.id,
            "school_id": timetable.school_id,
            "name": timetable.name,
            "valid_from": timetable.valid_from,
            "valid_to": timetable.valid_to,
            "is_primary": timetable.is_primary,
            "substitute_for_date": timetable.substitute_for_date,
            "base_timetable_id": timetable.base_timetable_id,
            "entries": timetable.entries,
            "class_lunch_hours": lunch_hours
        }
        result.append(TimetableResponse(**timetable_dict))
    
    return result

@router.get("/schools/{school_id}/timetables/{timetable_id}", response_model=TimetableResponse)
async def get_timetable(
    school_id: int,
    timetable_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.repositories.timetable_repository import TimetableRepository
    repo = TimetableRepository(db)
    timetable = await repo.get_by_id_with_entries(timetable_id)
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    if timetable.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate and add lunch hours
    lunch_hours = await calculate_class_lunch_hours(db, school_id, timetable_id)
    timetable_dict = {
        "id": timetable.id,
        "school_id": timetable.school_id,
        "name": timetable.name,
        "valid_from": timetable.valid_from,
        "valid_to": timetable.valid_to,
        "is_primary": timetable.is_primary,
        "substitute_for_date": timetable.substitute_for_date,
        "base_timetable_id": timetable.base_timetable_id,
        "entries": timetable.entries,
        "class_lunch_hours": lunch_hours
    }
    return TimetableResponse(**timetable_dict)

@router.delete("/schools/{school_id}/timetables/{timetable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable(
    school_id: int,
    timetable_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.repositories.timetable_repository import TimetableRepository, TimetableEntryRepository
    from sqlalchemy import select
    from app.models.timetable import TimetableEntry, Timetable
    
    repo = TimetableRepository(db)
    timetable = await repo.get_by_id(timetable_id)
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    if timetable.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # First, find and delete all substitute timetables that reference this timetable as their base
    substitute_result = await db.execute(
        select(Timetable).where(Timetable.base_timetable_id == timetable_id)
    )
    substitute_timetables = substitute_result.scalars().all()
    
    entry_repo = TimetableEntryRepository(db)
    
    # Delete entries and timetables for each substitute timetable
    for substitute_timetable in substitute_timetables:
        # Delete entries for this substitute timetable
        substitute_entries_result = await db.execute(
            select(TimetableEntry).where(TimetableEntry.timetable_id == substitute_timetable.id)
        )
        substitute_entries = substitute_entries_result.scalars().all()
        for entry in substitute_entries:
            await entry_repo.delete(entry.id)
        
        # Delete the substitute timetable
        await repo.delete(substitute_timetable.id)
    
    # Delete all timetable entries for the base timetable
    result = await db.execute(
        select(TimetableEntry).where(TimetableEntry.timetable_id == timetable_id)
    )
    entries = result.scalars().all()
    for entry in entries:
        await entry_repo.delete(entry.id)
    
    # Now delete the base timetable
    await repo.delete(timetable_id)

class SubstituteTimetableCreate(BaseModel):
    substitute_date: date

@router.post("/schools/{school_id}/timetables/{base_timetable_id}/generate-substitute", response_model=TimetableResponse)
async def generate_substitute_timetable(
    school_id: int,
    base_timetable_id: int,
    data: SubstituteTimetableCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Generate a substitute timetable for a specific date based on absences"""
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    substitute_service = SubstituteTimetableService(db)
    try:
        substitute_timetable = await substitute_service.generate_substitute_timetable(
            school_id=school_id,
            base_timetable_id=base_timetable_id,
            substitute_date=data.substitute_date
        )
        
        # Get full timetable with entries
        from app.repositories.timetable_repository import TimetableRepository
        repo = TimetableRepository(db)
        full_timetable = await repo.get_by_id_with_entries(substitute_timetable.id)
        if not full_timetable:
            raise HTTPException(status_code=404, detail="Substitute timetable not found after creation")
        
        # Calculate and add lunch hours (substitute timetables use same lunch hours as base)
        lunch_hours = await calculate_class_lunch_hours(db, school_id, full_timetable.id)
        timetable_dict = {
            "id": full_timetable.id,
            "school_id": full_timetable.school_id,
            "name": full_timetable.name,
            "valid_from": full_timetable.valid_from,
            "valid_to": full_timetable.valid_to,
            "is_primary": full_timetable.is_primary,
            "substitute_for_date": full_timetable.substitute_for_date,
            "base_timetable_id": full_timetable.base_timetable_id,
            "entries": full_timetable.entries,
            "class_lunch_hours": lunch_hours
        }
        return TimetableResponse(**timetable_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

