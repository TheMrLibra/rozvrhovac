from typing import Optional
import logging
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.database_manager import get_registry_db, get_school_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.registry import SchoolRegistry
from app.repositories.user_repository import UserRepository
from app.repositories.registry_repository import RegistryRepository

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_school_context(
    x_school_code: Optional[str] = Header(None, alias="X-School-Code"),
    authorization: Optional[str] = Header(None)
) -> Optional[SchoolRegistry]:
    """
    Extract school context from request.
    Priority: X-School-Code header > JWT token school_id
    """
    async for registry_db in get_registry_db():
        try:
            registry_repo = RegistryRepository(registry_db)
            
            # Try header first
            if x_school_code:
                registry_entry = await registry_repo.get_by_code(x_school_code)
                if registry_entry:
                    return registry_entry
            
            # Fall back to JWT token
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                payload = decode_token(token)
                if payload:
                    school_id = payload.get("school_id")
                    if school_id:
                        # Get school registry entry by school_id (maps to School.id in school database)
                        registry_entry = await registry_repo.get_by_school_id(school_id)
                        if registry_entry:
                            return registry_entry
            
            return None
        finally:
            break

async def get_db_for_school(
    school_registry: Optional[SchoolRegistry] = Depends(get_school_context)
):
    """
    Get database session for the current school.
    Falls back to default database if school context is not available.
    """
    if school_registry and school_registry.is_active:
        async for db in get_school_db(
            database_name=school_registry.database_name,
            host=school_registry.database_host,
            port=school_registry.database_port,
            user=school_registry.database_user
        ):
            yield db
    else:
        # Fall back to default database (for backward compatibility or admin operations)
        async for db in get_db():
            yield db

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_for_school)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id: int = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        logger.debug(f"User not found for id: {user_id}")
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(allowed_roles: list[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

