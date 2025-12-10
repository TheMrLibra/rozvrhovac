from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.teacher import (
    TeacherCreate, TeacherUpdate, TeacherResponse,
    TeacherSubjectCapabilityCreate, TeacherSubjectCapabilityResponse
)
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.timetable_repository import TimetableEntryRepository, TimetableRepository
from app.models.teacher import Teacher, TeacherSubjectCapability
from app.schemas.timetable import TimetableEntryResponse

router = APIRouter()

@router.post("/schools/{school_id}/teachers", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    school_id: int,
    teacher_data: TeacherCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.models.teacher import Teacher
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    
    repo = TeacherRepository(db)
    teacher = Teacher(
        school_id=school_id,
        **teacher_data.model_dump()
    )
    teacher = await repo.create(teacher)
    
    # Eagerly load capabilities for response
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher.id)
        .options(selectinload(Teacher.capabilities))
    )
    teacher = result.scalar_one()
    return teacher

@router.get("/schools/{school_id}/teachers", response_model=List[TeacherResponse])
async def list_teachers(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.teacher import Teacher
    
    result = await db.execute(
        select(Teacher)
        .where(Teacher.school_id == school_id)
        .options(selectinload(Teacher.capabilities))
    )
    teachers = result.scalars().all()
    return teachers

@router.get("/schools/{school_id}/teachers/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    school_id: int,
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.teacher import Teacher
    
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id, Teacher.school_id == school_id)
        .options(selectinload(Teacher.capabilities))
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher

@router.put("/schools/{school_id}/teachers/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    school_id: int,
    teacher_id: int,
    teacher_data: TeacherUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.teacher import Teacher
    
    repo = TeacherRepository(db)
    teacher = await repo.get_by_id(teacher_id)
    if not teacher or teacher.school_id != school_id:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    update_data = {k: v for k, v in teacher_data.model_dump().items() if v is not None}
    teacher = await repo.update(teacher_id, **update_data)
    
    # Eagerly load capabilities for response
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(selectinload(Teacher.capabilities))
    )
    teacher = result.scalar_one()
    return teacher

@router.delete("/schools/{school_id}/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    school_id: int,
    teacher_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = TeacherRepository(db)
    teacher = await repo.get_by_id(teacher_id)
    if not teacher or teacher.school_id != school_id:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    await repo.delete(teacher_id)

@router.get("/schools/{school_id}/teachers/{teacher_id}/timetable", response_model=List[TimetableEntryResponse])
async def get_teacher_timetable(
    school_id: int,
    teacher_id: int,
    day_of_week: Optional[int] = Query(None, description="Filter by day of week (0-4, Monday-Friday). If not provided, returns all days."),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # If user is a teacher, they can only see their own timetable
    if current_user.role == UserRole.TEACHER and current_user.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    entry_repo = TimetableEntryRepository(db)
    timetable_repo = TimetableRepository(db)
    timetables = await timetable_repo.get_by_school_id(school_id)
    
    teacher_entries = []
    for timetable in timetables:
        entries = await entry_repo.get_by_timetable_id(timetable.id)
        filtered_entries = [e for e in entries if e.teacher_id == teacher_id]
        if day_of_week is not None:
            filtered_entries = [e for e in filtered_entries if e.day_of_week == day_of_week]
        teacher_entries.extend(filtered_entries)
    
    return teacher_entries

# Teacher Subject Capability endpoints
@router.post("/schools/{school_id}/teachers/{teacher_id}/capabilities", response_model=TeacherSubjectCapabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher_capability(
    school_id: int,
    teacher_id: int,
    capability_data: TeacherSubjectCapabilityCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = TeacherRepository(db)
    teacher = await repo.get_by_id(teacher_id)
    if not teacher or teacher.school_id != school_id:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    if capability_data.teacher_id != teacher_id:
        raise HTTPException(status_code=400, detail="Teacher ID mismatch")
    
    # Verify subject belongs to school
    from app.repositories.subject_repository import SubjectRepository
    subject_repo = SubjectRepository(db)
    subject = await subject_repo.get_by_id(capability_data.subject_id)
    if not subject or subject.school_id != school_id:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # If setting as primary teacher, ensure no other teacher is primary for this class-subject
    if capability_data.is_primary == 1 and capability_data.class_group_id:
        from sqlalchemy import select
        from app.models.teacher import TeacherSubjectCapability
        result = await db.execute(
            select(TeacherSubjectCapability).where(
                TeacherSubjectCapability.subject_id == capability_data.subject_id,
                TeacherSubjectCapability.class_group_id == capability_data.class_group_id,
                TeacherSubjectCapability.is_primary == 1,
                TeacherSubjectCapability.teacher_id != teacher_id
            )
        )
        existing_primary = result.scalar_one_or_none()
        if existing_primary:
            # Remove primary status from existing primary teacher
            existing_primary.is_primary = 0
            await db.commit()
    
    capability = TeacherSubjectCapability(**capability_data.model_dump())
    db.add(capability)
    await db.commit()
    await db.refresh(capability)
    return capability

@router.get("/schools/{school_id}/teachers/{teacher_id}/capabilities", response_model=List[TeacherSubjectCapabilityResponse])
async def get_teacher_capabilities(
    school_id: int,
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.teacher import Teacher
    
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id, Teacher.school_id == school_id)
        .options(selectinload(Teacher.capabilities))
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return teacher.capabilities

@router.delete("/schools/{school_id}/teachers/{teacher_id}/capabilities/{capability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher_capability(
    school_id: int,
    teacher_id: int,
    capability_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = TeacherRepository(db)
    teacher = await repo.get_by_id(teacher_id)
    if not teacher or teacher.school_id != school_id:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    from sqlalchemy import select
    result = await db.execute(
        select(TeacherSubjectCapability).where(
            TeacherSubjectCapability.id == capability_id,
            TeacherSubjectCapability.teacher_id == teacher_id
        )
    )
    capability = result.scalar_one_or_none()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")
    
    await db.delete(capability)
    await db.commit()

