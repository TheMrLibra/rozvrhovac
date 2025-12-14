from typing import Optional
import logging
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.database_manager import get_registry_db, get_school_db
from app.core.security import decode_token

# Optional bearer token for school context (doesn't require auth)
optional_bearer = HTTPBearer(auto_error=False)
from app.models.user import User, UserRole
from app.models.registry import SchoolRegistry
from app.repositories.user_repository import UserRepository
from app.repositories.registry_repository import RegistryRepository

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_school_context(
    x_school_code: Optional[str] = Header(None, alias="X-School-Code"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer)
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
                logger.info(f"Getting school context from header: {x_school_code}")
                registry_entry = await registry_repo.get_by_code(x_school_code)
                if registry_entry:
                    logger.info(f"✅ Found school from header: {registry_entry.code}")
                    return registry_entry
            
            # Fall back to JWT token
            if credentials:
                token = credentials.credentials
                payload = decode_token(token)
                if payload:
                    school_id = payload.get("school_id")
                    logger.info(f"Getting school context from JWT token, school_id: {school_id}, payload keys: {list(payload.keys())}")
                    if school_id:
                        # Get school registry entry by school_id (maps to School.id in school database)
                        registry_entry = await registry_repo.get_by_school_id(school_id)
                        if registry_entry:
                            logger.info(f"✅ Found school from JWT: {registry_entry.code} (database: {registry_entry.database_name})")
                            return registry_entry
                        else:
                            logger.warning(f"❌ School registry entry not found for school_id: {school_id}")
                            # Try to find by searching all schools (fallback)
                            all_schools = await registry_repo.get_all_active()
                            logger.info(f"   Searching {len(all_schools)} active schools...")
                            for school in all_schools:
                                logger.info(f"   - School ID: {school.school_id}, Code: {school.code}, DB: {school.database_name}")
                    else:
                        logger.warning("JWT token does not contain school_id")
                else:
                    logger.warning("Failed to decode JWT token")
            else:
                logger.debug("No token found")
            
            logger.warning("Could not determine school context from request")
            return None
        finally:
            break

async def get_db_for_school(
    school_registry: Optional[SchoolRegistry] = Depends(get_school_context)
):
    """
    Get database session for the current school.
    Raises error if school context is not available (no fallback to default DB).
    """
    if not school_registry:
        logger.error("School context not available - cannot determine which database to use")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School context not found. Please provide X-School-Code header or ensure JWT token contains school_id."
        )
    
    if not school_registry.is_active:
        logger.error(f"School {school_registry.code} is not active")
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

