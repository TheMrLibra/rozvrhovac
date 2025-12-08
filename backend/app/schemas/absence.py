from pydantic import BaseModel
from typing import Optional
from datetime import date

class TeacherAbsenceBase(BaseModel):
    teacher_id: int
    date_from: date
    date_to: date
    reason: Optional[str] = None

class TeacherAbsenceCreate(TeacherAbsenceBase):
    pass

class TeacherAbsenceResponse(TeacherAbsenceBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

class SubstitutionBase(BaseModel):
    timetable_entry_id: int
    original_teacher_id: int
    substitute_teacher_id: Optional[int] = None
    new_classroom_id: Optional[int] = None

class SubstitutionCreate(SubstitutionBase):
    pass

class SubstitutionUpdate(BaseModel):
    substitute_teacher_id: Optional[int] = None
    new_classroom_id: Optional[int] = None
    status: Optional[str] = None  # AUTO_GENERATED, CONFIRMED, MANUAL_OVERRIDE

class SubstitutionResponse(SubstitutionBase):
    id: int
    school_id: int
    status: str
    
    class Config:
        from_attributes = True

