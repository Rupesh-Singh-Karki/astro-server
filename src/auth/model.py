from datetime import datetime, date, time
from enum import Enum as PyEnum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Date, Time, Enum as SQLEnum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.chat.model import ChatSession


class GenderEnum(str, PyEnum):
    """Gender enum for user details."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class MaritalStatusEnum(str, PyEnum):
    """Marital status enum for user details."""

    SINGLE = "single"
    MARRIED = "married"


class User(SQLModel, table=True):  # type: ignore[call-arg]
    """User model."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(
        sa_column=Column(String(255), unique=True, nullable=False, index=True)
    )
    is_email_verified: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False, onupdate=datetime.utcnow),
    )

    # Relationships - use string references to avoid circular imports
    user_details: Optional["UserDetails"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    chat_sessions: List["ChatSession"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class UserDetails(SQLModel, table=True):  # type: ignore[call-arg]
    """User details model representing the user_details table."""

    __tablename__ = "user_details"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", unique=True, index=True)
    full_name: str = Field(sa_column=Column(String(255), nullable=False))
    gender: GenderEnum = Field(sa_column=Column(SQLEnum(GenderEnum), nullable=False))
    marital_status: MaritalStatusEnum = Field(
        sa_column=Column(SQLEnum(MaritalStatusEnum), nullable=False)
    )
    date_of_birth: date = Field(sa_column=Column(Date, nullable=False))
    time_of_birth: time = Field(sa_column=Column(Time, nullable=False))
    place_of_birth: str = Field(sa_column=Column(String(255), nullable=False))
    timezone: str = Field(sa_column=Column(String(100), nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False, onupdate=datetime.utcnow),
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="user_details")


class OTPCode(SQLModel, table=True):  # type: ignore[call-arg]
    """OTP code model representing the otp_codes table."""

    __tablename__ = "otp_codes"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(sa_column=Column(String(255), nullable=False, index=True))
    otp: str = Field(sa_column=Column(String(255), nullable=False))
    expires_at: datetime = Field(sa_column=Column(DateTime, nullable=False))
    attempts: int = Field(default=0)
    is_used: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False)
    )
