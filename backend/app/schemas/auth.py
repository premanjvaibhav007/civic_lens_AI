from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from backend.app.models.entities import UserRole

class CitizenRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    city: Optional[str] = Field(None, max_length=100)

class OfficerRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: Optional[str] = None
    department_id: str
    jurisdiction_id: Optional[str] = None
    badge_number: str
    designation: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserSummaryResponse"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserSummaryResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    badge_score: Optional[int] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    badge_number: Optional[str] = None
    designation: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
