"""
FR12 — Notification & Alert System
Request/response schemas for notification inbox and delivery preferences.
"""
from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int
    organization_id: int | None
    title: str
    message: str
    notification_type: str
    related_type: str | None
    related_id: int | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PreferencesOut(BaseModel):
    id: int
    user_id: int
    email_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    compliance_alerts_enabled: bool
    reward_notifications_enabled: bool
    report_notifications_enabled: bool
    challenge_notifications_enabled: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class PreferencesUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    in_app_enabled: bool | None = None
    compliance_alerts_enabled: bool | None = None
    reward_notifications_enabled: bool | None = None
    report_notifications_enabled: bool | None = None
    challenge_notifications_enabled: bool | None = None
