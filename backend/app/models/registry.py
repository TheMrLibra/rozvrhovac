"""
Registry model for multi-tenant database management.
This model is stored in the registry database and contains metadata about each school
and their database connection information.
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

# Separate Base for registry database
RegistryBase = declarative_base()

class SchoolRegistry(RegistryBase):
    """
    Registry entry for a school. This is stored in the registry database.
    Each school has its own database, and this registry tracks which database to use.
    The school_id here maps to the School.id in the school's own database.
    """
    __tablename__ = "school_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, nullable=False, unique=True, index=True)  # Maps to School.id in school database
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    database_name = Column(String, nullable=False, unique=True, index=True)
    database_host = Column(String, nullable=False, default="localhost")
    database_port = Column(Integer, nullable=False, default=5432)
    database_user = Column(String, nullable=False, default="postgres")
    # Note: database_password should be stored securely (e.g., in secrets manager)
    # For now, we'll use environment variables or a shared password
    is_active = Column(Boolean, default=True, nullable=False)

