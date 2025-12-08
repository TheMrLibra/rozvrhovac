from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/schools/{school_id}/teachers")
async def list_teachers(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.repositories.teacher_repository import TeacherRepository
    repo = TeacherRepository(db)
    teachers = await repo.get_by_school_id(school_id)
    return teachers

@router.get("/schools/{school_id}/teachers/{teacher_id}/timetable")
async def get_teacher_timetable(
    school_id: int,
    teacher_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # If user is a teacher, they can only see their own timetable
    if current_user.role == UserRole.TEACHER and current_user.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.repositories.timetable_repository import TimetableEntryRepository
    entry_repo = TimetableEntryRepository(db)
    # Get all timetables for this school and filter entries by teacher
    from app.repositories.timetable_repository import TimetableRepository
    timetable_repo = TimetableRepository(db)
    timetables = await timetable_repo.get_by_school_id(school_id)
    
    teacher_entries = []
    for timetable in timetables:
        entries = await entry_repo.get_by_timetable_id(timetable.id)
        teacher_entries.extend([e for e in entries if e.teacher_id == teacher_id])
    
    return teacher_entries

