from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.school import SchoolSettingsUpdate, SchoolSettingsResponse
from app.repositories.school_repository import SchoolSettingsRepository

router = APIRouter()

@router.get("/{school_id}")
async def get_school(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user belongs to this school
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.repositories.school_repository import SchoolRepository
    repo = SchoolRepository(db)
    school = await repo.get_by_id(school_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.get("/{school_id}/settings", response_model=SchoolSettingsResponse)
async def get_school_settings(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SchoolSettingsRepository(db)
    settings = await repo.get_by_school_id(school_id)
    if not settings:
        raise HTTPException(status_code=404, detail="School settings not found")
    return settings

@router.put("/{school_id}/settings", response_model=SchoolSettingsResponse)
async def update_school_settings(
    school_id: int,
    settings_data: SchoolSettingsUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SchoolSettingsRepository(db)
    settings = await repo.get_by_school_id(school_id)
    if not settings:
        raise HTTPException(status_code=404, detail="School settings not found")
    
    update_data = {k: v for k, v in settings_data.model_dump().items() if v is not None}
    settings = await repo.update(settings.id, **update_data)
    return settings

