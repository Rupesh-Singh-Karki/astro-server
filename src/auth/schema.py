from datetime import datetime, date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict

from src.auth.model import GenderEnum, MaritalStatusEnum


# ============================================================================
# User Schemas
# ============================================================================


class UserBase(BaseModel):
    """Base schema for User."""

    email: EmailStr
    is_email_verified: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Schema for creating a User."""

    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserBase):
    """Schema for reading a User."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# UserDetails Schemas
# ============================================================================


class UserDetailsBase(BaseModel):
    """Base schema for UserDetails."""

    full_name: str
    gender: GenderEnum
    marital_status: MaritalStatusEnum
    date_of_birth: date
    time_of_birth: time
    place_of_birth: str
    timezone: str

    model_config = ConfigDict(from_attributes=True)


class UserDetailsCreate(UserDetailsBase):
    """Schema for creating UserDetails."""

    user_id: UUID

    model_config = ConfigDict(from_attributes=True)


class UserDetailsRegister(UserDetailsBase):
    """Schema for registering UserDetails (user_id will be taken from authenticated user)."""

    model_config = ConfigDict(from_attributes=True)


class UserDetailsRead(UserDetailsBase):
    """Schema for reading UserDetails."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# User with Details (Nested)
# ============================================================================


class UserReadWithDetails(UserRead):
    """Schema for reading a User with nested UserDetails."""

    user_details: Optional[UserDetailsRead] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# OTPCode Schemas
# ============================================================================


class OTPCodeBase(BaseModel):
    """Base schema for OTPCode."""

    email: EmailStr
    otp: str
    expires_at: datetime
    attempts: int = 0
    is_used: bool = False

    model_config = ConfigDict(from_attributes=True)


class OTPCodeCreate(BaseModel):
    """Schema for creating an OTPCode."""

    email: EmailStr
    otp: str
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OTPCodeRead(OTPCodeBase):
    """Schema for reading an OTPCode."""

    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Auth Request/Response Schemas
# ============================================================================


class SendOTPRequest(BaseModel):
    """Schema for requesting OTP to be sent to email."""

    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class SendOTPResponse(BaseModel):
    """Schema for OTP send response."""

    message: str
    email: EmailStr
    expires_in_minutes: int

    model_config = ConfigDict(from_attributes=True)


class VerifyOTPRequest(BaseModel):
    """Schema for verifying OTP."""

    email: EmailStr
    otp: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str

    model_config = ConfigDict(from_attributes=True)
