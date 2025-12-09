from pydantic import BaseModel
from typing import Optional

class SubjectBase(BaseModel):
    name: str
    grade_level_id: Optional[int] = None
    allow_consecutive_hours: bool = True
    max_consecutive_hours: Optional[int] = None
    allow_multiple_in_one_day: bool = True
    required_block_length: Optional[int] = None
    is_laboratory: bool = False
    requires_specialized_classroom: bool = False

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    grade_level_id: Optional[int] = None
    allow_consecutive_hours: Optional[bool] = None
    max_consecutive_hours: Optional[int] = None
    allow_multiple_in_one_day: Optional[bool] = None
    required_block_length: Optional[int] = None
    is_laboratory: Optional[bool] = None
    requires_specialized_classroom: Optional[bool] = None

class SubjectResponse(SubjectBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

class ClassSubjectAllocationBase(BaseModel):
    class_group_id: int
    subject_id: int
    weekly_hours: int
    primary_teacher_id: Optional[int] = None

class ClassSubjectAllocationCreate(ClassSubjectAllocationBase):
    pass

class ClassSubjectAllocationUpdate(BaseModel):
    weekly_hours: Optional[int] = None
    primary_teacher_id: Optional[int] = None

class TeacherSimpleResponse(BaseModel):
    id: int
    full_name: str
    
    class Config:
        from_attributes = True

class ClassSubjectAllocationResponse(ClassSubjectAllocationBase):
    id: int
    primary_teacher: Optional[TeacherSimpleResponse] = None
    
    class Config:
        from_attributes = True

