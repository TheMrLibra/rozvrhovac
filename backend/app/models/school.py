from sqlalchemy import Column, Integer, String, ForeignKey, Time, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    # settings_id removed - circular dependency. Use SchoolSettings.school_id instead
    
    settings = relationship("SchoolSettings", back_populates="school", uselist=False, foreign_keys="SchoolSettings.school_id")
    grade_levels = relationship("GradeLevel", back_populates="school", cascade="all, delete-orphan")
    classes = relationship("ClassGroup", back_populates="school", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="school", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="school", cascade="all, delete-orphan")
    classrooms = relationship("Classroom", back_populates="school", cascade="all, delete-orphan")
    users = relationship("User", back_populates="school", cascade="all, delete-orphan")
    timetables = relationship("Timetable", back_populates="school", cascade="all, delete-orphan")

class SchoolSettings(Base):
    __tablename__ = "school_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, unique=True, index=True)
    start_time = Column(Time, nullable=False)  # e.g., 08:00
    end_time = Column(Time, nullable=False)  # e.g., 16:00
    class_hour_length_minutes = Column(Integer, nullable=False, default=45)
    break_duration_minutes = Column(Integer, nullable=False, default=10)
    possible_lunch_hours = Column(JSON, nullable=True)  # e.g., [3, 4, 5]
    lunch_duration_minutes = Column(Integer, nullable=False, default=30)
    
    school = relationship("School", back_populates="settings", foreign_keys="SchoolSettings.school_id")

