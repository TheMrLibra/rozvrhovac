from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base

class Timetable(Base):
    __tablename__ = "timetables"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g., "Basic Timetable 2025/2026"
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_primary = Column(Integer, nullable=False, default=1)  # 1 = primary timetable, 0 = substitute timetable
    substitute_for_date = Column(Date, nullable=True)  # For substitute timetables: the date this applies to
    base_timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=True)  # For substitute timetables: reference to primary timetable
    
    school = relationship("School", back_populates="timetables")
    entries = relationship("TimetableEntry", back_populates="timetable", cascade="all, delete-orphan", foreign_keys="TimetableEntry.timetable_id")
    base_timetable = relationship("Timetable", remote_side=[id], foreign_keys=[base_timetable_id])

class TimetableEntry(Base):
    __tablename__ = "timetable_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"), nullable=False, index=True)
    class_group_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    day_of_week = Column(Integer, nullable=False)  # 0-4 (Monday-Friday) or 1-5
    lesson_index = Column(Integer, nullable=False)  # index of the lesson on that day
    
    timetable = relationship("Timetable", back_populates="entries")
    class_group = relationship("ClassGroup", back_populates="timetable_entries")
    subject = relationship("Subject", back_populates="timetable_entries")
    teacher = relationship("Teacher", back_populates="timetable_entries")
    classroom = relationship("Classroom", back_populates="timetable_entries")
    substitutions = relationship("Substitution", back_populates="timetable_entry", cascade="all, delete-orphan")

