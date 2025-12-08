from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole

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

