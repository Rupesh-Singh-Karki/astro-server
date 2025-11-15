"""
Tests for authentication services.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.services.otp_service import otp_service
from src.auth.services.auth_service import auth_service


@pytest.mark.asyncio
async def test_generate_otp(db: AsyncSession) -> None:
    """Test OTP generation."""
    email = "test@example.com"
    otp_record, plain_otp = await otp_service.create_otp(db, email)

    assert otp_record.email == email
    assert len(plain_otp) == 6
    assert plain_otp.isdigit()
    assert otp_record.is_used is False
    assert otp_record.attempts == 0


@pytest.mark.asyncio
async def test_verify_valid_otp(db: AsyncSession) -> None:
    """Test OTP verification with valid code."""
    email = "test@example.com"
    otp_record, plain_otp = await otp_service.create_otp(db, email)

    is_valid, error_message = await otp_service.verify_otp(db, email, plain_otp)

    assert is_valid is True
    assert error_message is None


@pytest.mark.asyncio
async def test_verify_invalid_otp(db: AsyncSession) -> None:
    """Test OTP verification with invalid code."""
    email = "test@example.com"
    otp_record, plain_otp = await otp_service.create_otp(db, email)

    is_valid, error_message = await otp_service.verify_otp(db, email, "000000")

    assert is_valid is False
    assert error_message is not None


@pytest.mark.asyncio
async def test_verify_expired_otp(db: AsyncSession) -> None:
    """Test OTP verification with expired code."""
    email = "test@example.com"
    otp_record, plain_otp = await otp_service.create_otp(db, email)

    # Manually set expiration to past
    otp_record.expires_at = datetime.utcnow() - timedelta(minutes=1)
    await db.commit()

    is_valid, error_message = await otp_service.verify_otp(db, email, plain_otp)

    assert is_valid is False
    assert error_message is not None
    assert "expired" in error_message.lower()


@pytest.mark.asyncio
async def test_otp_max_attempts(db: AsyncSession) -> None:
    """Test OTP verification with max attempts exceeded."""
    email = "test@example.com"
    otp_record, plain_otp = await otp_service.create_otp(db, email)

    # Try with wrong OTP 5 times (max attempts)
    for i in range(5):
        await otp_service.verify_otp(db, email, "000000")

    # Should now be locked - the OTP was marked as used after max attempts
    is_valid, error_message = await otp_service.verify_otp(db, email, plain_otp)

    assert is_valid is False
    # After max attempts, the OTP is invalidated, so we get "no valid otp" message
    assert error_message is not None


@pytest.mark.asyncio
async def test_create_user(db: AsyncSession) -> None:
    """Test user creation."""
    email = "newuser@example.com"
    user = await auth_service.create_user(db, email)

    assert user.email == email
    assert user.is_email_verified is False
    assert user.id is not None


@pytest.mark.asyncio
async def test_get_user_by_email(db: AsyncSession) -> None:
    """Test retrieving user by email."""
    email = "test@example.com"
    created_user = await auth_service.create_user(db, email)

    retrieved_user = await auth_service.get_user_by_email(db, email)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == email


@pytest.mark.asyncio
async def test_verify_user_email(db: AsyncSession) -> None:
    """Test email verification."""
    email = "test@example.com"
    user = await auth_service.create_user(db, email)

    verified_user = await auth_service.verify_user_email(db, user)

    assert verified_user.is_email_verified is True


@pytest.mark.asyncio
async def test_invalidate_previous_otps(db: AsyncSession) -> None:
    """Test that previous OTPs are invalidated when new one is created."""
    email = "test@example.com"

    # Create first OTP
    otp_record1, plain_otp1 = await otp_service.create_otp(db, email)

    # Create second OTP (this should invalidate the first)
    otp_record2, plain_otp2 = await otp_service.create_otp(db, email)

    # First OTP should not be valid anymore
    is_valid, error_message = await otp_service.verify_otp(db, email, plain_otp1)

    assert is_valid is False
    # The error can be either "invalid otp" (if it tries to verify against the new OTP)
    # or "no valid otp" (if the old one was marked as used)
    assert error_message is not None
    assert isinstance(error_message, str)
