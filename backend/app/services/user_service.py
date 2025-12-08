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
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
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

