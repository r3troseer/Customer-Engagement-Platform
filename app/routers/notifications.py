"""
FR12 — Notification & Alert System
Endpoints for reading notifications and managing delivery preferences.
Notification *creation* is handled internally by notification_service —
there is no public "send" endpoint.
"""
from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import MessageResponse

router = APIRouter()


# ── FR-12.1: Notification inbox ──────────────────────────────────────────────

@router.get("/", summary="FR-12.1 My notifications (unread first)")
async def list_notifications(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    # TODO: query Notification WHERE user_id=current AND order by is_read ASC, created_at DESC
    raise NotImplementedError


@router.patch("/{notification_id}/read", summary="FR-12.1 Mark notification as read")
async def mark_read(notification_id: int, db: DBSession, current_user: CurrentUser):
    # TODO: set is_read=True, read_at=now() on Notification row
    raise NotImplementedError


@router.patch("/read-all", summary="FR-12.1 Mark all notifications as read")
async def mark_all_read(db: DBSession, current_user: CurrentUser) -> MessageResponse:
    # TODO: bulk update all unread Notification rows for current user
    raise NotImplementedError


@router.delete("/{notification_id}", summary="Delete a notification")
async def delete_notification(notification_id: int, db: DBSession, current_user: CurrentUser):
    # TODO: hard delete Notification row (owned by current user only)
    raise NotImplementedError


# ── FR-12.4: Notification preferences ────────────────────────────────────────

@router.get("/preferences", summary="FR-12.4 Get my notification preferences")
async def get_preferences(db: DBSession, current_user: CurrentUser):
    # TODO: query NotificationPreference WHERE user_id=current
    # Create default row if not exists (upsert pattern)
    raise NotImplementedError


@router.patch("/preferences", summary="FR-12.4 Update notification preferences")
async def update_preferences(db: DBSession, current_user: CurrentUser):
    # TODO: upsert NotificationPreference for current user
    raise NotImplementedError
