from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import decode_token
from app.schemas.auth import Token, LoginRequest, UserResponse
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.school_repository import SchoolRepository
from app.models.tenant import Tenant
from app.models.school import School
from pydantic import BaseModel

router = APIRouter()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint. No X-Tenant header required.
    User's tenant and school are automatically determined from their email.
    Returns tenant and school information for frontend to store in localStorage.
    """
    user_service = UserService(db)
    # Authenticate without tenant_id - searches across all tenants
    user = await user_service.authenticate_user(login_data.email, login_data.password, tenant_id=None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Get tenant information
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant not found for user"
        )
    
    # Get school information
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(user.school_id, tenant_id=user.tenant_id)
    
    # Create tokens
    tokens = user_service.create_tokens(user)
    
    # Return tokens with tenant and school information
    return Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        tenant_id=user.tenant_id,
        tenant_slug=tenant.slug,
        school_id=user.school_id,
        school_name=school.name if school else None
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(refresh_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_for_auth(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    user_service = UserService(db)
    tokens = user_service.create_tokens(user)
    return tokens

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
):
    return current_user

