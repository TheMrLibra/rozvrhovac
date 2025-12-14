from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.core.tenant_context import get_tenant_context_with_user, TenantContext
from app.models.user import User, UserRole
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, ClassSubjectAllocationCreate, ClassSubjectAllocationUpdate, ClassSubjectAllocationResponse
from app.repositories.subject_repository import SubjectRepository, ClassSubjectAllocationRepository
from app.models.subject import Subject, ClassSubjectAllocation

router = APIRouter()

async def get_tenant_from_user(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """Get tenant context from authenticated user."""
    return await get_tenant_context_with_user(request, db, current_user)

# Subject endpoints
@router.post("/schools/{school_id}/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    school_id: int,
    subject_data: SubjectCreate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.models.subject import Subject
    repo = SubjectRepository(db)
    subject = Subject(
        tenant_id=tenant.tenant_id,
        school_id=school_id,
        **subject_data.model_dump()
    )
    return await repo.create(subject, tenant_id=tenant.tenant_id)

@router.get("/schools/{school_id}/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    school_id: int,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SubjectRepository(db)
    subjects = await repo.get_by_school_id(school_id, tenant_id=tenant.tenant_id)
    return subjects

@router.get("/schools/{school_id}/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    school_id: int,
    subject_id: int,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SubjectRepository(db)
    subject = await repo.get_by_id(subject_id, tenant_id=tenant.tenant_id)
    if not subject or subject.school_id != school_id:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@router.put("/schools/{school_id}/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    school_id: int,
    subject_id: int,
    subject_data: SubjectUpdate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SubjectRepository(db)
    subject = await repo.get_by_id(subject_id, tenant_id=tenant.tenant_id)
    if not subject or subject.school_id != school_id:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    update_data = {k: v for k, v in subject_data.model_dump().items() if v is not None}
    subject = await repo.update(subject_id, tenant_id=tenant.tenant_id, **update_data)
    return subject

@router.delete("/schools/{school_id}/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    school_id: int,
    subject_id: int,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = SubjectRepository(db)
    subject = await repo.get_by_id(subject_id, tenant_id=tenant.tenant_id)
    if not subject or subject.school_id != school_id:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Delete all related class subject allocations first
    from app.repositories.subject_repository import ClassSubjectAllocationRepository
    allocation_repo = ClassSubjectAllocationRepository(db)
    allocations = await allocation_repo.get_by_subject_id(subject_id, tenant_id=tenant.tenant_id)
    
    for allocation in allocations:
        # Delete through class_group relationship to ensure tenant filtering
        from sqlalchemy import delete
        from app.models.class_group import ClassGroup
        await db.execute(
            delete(ClassSubjectAllocation)
            .where(ClassSubjectAllocation.id == allocation.id)
            .where(ClassSubjectAllocation.class_group_id.in_(
                select(ClassGroup.id).where(ClassGroup.tenant_id == tenant.tenant_id)
            ))
        )
    await db.commit()
    
    # Delete teacher capabilities (these should cascade, but doing it explicitly to be safe)
    from sqlalchemy import select
    from app.models.teacher import TeacherSubjectCapability
    result = await db.execute(
        select(TeacherSubjectCapability)
        .join("teacher")
        .where(TeacherSubjectCapability.subject_id == subject_id)
        .where(TeacherSubjectCapability.teacher.has(tenant_id=tenant.tenant_id))
    )
    capabilities = result.scalars().all()
    for capability in capabilities:
        await db.delete(capability)
    
    if capabilities:
        await db.commit()
    
    # Check for timetable entries
    from app.models.timetable import TimetableEntry
    result = await db.execute(
        select(TimetableEntry)
        .where(TimetableEntry.subject_id == subject_id)
        .where(TimetableEntry.tenant_id == tenant.tenant_id)
    )
    timetable_entries = result.scalars().all()
    if timetable_entries:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete subject: it is used in {len(timetable_entries)} timetable entries. Please remove it from the timetable first."
        )
    
    # Now safe to delete the subject
    await repo.delete(subject_id, tenant_id=tenant.tenant_id)

# ClassSubjectAllocation endpoints
@router.post("/class-subject-allocations", response_model=ClassSubjectAllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_allocation(
    allocation_data: ClassSubjectAllocationCreate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = ClassSubjectAllocationRepository(db)
    # Verify class_group belongs to user's school
    from app.repositories.class_group_repository import ClassGroupRepository
    class_repo = ClassGroupRepository(db)
    class_group = await class_repo.get_by_id(allocation_data.class_group_id, tenant_id=tenant.tenant_id)
    if not class_group or class_group.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Class group not found")
    
    from app.models.subject import ClassSubjectAllocation
    allocation = ClassSubjectAllocation(**allocation_data.model_dump())
    # Note: ClassSubjectAllocation doesn't have tenant_id, tenant isolation is through class_group
    await repo.create(allocation)
    # Reload with primary_teacher relationship, filtered by tenant
    return await repo.get_by_id_with_primary_teacher(allocation.id, tenant_id=tenant.tenant_id)

@router.get("/class-subject-allocations", response_model=List[ClassSubjectAllocationResponse])
async def list_allocations(
    class_group_id: int = None,
    request: Request = None,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    repo = ClassSubjectAllocationRepository(db)
    if class_group_id:
        # Verify class_group belongs to user's school and tenant
        from app.repositories.class_group_repository import ClassGroupRepository
        class_repo = ClassGroupRepository(db)
        class_group = await class_repo.get_by_id(class_group_id, tenant_id=tenant.tenant_id)
        if not class_group or class_group.school_id != current_user.school_id:
            raise HTTPException(status_code=404, detail="Class group not found")
        # Get allocations filtered by tenant
        allocations = await repo.get_by_class_group_id(class_group_id, tenant_id=tenant.tenant_id)
    else:
        # Get all allocations for user's school, filtered by tenant
        from app.repositories.class_group_repository import ClassGroupRepository
        from sqlalchemy import select
        from app.models.class_group import ClassGroup
        
        # Get classes for school, filtered by tenant
        result = await db.execute(
            select(ClassGroup)
            .where(ClassGroup.school_id == current_user.school_id)
            .where(ClassGroup.tenant_id == tenant.tenant_id)
        )
        classes = result.scalars().all()
        allocations = []
        for class_group in classes:
            class_allocations = await repo.get_by_class_group_id(class_group.id, tenant_id=tenant.tenant_id)
            allocations.extend(class_allocations)
    
    return allocations

@router.put("/class-subject-allocations/{allocation_id}", response_model=ClassSubjectAllocationResponse)
async def update_allocation(
    allocation_id: int,
    allocation_data: ClassSubjectAllocationUpdate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = ClassSubjectAllocationRepository(db)
    # Get allocation through class_group to ensure tenant filtering
    from app.repositories.class_group_repository import ClassGroupRepository
    from sqlalchemy import select
    from app.models.class_group import ClassGroup
    
    # First verify we can access the allocation through tenant-scoped class_group
    result = await db.execute(
        select(ClassSubjectAllocation)
        .join(ClassGroup)
        .where(ClassSubjectAllocation.id == allocation_id)
        .where(ClassGroup.tenant_id == tenant.tenant_id)
        .where(ClassGroup.school_id == current_user.school_id)
    )
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    update_data = {k: v for k, v in allocation_data.model_dump().items() if v is not None}
    allocation = await repo.update(allocation_id, tenant_id=tenant.tenant_id, **update_data)
    return allocation

@router.delete("/class-subject-allocations/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation(
    allocation_id: int,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    repo = ClassSubjectAllocationRepository(db)
    # Get allocation through class_group to ensure tenant filtering
    from app.repositories.class_group_repository import ClassGroupRepository
    from sqlalchemy import select
    from app.models.class_group import ClassGroup
    
    # First verify we can access the allocation through tenant-scoped class_group
    result = await db.execute(
        select(ClassSubjectAllocation)
        .join(ClassGroup)
        .where(ClassSubjectAllocation.id == allocation_id)
        .where(ClassGroup.tenant_id == tenant.tenant_id)
        .where(ClassGroup.school_id == current_user.school_id)
    )
    allocation = result.scalar_one_or_none()
    
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    await repo.delete(allocation_id, tenant_id=tenant.tenant_id)

