from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.absence import SubstitutionStatus
from app.schemas.absence import SubstitutionResponse, SubstitutionUpdate
from app.services.substitution_service import SubstitutionService
from app.repositories.absence_repository import SubstitutionRepository

router = APIRouter()

@router.post("/schools/{school_id}/substitutions/generate", response_model=List[SubstitutionResponse])
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

@router.get("/schools/{school_id}/substitutions", response_model=List[SubstitutionResponse])
async def list_substitutions(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SubstitutionRepository(db)
    substitutions = await repo.get_by_school_id(school_id)
    return substitutions

@router.put("/schools/{school_id}/substitutions/{substitution_id}", response_model=SubstitutionResponse)
async def update_substitution(
    school_id: int,
    substitution_id: int,
    substitution_data: SubstitutionUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SubstitutionRepository(db)
    substitution = await repo.get_by_id(substitution_id)
    if not substitution or substitution.school_id != school_id:
        raise HTTPException(status_code=404, detail="Substitution not found")
    
    update_data = {k: v for k, v in substitution_data.model_dump().items() if v is not None}
    if "status" in update_data:
        update_data["status"] = SubstitutionStatus(update_data["status"])
    substitution = await repo.update(substitution_id, **update_data)
    return substitution

