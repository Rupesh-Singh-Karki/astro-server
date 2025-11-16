from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schema import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    TokenResponse,
    UserRead,
    UserDetailsRegister,
    UserDetailsRead,
)
from src.auth.services.auth_service import auth_service
from src.auth.services.dependencies import get_current_user
from src.auth.model import User
from src.utils.db import get_db
from src.utils.logger import logger

log = logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Send OTP to email",
    description="Send a one-time password (OTP) to the specified email address for authentication.",
)
async def send_otp(
    request: SendOTPRequest,  # intead of async def send_otp(email: str):
    db: AsyncSession = Depends(get_db),
) -> SendOTPResponse:  # yaha humne response define kar diya
    """
    Send OTP to the user's email address.

    - **email**: Email address to send OTP to

    Returns a confirmation message with expiration time.
    """
    success, error_message, expires_in_minutes = await auth_service.send_otp(
        db, request.email
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message or "Failed to send OTP",
        )

    return SendOTPResponse(
        message="OTP sent successfully",
        email=request.email,
        expires_in_minutes=expires_in_minutes or 10,
    )


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and authenticate",
    description="Verify the OTP sent to the email and return an access token if valid.",
)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Verify OTP and authenticate the user.

    - **email**: Email address that received the OTP
    - **otp**: One-time password received via email

    Returns an access token and user information upon successful verification.
    """
    success, error_message, token_response = (
        await auth_service.verify_otp_and_authenticate(db, request.email, request.otp)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message or "Invalid OTP",
        )

    if token_response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication token",
        )

    return token_response


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Get current authenticated user's information.

    Requires valid JWT token in Authorization header.
    """
    return UserRead.model_validate(current_user)


@router.post(
    "/logout",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout the current user (token revocation handled client-side).",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Logout the current user.

    Note: Since we're using stateless JWT tokens, actual logout should be handled
    client-side by removing the token. This endpoint serves as a logout confirmation.

    For production, consider implementing token blacklisting or short-lived tokens
    with refresh tokens for better security.
    """
    log.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}


@router.get(
    "/verify-token",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Verify token validity",
    description="Verify if the provided JWT token is valid and not expired.",
)
async def verify_token(
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Verify that the current JWT token is valid.

    Requires valid JWT token in Authorization header.
    """
    return {
        "message": "Token is valid",
        "user_id": str(current_user.id),
        "email": current_user.email,
    }


@router.post(
    "/register-details",
    response_model=UserDetailsRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register user details",
    description="Register detailed information for the authenticated user.",
)
async def register_user_details(
    user_details: UserDetailsRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserDetailsRead:
    """
    Register user details for the authenticated user.

    - **full_name**: Full name of the user
    - **gender**: Gender (male/female/other)
    - **marital_status**: Marital status (single/married)
    - **date_of_birth**: Date of birth
    - **time_of_birth**: Time of birth
    - **place_of_birth**: Place of birth
    - **timezone**: Timezone

    Requires valid JWT token in Authorization header.
    """
    # Check if user details already exist
    existing_details = await auth_service.get_user_details(db, current_user.id)
    if existing_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User details already exist. Use the update endpoint to modify them.",
        )

    # Create user details
    created_details = await auth_service.create_user_details(
        db=db,
        user_id=current_user.id,
        full_name=user_details.full_name,
        gender=user_details.gender,
        marital_status=user_details.marital_status,
        date_of_birth=user_details.date_of_birth,
        time_of_birth=user_details.time_of_birth,
        place_of_birth=user_details.place_of_birth,
        timezone=user_details.timezone,
    )

    log.info(f"User details registered for user: {current_user.email}")
    return UserDetailsRead.model_validate(created_details)


@router.get(
    "/user-details",
    response_model=UserDetailsRead,
    status_code=status.HTTP_200_OK,
    summary="Get user details",
    description="Get detailed information for the authenticated user.",
)
async def get_user_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserDetailsRead:
    """
    Get user details for the authenticated user.

    Requires valid JWT token in Authorization header.
    """
    user_details = await auth_service.get_user_details(db, current_user.id)
    if not user_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User details not found. Please register your details first.",
        )

    return UserDetailsRead.model_validate(user_details)
