import logging
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

logger = logging.getLogger(__name__)
router = APIRouter()

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest
):
    """
    Login endpoint. If school_code is provided, uses that school.
    If not provided, tries to find the user's school by searching all active schools.
    """
    try:
        async for registry_db in get_registry_db():
            try:
                registry_repo = RegistryRepository(registry_db)
                
                # If school_code is provided, use it directly
                if login_data.school_code and login_data.school_code.strip():
                    school_code = login_data.school_code.strip()
                    logger.info(f"Login attempt with school_code: {school_code}, email: {login_data.email}")
                    
                    registry_entry = await registry_repo.get_by_code(school_code)
                    
                    if not registry_entry or not registry_entry.is_active:
                        logger.warning(f"School not found or inactive: {school_code}")
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="School not found or inactive"
                        )
                    
                    # Try to authenticate in this school's database
                    async for db in get_school_db(
                        database_name=registry_entry.database_name,
                        host=registry_entry.database_host,
                        port=registry_entry.database_port,
                        user=registry_entry.database_user
                    ):
                        try:
                            user_service = UserService(db)
                            user = await user_service.authenticate_user(login_data.email, login_data.password)
                            if user:
                                logger.info(f"User authenticated successfully: {login_data.email} in school {school_code}")
                                tokens = user_service.create_tokens(user)
                                return tokens
                        except HTTPException:
                            raise
                        except Exception as e:
                            logger.error(f"Error authenticating user in school {school_code}: {e}", exc_info=True)
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Authentication error"
                            )
                    
                    # If we get here, authentication failed
                    logger.warning(f"Authentication failed for email: {login_data.email} in school: {school_code}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect email or password"
                    )
                
                # No school_code provided - try to find user in all active schools
                logger.info(f"Login attempt without school_code, email: {login_data.email}")
                all_schools = await registry_repo.get_all_active()
                
                if not all_schools:
                    logger.warning("No active schools found in registry")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No active schools found"
                    )
                
                logger.info(f"Searching {len(all_schools)} active schools for user: {login_data.email}")
                
                # Try each school database until we find the user
                last_error = None
                for registry_entry in all_schools:
                    try:
                        async for db in get_school_db(
                            database_name=registry_entry.database_name,
                            host=registry_entry.database_host,
                            port=registry_entry.database_port,
                            user=registry_entry.database_user
                        ):
                            try:
                                user_service = UserService(db)
                                user = await user_service.authenticate_user(login_data.email, login_data.password)
                                if user:
                                    # Found the user! Return tokens
                                    logger.info(f"User authenticated successfully: {login_data.email} in school {registry_entry.code}")
                                    tokens = user_service.create_tokens(user)
                                    return tokens
                            except HTTPException as e:
                                # If it's a 401, continue searching other schools
                                # Other HTTP exceptions should be raised
                                if e.status_code == status.HTTP_401_UNAUTHORIZED:
                                    last_error = e
                                    break
                                raise
                            except Exception as e:
                                logger.debug(f"Error checking school {registry_entry.code}: {e}")
                                last_error = e
                                break
                    except HTTPException:
                        raise
                    except Exception as e:
                        logger.debug(f"Error connecting to school {registry_entry.code}: {e}")
                        continue
                
                # If we get here, user not found in any school
                logger.warning(f"User not found in any school: {login_data.email}")
                if last_error and isinstance(last_error, HTTPException):
                    raise last_error
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            finally:
                break
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

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

