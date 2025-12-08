from fastapi import APIRouter
from app.api.v1 import auth_router, schools_router, timetable_router, teachers_router, substitution_router

api_router = APIRouter()

api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
api_router.include_router(schools_router.router, prefix="/schools", tags=["schools"])
api_router.include_router(timetable_router.router, prefix="/timetables", tags=["timetables"])
api_router.include_router(teachers_router.router, prefix="/teachers", tags=["teachers"])
api_router.include_router(substitution_router.router, prefix="/substitutions", tags=["substitutions"])

