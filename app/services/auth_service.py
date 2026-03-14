"""
FR1 — Auth service layer (Omar).
User registration, login, JWT issuance, password hashing, sessions, security logs.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.auth import LoginSession, Role, SecurityLog, User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, roles: list[str]) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


async def register_user(db: AsyncSession, data: dict) -> User:
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == data["email"]))
    if existing.scalar_one_or_none():
        from app.core.exceptions import ConflictError
        raise ConflictError(f"Email {data['email']} already registered")

    user = User(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        phone=data.get("phone"),
        password_hash=hash_password(data["password"]),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Assign default "customer" role if it exists
    role_result = await db.execute(select(Role).where(Role.role_name == "customer"))
    role = role_result.scalar_one_or_none()
    if role:
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            assigned_at=datetime.now(timezone.utc),
        )
        db.add(user_role)
        await db.flush()

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    # Update last_login_at
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()
    return user


async def get_user_roles(db: AsyncSession, user_id: int) -> list[str]:
    result = await db.execute(
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    return [row[0] for row in result.all()]


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession, offset: int = 0, limit: int = 50) -> list[User]:
    result = await db.execute(select(User).offset(offset).limit(limit))
    return list(result.scalars().all())


async def create_login_session(
    db: AsyncSession, user_id: int, session_token: str,
    ip_address: str | None = None, user_agent: str | None = None,
) -> LoginSession:
    session = LoginSession(
        user_id=user_id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        login_time=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()
    return session


async def assign_role(db: AsyncSession, user_id: int, role_name: str) -> UserRole:
    """
    Assign a named role to a user. Idempotent — returns the existing UserRole if the
    assignment already exists. Raises 404 if the user or role_name does not exist.
    """
    from app.core.exceptions import NotFoundError

    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise NotFoundError(f"User {user_id} not found")

    role_result = await db.execute(select(Role).where(Role.role_name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise NotFoundError(f"Role '{role_name}' not found")

    existing = await db.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.id)
    )
    user_role = existing.scalar_one_or_none()
    if user_role:
        return user_role

    user_role = UserRole(
        user_id=user_id,
        role_id=role.id,
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(user_role)
    await db.flush()
    return user_role


async def log_security_event(
    db: AsyncSession, user_id: int | None, event_type: str,
    ip_address: str | None = None, description: str | None = None,
) -> SecurityLog:
    log = SecurityLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        description=description,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    return log