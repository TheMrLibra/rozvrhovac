from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

class Classroom(Base):
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=True)
    specializations = Column(JSON, nullable=True)  # e.g., ["laboratory", "computer_science"]
    restrictions = Column(JSON, nullable=True)  # e.g., ["no_physical_education"]
    
    school = relationship("School", back_populates="classrooms")
    teachers = relationship("Teacher", secondary="teacher_classroom_association", back_populates="classrooms")
    timetable_entries = relationship("TimetableEntry", back_populates="classroom")

