"""User schemas."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: str = Field(default="worker")
    department_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str = Field(..., max_length=255)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role: str
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserWithBalance(UserResponse):
    overtime_balance_minutes: int = 0


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)
