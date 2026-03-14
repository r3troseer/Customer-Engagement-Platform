"""
FR13 — Audit and Governance
API router for audit logs, change history, and approvals.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.dependencies.db import DBSession
from app.schemas.audit import (
    ApprovalCreate,
    ApprovalOut,
    ApprovalUpdate,
    AuditLogCreate,
    AuditLogOut,
    ChangeHistoryCreate,
    ChangeHistoryOut,
    ChangeHistoryUpdate,
)
from app.services.audit_service import ApprovalService, AuditLogService, ChangeHistoryService

router = APIRouter(prefix="/audit", tags=["FR13 — Audit & Governance"])


# ── Audit Logs ────────────────────────────────────────────────────────────────

@router.post(
    "/logs",
    response_model=AuditLogOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_audit_log(payload: AuditLogCreate, db: DBSession) -> AuditLogOut:
    return await AuditLogService.create(db, payload.model_dump())


@router.get(
    "/logs",
    response_model=list[AuditLogOut],
)
async def list_audit_logs(
    db: DBSession,
    user_id: int | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    location_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AuditLogOut]:
    return await AuditLogService.list(
        db,
        user_id=user_id,
        organization_id=organization_id,
        location_id=location_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/logs/{audit_log_id}",
    response_model=AuditLogOut,
)
async def get_audit_log(audit_log_id: int, db: DBSession) -> AuditLogOut:
    return await AuditLogService.get_by_id(db, audit_log_id)


@router.delete(
    "/logs/{audit_log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_audit_log(audit_log_id: int, db: DBSession) -> Response:
    await AuditLogService.delete(db, audit_log_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Change History ────────────────────────────────────────────────────────────

@router.post(
    "/changes",
    response_model=ChangeHistoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_change_history(payload: ChangeHistoryCreate, db: DBSession) -> ChangeHistoryOut:
    return await ChangeHistoryService.create(db, payload.model_dump())


@router.get(
    "/changes",
    response_model=list[ChangeHistoryOut],
)
async def list_change_history(
    db: DBSession,
    user_id: int | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    field_name: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ChangeHistoryOut]:
    return await ChangeHistoryService.list(
        db,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/changes/{change_id}",
    response_model=ChangeHistoryOut,
)
async def get_change_history(change_id: int, db: DBSession) -> ChangeHistoryOut:
    return await ChangeHistoryService.get_by_id(db, change_id)


@router.patch(
    "/changes/{change_id}",
    response_model=ChangeHistoryOut,
)
async def update_change_history(
    change_id: int,
    payload: ChangeHistoryUpdate,
    db: DBSession,
) -> ChangeHistoryOut:
    return await ChangeHistoryService.update(
        db,
        change_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/changes/{change_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_change_history(change_id: int, db: DBSession) -> Response:
    await ChangeHistoryService.delete(db, change_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Approvals ─────────────────────────────────────────────────────────────────

@router.post(
    "/approvals",
    response_model=ApprovalOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_approval(payload: ApprovalCreate, db: DBSession) -> ApprovalOut:
    return await ApprovalService.create(db, payload.model_dump())


@router.get(
    "/approvals",
    response_model=list[ApprovalOut],
)
async def list_approvals(
    db: DBSession,
    approval_type: str | None = Query(default=None),
    related_type: str | None = Query(default=None),
    related_id: int | None = Query(default=None),
    requested_by: int | None = Query(default=None),
    approved_by: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ApprovalOut]:
    return await ApprovalService.list(
        db,
        approval_type=approval_type,
        related_type=related_type,
        related_id=related_id,
        requested_by=requested_by,
        approved_by=approved_by,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/approvals/{approval_id}",
    response_model=ApprovalOut,
)
async def get_approval(approval_id: int, db: DBSession) -> ApprovalOut:
    return await ApprovalService.get_by_id(db, approval_id)


@router.patch(
    "/approvals/{approval_id}",
    response_model=ApprovalOut,
)
async def update_approval(
    approval_id: int,
    payload: ApprovalUpdate,
    db: DBSession,
) -> ApprovalOut:
    return await ApprovalService.update(
        db,
        approval_id,
        payload.model_dump(exclude_unset=True),
    )


@router.delete(
    "/approvals/{approval_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_approval(approval_id: int, db: DBSession) -> Response:
    await ApprovalService.delete(db, approval_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
