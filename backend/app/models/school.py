from sqlalchemy import Column, Integer, String, ForeignKey, Time, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, index=True)
    # settings_id removed - circular dependency. Use SchoolSettings.school_id instead
    
    # Unique constraint: code must be unique per tenant
    __table_args__ = (
        Index('ix_schools_tenant_code', 'tenant_id', 'code', unique=True),
    )
    
    tenant = relationship("Tenant")
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
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, unique=True, index=True)
    start_time = Column(Time, nullable=False)  # e.g., 08:00
    end_time = Column(Time, nullable=False)  # e.g., 16:00
    class_hour_length_minutes = Column(Integer, nullable=False, default=45)
    break_duration_minutes = Column(Integer, nullable=False, default=10)  # Deprecated: kept for backward compatibility
    break_durations = Column(JSON, nullable=True)  # e.g., [5, 20, 10, 10, 10] - break durations after each lesson (index 0 = after lesson 1)
    possible_lunch_hours = Column(JSON, nullable=True)  # e.g., [3, 4, 5]
    lunch_duration_minutes = Column(Integer, nullable=False, default=30)
    
    tenant = relationship("Tenant")
    school = relationship("School", back_populates="settings", foreign_keys="SchoolSettings.school_id")

