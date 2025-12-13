from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.schemas.class_group import ClassGroupResponse
from app.schemas.subject import SubjectResponse
from app.schemas.classroom import ClassroomResponse

class TimetableCreate(BaseModel):
    name: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

# Simple teacher response for timetable entries (without capabilities to avoid lazy loading)
class TeacherSimpleResponse(BaseModel):
    id: int
    school_id: int
    full_name: str
    max_weekly_hours: int
    user_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class TimetableEntryResponse(BaseModel):
    id: int
    timetable_id: int
    class_group_id: int
    subject_id: int
    teacher_id: int
    classroom_id: Optional[int]
    day_of_week: int
    lesson_index: int
    class_group: Optional[ClassGroupResponse] = None
    subject: Optional[SubjectResponse] = None
    teacher: Optional[TeacherSimpleResponse] = None
    classroom: Optional[ClassroomResponse] = None
    
    class Config:
        from_attributes = True

class TimetableResponse(BaseModel):
    id: int
    school_id: int
    name: str
    valid_from: Optional[date]
    valid_to: Optional[date]
    is_primary: Optional[int] = 1
    substitute_for_date: Optional[date] = None
    base_timetable_id: Optional[int] = None
    entries: list[TimetableEntryResponse] = []
    class_lunch_hours: Optional[dict[int, dict[int, list[int]]]] = None  # class_id -> {day: list of lunch hour lesson indices}
    
    class Config:
        from_attributes = True

class ValidationErrorResponse(BaseModel):
    type: str
    message: str
    entry_id: Optional[int] = None

class ValidationResponse(BaseModel):
    is_valid: bool
    errors: list[ValidationErrorResponse]

