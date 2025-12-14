"""
Tenant context and resolution for multi-tenancy support.
"""
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class TenantContext(BaseModel):
    """Tenant context holding tenant information for the current request."""
    tenant_id: UUID
    tenant: Optional[Tenant] = None
    
    class Config:
        arbitrary_types_allowed = True


async def get_tenant_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)  # Will be injected by endpoint if needed
) -> TenantContext:
    """
    Resolve tenant context for the current request.
    
    Priority order:
    1. From authenticated user's tenant_id (if user has tenant_id)
    2. From X-Tenant header (UUID or slug)
    3. From DEFAULT_TENANT_SLUG (dev only)
    4. Raise 400 error if cannot resolve (prod) or dev without default
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user (optional)
    
    Returns:
        TenantContext with tenant_id
    
    Raises:
        HTTPException: 400 if tenant cannot be resolved, 404 if tenant not found
    """
    tenant_id: Optional[UUID] = None
    tenant: Optional[Tenant] = None
    
    # Priority 1: From authenticated user
    if current_user and hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
        logger.debug(f"Resolved tenant from user: {tenant_id}")
    
    # Priority 2: From X-Tenant header
    if not tenant_id:
        tenant_header = request.headers.get("X-Tenant")
        if tenant_header:
            tenant_header = tenant_header.strip()
            # Try as UUID first
            try:
                tenant_id = UUID(tenant_header)
                logger.debug(f"Resolved tenant from X-Tenant header (UUID): {tenant_id}")
            except ValueError:
                # Try as slug
                result = await db.execute(
                    select(Tenant).where(Tenant.slug == tenant_header)
                )
                tenant = result.scalar_one_or_none()
                if tenant:
                    tenant_id = tenant.id
                    logger.debug(f"Resolved tenant from X-Tenant header (slug): {tenant_id}")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Tenant with slug '{tenant_header}' not found"
                    )
    
    # Priority 3: Default tenant (dev only)
    if not tenant_id:
        if settings.is_dev and settings.DEFAULT_TENANT_SLUG:
            result = await db.execute(
                select(Tenant).where(Tenant.slug == settings.DEFAULT_TENANT_SLUG)
            )
            tenant = result.scalar_one_or_none()
            if tenant:
                tenant_id = tenant.id
                logger.debug(f"Resolved tenant from DEFAULT_TENANT_SLUG: {tenant_id}")
            else:
                logger.warning(f"DEFAULT_TENANT_SLUG '{settings.DEFAULT_TENANT_SLUG}' not found in database")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant must be specified via X-Tenant header or user must have tenant_id"
            )
    
    # If we still don't have tenant_id, fail
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not resolve tenant context"
        )
    
    # Fetch tenant object if not already fetched
    if not tenant:
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with id '{tenant_id}' not found"
            )
    
    return TenantContext(tenant_id=tenant_id, tenant=tenant)


async def get_tenant_context_with_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Will be injected by endpoint
) -> TenantContext:
    """
    Get tenant context with authenticated user.
    This is a helper that endpoints can use with get_current_active_user.
    """
    return await get_tenant_context(request, db, current_user)


async def get_tenant_context_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = None
) -> Optional[TenantContext]:
    """
    Optional tenant context resolution - returns None if tenant cannot be resolved.
    Useful for endpoints that work with or without tenant context.
    """
    try:
        return await get_tenant_context(request, db, current_user)
    except HTTPException as e:
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return None
        raise

