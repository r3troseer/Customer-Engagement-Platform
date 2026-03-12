"""
FR12 — Notification & Alert System
Endpoints for reading notifications and managing delivery preferences.
Notification *creation* is handled internally by notification_service —
there is no public "send" endpoint.
"""
from datetime import datetime

from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.notifications import NotificationOut, PreferencesOut, PreferencesUpdate

router = APIRouter()

# ── Stub helpers ──────────────────────────────────────────────────────────────

_STUB_NOTIFICATION = NotificationOut(
    id=1,
    user_id=1,
    organization_id=1,
    title="Token Reward Earned",
    message="You earned 50 GreenTokens for logging 8 hours on 2024-06-03.",
    notification_type="token_reward",
    related_type="work_log",
    related_id=1,
    is_read=False,
    read_at=None,
    created_at=datetime(2024, 6, 3, 16, 5, 0),
)

_STUB_PREFERENCES = PreferencesOut(
    id=1,
    user_id=1,
    email_enabled=True,
    push_enabled=True,
    in_app_enabled=True,
    compliance_alerts_enabled=True,
    reward_notifications_enabled=True,
    report_notifications_enabled=True,
    challenge_notifications_enabled=True,
    updated_at=datetime(2024, 1, 15, 9, 0, 0),
)


# ── FR-12.1: Notification inbox ──────────────────────────────────────────────

@router.get("/", response_model=PaginatedResponse[NotificationOut], summary="FR-12.1 My notifications (unread first)")
async def list_notifications(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: query Notification WHERE user_id=current AND order by is_read ASC, created_at DESC
    return PaginatedResponse.create(items=[_STUB_NOTIFICATION], total=1, page=pagination.page, page_size=pagination.page_size)


@router.patch("/{notification_id}/read", response_model=NotificationOut, summary="FR-12.1 Mark notification as read")
async def mark_read(notification_id: int, db: DBSession, current_user: CurrentUser):
    # TODO: set is_read=True, read_at=now() on Notification row
    return NotificationOut(**{
        **_STUB_NOTIFICATION.model_dump(),
        "id": notification_id,
        "is_read": True,
        "read_at": datetime.utcnow(),
    })


@router.patch("/read-all", response_model=MessageResponse, summary="FR-12.1 Mark all notifications as read")
async def mark_all_read(db: DBSession, current_user: CurrentUser) -> MessageResponse:
    # TODO: bulk update all unread Notification rows for current user
    return MessageResponse(message="All notifications marked as read")


@router.delete("/{notification_id}", response_model=MessageResponse, summary="Delete a notification")
async def delete_notification(notification_id: int, db: DBSession, current_user: CurrentUser):
    # TODO: hard delete Notification row (owned by current user only)
    return MessageResponse(message="Notification deleted", detail=f"notification_id={notification_id}")


# ── FR-12.4: Notification preferences ────────────────────────────────────────

@router.get("/preferences", response_model=PreferencesOut, summary="FR-12.4 Get my notification preferences")
async def get_preferences(db: DBSession, current_user: CurrentUser):
    # TODO: query NotificationPreference WHERE user_id=current
    # Create default row if not exists (upsert pattern)
    return _STUB_PREFERENCES


@router.patch("/preferences", response_model=PreferencesOut, summary="FR-12.4 Update notification preferences")
async def update_preferences(body: PreferencesUpdate, db: DBSession, current_user: CurrentUser):
    # TODO: upsert NotificationPreference for current user
    updated = _STUB_PREFERENCES.model_dump()
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    updated.update(patch)
    updated["updated_at"] = datetime.utcnow()
    return PreferencesOut(**updated)
