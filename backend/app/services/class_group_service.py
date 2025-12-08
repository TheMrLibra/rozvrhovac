from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.class_group import ClassGroup
from app.models.grade_level import GradeLevel
from app.repositories.class_group_repository import ClassGroupRepository
from app.repositories.base_repository import BaseRepository
from app.schemas.class_group import ClassGroupCreate, ClassGroupUpdate

class ClassGroupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.class_group_repo = ClassGroupRepository(db)
        self.grade_level_repo = BaseRepository(db, GradeLevel)
    
    async def create_class_group(self, school_id: int, class_group_data: ClassGroupCreate) -> ClassGroup:
        # Verify grade level exists and belongs to school
        grade_level = await self.grade_level_repo.get_by_id(class_group_data.grade_level_id)
        if not grade_level or grade_level.school_id != school_id:
            raise ValueError("Grade level not found or does not belong to school")
        
        class_group = ClassGroup(
            school_id=school_id,
            name=class_group_data.name,
            grade_level_id=class_group_data.grade_level_id
        )
        return await self.class_group_repo.create(class_group)
    
    async def get_class_groups_by_school(self, school_id: int) -> List[ClassGroup]:
        return await self.class_group_repo.get_by_school_id(school_id)
    
    async def get_class_group_by_id(self, class_group_id: int, school_id: int) -> Optional[ClassGroup]:
        class_group = await self.class_group_repo.get_by_id(class_group_id)
        if class_group and class_group.school_id == school_id:
            return class_group
        return None
    
    async def update_class_group(self, class_group_id: int, school_id: int, update_data: ClassGroupUpdate) -> Optional[ClassGroup]:
        class_group = await self.get_class_group_by_id(class_group_id, school_id)
        if not class_group:
            return None
        
        update_dict = {}
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        
        if update_data.grade_level_id is not None:
            # Verify grade level exists and belongs to school
            grade_level = await self.grade_level_repo.get_by_id(update_data.grade_level_id)
            if not grade_level or grade_level.school_id != school_id:
                raise ValueError("Grade level not found or does not belong to school")
            update_dict["grade_level_id"] = update_data.grade_level_id
        
        if update_dict:
            return await self.class_group_repo.update(class_group_id, **update_dict)
        return class_group
    
    async def delete_class_group(self, class_group_id: int, school_id: int) -> bool:
        class_group = await self.get_class_group_by_id(class_group_id, school_id)
        if not class_group:
            return False
        await self.class_group_repo.delete(class_group_id)
        return True

