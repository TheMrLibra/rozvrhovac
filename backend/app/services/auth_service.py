"""
Authentication Service (Business Logic Layer)
Handles multi-tenant authentication logic.
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

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service for handling authentication across multiple school databases.
    Implements multi-tenant authentication with proper error handling.
    """
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        school_code: Optional[str] = None
    ) -> User:
        """
        Authenticate a user across school databases.
        
        Args:
            email: User email address
            password: User password (plain text)
            school_code: Optional school code. If provided, only checks that school.
                        If not provided, searches all active schools.
        
        Returns:
            Authenticated User object
        
        Raises:
            ValueError: If authentication fails (with descriptive message)
        """
        email = email.strip().lower()
        
        # Get registry database connection
        async for registry_db in get_registry_db():
            registry_repo = RegistryRepository(registry_db)
            
            # Case 1: School code provided - authenticate in specific school
            if school_code and school_code.strip():
                school_code = school_code.strip().upper()
                return await self._authenticate_in_specific_school(
                    registry_repo, school_code, email, password
                )
            
            # Case 2: No school code - search all active schools
            return await self._authenticate_across_schools(
                registry_repo, email, password
            )
        
        # Should never reach here, but handle edge case
        raise ValueError("Failed to access registry database")
    
    async def _authenticate_in_specific_school(
        self,
        registry_repo: RegistryRepository,
        school_code: str,
        email: str,
        password: str
    ) -> User:
        """
        Authenticate user in a specific school.
        
        Args:
            registry_repo: Registry repository instance
            school_code: School code to authenticate in
            email: User email
            password: User password
        
        Returns:
            Authenticated User
        
        Raises:
            ValueError: If school not found or authentication fails
        """
        logger.info(f"Authenticating user '{email}' in school '{school_code}'")
        
        # Get school registry entry
        registry_entry = await registry_repo.get_by_code(school_code)
        
        if not registry_entry:
            logger.warning(f"School not found: {school_code}")
            raise ValueError("School not found")
        
        if not registry_entry.is_active:
            logger.warning(f"School is inactive: {school_code}")
            raise ValueError("School is not active")
        
        # Authenticate in school database
        user = await self._authenticate_in_school_db(registry_entry, email, password)
        
        if not user:
            logger.warning(f"Authentication failed for '{email}' in school '{school_code}'")
            raise ValueError("Invalid email or password")
        
        logger.info(f"User '{email}' authenticated successfully in school '{school_code}'")
        return user
    
    async def _authenticate_across_schools(
        self,
        registry_repo: RegistryRepository,
        email: str,
        password: str
    ) -> User:
        """
        Search for user across all active schools.
        
        Args:
            registry_repo: Registry repository instance
            email: User email
            password: User password
        
        Returns:
            Authenticated User
        
        Raises:
            ValueError: If no schools found or authentication fails
        """
        logger.info(f"Searching for user '{email}' across all active schools")
        
        # Get all active schools
        active_schools = await registry_repo.get_all_active()
        
        if not active_schools:
            logger.warning("No active schools found in registry")
            raise ValueError("No active schools found")
        
        logger.info(f"Checking {len(active_schools)} active schools for user '{email}'")
        
        # Try each school database
        for registry_entry in active_schools:
            try:
                user = await self._authenticate_in_school_db(
                    registry_entry, email, password
                )
                if user:
                    logger.info(
                        f"User '{email}' authenticated successfully in school '{registry_entry.code}'"
                    )
                    return user
            except Exception as e:
                # Log but continue searching other schools
                logger.debug(
                    f"Error checking school '{registry_entry.code}': {e}",
                    exc_info=True
                )
                continue
        
        # User not found in any school
        logger.warning(f"User '{email}' not found in any active school")
        raise ValueError("Invalid email or password")
    
    async def _authenticate_in_school_db(
        self,
        registry_entry: SchoolRegistry,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user in a specific school database.
        
        Args:
            registry_entry: School registry entry
            email: User email
            password: User password
        
        Returns:
            User if authentication succeeds, None otherwise
        """
        logger.debug(
            f"Checking school '{registry_entry.code}' "
            f"(database: {registry_entry.database_name})"
        )
        
        # Get school database connection
        async for db in get_school_db(
            database_name=registry_entry.database_name,
            host=registry_entry.database_host,
            port=registry_entry.database_port,
            user=registry_entry.database_user
        ):
            try:
                user_service = UserService(db)
                user = await user_service.authenticate_user(email, password)
                return user
            except Exception as e:
                logger.debug(
                    f"Error authenticating in school '{registry_entry.code}': {e}",
                    exc_info=True
                )
                return None
        
        return None
