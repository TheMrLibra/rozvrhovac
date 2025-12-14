from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    tenant_id: UUID
    tenant_slug: str
    school_id: int
    school_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    school_id: int
    tenant_id: UUID
    
    class Config:
        from_attributes = True

