"""
Authentication Schemas (Data Transfer Objects)
Defines request/response models for authentication endpoints.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """
    Login request schema.
    
    Attributes:
        email: User email address
        password: User password
        school_code: Optional school code. If not provided, searches all schools.
    """
    email: EmailStr
    password: str
    school_code: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request schema.
    
    Attributes:
        refresh_token: Refresh token string
    """
    refresh_token: str


class Token(BaseModel):
    """
    Token response schema.
    
    Attributes:
        access_token: JWT access token
        refresh_token: JWT refresh token
        token_type: Token type (always "bearer")
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    User information response schema.
    
    Attributes:
        id: User ID
        email: User email address
        role: User role
        school_id: School ID
    """
    id: int
    email: str
    role: str
    school_id: int
    
    class Config:
        from_attributes = True
