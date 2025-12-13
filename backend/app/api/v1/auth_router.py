from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
# get_db removed - using get_db_for_school from dependencies
from app.core.database_manager import get_registry_db, get_school_db
from app.core.dependencies import get_current_active_user, get_db_for_school
from app.core.security import decode_token
from app.schemas.auth import Token, LoginRequest, UserResponse
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.repositories.registry_repository import RegistryRepository
from pydantic import BaseModel

router = APIRouter()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest
):
    """
    Login endpoint. Requires school_code in request body to identify which school database to use.
    """
    # Get registry entry
    async for registry_db in get_registry_db():
        try:
            registry_repo = RegistryRepository(registry_db)
            registry_entry = await registry_repo.get_by_code(login_data.school_code)
            
            if not registry_entry or not registry_entry.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="School not found or inactive"
                )
            
            # Connect to school database
            async for db in get_school_db(
                database_name=registry_entry.database_name,
                host=registry_entry.database_host,
                port=registry_entry.database_port,
                user=registry_entry.database_user
            ):
                try:
                    user_service = UserService(db)
                    user = await user_service.authenticate_user(login_data.email, login_data.password)
                    if not user:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password"
                        )
                    tokens = user_service.create_tokens(user)
                    return tokens
                finally:
                    break
        finally:
            break

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_for_school)
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
    user = await user_repo.get_by_id(user_id)
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

