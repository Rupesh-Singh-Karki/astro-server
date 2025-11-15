from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.model import User
from src.auth.schema import UserRead, TokenResponse
from src.auth.services.otp_service import otp_service
from src.auth.services.email_service import email_service
from src.utils.jwt import create_access_token
from src.utils.logger import logger
from src.config import settings

log = logger(__name__)


class AuthService:
    """Service for user authentication and management."""

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email address."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, email: str) -> User:
        """Create a new user."""
        user = User(email=email, is_email_verified=False)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        log.info(f"Created new user with email: {email}")
        return user

    async def verify_user_email(self, db: AsyncSession, user: User) -> User:
        """Mark user's email as verified."""
        user.is_email_verified = True
        await db.commit()
        await db.refresh(user)
        log.info(f"Verified email for user: {user.email}")
        return user

    async def send_otp(
        self, db: AsyncSession, email: str
    ) -> tuple[bool, Optional[str], Optional[int]]:
        """
        Send OTP to the user's email.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Tuple of (success: bool, error_message: Optional[str], expires_in_minutes: Optional[int])
        """
        try:
            # Create OTP
            otp_record, plain_otp = await otp_service.create_otp(db, email)

            # Send OTP via email
            email_sent = await email_service.send_otp_email(
                to_email=email,
                otp=plain_otp,
                expires_in_minutes=settings.otp_expire_minutes,
            )

            if not email_sent:
                return False, "Failed to send OTP email", None

            return True, None, settings.otp_expire_minutes

        except Exception as e:
            log.error(f"Error sending OTP: {str(e)}")
            return False, "An error occurred while sending OTP", None

    async def verify_otp_and_authenticate(
        self, db: AsyncSession, email: str, otp: str
    ) -> tuple[bool, Optional[str], Optional[TokenResponse]]:
        """
        Verify OTP and authenticate user.

        Args:
            db: Database session
            email: User's email address
            otp: OTP to verify

        Returns:
            Tuple of (success: bool, error_message: Optional[str], token_response: Optional[TokenResponse])
        """
        # Verify OTP
        is_valid, error_message = await otp_service.verify_otp(db, email, otp)

        if not is_valid:
            return False, error_message, None

        # Get or create user
        user = await self.get_user_by_email(db, email)
        if not user:
            user = await self.create_user(db, email)

        # Verify user's email if not already verified
        if not user.is_email_verified:
            user = await self.verify_user_email(db, user)

        # Generate access token
        access_token = create_access_token(identity=str(user.id))

        # Create token response
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes
            * 60,  # Convert to seconds
            user=UserRead.model_validate(user),
        )

        log.info(f"User authenticated successfully: {user.email}")
        return True, None, token_response


# Singleton instance
auth_service = AuthService()
