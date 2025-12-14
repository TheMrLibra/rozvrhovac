"""
Authentication service - handles multi-tenant login logic.
This is the service layer that contains business logic for authentication.
"""
import logging
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database_manager import get_registry_db, get_school_db
from app.models.user import User
from app.models.registry import SchoolRegistry
from app.repositories.registry_repository import RegistryRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.core.security import verify_password

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication across multiple school databases."""
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        school_code: Optional[str] = None
    ) -> Tuple[User, SchoolRegistry]:
        """
        Authenticate a user across school databases.
        
        Args:
            email: User email
            password: User password
            school_code: Optional school code. If not provided, searches all schools.
        
        Returns:
            Tuple of (User, SchoolRegistry) if authentication succeeds
        
        Raises:
            ValueError: If school not found or user not found/invalid credentials
        """
        # Get registry database connection
        async for registry_db in get_registry_db():
            registry_repo = RegistryRepository(registry_db)
            
            # If school_code is provided, use it directly
            if school_code and school_code.strip():
                school_code = school_code.strip()
                logger.info(f"Login attempt with school_code: {school_code}, email: {email}")
                
                registry_entry = await registry_repo.get_by_code(school_code)
                
                if not registry_entry or not registry_entry.is_active:
                    logger.warning(f"School not found or inactive: {school_code}")
                    raise ValueError("School not found or inactive")
                
                # Try to authenticate in this school's database
                user, registry = await self._authenticate_in_school(
                    registry_entry, email, password
                )
                if user:
                    logger.info(f"User authenticated successfully: {email} in school {school_code}")
                    return user, registry
                
                # Authentication failed
                logger.warning(f"Authentication failed for email: {email} in school: {school_code}")
                raise ValueError("Incorrect email or password")
            
            # No school_code provided - try to find user in all active schools
            logger.info(f"Login attempt without school_code, email: {email}")
            all_schools = await registry_repo.get_all_active()
            
            if not all_schools:
                logger.warning("No active schools found in registry")
                raise ValueError("No active schools found")
            
            logger.info(f"Searching {len(all_schools)} active schools for user: {email}")
            
            # Try each school database until we find the user
            for registry_entry in all_schools:
                try:
                    user, registry = await self._authenticate_in_school(
                        registry_entry, email, password
                    )
                    if user:
                        logger.info(f"User authenticated successfully: {email} in school {registry_entry.code}")
                        return user, registry
                except ValueError:
                    # Continue to next school if authentication fails
                    continue
                except Exception as e:
                    logger.debug(f"Error checking school {registry_entry.code}: {e}")
                    continue
            
            # If we get here, user not found in any school
            logger.warning(f"User not found in any school: {email}")
            raise ValueError("Incorrect email or password")
        
        # This should never be reached, but if it is, raise an error
        raise ValueError("Failed to access registry database")
    
    async def _authenticate_in_school(
        self,
        registry_entry: SchoolRegistry,
        email: str,
        password: str
    ) -> Tuple[Optional[User], SchoolRegistry]:
        """
        Authenticate user in a specific school database.
        
        Args:
            registry_entry: School registry entry
            email: User email
            password: User password
        
        Returns:
            Tuple of (User, SchoolRegistry) if authentication succeeds, (None, registry_entry) otherwise
        """
        try:
            async for db in get_school_db(
                database_name=registry_entry.database_name,
                host=registry_entry.database_host,
                port=registry_entry.database_port,
                user=registry_entry.database_user
            ):
                try:
                    user_service = UserService(db)
                    user = await user_service.authenticate_user(email, password)
                    return user, registry_entry
                except Exception as e:
                    logger.debug(f"Error authenticating in school {registry_entry.code}: {e}")
                    return None, registry_entry
                finally:
                    break
        except Exception as e:
            logger.error(f"Error connecting to school database {registry_entry.database_name}: {e}", exc_info=True)
            return None, registry_entry
        
        return None, registry_entry

