"""
Pytest configuration and fixtures for testing.
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from uuid import uuid4
import os

from app.core.database import Base, get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.teacher import Teacher
from app.core.security import get_password_hash


# Test database URL (use in-memory SQLite for speed, or separate test PostgreSQL)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def tenant_a(db_session: AsyncSession) -> Tenant:
    """Create tenant A for testing."""
    tenant = Tenant(
        id=uuid4(),
        name="Test School A",
        slug="test-school-a"
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def tenant_b(db_session: AsyncSession) -> Tenant:
    """Create tenant B for testing."""
    tenant = Tenant(
        id=uuid4(),
        name="Test School B",
        slug="test-school-b"
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def user_tenant_a(db_session: AsyncSession, tenant_a: Tenant) -> User:
    """Create a user for tenant A."""
    # Create a school for tenant_a first (required FK)
    from app.models.school import School
    school = School(
        id=1,
        tenant_id=tenant_a.id,
        name="School A",
        code="SCHOOL_A"
    )
    db_session.add(school)
    await db_session.commit()
    
    user = User(
        email="user_a@test.com",
        password_hash=get_password_hash("password"),
        tenant_id=tenant_a.id,
        school_id=1,
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_tenant_b(db_session: AsyncSession, tenant_b: Tenant) -> User:
    """Create a user for tenant B."""
    # Create a school for tenant_b first (required FK)
    from app.models.school import School
    school = School(
        id=2,
        tenant_id=tenant_b.id,
        name="School B",
        code="SCHOOL_B"
    )
    db_session.add(school)
    await db_session.commit()
    
    user = User(
        email="user_b@test.com",
        password_hash=get_password_hash("password"),
        tenant_id=tenant_b.id,
        school_id=2,
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def teacher_tenant_a(db_session: AsyncSession, tenant_a: Tenant) -> Teacher:
    """Create a teacher for tenant A."""
    from app.models.school import School
    school = School(
        id=1,
        tenant_id=tenant_a.id,
        name="School A",
        code="SCHOOL_A"
    )
    db_session.add(school)
    await db_session.commit()
    
    teacher = Teacher(
        tenant_id=tenant_a.id,
        school_id=1,
        full_name="Teacher A",
        max_weekly_hours=20
    )
    db_session.add(teacher)
    await db_session.commit()
    await db_session.refresh(teacher)
    return teacher


@pytest.fixture
async def teacher_tenant_b(db_session: AsyncSession, tenant_b: Tenant) -> Teacher:
    """Create a teacher for tenant B."""
    from app.models.school import School
    school = School(
        id=2,
        tenant_id=tenant_b.id,
        name="School B",
        code="SCHOOL_B"
    )
    db_session.add(school)
    await db_session.commit()
    
    teacher = Teacher(
        tenant_id=tenant_b.id,
        school_id=2,
        full_name="Teacher B",
        max_weekly_hours=20
    )
    db_session.add(teacher)
    await db_session.commit()
    await db_session.refresh(teacher)
    return teacher

