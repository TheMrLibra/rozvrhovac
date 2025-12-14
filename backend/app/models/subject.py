from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    grade_level_id = Column(Integer, ForeignKey("grade_levels.id"), nullable=True)
    name = Column(String, nullable=False)  # e.g., "Mathematics"
    allow_consecutive_hours = Column(Boolean, default=True)
    max_consecutive_hours = Column(Integer, nullable=True)  # e.g., max 2 hours in a row
    allow_multiple_in_one_day = Column(Boolean, default=True)
    required_block_length = Column(Integer, nullable=True)  # e.g., 2-hour lab block required
    is_laboratory = Column(Boolean, default=False)
    requires_specialized_classroom = Column(Boolean, default=False)
    
    tenant = relationship("Tenant")
    school = relationship("School", back_populates="subjects")
    grade_level = relationship("GradeLevel", back_populates="subjects")
    class_allocations = relationship("ClassSubjectAllocation", back_populates="subject", cascade="all, delete-orphan")
    teacher_capabilities = relationship("TeacherSubjectCapability", back_populates="subject", cascade="all, delete-orphan")
    timetable_entries = relationship("TimetableEntry", back_populates="subject")

class ClassSubjectAllocation(Base):
    __tablename__ = "class_subject_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    class_group_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    weekly_hours = Column(Integer, nullable=False)  # number of hours per week
    primary_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True, index=True)  # Primary teacher for this class-subject
    allow_multiple_in_one_day = Column(Boolean, nullable=False, default=False)  # Override subject setting for this class-subject allocation
    required_consecutive_hours = Column(Integer, nullable=True)  # Number of lessons that must be in a row for this class-subject
    
    class_group = relationship("ClassGroup", back_populates="subject_allocations")
    subject = relationship("Subject", back_populates="class_allocations")
    primary_teacher = relationship("Teacher", foreign_keys=[primary_teacher_id])

