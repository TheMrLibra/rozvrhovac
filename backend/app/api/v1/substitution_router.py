from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.services.substitution_service import SubstitutionService

router = APIRouter()

@router.post("/schools/{school_id}/substitutions/generate")
async def generate_substitutions(
    school_id: int,
    absence_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    substitution_service = SubstitutionService(db)
    try:
        substitutions = await substitution_service.generate_substitutions(school_id, absence_id)
        return substitutions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/schools/{school_id}/substitutions")
async def list_substitutions(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.repositories.absence_repository import SubstitutionRepository
    repo = SubstitutionRepository(db)
    substitutions = await repo.get_by_school_id(school_id)
    return substitutions

