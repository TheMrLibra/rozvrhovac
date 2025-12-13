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
        
        # Get full timetable with entries
        from app.repositories.timetable_repository import TimetableRepository
        repo = TimetableRepository(db)
        full_timetable = await repo.get_by_id_with_entries(timetable.id)
        if not full_timetable:
            raise HTTPException(status_code=404, detail="Timetable not found after creation")
        return full_timetable
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
    return timetables

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
    return timetable

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
        return full_timetable
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

