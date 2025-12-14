"""
Authentication Router (Presentation Layer)
Handles HTTP requests and responses for authentication endpoints.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db_for_school
from app.schemas.auth import Token, LoginRequest, UserResponse, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(login_data: LoginRequest) -> Token:
    """
    Authenticate user and return JWT tokens.
    
    Args:
        login_data: Login credentials (email, password, optional school_code)
    
    Returns:
        Token response with access_token and refresh_token
    
    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 404 if school not found
        HTTPException: 500 for internal server errors
    """
    try:
        auth_service = AuthService()
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            school_code=login_data.school_code
        )
        
        # Generate tokens
        tokens = UserService.create_tokens_for_user(user)
        logger.info(f"Login successful for user: {user.email} (school_id: {user.school_id})")
        return Token(**tokens)
        
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Authentication failed: {error_msg}")
        
        # Determine appropriate status code based on error message
        if "School not found" in error_msg or "No active schools" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            # Invalid credentials - use generic message for security
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_for_school)
) -> Token:
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token request
        db: Database session (injected)
    
    Returns:
        New token response with access_token and refresh_token
    
    Raises:
        HTTPException: 401 if refresh token is invalid
    """
    from app.core.security import decode_token
    
    # Validate refresh token
    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        logger.warning("Invalid refresh token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract user ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        logger.warning("Refresh token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        logger.warning(f"Invalid user ID in refresh token: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user or not user.is_active:
        logger.warning(f"User not found or inactive: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Generate new tokens
    user_service = UserService(db)
    tokens = user_service.create_tokens(user)
    logger.info(f"Token refreshed for user: {user.email}")
    return Token(**tokens)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user (injected)
    
    Returns:
        User information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        school_id=current_user.school_id
    )
