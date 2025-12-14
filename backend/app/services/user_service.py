"""
User Service (Business Logic Layer)
Handles user-related business logic operations.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """
    Service for user-related operations.
    Handles user authentication, creation, and token generation.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize UserService with database session.
        
        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User email address
            password: Plain text password
        
        Returns:
            User object if authentication succeeds, None otherwise
        """
        # Normalize email
        email = email.strip().lower()
        
        # Find user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            logger.debug(f"User not found: {email}")
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            logger.debug(f"Password verification failed for user: {email}")
            return None
        
        # Check if user is active
        if not user.is_active:
            logger.debug(f"User is inactive: {email}")
            return None
        
        logger.debug(f"User authenticated successfully: {email}")
        return user
    
    async def create_user(
        self,
        email: str,
        password: str,
        school_id: int,
        role: UserRole,
        teacher_id: Optional[int] = None,
        class_group_id: Optional[int] = None
    ) -> User:
        """
        Create a new user.
        
        Args:
            email: User email address
            password: Plain text password (will be hashed)
            school_id: School ID
            role: User role
            teacher_id: Optional teacher ID
            class_group_id: Optional class group ID
        
        Returns:
            Created User object
        """
        # Normalize email
        email = email.strip().lower()
        
        # Hash password
        password_hash = get_password_hash(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            school_id=school_id,
            role=role,
            teacher_id=teacher_id,
            class_group_id=class_group_id
        )
        
        user = await self.user_repo.create(user)
        logger.info(f"User created: {email} (school_id: {school_id}, role: {role.value})")
        return user
    
    def create_tokens(self, user: User) -> dict:
        """
        Create JWT tokens for a user.
        
        Args:
            user: User object
        
        Returns:
            Dictionary with access_token, refresh_token, and token_type
        """
        return self.create_tokens_for_user(user)
    
    @staticmethod
    def create_tokens_for_user(user: User) -> dict:
        """
        Create JWT tokens for a user (static method).
        This method doesn't require a database session.
        
        Args:
            user: User object
        
        Returns:
            Dictionary with access_token, refresh_token, and token_type
        
        Note:
            The access token includes:
            - sub: User ID (as string)
            - role: User role
            - school_id: School ID (for multi-tenant routing)
        """
        # Create access token with user information
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "role": user.role.value,
                "school_id": user.school_id
            }
        )
        
        # Create refresh token (only contains user ID)
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
