from typing import Optional
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        import logging
        logger = logging.getLogger(__name__)
        
        user = await self.user_repo.get_by_email(email)
        if not user:
            logger.debug(f"User not found: {email}")
            return None
        
        logger.debug(f"User found: {email}, checking password...")
        logger.debug(f"Password hash in DB: {user.password_hash[:20]}...")
        
        password_valid = verify_password(password, user.password_hash)
        logger.debug(f"Password verification result: {password_valid}")
        
        if not password_valid:
            logger.warning(f"Password verification failed for user: {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"User is inactive: {email}")
            return None
        
        logger.info(f"User authenticated successfully: {email}")
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
        password_hash = get_password_hash(password)
        user = User(
            email=email,
            password_hash=password_hash,
            school_id=school_id,
            role=role,
            teacher_id=teacher_id,
            class_group_id=class_group_id
        )
        return await self.user_repo.create(user)
    
    def create_tokens(self, user: User) -> dict:
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value, "school_id": user.school_id}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def create_tokens_for_user(user: User) -> dict:
        """Static method to create tokens without needing a UserService instance."""
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value, "school_id": user.school_id}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

