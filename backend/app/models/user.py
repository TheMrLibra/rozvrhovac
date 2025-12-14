from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    SCHOLAR = "SCHOLAR"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)  # Kept for backward compatibility
    email = Column(String, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    class_group_id = Column(Integer, ForeignKey("class_groups.id"), nullable=True)  # for scholars
    
    # Unique constraint: email must be unique per tenant
    __table_args__ = (
        Index('ix_users_tenant_email', 'tenant_id', 'email', unique=True),
    )
    
    tenant = relationship("Tenant")
    school = relationship("School", back_populates="users")
    teacher = relationship("Teacher", back_populates="user", uselist=False, foreign_keys="User.teacher_id")
    class_group = relationship("ClassGroup")

