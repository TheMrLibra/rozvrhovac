from pydantic import BaseModel
from typing import Optional, Dict, List

class TeacherBase(BaseModel):
    full_name: str
    max_weekly_hours: int
    availability: Optional[Dict[str, List[int]]] = None  # e.g., {"monday": [1, 2, 3, 4, 5]}

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    max_weekly_hours: Optional[int] = None
    availability: Optional[Dict[str, List[int]]] = None

class TeacherSubjectCapabilityBase(BaseModel):
    teacher_id: int
    subject_id: int
    grade_level_id: Optional[int] = None
    class_group_id: Optional[int] = None

class TeacherSubjectCapabilityCreate(TeacherSubjectCapabilityBase):
    pass

class TeacherSubjectCapabilityResponse(TeacherSubjectCapabilityBase):
    id: int
    
    class Config:
        from_attributes = True

class TeacherResponse(TeacherBase):
    id: int
    school_id: int
    user_id: Optional[int] = None
    capabilities: Optional[List[TeacherSubjectCapabilityResponse]] = None
    
    class Config:
        from_attributes = True

