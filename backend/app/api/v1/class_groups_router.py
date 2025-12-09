from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.schemas.class_group import ClassGroupCreate, ClassGroupUpdate, ClassGroupResponse, GradeLevelCreate, GradeLevelResponse
from app.services.class_group_service import ClassGroupService
from app.repositories.base_repository import BaseRepository
from app.models.grade_level import GradeLevel

router = APIRouter()

@router.post("/", response_model=ClassGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_class_group(
    class_group_data: ClassGroupCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    service = ClassGroupService(db)
    try:
        class_group = await service.create_class_group(current_user.school_id, class_group_data)
        return class_group
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("", response_model=List[ClassGroupResponse])
@router.get("/", response_model=List[ClassGroupResponse])
async def get_class_groups(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = ClassGroupService(db)
    class_groups = await service.get_class_groups_by_school(current_user.school_id)
    return class_groups

@router.get("/{class_group_id}", response_model=ClassGroupResponse)
async def get_class_group(
    class_group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = ClassGroupService(db)
    class_group = await service.get_class_group_by_id(class_group_id, current_user.school_id)
    if not class_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found")
    return class_group

@router.put("/{class_group_id}", response_model=ClassGroupResponse)
async def update_class_group(
    class_group_id: int,
    update_data: ClassGroupUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    service = ClassGroupService(db)
    try:
        class_group = await service.update_class_group(class_group_id, current_user.school_id, update_data)
        if not class_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found")
        return class_group
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{class_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class_group(
    class_group_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    service = ClassGroupService(db)
    deleted = await service.delete_class_group(class_group_id, current_user.school_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class group not found")

# Grade Level endpoints
@router.post("/grade-levels/", response_model=GradeLevelResponse, status_code=status.HTTP_201_CREATED)
async def create_grade_level(
    grade_level_data: GradeLevelCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    grade_level_repo = BaseRepository(db, GradeLevel)
    grade_level = GradeLevel(
        school_id=current_user.school_id,
        name=grade_level_data.name,
        level=grade_level_data.level
    )
    return await grade_level_repo.create(grade_level)

@router.get("/grade-levels/", response_model=List[GradeLevelResponse])
async def get_grade_levels(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    grade_level_repo = BaseRepository(db, GradeLevel)
    from sqlalchemy import select
    result = await db.execute(
        select(GradeLevel).where(GradeLevel.school_id == current_user.school_id).order_by(GradeLevel.level)
    )
    return list(result.scalars().all())

