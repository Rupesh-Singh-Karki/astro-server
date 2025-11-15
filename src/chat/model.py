from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from src.auth.model import User


class MessageSenderEnum(str, PyEnum):
    """Message sender enum for chat messages."""

    USER = "user"
    AI = "ai"


class ChatSession(SQLModel, table=True):  # type: ignore[call-arg]
    """Chat session model representing the chat_sessions table."""

    __tablename__ = "chat_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: Optional[str] = Field(
        default=None, sa_column=Column(String(500), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False)
    )

    # Relationships - use string references to avoid circular imports
    user: Optional["User"] = Relationship(back_populates="chat_sessions")
    chat_messages: List["ChatMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class ChatMessage(SQLModel, table=True):  # type: ignore[call-arg]
    """Chat message model representing the chat_messages table."""

    __tablename__ = "chat_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_sessions.id", index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
    sender: MessageSenderEnum = Field(
        sa_column=Column(SQLEnum(MessageSenderEnum), nullable=False)
    )
    message: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False)
    )

    # Relationships
    session: Optional["ChatSession"] = Relationship(back_populates="chat_messages")
    user: Optional["User"] = Relationship()
