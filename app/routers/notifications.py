"""
FR12 — Notification & Alert System
Endpoints for reading notifications and managing delivery preferences.
Notification *creation* is handled internally by notification_service —
there is no public "send" endpoint.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update

from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.models.notifications import Notification, NotificationPreference
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.notifications import NotificationOut, PreferencesOut, PreferencesUpdate

router = APIRouter()


# ── FR-12.1: Notification inbox ──────────────────────────────────────────────

@router.get("/", response_model=PaginatedResponse[NotificationOut], summary="FR-12.1 My notifications (unread first)")
async def list_notifications(db: DBSession, current_user: CurrentUser, pagination: Pagination):
    user_id = current_user["user_id"]
    base = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
    )
    from sqlalchemy import func, select as sa_select
    total = (await db.execute(sa_select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.offset(pagination.offset).limit(pagination.page_size))).scalars().all()
    return PaginatedResponse.create(
        items=[NotificationOut.model_validate(n) for n in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut, summary="FR-12.1 Mark notification as read")
async def mark_read(notification_id: int, db: DBSession, current_user: CurrentUser):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user["user_id"],
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notification)
    return NotificationOut.model_validate(notification)


@router.patch("/read-all", response_model=MessageResponse, summary="FR-12.1 Mark all notifications as read")
async def mark_all_read(db: DBSession, current_user: CurrentUser) -> MessageResponse:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user["user_id"], Notification.is_read.is_(False))
        .values(is_read=True, read_at=now)
    )
    await db.commit()
    return MessageResponse(message="All notifications marked as read")


@router.delete("/{notification_id}", response_model=MessageResponse, summary="Delete a notification")
async def delete_notification(notification_id: int, db: DBSession, current_user: CurrentUser):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user["user_id"],
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notification)
    await db.commit()
    return MessageResponse(message="Notification deleted")


# ── FR-12.4: Notification preferences ────────────────────────────────────────

@router.get("/preferences", response_model=PreferencesOut, summary="FR-12.4 Get my notification preferences")
async def get_preferences(db: DBSession, current_user: CurrentUser):
    user_id = current_user["user_id"]
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if prefs is None:
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return PreferencesOut.model_validate(prefs)


@router.patch("/preferences", response_model=PreferencesOut, summary="FR-12.4 Update notification preferences")
async def update_preferences(body: PreferencesUpdate, db: DBSession, current_user: CurrentUser):
    user_id = current_user["user_id"]
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if prefs is None:
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)
    return PreferencesOut.model_validate(prefs)
