from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator

class UserBase(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    phone_number: Optional[str] = None

class UserCreate(BaseModel):
    full_name: str
    username: str
    phone_number: Optional[str] = None
    password: str
    email: Optional[EmailStr] = None
    
    @field_validator('email', mode='before')
    @classmethod
    def generate_email_from_username(cls, v, info):
        """Auto-generate email from username if not provided."""
        if v is None and info.data and 'username' in info.data:
            return f"{info.data['username']}@pathway-foundation.org"
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    username: str
    phoneNumber: Optional[str] = None
    
    @classmethod
    def from_user(cls, user):
        """Create UserResponse from User model."""
        return cls(
            id=str(user.id),
            name=user.full_name,
            email=user.email,
            username=user.username,
            phoneNumber=user.phone_number
        )

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
