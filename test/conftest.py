"""
Pytest configuration and fixtures for testing.
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlmodel import SQLModel

from src.auth.model import User, UserDetails, OTPCode  # noqa: F401
from src.chat.model import ChatSession, ChatMessage  # noqa: F401
from src.config import settings


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def disable_bypass_mode() -> Generator[None, None, None]:
    """Disable OTP bypass mode for all tests."""
    # Store original value
    original_bypass = settings.bypass_otp_validation
    # Set to False for tests
    settings.bypass_otp_validation = False
    yield
    # Restore original value after tests
    settings.bypass_otp_validation = original_bypass


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    """Create test database engine."""
    return create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )


@pytest_asyncio.fixture(scope="function")
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    Tables are created before the test and dropped after.
    """
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
