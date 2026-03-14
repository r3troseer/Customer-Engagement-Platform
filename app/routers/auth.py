"""
FR1 — User Roles & Access Control (Omar).
Registration, login, JWT issuance, user management, sessions, security logs.
"""
import uuid

from fastapi import APIRouter, Request, status

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.auth import (
    PasswordChange,
    RoleAssignByName,
    RoleOut,
    SecurityLogOut,
    SessionOut,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
    UserRoleOut,
    UserUpdate,
)
from app.schemas.common import MessageResponse, PaginatedResponse
import app.services.auth_service as svc

router = APIRouter()


# ── FR-1.1: Registration ─────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="FR-1.1 Register a new user",
)
async def register(body: UserRegister, db: DBSession):
    user = await svc.register_user(db, body.model_dump())
    return UserOut.model_validate(user)


# ── FR-1.1: Login ────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse, summary="FR-1.1 Login and get JWT")
async def login(body: UserLogin, db: DBSession, request: Request):
    user = await svc.authenticate_user(db, body.email, body.password)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    roles = await svc.get_user_roles(db, user.id)
    token, expires_in = svc.create_access_token(user.id, roles)

    # Create session
    await svc.create_login_session(
        db, user.id,
        session_token=uuid.uuid4().hex,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Security log
    await svc.log_security_event(
        db, user.id, "login_success",
        ip_address=request.client.host if request.client else None,
    )

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user_id=user.id,
        roles=roles,
    )


# ── FR-1.2: User CRUD ────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut, summary="FR-1.2 Get current user profile")
async def get_me(db: DBSession, current_user: CurrentUser):
    user = await svc.get_user_by_id(db, current_user["user_id"])
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut, summary="FR-1.2 Update current user profile")
async def update_me(body: UserUpdate, db: DBSession, current_user: CurrentUser):
    user = await svc.get_user_by_id(db, current_user["user_id"])
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/users", response_model=list[UserOut], summary="FR-1.3 List users (admin)")
async def list_users(db: DBSession, current_user: AdminUser, pagination: Pagination):
    users = await svc.list_users(db, offset=pagination.offset, limit=pagination.page_size)
    return [UserOut.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=UserOut, summary="FR-1.3 Get user by ID (admin)")
async def get_user(user_id: int, db: DBSession, current_user: AdminUser):
    user = await svc.get_user_by_id(db, user_id)
    if not user:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User", user_id)
    return UserOut.model_validate(user)


# ── FR-1.3: Password ─────────────────────────────────────────────────────────

@router.post("/change-password", response_model=MessageResponse, summary="FR-1.3 Change password")
async def change_password(body: PasswordChange, db: DBSession, current_user: CurrentUser):
    user = await svc.get_user_by_id(db, current_user["user_id"])
    if not user or not svc.verify_password(body.current_password, user.password_hash):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = svc.hash_password(body.new_password)
    await db.flush()
    return MessageResponse(message="Password changed successfully")


# ── FR-1.3: Role assignment ──────────────────────────────────────────────────

@router.post(
    "/users/{user_id}/roles",
    response_model=UserRoleOut,
    status_code=status.HTTP_201_CREATED,
    summary="FR-1.3 Assign a role to a user (admin)",
)
async def assign_role(user_id: int, body: RoleAssignByName, db: DBSession, current_user: AdminUser):
    user_role = await svc.assign_role(db, user_id, body.role_name)
    role_name = user_role.role.role_name  # type: ignore[union-attr]
    return UserRoleOut(user_id=user_role.user_id, role_name=role_name, assigned_at=user_role.assigned_at)


# ── FR-1.4: Roles ──────────��─────────────────────────────────────────────────

@router.get("/roles", response_model=list[RoleOut], summary="FR-1.4 List all roles")
async def list_roles(db: DBSession, current_user: AdminUser):
    from sqlalchemy import select
    from app.models.auth import Role
    result = await db.execute(select(Role))
    return [RoleOut.model_validate(r) for r in result.scalars().all()]


# ── FR-1.5: Security logs ────────────────────────────────────────────────────

@router.get("/security-logs", response_model=list[SecurityLogOut], summary="FR-1.5 Security audit logs")
async def list_security_logs(db: DBSession, current_user: AdminUser, pagination: Pagination):
    from sqlalchemy import select
    from app.models.auth import SecurityLog
    result = await db.execute(
        select(SecurityLog)
        .order_by(SecurityLog.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [SecurityLogOut.model_validate(s) for s in result.scalars().all()]