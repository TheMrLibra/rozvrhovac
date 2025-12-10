from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ClassGroup(Base):
    __tablename__ = "class_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "1.A"
    number_of_students = Column(Integer, nullable=True)  # Number of students in this class
    
    school = relationship("School", back_populates="classes")
    grade_level = relationship("GradeLevel", back_populates="classes")
    subject_allocations = relationship("ClassSubjectAllocation", back_populates="class_group", cascade="all, delete-orphan")
    timetable_entries = relationship("TimetableEntry", back_populates="class_group")

