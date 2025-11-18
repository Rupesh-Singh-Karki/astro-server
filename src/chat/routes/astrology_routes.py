"""Astrology chat routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.chat.model import MessageSenderEnum
from src.chat.schema import (
    KundliRequest,
    AstrologyResponse,
    ChatSessionResponse,
    ChatSessionWithMessagesResponse,
)
from src.chat.services.astrology_service import astrology_service
from src.chat.services.chat_service import chat_service
from src.chat.services.llm_client import llm_client
from src.auth.services.dependencies import get_current_verified_user
from src.utils.db import get_db
from src.auth.model import User
from src.utils.logger import logger

log = logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/astrologer",
    response_model=AstrologyResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Vedic Astrologer",
    description="Compute Vedic astrology kundli and get insights from an AI astrologer based on birth details",
)
async def astrologer_chat(
    birth_details: KundliRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> AstrologyResponse:
    """
    Chat with a Vedic astrologer AI.

    This endpoint:
    1. Creates or retrieves a chat session
    2. Computes a Vedic astrology kundli (birth chart) based on provided birth details
    3. Saves the user's question as a chat message
    4. Sends the kundli data along with your question to an AI astrologer
    5. Saves the AI response as a chat message
    6. Returns insights and answers based on authentic Vedic astrology calculations

    Args:
        birth_details: Birth details including date, time, location coordinates, question, and optional session_id
        current_user: Authenticated user
        db: Database session

    Returns:
        AstrologyResponse with session_id, answer, and complete kundli data

    Raises:
        HTTPException: If kundli computation fails or LLM service is unavailable
    """
    try:
        # Get or create chat session
        if birth_details.session_id:
            session = await chat_service.get_session(
                db, birth_details.session_id, current_user.id
            )
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {birth_details.session_id} not found or access denied",
                )
            log.info(f"Using existing session {session.id}")
        else:
            # Create new session with title from first question
            title = (
                birth_details.question[:50] + "..."
                if len(birth_details.question) > 50
                else birth_details.question
            )
            session = await chat_service.create_session(
                db, current_user.id, title=title
            )
            log.info(f"Created new session {session.id}")

        # Save user's question as a chat message
        await chat_service.add_message(
            db=db,
            session_id=session.id,
            user_id=current_user.id,
            sender=MessageSenderEnum.USER,
            message=birth_details.question,
        )

        # Compute kundli using jyotishyamitra
        log.info(
            f"Computing kundli for birth date {birth_details.birth_year}-{birth_details.birth_month}-{birth_details.birth_day}"
        )

        # Convert birth details to format expected by astrology service
        from datetime import date, time

        birth_data = {
            "date_of_birth": date(
                birth_details.birth_year,
                birth_details.birth_month,
                birth_details.birth_day,
            ),
            "time_of_birth": time(birth_details.birth_hour, birth_details.birth_minute),
            "place_of_birth": {
                "latitude": birth_details.location.latitude,
                "longitude": birth_details.location.longitude,
            },
            "timezone": birth_details.location.timezone,
        }

        kundli_data = astrology_service.compute_kundli(birth_data)

        # Get response from LLM
        log.info("Getting astrology insights from LLM")
        answer = await llm_client.ask(kundli_data, birth_details.question)

        # Save AI response as a chat message
        await chat_service.add_message(
            db=db,
            session_id=session.id,
            user_id=current_user.id,
            sender=MessageSenderEnum.AI,
            message=answer,
        )

        return AstrologyResponse(
            session_id=session.id,
            answer=answer,
            kundli=kundli_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        log.error(f"Invalid input data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid birth details: {str(e)}",
        )
    except Exception as e:
        log.error(f"Error processing astrology request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process astrology request",
        )


@router.get(
    "/sessions",
    response_model=list[ChatSessionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get User's Chat Sessions",
    description="Retrieve all chat sessions for the authenticated user",
)
async def get_user_sessions(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
) -> list[ChatSessionResponse]:
    """
    Get all chat sessions for the authenticated user.

    Args:
        current_user: Authenticated user
        db: Database session
        limit: Maximum number of sessions to return

    Returns:
        List of chat sessions with basic info
    """
    sessions = await chat_service.get_user_sessions(db, current_user.id, limit)
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            message_count=len(s.chat_messages) if s.chat_messages else 0,
        )
        for s in sessions
    ]


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionWithMessagesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Chat Session with Messages",
    description="Retrieve a specific chat session with all its messages",
)
async def get_session_with_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionWithMessagesResponse:
    """
    Get a specific chat session with all messages.

    Args:
        session_id: ID of the chat session
        current_user: Authenticated user
        db: Database session

    Returns:
        Chat session with all messages

    Raises:
        HTTPException: If session not found or access denied
    """
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or access denied",
        )

    return ChatSessionWithMessagesResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        messages=[
            {
                "id": m.id,
                "session_id": m.session_id,
                "sender": m.sender,
                "message": m.message,
                "created_at": m.created_at,
            }
            for m in session.chat_messages
        ],
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Chat Session",
    description="Delete a chat session and all its messages",
)
async def delete_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a specific chat session and all its messages.

    Args:
        session_id: ID of the chat session to delete
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If session not found or access denied
    """
    deleted = await chat_service.delete_session(db, session_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or access denied",
        )
    log.info(f"User {current_user.id} deleted session {session_id}")


@router.delete(
    "/sessions/{session_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Chat Message",
    description="Delete a specific message from a chat session",
)
async def delete_chat_message(
    session_id: UUID,
    message_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a specific message from a chat session.

    Args:
        session_id: ID of the chat session
        message_id: ID of the message to delete
        current_user: Authenticated user
        db: Database session

    Raises:
        HTTPException: If session/message not found or access denied
    """
    # Verify session belongs to user
    session = await chat_service.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found or access denied",
        )

    # Delete the message
    deleted = await chat_service.delete_message(
        db, message_id, session_id, current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found in session {session_id}",
        )
    log.info(
        f"User {current_user.id} deleted message {message_id} from session {session_id}"
    )
