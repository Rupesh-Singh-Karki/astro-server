import secrets
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.sql import desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.model import OTPCode
from src.config import settings
from src.utils.logger import logger

log = logger(__name__)


class OTPService:
    """Service for OTP generation, validation, and management."""

    def __init__(self) -> None:
        self.otp_length = settings.otp_length
        self.otp_expire_minutes = settings.otp_expire_minutes
        self.otp_max_attempts = settings.otp_max_attempts

    def _generate_otp(self) -> str:
        """Generate a random numeric OTP."""
        digits = string.digits
        otp = "".join(secrets.choice(digits) for _ in range(self.otp_length))
        return otp

    def _hash_otp(self, otp: str) -> str:
        """Hash OTP using SHA256."""
        return hashlib.sha256(otp.encode()).hexdigest()

    def _verify_otp_hash(self, plain_otp: str, hashed_otp: str) -> bool:
        """Verify OTP against hashed version."""
        return hashlib.sha256(plain_otp.encode()).hexdigest() == hashed_otp

    async def create_otp(self, db: AsyncSession, email: str) -> tuple[OTPCode, str]:
        """
        Create a new OTP for the given email.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Tuple of (OTPCode object, plain OTP string)
        """
        # Invalidate all previous OTPs for this email
        await self._invalidate_previous_otps(db, email)

        # Generate new OTP
        plain_otp = self._generate_otp()
        hashed_otp = self._hash_otp(plain_otp)
        expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expire_minutes)

        # Create OTP record
        otp_record = OTPCode(
            email=email,
            otp=hashed_otp,
            expires_at=expires_at,
            attempts=0,
            is_used=False,
        )

        db.add(otp_record)
        await db.commit()
        await db.refresh(otp_record)

        log.info(f"Created OTP for email: {email}")
        return otp_record, plain_otp

    async def verify_otp(
        self, db: AsyncSession, email: str, plain_otp: str
    ) -> tuple[bool, Optional[str]]:
        """
        Verify OTP for the given email.

        Args:
            db: Database session
            email: User's email address
            plain_otp: Plain text OTP to verify

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        # Get the most recent unused OTP for this email
        stmt = (
            select(OTPCode)
            .where(
                and_(
                    OTPCode.email == email,
                    OTPCode.is_used == False,  # noqa: E712
                )
            )
            .order_by(desc(OTPCode.created_at))
        )
        result = await db.execute(stmt)
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            return False, "No valid OTP found for this email"

        # Check if OTP has expired
        if datetime.utcnow() > otp_record.expires_at:
            otp_record.is_used = True
            await db.commit()
            return False, "OTP has expired"

        # Check if max attempts exceeded
        if otp_record.attempts >= self.otp_max_attempts:
            otp_record.is_used = True
            await db.commit()
            return False, "Maximum verification attempts exceeded"

        # Increment attempts
        otp_record.attempts += 1
        await db.commit()

        # Verify OTP
        is_valid = self._verify_otp_hash(plain_otp, otp_record.otp)

        if is_valid:
            # Mark OTP as used
            otp_record.is_used = True
            await db.commit()
            log.info(f"OTP verified successfully for email: {email}")
            return True, None
        else:
            remaining_attempts = self.otp_max_attempts - otp_record.attempts
            if remaining_attempts > 0:
                return False, f"Invalid OTP. {remaining_attempts} attempts remaining"
            else:
                otp_record.is_used = True
                await db.commit()
                return False, "Invalid OTP. Maximum attempts exceeded"

    async def _invalidate_previous_otps(self, db: AsyncSession, email: str) -> None:
        """Mark all previous unused OTPs for this email as used."""
        stmt = select(OTPCode).where(
            and_(
                OTPCode.email == email,
                OTPCode.is_used == False,  # noqa: E712
            )
        )
        result = await db.execute(stmt)
        otp_records = result.scalars().all()

        for otp_record in otp_records:
            otp_record.is_used = True

        await db.commit()
        log.debug(f"Invalidated {len(otp_records)} previous OTPs for email: {email}")

    async def cleanup_expired_otps(self, db: AsyncSession) -> int:
        """
        Delete expired OTPs from the database.

        Args:
            db: Database session

        Returns:
            Number of deleted OTP records
        """
        stmt = select(OTPCode).where(OTPCode.expires_at < datetime.utcnow())
        result = await db.execute(stmt)
        expired_otps = result.scalars().all()

        count = len(expired_otps)
        for otp in expired_otps:
            await db.delete(otp)

        await db.commit()
        log.info(f"Cleaned up {count} expired OTP records")
        return count


# Singleton instance
otp_service = OTPService()
