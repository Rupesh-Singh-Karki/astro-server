import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
import jwt
from src.utils.jwt import (
    create_access_token,
    decode_token,
    revoke_jti,
    BLACKLIST,
    ACCESS_TOKEN_EXPIRE_HOURS,
)


def test_create_access_token() -> None:
    with (
        patch("src.utils.jwt.datetime") as mock_datetime,
        patch("src.utils.jwt._make_jti") as mock_jti,
        patch("src.utils.jwt.JWT_SECRET", "secret"),
        patch("src.utils.jwt.JWT_ALGORITHM", "HS256"),
        patch("src.config.settings") as mock_settings,
    ):

        mock_settings.jwt_access_token_expire_minutes = 60

        # Set to past date to avoid immature signature
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_jti.return_value = "test-jti"

        token = create_access_token("test-identity")

        # Decode to verify
        payload = jwt.decode(
            token,
            "secret",
            algorithms=["HS256"],
            options={"verify_iat": False, "verify_exp": False},
        )
        assert payload["sub"] == "test-identity"
        assert payload["jti"] == "test-jti"
        assert payload["iat"] == int(mock_now.timestamp())
        expected_exp = int(
            (mock_now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).timestamp()
        )
        assert payload["exp"] == expected_exp


def test_decode_token_valid() -> None:
    with (
        patch("src.utils.jwt.JWT_SECRET", "secret"),
        patch("src.utils.jwt.JWT_ALGORITHM", "HS256"),
    ):

        # Add exp to future
        future = datetime(2026, 1, 1, 12, 0, 0)
        payload = {"sub": "test", "jti": "jti123", "exp": int(future.timestamp())}
        token = jwt.encode(payload, "secret", algorithm="HS256")

        decoded = decode_token(token)
        assert decoded["sub"] == "test"
        assert decoded["jti"] == "jti123"


def test_decode_token_revoked() -> None:
    with (
        patch("src.utils.jwt.JWT_SECRET", "secret"),
        patch("src.utils.jwt.JWT_ALGORITHM", "HS256"),
    ):

        future = datetime(2026, 1, 1, 12, 0, 0)
        payload = {"sub": "test", "jti": "revoked-jti", "exp": int(future.timestamp())}
        token = jwt.encode(payload, "secret", algorithm="HS256")

        BLACKLIST.add("revoked-jti")

        with pytest.raises(jwt.InvalidTokenError):
            decode_token(token)

        BLACKLIST.clear()


def test_decode_token_invalid() -> None:
    with (
        patch("src.utils.jwt.JWT_SECRET", "secret"),
        patch("src.utils.jwt.JWT_ALGORITHM", "HS256"),
    ):

        # Invalid token
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("invalid-token")


def test_revoke_jti() -> None:
    jti = "test-jti"
    assert jti not in BLACKLIST
    revoke_jti(jti)
    assert jti in BLACKLIST
    BLACKLIST.clear()
