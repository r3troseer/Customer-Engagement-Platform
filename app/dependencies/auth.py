"""
Auth dependency layer.
get_current_user decodes JWTs issued by Omar's auth router (FR1).
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token, extract_roles, extract_user_id
from app.models.auth import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    """
    Decode the Bearer JWT, load the full User row from the DB, and return
    an enriched user context dict.
    Shape: {"user_id": int, "roles": list[str], "email": str,
            "first_name": str, "last_name": str, "status": str}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = extract_user_id(payload)
        roles = extract_roles(payload)
    except (InvalidTokenError, ValueError):
        raise credentials_exception

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None or user.status != "active":
        raise credentials_exception

    return {
        "user_id": user.id,
        "roles": roles,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "status": user.status,
    }


def require_role(*allowed_roles: str):
    """
    Factory that returns a dependency enforcing at least one of the given roles.
    Usage:  Depends(require_role("admin", "platform_admin"))
    """
    async def checker(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        if not any(r in current_user["roles"] for r in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return checker


# Convenience type aliases for routers
CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_role("admin", "platform_admin", "restaurant_admin"))]
ManagerUser = Annotated[dict, Depends(require_role("admin", "platform_admin", "restaurant_admin", "restaurant_manager"))]
