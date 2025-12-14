from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.core.database import Base

class SubstitutionStatus(str, enum.Enum):
    AUTO_GENERATED = "AUTO_GENERATED"
    CONFIRMED = "CONFIRMED"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"

class TeacherAbsence(Base):
    __tablename__ = "teacher_absences"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    
    tenant = relationship("Tenant")
    teacher = relationship("Teacher", back_populates="absences")
    school = relationship("School")

class Substitution(Base):
    __tablename__ = "substitutions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    timetable_entry_id = Column(Integer, ForeignKey("timetable_entries.id"), nullable=False)
    original_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    substitute_teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    status = Column(Enum(SubstitutionStatus), nullable=False, default=SubstitutionStatus.AUTO_GENERATED)
    new_classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    
    tenant = relationship("Tenant")
    school = relationship("School")
    timetable_entry = relationship("TimetableEntry", back_populates="substitutions")
    original_teacher = relationship("Teacher", foreign_keys=[original_teacher_id], back_populates="original_substitutions")
    substitute_teacher = relationship("Teacher", foreign_keys=[substitute_teacher_id], back_populates="substitute_substitutions")
    new_classroom = relationship("Classroom")

