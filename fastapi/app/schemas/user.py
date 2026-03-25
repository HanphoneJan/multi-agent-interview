"""User schemas"""
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.core.constants import LearningStage, Gender
from app.schemas.interviewer import InterviewerSettings


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    name: str = Field(default="", max_length=40)
    phone: Optional[str] = Field(None, pattern=r'^1[3-9]\d{9}$')
    major: str = Field(default="", max_length=100)
    university: str = Field(default="", max_length=100)
    gender: Literal["M", "F", "O"] = "O"
    age: Optional[int] = Field(None, ge=1, le=120)
    learning_stage: Optional[Literal[
        "FRESHMAN_1", "FRESHMAN_2", "SOPHOMORE_1", "SOPHOMORE_2", 
        "JUNIOR_1", "JUNIOR_2", "SENIOR_1", "SENIOR_2", 
        "GRADUATE_STUDENT", "JOB_SEEKER", "EMPLOYED", "OTHER"
    ]] = None
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    ethnicity: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, max_length=40)
    phone: Optional[str] = Field(None, pattern=r'^1[3-9]\d{9}$')
    major: Optional[str] = Field(None, max_length=100)
    university: Optional[str] = Field(None, max_length=100)
    gender: Optional[Gender] = None
    age: Optional[int] = Field(None, ge=1, le=120)
    learning_stage: Optional[LearningStage] = None
    province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None
    interviewer_settings: Optional[InterviewerSettings] = None


class UserResponse(UserBase):
    """User response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    avatar_url: Optional[str] = None
    is_email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserRegister(UserCreate):
    """User registration schema"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ApiMessage(BaseModel):
    """Simple message response schema"""
    message: str


class EmailVerificationCodeCreate(BaseModel):
    """Create email verification code schema"""
    email: EmailStr


class EmailVerificationCodeVerify(BaseModel):
    """Verify email verification code schema"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirm schema"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema"""
    refresh: str


class WechatLoginRequest(BaseModel):
    """Wechat login request schema"""
    code: str


class UnifiedLoginRequest(BaseModel):
    """Unified login request (phone or email)"""
    phone: Optional[str] = Field(None, pattern=r'^1[3-9]\d{9}$')
    email: Optional[EmailStr] = None
    password: str

    def __init__(self, **data):
        super().__init__(**data)
        if not self.phone and not self.email:
            raise ValueError("Either phone or email must be provided")
