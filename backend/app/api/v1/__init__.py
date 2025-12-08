from fastapi import APIRouter
from app.api.v1 import (
    auth_router, schools_router, timetable_router, teachers_router, 
    substitution_router, class_groups_router, subjects_router, 
    classrooms_router, absence_router
)

api_router = APIRouter()

api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
api_router.include_router(schools_router.router, prefix="/schools", tags=["schools"])
api_router.include_router(timetable_router.router, prefix="/timetables", tags=["timetables"])
api_router.include_router(teachers_router.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(substitution_router.router, prefix="/substitutions", tags=["substitutions"])
api_router.include_router(class_groups_router.router, prefix="/class-groups", tags=["class-groups"])
api_router.include_router(subjects_router.router, prefix="/subjects", tags=["subjects"])
api_router.include_router(classrooms_router.router, prefix="/classrooms", tags=["classrooms"])
api_router.include_router(absence_router.router, prefix="/absences", tags=["absences"])

