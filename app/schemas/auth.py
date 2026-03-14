"""
FR1 — Auth schemas (Omar).
User registration, login, sessions, roles.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Registration / Login ────────────────────────────────────────────────���─────

class UserRegister(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone: str | None = Field(None, max_length=30)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    roles: list[str]


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User output ───────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    mfa_enabled: bool
    email_verified: bool
    status: str
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


# ── Password ──────────────────────────────────────────────────────────────────

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# ── Roles ─────────────────────────────────────────────────────────────────────

class RoleOut(BaseModel):
    id: int
    role_name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleAssign(BaseModel):
    user_id: int
    role_id: int


class RoleAssignByName(BaseModel):
    role_name: str


class UserRoleOut(BaseModel):
    user_id: int
    role_name: str
    assigned_at: datetime

    model_config = {"from_attributes": True}


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionOut(BaseModel):
    id: int
    user_id: int
    ip_address: str | None = None
    user_agent: str | None = None
    login_time: datetime
    logout_time: datetime | None = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Security logs ─────────────────────────────────────────────────────────────

class SecurityLogOut(BaseModel):
    id: int
    user_id: int | None = None
    event_type: str
    ip_address: str | None = None
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}