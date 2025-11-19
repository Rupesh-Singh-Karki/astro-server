import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import settings
from src.utils.logger import logger

log = logger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self) -> None:
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

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
        Send OTP email to the specified address.

        Args:
            to_email: Recipient email address
            otp: One-time password code
            expires_in_minutes: OTP expiration time in minutes

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Your Verification Code - {self.from_name}"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Create both plain text and HTML versions
            text_content = self._create_otp_email_text(otp, expires_in_minutes)
            html_content = self._create_otp_email_html(otp, expires_in_minutes)

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            msg.attach(part1)
            msg.attach(part2)

            # Try STARTTLS first (port 587), then SSL (port 465) as fallback
            def _send_smtp() -> None:
                last_error = None
                
                # Try port 587 with STARTTLS
                try:
                    log.info(f"Attempting SMTP connection to {self.smtp_host}:{self.smtp_port}")
                    with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                        server.starttls()
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(msg)
                    log.info("Email sent successfully via STARTTLS (port 587)")
                    return
                except Exception as e:
                    last_error = e
                    log.warning(f"STARTTLS (port 587) failed: {str(e)}, trying SSL...")
                
                # Fallback to port 465 with SSL
                try:
                    log.info(f"Attempting SMTP_SSL connection to {self.smtp_host}:465")
                    with smtplib.SMTP_SSL(self.smtp_host, 465, timeout=10) as server:
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(msg)
                    log.info("Email sent successfully via SSL (port 465)")
                    return
                except Exception as e:
                    log.error(f"SSL (port 465) also failed: {str(e)}")
                    if last_error:
                        raise last_error
                    raise e

            await asyncio.wait_for(
                asyncio.to_thread(_send_smtp), timeout=20.0  # 20 second total timeout
            )

            log.info(f"OTP email sent successfully to {to_email}")
            return True

        except asyncio.TimeoutError:
            log.error("Email sending timed out after 20 seconds")
            return False
        except smtplib.SMTPAuthenticationError:
            log.error("SMTP authentication failed. Check username and password.")
            return False
        except smtplib.SMTPException as e:
            log.error(f"SMTP error occurred while sending email: {str(e)}")
            return False
        except OSError as e:
            log.error(f"Network error sending email: {str(e)}. Check firewall/network restrictions.")
            return False
        except Exception as e:
            log.error(f"Unexpected error sending email: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()
