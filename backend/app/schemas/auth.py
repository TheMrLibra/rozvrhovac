from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    school_code: str  # Required: identifies which school database to use

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    school_id: int
    
    class Config:
        from_attributes = True

