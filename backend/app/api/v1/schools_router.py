from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.core.tenant_context import get_tenant_context, TenantContext
from app.models.user import User, UserRole
from app.schemas.school import SchoolSettingsUpdate, SchoolSettingsResponse
from app.services.school_service import SchoolService

router = APIRouter()

async def get_tenant_from_user(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """Get tenant context from authenticated user."""
    return await get_tenant_context(request, db, current_user)

@router.get("/{school_id}")
async def get_school(
    school_id: int,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify user belongs to this school
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    school_service = SchoolService(db)
    school = await school_service.get_school(school_id, tenant_id=tenant.tenant_id)
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school

@router.get("/{school_id}/settings", response_model=SchoolSettingsResponse)
async def get_school_settings(
    school_id: int,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    school_service = SchoolService(db)
    # Get or create settings (creates default if doesn't exist)
    settings = await school_service.get_or_create_school_settings(school_id, tenant_id=tenant.tenant_id)
    return settings

@router.put("/{school_id}/settings", response_model=SchoolSettingsResponse)
async def update_school_settings(
    school_id: int,
    settings_data: SchoolSettingsUpdate,
    request: Request,
    tenant: TenantContext = Depends(get_tenant_from_user),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    if current_user.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    school_service = SchoolService(db)
    settings = await school_service.update_school_settings(school_id, settings_data, tenant_id=tenant.tenant_id)
    if not settings:
        raise HTTPException(status_code=404, detail="School settings not found")
    return settings

