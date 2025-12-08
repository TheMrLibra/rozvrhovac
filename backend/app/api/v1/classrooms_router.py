from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate, ClassroomResponse
from app.repositories.classroom_repository import ClassroomRepository

router = APIRouter()

@router.post("/schools/{school_id}/classrooms", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    school_id: int,
    classroom_data: ClassroomCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.models.classroom import Classroom
    repo = ClassroomRepository(db)
    classroom = Classroom(
        school_id=school_id,
        **classroom_data.model_dump()
    )
    return await repo.create(classroom)

@router.get("/schools/{school_id}/classrooms", response_model=List[ClassroomResponse])
async def list_classrooms(
    school_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = ClassroomRepository(db)
    classrooms = await repo.get_by_school_id(school_id)
    return classrooms

@router.get("/schools/{school_id}/classrooms/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(
    school_id: int,
    classroom_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = ClassroomRepository(db)
    classroom = await repo.get_by_id(classroom_id)
    if not classroom or classroom.school_id != school_id:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom

@router.put("/schools/{school_id}/classrooms/{classroom_id}", response_model=ClassroomResponse)
async def update_classroom(
    school_id: int,
    classroom_id: int,
    classroom_data: ClassroomUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = ClassroomRepository(db)
    classroom = await repo.get_by_id(classroom_id)
    if not classroom or classroom.school_id != school_id:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    update_data = {k: v for k, v in classroom_data.model_dump().items() if v is not None}
    classroom = await repo.update(classroom_id, **update_data)
    return classroom

@router.delete("/schools/{school_id}/classrooms/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_classroom(
    school_id: int,
    classroom_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = ClassroomRepository(db)
    classroom = await repo.get_by_id(classroom_id)
    if not classroom or classroom.school_id != school_id:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    await repo.delete(classroom_id)

