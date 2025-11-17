"""Chat schemas."""

from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.chat.model import MessageSenderEnum


# ============================================================================
# ChatSession Schemas
# ============================================================================


class ChatSessionBase(BaseModel):
    """Base schema for ChatSession."""

    title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreate(BaseModel):
    """Schema for creating a ChatSession."""

    user_id: UUID
    title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChatSessionRead(ChatSessionBase):
    """Schema for reading a ChatSession."""

    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ChatMessage Schemas
# ============================================================================


class ChatMessageBase(BaseModel):
    """Base schema for ChatMessage."""

    sender: MessageSenderEnum
    message: str

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    """Schema for creating a ChatMessage."""

    session_id: UUID
    user_id: Optional[UUID] = None
    sender: MessageSenderEnum
    message: str

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(ChatMessageBase):
    """Schema for reading a ChatMessage."""

    id: UUID
    session_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ChatSession with Messages (Nested)
# ============================================================================


class ChatSessionReadWithMessages(ChatSessionRead):
    """Schema for reading a ChatSession with nested ChatMessages."""

    chat_messages: list[ChatMessageRead] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Kundli / Astrology Schemas
# ============================================================================


class LocationCoordinates(BaseModel):
    """Location coordinates for birth chart calculation."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    timezone: str = Field(
        ..., description="Timezone (e.g., 'Asia/Kolkata', 'America/New_York')"
    )


class KundliRequest(BaseModel):
    """Request schema for kundli computation and astrology chat."""

    birth_year: int = Field(..., gt=1900, lt=2100, description="Birth year")
    birth_month: int = Field(..., ge=1, le=12, description="Birth month (1-12)")
    birth_day: int = Field(..., ge=1, le=31, description="Birth day")
    birth_hour: int = Field(..., ge=0, le=23, description="Birth hour (0-23)")
    birth_minute: int = Field(..., ge=0, le=59, description="Birth minute")
    location: LocationCoordinates = Field(..., description="Birth location coordinates")
    question: str = Field(..., min_length=1, description="Question for the astrologer")
    session_id: Optional[UUID] = Field(
        None, description="Optional session ID to continue existing chat"
    )


class AstrologyResponse(BaseModel):
    """Response schema for astrology chat."""

    session_id: UUID = Field(..., description="ID of the chat session")
    answer: str = Field(..., description="Answer from the astrologer")
    kundli: Dict[str, Any] = Field(..., description="Computed kundli data")


class ChatMessageResponse(BaseModel):
    """Response schema for a chat message."""

    id: UUID
    session_id: UUID
    sender: MessageSenderEnum
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Response schema for a chat session."""

    id: UUID
    title: Optional[str]
    created_at: datetime
    message_count: Optional[int] = None

    class Config:
        from_attributes = True


class ChatSessionWithMessagesResponse(BaseModel):
    """Response schema for a chat session with all messages."""

    id: UUID
    title: Optional[str]
    created_at: datetime
    messages: list[ChatMessageResponse]

    class Config:
        from_attributes = True
