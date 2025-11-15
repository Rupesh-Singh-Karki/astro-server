#!/usr/bin/env python3
"""
Quick verification script to test authentication setup.
Run this after configuring .env to verify everything is working.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import logger
from src.config import settings
import smtplib

log = logger(__name__)


def check_env_vars() -> bool:
    """Check if required environment variables are set."""
    log.info("Checking environment variables...")

    required_vars = [
        ("DB_URI", settings.db_uri),
        ("JWT_SECRET_KEY", settings.jwt_secret_key),
        ("SMTP_USERNAME", settings.smtp_username),
        ("SMTP_PASSWORD", settings.smtp_password),
        ("SMTP_FROM_EMAIL", settings.smtp_from_email),
    ]

    all_set = True
    for var_name, var_value in required_vars:
        if not var_value or var_value == "...":
            log.error(f"❌ {var_name} is not set or invalid")
            all_set = False
        else:
            # Show partial value for verification
            if "PASSWORD" in var_name or "SECRET" in var_name:
                display_value = (
                    f"{var_value[:4]}...{var_value[-4:]}"
                    if len(var_value) > 8
                    else "***"
                )
            else:
                display_value = var_value[:50]
            log.info(f"✅ {var_name}: {display_value}")

    return all_set


async def check_database() -> bool:
    """Check database connection."""
    log.info("Checking database connection...")

    try:
        from src.utils.db import async_engine

        async with async_engine.connect():
            log.info("✅ Database connection successful")
            return True

    except Exception as e:
        log.error(f"❌ Database connection failed: {str(e)}")
        return False


def check_smtp() -> bool:
    """Check SMTP connection."""
    log.info("Checking SMTP connection...")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            log.info("✅ SMTP connection successful")
            return True

    except smtplib.SMTPAuthenticationError:
        log.error("❌ SMTP authentication failed - check username/password")
        return False
    except Exception as e:
        log.error(f"❌ SMTP connection failed: {str(e)}")
        return False


async def check_models() -> bool:
    """Check if models can be imported."""
    log.info("Checking models...")

    try:
        from src.auth.model import User, UserDetails, OTPCode  # noqa: F401
        from src.chat.model import ChatSession, ChatMessage  # noqa: F401

        log.info("✅ All models imported successfully")
        return True

    except Exception as e:
        log.error(f"❌ Model import failed: {str(e)}")
        return False


async def check_services() -> bool:
    """Check if services can be imported."""
    log.info("Checking services...")

    try:
        from src.auth.services.auth_service import auth_service  # noqa: F401
        from src.auth.services.otp_service import otp_service  # noqa: F401
        from src.auth.services.email_service import email_service  # noqa: F401
        from src.auth.services.dependencies import get_current_user  # noqa: F401

        log.info("✅ All services imported successfully")
        return True

    except Exception as e:
        log.error(f"❌ Service import failed: {str(e)}")
        return False


async def check_routes() -> bool:
    """Check if routes can be imported."""
    log.info("Checking routes...")

    try:
        from src.auth.routes.auth_routes import router

        # Count routes
        route_count = len(router.routes)
        log.info(f"✅ Auth router loaded with {route_count} routes")
        return True

    except Exception as e:
        log.error(f"❌ Route import failed: {str(e)}")
        return False


async def main() -> None:
    """Run all verification checks."""
    log.info("=" * 60)
    log.info("Authentication Setup Verification")
    log.info("=" * 60)

    results = []

    # Run checks
    results.append(("Environment Variables", check_env_vars()))
    results.append(("Models", await check_models()))
    results.append(("Services", await check_services()))
    results.append(("Routes", await check_routes()))
    results.append(("Database Connection", await check_database()))
    results.append(("SMTP Connection", check_smtp()))

    # Summary
    log.info("=" * 60)
    log.info("Verification Summary")
    log.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        log.info(f"{status}: {check_name}")

    log.info("=" * 60)
    log.info(f"Results: {passed}/{total} checks passed")
    log.info("=" * 60)

    if passed == total:
        log.info("🎉 All checks passed! Your authentication system is ready.")
        log.info("")
        log.info("Next steps:")
        log.info("1. Run: python src/main.py")
        log.info("2. Visit: http://localhost:8000/docs")
        log.info("3. Test: POST /auth/send-otp")
        sys.exit(0)
    else:
        log.error("⚠️  Some checks failed. Please review the errors above.")
        log.info("")
        log.info("Common fixes:")
        log.info("- Environment variables: Copy .env.example to .env and configure")
        log.info("- Database: Ensure PostgreSQL is running and DB exists")
        log.info("- SMTP: Use Gmail App Password, not regular password")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("\nVerification cancelled by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
