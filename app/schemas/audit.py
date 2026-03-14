from datetime import datetime

from pydantic import BaseModel


# ── Audit Logs ────────────────────────────────────────────────────────────────

class AuditLogCreate(BaseModel):
    user_id: int | None = None
    organization_id: int | None = None
    location_id: int | None = None
    action: str
    entity_type: str
    entity_id: int | None = None
    description: str | None = None
    ip_address: str | None = None
    created_at: datetime


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    organization_id: int | None
    location_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Change History ────────────────────────────────────────────────────────────

class ChangeHistoryCreate(BaseModel):
    user_id: int | None = None
    entity_type: str
    entity_id: int
    field_name: str
    old_value: str | None = None
    new_value: str | None = None
    changed_at: datetime


class ChangeHistoryUpdate(BaseModel):
    old_value: str | None = None
    new_value: str | None = None
    changed_at: datetime | None = None


class ChangeHistoryOut(BaseModel):
    id: int
    user_id: int | None
    entity_type: str
    entity_id: int
    field_name: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Approvals ─────────────────────────────────────────────────────────────────

class ApprovalCreate(BaseModel):
    approval_type: str
    related_type: str
    related_id: int
    requested_by: int | None = None
    approved_by: int | None = None
    status: str = "pending"
    request_notes: str | None = None
    decision_notes: str | None = None
    requested_at: datetime
    decided_at: datetime | None = None


class ApprovalUpdate(BaseModel):
    approved_by: int | None = None
    status: str | None = None
    request_notes: str | None = None
    decision_notes: str | None = None
    decided_at: datetime | None = None


class ApprovalOut(BaseModel):
    id: int
    approval_type: str
    related_type: str
    related_id: int
    requested_by: int | None
    approved_by: int | None
    status: str
    request_notes: str | None
    decision_notes: str | None
    requested_at: datetime
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
