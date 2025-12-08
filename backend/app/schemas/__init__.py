from app.schemas.auth import Token, LoginRequest, UserResponse
from app.schemas.timetable import TimetableCreate, TimetableResponse, ValidationResponse, ValidationErrorResponse
from app.schemas.class_group import ClassGroupCreate, ClassGroupUpdate, ClassGroupResponse, GradeLevelCreate, GradeLevelResponse
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, ClassSubjectAllocationCreate, ClassSubjectAllocationUpdate, ClassSubjectAllocationResponse
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate, ClassroomResponse
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse, TeacherSubjectCapabilityCreate, TeacherSubjectCapabilityResponse
from app.schemas.school import SchoolSettingsUpdate, SchoolSettingsResponse
from app.schemas.absence import TeacherAbsenceCreate, TeacherAbsenceResponse, SubstitutionCreate, SubstitutionUpdate, SubstitutionResponse

__all__ = [
    "Token",
    "LoginRequest",
    "UserResponse",
    "TimetableCreate",
    "TimetableResponse",
    "ValidationResponse",
    "ValidationErrorResponse",
    "ClassGroupCreate",
    "ClassGroupUpdate",
    "ClassGroupResponse",
    "GradeLevelCreate",
    "GradeLevelResponse",
    "SubjectCreate",
    "SubjectUpdate",
    "SubjectResponse",
    "ClassSubjectAllocationCreate",
    "ClassSubjectAllocationUpdate",
    "ClassSubjectAllocationResponse",
    "ClassroomCreate",
    "ClassroomUpdate",
    "ClassroomResponse",
    "TeacherCreate",
    "TeacherUpdate",
    "TeacherResponse",
    "TeacherSubjectCapabilityCreate",
    "TeacherSubjectCapabilityResponse",
    "SchoolSettingsUpdate",
    "SchoolSettingsResponse",
    "TeacherAbsenceCreate",
    "TeacherAbsenceResponse",
    "SubstitutionCreate",
    "SubstitutionUpdate",
    "SubstitutionResponse",
]
