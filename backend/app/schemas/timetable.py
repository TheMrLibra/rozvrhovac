from pydantic import BaseModel
from typing import Optional
from datetime import date

class TimetableCreate(BaseModel):
    name: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class TimetableEntryResponse(BaseModel):
    id: int
    timetable_id: int
    class_group_id: int
    subject_id: int
    teacher_id: int
    classroom_id: Optional[int]
    day_of_week: int
    lesson_index: int
    
    class Config:
        from_attributes = True

class TimetableResponse(BaseModel):
    id: int
    school_id: int
    name: str
    valid_from: Optional[date]
    valid_to: Optional[date]
    entries: list[TimetableEntryResponse] = []
    
    class Config:
        from_attributes = True

class ValidationErrorResponse(BaseModel):
    type: str
    message: str
    entry_id: Optional[int] = None

class ValidationResponse(BaseModel):
    is_valid: bool
    errors: list[ValidationErrorResponse]

