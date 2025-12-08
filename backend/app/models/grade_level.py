from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class GradeLevel(Base):
    __tablename__ = "grade_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g., "1st", "2nd", "3rd"
    level = Column(Integer, nullable=True)  # for sorting
    
    school = relationship("School", back_populates="grade_levels")
    classes = relationship("ClassGroup", back_populates="grade_level")
    subjects = relationship("Subject", back_populates="grade_level")

