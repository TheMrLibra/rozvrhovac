"""
Dependencies (Dependency Injection)
Provides FastAPI dependencies for authentication and database access.
"""
from typing import Optional
import logging
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database_manager import get_registry_db, get_school_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.registry import SchoolRegistry
from app.repositories.user_repository import UserRepository
from app.repositories.registry_repository import RegistryRepository

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_school_context(
    request: Request,
    x_school_code: Optional[str] = Header(None, alias="X-School-Code")
) -> Optional[SchoolRegistry]:
    """
    Extract school context from request.
    
    Priority:
    1. X-School-Code header (if provided)
    2. JWT token school_id (from Authorization header)
    
    Args:
        request: FastAPI request object
        x_school_code: Optional school code header
    
    Returns:
        SchoolRegistry entry if found, None otherwise
    """
    async for registry_db in get_registry_db():
        try:
            registry_repo = RegistryRepository(registry_db)
            
            # Priority 1: Check X-School-Code header
            if x_school_code:
                x_school_code = x_school_code.strip().upper()
                logger.debug(f"Extracting school context from header: {x_school_code}")
                registry_entry = await registry_repo.get_by_code(x_school_code)
                if registry_entry:
                    logger.debug(f"Found school from header: {registry_entry.code}")
                    return registry_entry
                logger.warning(f"School code not found in registry: {x_school_code}")
            
            # Priority 2: Extract from JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                
                if payload:
                    school_id = payload.get("school_id")
                    if school_id:
                        logger.debug(f"Extracting school context from JWT (school_id: {school_id})")
                        registry_entry = await registry_repo.get_by_school_id(school_id)
                        
                        if registry_entry:
                            logger.debug(
                                f"Found school from JWT: {registry_entry.code} "
                                f"(database: {registry_entry.database_name})"
                            )
                            return registry_entry
                        
                        # Log all registry entries for debugging
                        logger.error(f"Registry entry not found for school_id: {school_id}")
                        all_schools = await registry_repo.get_all_active()
                        logger.error(f"Active schools in registry ({len(all_schools)}):")
                        for school in all_schools:
                            logger.error(
                                f"  - School ID: {school.school_id}, "
                                f"Code: {school.code}, "
                                f"DB: {school.database_name}"
                            )
                    else:
                        logger.warning("JWT token does not contain school_id")
                else:
                    logger.warning("Failed to decode JWT token")
            else:
                logger.debug("No Authorization header found")
            
            logger.warning("Could not determine school context from request")
            return None
        finally:
            break


async def get_db_for_school(
    school_registry: Optional[SchoolRegistry] = Depends(get_school_context)
) -> AsyncSession:
    """
    Get database session for the current school.
    
    Args:
        school_registry: School registry entry (injected)
    
    Yields:
        Database session for the school
    
    Raises:
        HTTPException: 400 if school context not found
        HTTPException: 403 if school is inactive
    """
    if not school_registry:
        logger.error("School context not available")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "School context not found. "
                "Please provide X-School-Code header or ensure JWT token contains school_id."
            )
        )
    
    if not school_registry.is_active:
        logger.error(f"School is inactive: {school_registry.code}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="School is not active"
        )
    
    logger.debug(f"Connecting to school database: {school_registry.database_name}")
    async for db in get_school_db(
        database_name=school_registry.database_name,
        host=school_registry.database_host,
        port=school_registry.database_port,
        user=school_registry.database_user
    ):
        yield db


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_for_school)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token (injected via oauth2_scheme)
        db: Database session (injected)
    
    Returns:
        Current authenticated User
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        logger.warning("Invalid token: failed to decode")
        raise credentials_exception
    
    # Extract user ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        logger.warning("Invalid token: missing user ID")
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        logger.warning(f"Invalid token: invalid user ID format: {user_id_str}")
        raise credentials_exception
    
    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current authenticated and active user.
    
    Args:
        current_user: Current user (injected)
    
    Returns:
        Active User
    
    Raises:
        HTTPException: 400 if user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_roles: List of allowed user roles
    
    Returns:
        Dependency function that checks user role
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Access denied for user {current_user.email}: "
                f"required roles {[r.value for r in allowed_roles]}, "
                f"user role: {current_user.role.value}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
