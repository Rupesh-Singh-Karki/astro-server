from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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
