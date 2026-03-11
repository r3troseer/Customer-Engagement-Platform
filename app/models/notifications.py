"""
Notification & audit models.
notifications, notification_preferences, notification_logs — owned by Pius (FR12).
audit_logs — owned by Sunny (FR13); model lives here because FR12 and FR13 share this file.
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import DeliveryChannelEnum, DeliveryStatusEnum, NotificationTypeEnum


class Notification(Base, TimestampMixin):
    """FR-12.1: In-app notification records."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(NotificationTypeEnum, nullable=False)
    related_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationPreference(Base, TimestampMixin):
    """FR-12.4: Per-user notification channel + category preferences."""
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    compliance_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reward_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    report_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    challenge_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NotificationLog(Base, TimestampMixin):
    """FR-12.3: Delivery attempt record per channel per notification."""
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notification_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False)
    delivery_channel: Mapped[str] = mapped_column(DeliveryChannelEnum, nullable=False)
    delivery_status: Mapped[str] = mapped_column(DeliveryStatusEnum, nullable=False, default="queued")
    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """
    FR-13.1 / FR-13.4: Immutable audit trail.
    Write-only — no updated_at. Sunny's audit_service.py writes to this table.
    Uses JSONB before/after state for rich diff capture.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    # e.g. "supplier.document.approved", "leaderboard.reset", "tokens.bonus_awarded"
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
