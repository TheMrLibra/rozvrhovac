from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    full_name = Column(String, nullable=False)
    max_weekly_hours = Column(Integer, nullable=False)
    availability = Column(JSON, nullable=True)  # e.g., {"monday": [1, 2, 3, 4, 5], "tuesday": [1, 2, 3]}
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    
    school = relationship("School", back_populates="teachers")
    user = relationship("User", back_populates="teacher", uselist=False)
    capabilities = relationship("TeacherSubjectCapability", back_populates="teacher", cascade="all, delete-orphan")
    timetable_entries = relationship("TimetableEntry", back_populates="teacher")
    absences = relationship("TeacherAbsence", back_populates="teacher", cascade="all, delete-orphan")
    original_substitutions = relationship("Substitution", foreign_keys="Substitution.original_teacher_id", back_populates="original_teacher")
    substitute_substitutions = relationship("Substitution", foreign_keys="Substitution.substitute_teacher_id", back_populates="substitute_teacher")

class TeacherSubjectCapability(Base):
    __tablename__ = "teacher_subject_capabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id"), nullable=True)
    class_group_id = Column(Integer, ForeignKey("class_groups.id"), nullable=True)
    
    teacher = relationship("Teacher", back_populates="capabilities")
    subject = relationship("Subject", back_populates="teacher_capabilities")
    grade_level = relationship("GradeLevel")
    class_group = relationship("ClassGroup")

