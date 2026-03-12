"""
JWT decode utilities.
Token *issuance* is owned by Omar (FR1 / auth router).
This module is used by the dependency layer to validate incoming tokens.
"""
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.
    Returns the payload dict on success.
    Raises InvalidTokenError on invalid / expired tokens.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def extract_user_id(payload: dict) -> int:
    """Pull user_id (stored as 'sub') from a decoded JWT payload."""
    sub = payload.get("sub")
    if sub is None:
        raise InvalidTokenError("Missing 'sub' claim in token")
    return int(sub)


def extract_roles(payload: dict) -> list[str]:
    """Pull roles list from a decoded JWT payload."""
    return payload.get("roles", [])
