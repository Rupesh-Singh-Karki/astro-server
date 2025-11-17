"""Tests for chat and astrology services."""

import pytest
from datetime import date, time
from uuid import uuid4
from typing import Any

from src.chat.services.chat_service import chat_service
from src.chat.services.astrology_service import astrology_service
from src.chat.model import MessageSenderEnum


@pytest.mark.asyncio
async def test_create_chat_session(db: Any) -> None:
    """Test creating a new chat session."""
    user_id = uuid4()
    title = "Test astrology question"

    session = await chat_service.create_session(db, user_id, title)

    assert session.id is not None
    assert session.user_id == user_id
    assert session.title == title
    assert session.created_at is not None


@pytest.mark.asyncio
async def test_get_chat_session(db: Any) -> None:
    """Test retrieving a chat session."""
    user_id = uuid4()
    title = "Test session"

    # Create session
    created_session = await chat_service.create_session(db, user_id, title)

    # Retrieve session
    retrieved_session = await chat_service.get_session(db, created_session.id, user_id)

    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.user_id == user_id
    assert retrieved_session.title == title


@pytest.mark.asyncio
async def test_get_session_wrong_user(db: Any) -> None:
    """Test retrieving a session with wrong user ID returns None."""
    user_id = uuid4()
    wrong_user_id = uuid4()

    # Create session for user_id
    session = await chat_service.create_session(db, user_id, "Test")

    # Try to retrieve with wrong user ID
    retrieved = await chat_service.get_session(db, session.id, wrong_user_id)

    assert retrieved is None


@pytest.mark.asyncio
async def test_add_message_to_session(db: Any) -> None:
    """Test adding messages to a chat session."""
    user_id = uuid4()

    # Create session
    session = await chat_service.create_session(db, user_id, "Test")

    # Add user message
    user_message = await chat_service.add_message(
        db, session.id, user_id, MessageSenderEnum.USER, "What is my career?"
    )

    assert user_message.id is not None
    assert user_message.session_id == session.id
    assert user_message.sender == MessageSenderEnum.USER
    assert user_message.message == "What is my career?"

    # Add AI message
    ai_message = await chat_service.add_message(
        db, session.id, user_id, MessageSenderEnum.AI, "Based on your chart..."
    )

    assert ai_message.sender == MessageSenderEnum.AI
    assert ai_message.user_id is None  # AI messages don't have user_id


@pytest.mark.asyncio
async def test_get_session_messages(db: Any) -> None:
    """Test retrieving all messages for a session."""
    user_id = uuid4()

    # Create session
    session = await chat_service.create_session(db, user_id, "Test")

    # Add messages
    await chat_service.add_message(
        db, session.id, user_id, MessageSenderEnum.USER, "Question 1"
    )
    await chat_service.add_message(
        db, session.id, user_id, MessageSenderEnum.AI, "Answer 1"
    )
    await chat_service.add_message(
        db, session.id, user_id, MessageSenderEnum.USER, "Question 2"
    )

    # Get all messages
    messages = await chat_service.get_session_messages(db, session.id, user_id)

    assert len(messages) == 3
    assert messages[0].sender == MessageSenderEnum.USER
    assert messages[1].sender == MessageSenderEnum.AI
    assert messages[2].sender == MessageSenderEnum.USER


@pytest.mark.asyncio
async def test_get_user_sessions(db: Any) -> None:
    """Test retrieving all sessions for a user."""
    user_id = uuid4()

    # Create multiple sessions
    session1 = await chat_service.create_session(db, user_id, "Session 1")
    session2 = await chat_service.create_session(db, user_id, "Session 2")
    session3 = await chat_service.create_session(db, user_id, "Session 3")

    # Get all user sessions
    sessions = await chat_service.get_user_sessions(db, user_id, limit=50)

    assert len(sessions) >= 3
    session_ids = [s.id for s in sessions]
    assert session1.id in session_ids
    assert session2.id in session_ids
    assert session3.id in session_ids


@pytest.mark.asyncio
async def test_get_user_sessions_limit(db: Any) -> None:
    """Test that get_user_sessions respects limit parameter."""
    user_id = uuid4()

    # Create 5 sessions
    for i in range(5):
        await chat_service.create_session(db, user_id, f"Session {i}")

    # Get with limit of 3
    sessions = await chat_service.get_user_sessions(db, user_id, limit=3)

    assert len(sessions) == 3


@pytest.mark.asyncio
async def test_update_session_title(db: Any) -> None:
    """Test updating a session title."""
    user_id = uuid4()

    # Create session
    session = await chat_service.create_session(db, user_id, "Old Title")

    # Update title
    updated = await chat_service.update_session_title(
        db, session.id, user_id, "New Title"
    )

    assert updated is not None
    assert updated.title == "New Title"


@pytest.mark.asyncio
async def test_delete_session(db: Any) -> None:
    """Test deleting a chat session."""
    user_id = uuid4()

    # Create session with messages
    session = await chat_service.create_session(db, user_id, "Test")
    await chat_service.add_message(
        db, session.id, user_id, MessageSenderEnum.USER, "Question"
    )

    # Delete session
    result = await chat_service.delete_session(db, session.id, user_id)

    assert result is True

    # Verify session is deleted
    deleted = await chat_service.get_session(db, session.id, user_id)
    assert deleted is None


def test_compute_kundli() -> None:
    """Test kundli computation with valid birth data."""
    birth_data = {
        "date_of_birth": date(1990, 5, 15),
        "time_of_birth": time(14, 30, 0),
        "place_of_birth": {"latitude": 19.0760, "longitude": 72.8777},
        "timezone": "Asia/Kolkata",
    }

    result = astrology_service.compute_kundli(birth_data)

    # Verify result structure
    assert isinstance(result, dict)
    assert "birth_details" in result

    # Verify birth details contain the data we passed
    birth_details = result["birth_details"]
    assert "year" in birth_details or "date" in birth_details
    # Just verify it returned some data
    assert len(result) > 0


def test_compute_kundli_with_different_location() -> None:
    """Test kundli computation with different location."""
    birth_data = {
        "date_of_birth": date(2004, 12, 27),
        "time_of_birth": time(10, 15, 0),
        "place_of_birth": {"latitude": 28.6139, "longitude": 77.2090},  # New Delhi
        "timezone": "Asia/Kolkata",
    }

    result = astrology_service.compute_kundli(birth_data)

    assert isinstance(result, dict)
    assert "birth_details" in result


def test_compute_kundli_invalid_place() -> None:
    """Test kundli computation with invalid place format."""
    birth_data = {
        "date_of_birth": date(1990, 5, 15),
        "time_of_birth": time(14, 30, 0),
        "place_of_birth": "Invalid String",  # Should be a dict
        "timezone": "Asia/Kolkata",
    }

    with pytest.raises(ValueError, match="place_of_birth must be a dict"):
        astrology_service.compute_kundli(birth_data)


def test_compute_kundli_missing_coordinates() -> None:
    """Test kundli computation with missing coordinates."""
    birth_data = {
        "date_of_birth": date(1990, 5, 15),
        "time_of_birth": time(14, 30, 0),
        "place_of_birth": {},  # Empty dict
        "timezone": "Asia/Kolkata",
    }

    # Should use default 0, 0 coordinates
    result = astrology_service.compute_kundli(birth_data)
    assert isinstance(result, dict)
