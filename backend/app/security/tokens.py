import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.core.config import Settings
from app.models.base import utc_now

REFRESH_TOKEN_BYTES = 48


class TokenValidationError(Exception):
    pass


def create_access_token(user_id: UUID, settings: Settings) -> tuple[str, int]:
    expires_in = settings.jwt_access_token_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, settings.jwt_secret_key.get_secret_value(), algorithm="HS256")
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=["HS256"],
        )
        if payload.get("type") != "access":
            raise TokenValidationError
        return UUID(str(payload["sub"]))
    except (InvalidTokenError, KeyError, ValueError) as error:
        raise TokenValidationError from error


def create_refresh_token(settings: Settings) -> tuple[str, str, datetime]:
    """Return the raw token, its stored hash and its naive UTC expiry."""
    token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    expires_at = utc_now() + timedelta(days=settings.jwt_refresh_token_days)
    return token, hash_refresh_token(token), expires_at


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_ip_address(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()
