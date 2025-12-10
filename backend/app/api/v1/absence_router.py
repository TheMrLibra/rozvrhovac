from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.absence import TeacherAbsence
from app.schemas.absence import TeacherAbsenceCreate, TeacherAbsenceResponse
from app.repositories.absence_repository import TeacherAbsenceRepository

router = APIRouter()

@router.post("/schools/{school_id}/absences", response_model=TeacherAbsenceResponse, status_code=status.HTTP_201_CREATED)
async def create_absence(
    school_id: int,
    absence_data: TeacherAbsenceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Teachers can only report their own absences
    if current_user.role == UserRole.TEACHER:
        if current_user.teacher_id != absence_data.teacher_id:
            raise HTTPException(status_code=403, detail="Teachers can only report their own absences")
    
    # Verify teacher belongs to school
    from app.repositories.teacher_repository import TeacherRepository
    teacher_repo = TeacherRepository(db)
    teacher = await teacher_repo.get_by_id(absence_data.teacher_id)
    if not teacher or teacher.school_id != school_id:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    from app.models.absence import TeacherAbsence
    repo = TeacherAbsenceRepository(db)
    absence = TeacherAbsence(
        school_id=school_id,
        **absence_data.model_dump()
    )
    created_absence = await repo.create(absence)
    
    # Reload with teacher relationship eagerly loaded
    result = await db.execute(
        select(TeacherAbsence)
        .options(selectinload(TeacherAbsence.teacher))
        .where(TeacherAbsence.id == created_absence.id)
    )
    return result.scalar_one()

@router.get("/schools/{school_id}/absences", response_model=List[TeacherAbsenceResponse])
async def list_absences(
    school_id: int,
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = TeacherAbsenceRepository(db)
    if teacher_id:
        # Teachers can only see their own absences
        if current_user.role == UserRole.TEACHER and current_user.teacher_id != teacher_id:
            raise HTTPException(status_code=403, detail="Access denied")
        absences = await repo.get_by_teacher_id(teacher_id)
    else:
        # Admins can see all absences for the school
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Only admins can view all absences")
        absences = await repo.get_by_school_id(school_id)
    
    return absences

@router.get("/schools/{school_id}/absences/{absence_id}", response_model=TeacherAbsenceResponse)
async def get_absence(
    school_id: int,
    absence_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from sqlalchemy.orm import selectinload
    repo = TeacherAbsenceRepository(db)
    result = await repo.db.execute(
        select(TeacherAbsence)
        .options(selectinload(TeacherAbsence.teacher))
        .where(TeacherAbsence.id == absence_id)
    )
    absence = result.scalar_one_or_none()
    if not absence or absence.school_id != school_id:
        raise HTTPException(status_code=404, detail="Absence not found")
    
    # Teachers can only see their own absences
    if current_user.role == UserRole.TEACHER and current_user.teacher_id != absence.teacher_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return absence

@router.delete("/schools/{school_id}/absences/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_absence(
    school_id: int,
    absence_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = TeacherAbsenceRepository(db)
    absence = await repo.get_by_id(absence_id)
    if not absence or absence.school_id != school_id:
        raise HTTPException(status_code=404, detail="Absence not found")
    
    await repo.delete(absence_id)

