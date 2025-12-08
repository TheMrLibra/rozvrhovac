from pydantic import BaseModel
from typing import Optional, List

class ClassroomBase(BaseModel):
    name: str
    capacity: Optional[int] = None
    specializations: Optional[List[int]] = None  # List of subject IDs
    restrictions: Optional[List[str]] = None

class ClassroomCreate(ClassroomBase):
    pass

class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    specializations: Optional[List[int]] = None  # List of subject IDs
    restrictions: Optional[List[str]] = None

class ClassroomResponse(ClassroomBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

