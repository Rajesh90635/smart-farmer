"""
JWT strategy: short-lived access tokens (role + subject claims), verified on
every request via the FastAPI dependency in app/core/current_user.py.

Refresh-token issuance/rotation and the real login endpoint (OTP verification
for farmers, password verification for staff/admin roles) belong to the
Auth module — a later phase. This file only provides the encode/decode
primitives plus a development-only token issuer so protected endpoints are
testable now.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


class TokenError(Exception):
    pass


def create_access_token(*, subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_signing_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_signing_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc
