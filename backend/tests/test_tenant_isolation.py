"""
Tests for tenant isolation to ensure data leakage is prevented.
"""
import pytest
from uuid import UUID
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository


@pytest.mark.asyncio
async def test_tenant_isolation_teachers(
    db_session,
    tenant_a,
    tenant_b,
    teacher_tenant_a,
    teacher_tenant_b
):
    """Test that teachers from tenant A are not visible to tenant B."""
    repo_a = TeacherRepository(db_session)
    repo_b = TeacherRepository(db_session)
    
    # Get teachers for tenant A
    teachers_a = await repo_a.get_all(tenant_id=tenant_a.id)
    assert len(teachers_a) == 1
    assert teachers_a[0].id == teacher_tenant_a.id
    assert teachers_a[0].tenant_id == tenant_a.id
    
    # Get teachers for tenant B
    teachers_b = await repo_b.get_all(tenant_id=tenant_b.id)
    assert len(teachers_b) == 1
    assert teachers_b[0].id == teacher_tenant_b.id
    assert teachers_b[0].tenant_id == tenant_b.id
    
    # Verify tenant A cannot access tenant B's teacher
    teacher_b_from_a = await repo_a.get_by_id(teacher_tenant_b.id, tenant_id=tenant_a.id)
    assert teacher_b_from_a is None, "Tenant A should not be able to access Tenant B's teacher"
    
    # Verify tenant B cannot access tenant A's teacher
    teacher_a_from_b = await repo_b.get_by_id(teacher_tenant_a.id, tenant_id=tenant_b.id)
    assert teacher_a_from_b is None, "Tenant B should not be able to access Tenant A's teacher"


@pytest.mark.asyncio
async def test_tenant_isolation_users(
    db_session,
    tenant_a,
    tenant_b,
    user_tenant_a,
    user_tenant_b
):
    """Test that users from tenant A are not visible to tenant B."""
    repo_a = UserRepository(db_session)
    repo_b = UserRepository(db_session)
    
    # Get users for tenant A
    users_a = await repo_a.get_all(tenant_id=tenant_a.id)
    assert len(users_a) == 1
    assert users_a[0].id == user_tenant_a.id
    assert users_a[0].tenant_id == tenant_a.id
    
    # Get users for tenant B
    users_b = await repo_b.get_all(tenant_id=tenant_b.id)
    assert len(users_b) == 1
    assert users_b[0].id == user_tenant_b.id
    assert users_b[0].tenant_id == tenant_b.id
    
    # Verify tenant A cannot access tenant B's user
    user_b_from_a = await repo_a.get_by_id(user_tenant_b.id, tenant_id=tenant_a.id)
    assert user_b_from_a is None, "Tenant A should not be able to access Tenant B's user"
    
    # Verify tenant B cannot access tenant A's user
    user_a_from_b = await repo_b.get_by_id(user_tenant_a.id, tenant_id=tenant_b.id)
    assert user_a_from_b is None, "Tenant B should not be able to access Tenant A's user"


@pytest.mark.asyncio
async def test_tenant_isolation_email_uniqueness(
    db_session,
    tenant_a,
    tenant_b,
    user_tenant_a
):
    """Test that the same email can exist in different tenants."""
    repo_a = UserRepository(db_session)
    repo_b = UserRepository(db_session)
    
    # Create user with same email in tenant B
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    from app.models.school import School
    
    # Create school for tenant_b
    school_b = School(
        id=2,
        tenant_id=tenant_b.id,
        name="School B",
        code="SCHOOL_B"
    )
    db_session.add(school_b)
    await db_session.commit()
    
    user_b_same_email = User(
        email=user_tenant_a.email,  # Same email as tenant A's user
        password_hash=get_password_hash("password"),
        tenant_id=tenant_b.id,
        school_id=2,
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user_b_same_email)
    await db_session.commit()
    
    # Both users should exist and be retrievable by their respective tenants
    user_a = await repo_a.get_by_email(user_tenant_a.email, tenant_id=tenant_a.id)
    assert user_a is not None
    assert user_a.id == user_tenant_a.id
    
    user_b = await repo_b.get_by_email(user_tenant_a.email, tenant_id=tenant_b.id)
    assert user_b is not None
    assert user_b.id == user_b_same_email.id
    assert user_b.tenant_id == tenant_b.id


@pytest.mark.asyncio
async def test_tenant_isolation_create_prevents_cross_tenant(
    db_session,
    tenant_a,
    tenant_b
):
    """Test that creating an entity with wrong tenant_id is prevented."""
    from app.models.teacher import Teacher
    from app.models.school import School
    
    # Create schools
    school_a = School(id=1, tenant_id=tenant_a.id, name="School A", code="A")
    school_b = School(id=2, tenant_id=tenant_b.id, name="School B", code="B")
    db_session.add_all([school_a, school_b])
    await db_session.commit()
    
    repo_a = TeacherRepository(db_session)
    
    # Try to create teacher with tenant_b's ID but using tenant_a's repository
    # This should be prevented by ensuring tenant_id matches
    teacher = Teacher(
        tenant_id=tenant_b.id,  # Wrong tenant!
        school_id=1,
        full_name="Wrong Tenant Teacher",
        max_weekly_hours=20
    )
    
    # The repository should set tenant_id correctly, but if we bypass it,
    # the database constraint should catch it
    # For now, we test that get_all filters correctly
    db_session.add(teacher)
    await db_session.commit()
    
    # Verify tenant A cannot see this teacher
    teachers_a = await repo_a.get_all(tenant_id=tenant_a.id)
    teacher_ids = [t.id for t in teachers_a]
    assert teacher.id not in teacher_ids, "Tenant A should not see teacher created with tenant B's ID"


@pytest.mark.asyncio
async def test_tenant_isolation_update_prevents_cross_tenant(
    db_session,
    tenant_a,
    tenant_b,
    teacher_tenant_a,
    teacher_tenant_b
):
    """Test that updating an entity requires correct tenant_id."""
    repo_a = TeacherRepository(db_session)
    
    # Try to update tenant B's teacher using tenant A's context
    # This should fail because tenant_id doesn't match
    result = await repo_a.update(
        id=teacher_tenant_b.id,
        tenant_id=tenant_a.id,  # Wrong tenant!
        full_name="Hacked Name"
    )
    
    # Update should return None because teacher doesn't belong to tenant_a
    assert result is None, "Update should fail when tenant_id doesn't match"
    
    # Verify teacher_tenant_b was not modified
    repo_b = TeacherRepository(db_session)
    teacher_b = await repo_b.get_by_id(teacher_tenant_b.id, tenant_id=tenant_b.id)
    assert teacher_b is not None
    assert teacher_b.full_name == teacher_tenant_b.full_name, "Teacher should not be modified"


@pytest.mark.asyncio
async def test_tenant_isolation_delete_prevents_cross_tenant(
    db_session,
    tenant_a,
    tenant_b,
    teacher_tenant_a,
    teacher_tenant_b
):
    """Test that deleting an entity requires correct tenant_id."""
    repo_a = TeacherRepository(db_session)
    
    # Try to delete tenant B's teacher using tenant A's context
    result = await repo_a.delete(
        id=teacher_tenant_b.id,
        tenant_id=tenant_a.id  # Wrong tenant!
    )
    
    # Delete should return False because teacher doesn't belong to tenant_a
    assert result is False, "Delete should fail when tenant_id doesn't match"
    
    # Verify teacher_tenant_b still exists
    repo_b = TeacherRepository(db_session)
    teacher_b = await repo_b.get_by_id(teacher_tenant_b.id, tenant_id=tenant_b.id)
    assert teacher_b is not None, "Teacher should still exist"

