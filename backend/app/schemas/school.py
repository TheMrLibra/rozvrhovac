from pydantic import BaseModel
from typing import Optional, List
from datetime import time

class SchoolSettingsBase(BaseModel):
    start_time: time
    end_time: time
    class_hour_length_minutes: int = 45
    break_duration_minutes: int = 10  # Deprecated: kept for backward compatibility
    break_durations: Optional[List[int]] = None  # Break durations after each lesson (index 0 = after lesson 1)
    possible_lunch_hours: Optional[List[int]] = None
    lunch_duration_minutes: int = 30

class SchoolSettingsUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    class_hour_length_minutes: Optional[int] = None
    break_duration_minutes: Optional[int] = None  # Deprecated: kept for backward compatibility
    break_durations: Optional[List[int]] = None
    possible_lunch_hours: Optional[List[int]] = None
    lunch_duration_minutes: Optional[int] = None

class SchoolSettingsResponse(SchoolSettingsBase):
    id: int
    school_id: int
    
    class Config:
        from_attributes = True

