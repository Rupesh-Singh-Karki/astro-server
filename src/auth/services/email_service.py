import asyncio
from typing import Any, Dict

from mailersend import MailerSendClient, EmailBuilder

from src.config import settings
from src.utils.logger import logger

log = logger(__name__)


class EmailService:
    """Service for sending emails via MailerSend."""

    def __init__(self) -> None:
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

        # Configure MailerSend
        if not settings.mailersend_api_key:
            log.warning(
                "MAILERSEND_API_KEY not set - email sending will fail in production"
            )
            self.mailer = None
            return

        self.mailer = MailerSendClient(api_key=settings.mailersend_api_key)
        log.info("Email service initialized with MailerSend")

    def _create_otp_email_html(self, otp: str, expires_in_minutes: int) -> str:
        """Create HTML content for OTP email."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4a90e2; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; border-radius: 5px; }}
                .otp-code {{ font-size: 32px; font-weight: bold; color: #4a90e2; 
                            text-align: center; padding: 20px; background-color: white; 
                            border-radius: 5px; letter-spacing: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{self.from_name}</h1>
                </div>
                <div class="content">
                    <h2>Your Verification Code</h2>
                    <p>Hello,</p>
                    <p>You have requested to sign in to your account. Please use the following verification code:</p>
                    <div class="otp-code">{otp}</div>
                    <p>This code will expire in <strong>{expires_in_minutes} minutes</strong>.</p>
                    <p>If you did not request this code, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_otp_email_text(self, otp: str, expires_in_minutes: int) -> str:
        """Create plain text content for OTP email."""
        return f"""
        {self.from_name}
        
        Your Verification Code
        
        Hello,
        
        You have requested to sign in to your account. Please use the following verification code:
        
        {otp}
        
        This code will expire in {expires_in_minutes} minutes.
        
        If you did not request this code, please ignore this email.
        
        This is an automated message, please do not reply.
        """

    async def send_otp_email(
        self, to_email: str, otp: str, expires_in_minutes: int
    ) -> bool:
        """
        Send OTP email to the specified address using MailerSend.

        Args:
            to_email: Recipient email address
            otp: One-time password code
            expires_in_minutes: OTP expiration time in minutes

        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.mailersend_api_key or not self.mailer:
            log.error("Cannot send email: MAILERSEND_API_KEY not configured")
            return False

        try:
            html_content = self._create_otp_email_html(otp, expires_in_minutes)
            text_content = self._create_otp_email_text(otp, expires_in_minutes)

            # Send email in thread pool to avoid blocking
            def _send_mailersend() -> Dict[str, Any]:
                email = (
                    EmailBuilder()
                    .from_email(self.from_email, self.from_name)
                    .to(to_email)
                    .subject(f"Your Verification Code - {self.from_name}")
                    .html(html_content)
                    .text(text_content)
                    .build()
                )

                assert self.mailer is not None
                response = self.mailer.emails.send(email)
                return {
                    "id": getattr(response, "message_id", "unknown"),
                    "success": True,
                }

            result = await asyncio.wait_for(
                asyncio.to_thread(_send_mailersend), timeout=10.0
            )

            log.info(
                f"OTP email sent successfully via MailerSend to {to_email} (ID: {result.get('id', 'unknown')})"
            )
            return True

        except asyncio.TimeoutError:
            log.error("MailerSend email sending timed out after 10 seconds")
            return False
        except Exception as e:
            log.error(f"MailerSend email error: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()
