from pydantic import BaseModel
from typing import Optional

class ClassGroupBase(BaseModel):
    name: str  # e.g., "1.A", "1.B"
    grade_level_id: int
    number_of_students: Optional[int] = None

class ClassGroupCreate(ClassGroupBase):
    pass

class ClassGroupUpdate(BaseModel):
    name: Optional[str] = None
    grade_level_id: Optional[int] = None
    number_of_students: Optional[int] = None

class ClassGroupResponse(ClassGroupBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

class GradeLevelBase(BaseModel):
    name: str  # e.g., "1st", "2nd", "3rd"
    level: Optional[int] = None  # for sorting

class GradeLevelCreate(GradeLevelBase):
    pass

class GradeLevelResponse(GradeLevelBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

