from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.tenant_context import get_tenant_context_optional, TenantContext
from app.core.security import decode_token
from app.schemas.auth import Token, LoginRequest, UserResponse
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
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
    Login endpoint. Accepts X-Tenant header (optional in dev, required in prod).
    If tenant is provided, user lookup is scoped to that tenant.
    """
    # Try to resolve tenant (optional for login - allows cross-tenant email lookup if needed)
    tenant_context = await get_tenant_context_optional(request, db)
    tenant_id = tenant_context.tenant_id if tenant_context else None
    
    user_service = UserService(db)
    user = await user_service.authenticate_user(login_data.email, login_data.password, tenant_id=tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    tokens = user_service.create_tokens(user)
    return tokens

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

