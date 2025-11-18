"""Chat service for managing chat sessions and messages."""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.chat.model import ChatSession, ChatMessage, MessageSenderEnum
from src.utils.logger import logger

log = logger(__name__)


class ChatService:
    """Service for managing chat sessions and messages."""

    async def create_session(
        self, db: AsyncSession, user_id: UUID, title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        log.info(f"Created chat session {session.id} for user {user_id}")
        return session

    async def get_session(
        self, db: AsyncSession, session_id: UUID, user_id: UUID
    ) -> Optional[ChatSession]:
        """Get a chat session by ID, ensuring it belongs to the user."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.chat_messages))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self, db: AsyncSession, user_id: UUID, limit: int = 50
    ) -> List[ChatSession]:
        """Get all chat sessions for a user with message count."""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.chat_messages))
            .order_by(desc(ChatSession.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        sender: MessageSenderEnum,
        message: str,
    ) -> ChatMessage:
        """Add a message to a chat session."""
        chat_message = ChatMessage(
            session_id=session_id,
            user_id=user_id if sender == MessageSenderEnum.USER else None,
            sender=sender,
            message=message,
        )
        db.add(chat_message)
        await db.commit()
        await db.refresh(chat_message)
        log.debug(f"Added {sender.value} message to session {session_id}")
        return chat_message

    async def get_session_messages(
        self, db: AsyncSession, session_id: UUID, user_id: UUID
    ) -> List[ChatMessage]:
        """Get all messages in a chat session."""
        # First verify the session belongs to the user
        session = await self.get_session(db, session_id, user_id)
        if not session:
            return []

        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(asc(ChatMessage.created_at))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update_session_title(
        self, db: AsyncSession, session_id: UUID, user_id: UUID, title: str
    ) -> Optional[ChatSession]:
        """Update the title of a chat session."""
        session = await self.get_session(db, session_id, user_id)
        if not session:
            return None

        session.title = title
        await db.commit()
        await db.refresh(session)
        log.info(f"Updated title for session {session_id}")
        return session

    async def delete_session(
        self, db: AsyncSession, session_id: UUID, user_id: UUID
    ) -> bool:
        """Delete a chat session and all its messages."""
        session = await self.get_session(db, session_id, user_id)
        if not session:
            return False

        await db.delete(session)
        await db.commit()
        log.info(f"Deleted chat session {session_id}")
        return True


# Singleton instance
chat_service = ChatService()
