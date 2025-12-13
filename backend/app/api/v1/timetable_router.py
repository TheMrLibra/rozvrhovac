from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.timetable import TimetableCreate, TimetableResponse, ValidationResponse, ValidationErrorResponse
from app.repositories.timetable_repository import TimetableRepository
from app.models.timetable import TimetableEntry, Timetable
from pydantic import BaseModel
from app.services.timetable_service import TimetableService
from app.services.timetable_validation_service import TimetableValidationService, ValidationError
from app.services.substitute_timetable_service import SubstituteTimetableService
from datetime import date

router = APIRouter()

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
        
        if not timetable:
            raise HTTPException(status_code=404, detail="Timetable not found after creation")
        
        # Get full timetable with entries and lunch hours
        full_timetable, lunch_hours = await timetable_service.get_timetable_with_lunch_hours(
            school_id, timetable.id
        )
        if not full_timetable:
            raise HTTPException(status_code=404, detail="Timetable not found after creation")
        
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
    
    repo = TimetableRepository(db)
    timetables = await repo.get_by_school_id(school_id)
    
    # Add lunch hours for each timetable
    timetable_service = TimetableService(db)
    result = []
    for timetable in timetables:
        lunch_hours = await timetable_service.calculate_class_lunch_hours(school_id, timetable.id)
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
    
    repo = TimetableRepository(db)
    timetable = await repo.get_by_id_with_entries(timetable_id)
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    if timetable.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate and add lunch hours
    timetable_service = TimetableService(db)
    lunch_hours = await timetable_service.calculate_class_lunch_hours(school_id, timetable_id)
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
    
    timetable_service = TimetableService(db)
    try:
        await timetable_service.delete_timetable(school_id, timetable_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

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
        
        if not substitute_timetable:
            raise HTTPException(status_code=404, detail="Substitute timetable not found after creation")
        
        # Get full timetable with entries and lunch hours
        full_timetable, lunch_hours = await substitute_service.get_substitute_timetable_with_lunch_hours(
            school_id, substitute_timetable.id
        )
        if not full_timetable:
            raise HTTPException(status_code=404, detail="Substitute timetable not found after creation")
        
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

