"""
Audit and governance models — owned by Sunny (FR13).
Tables:
- audit_logs
- change_history
- approvals
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import ApprovalStatusEnum, ApprovalTypeEnum


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChangeHistory(Base, TimestampMixin):
    __tablename__ = "change_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    approval_type: Mapped[str] = mapped_column(ApprovalTypeEnum, nullable=False)
    related_type: Mapped[str] = mapped_column(String(100), nullable=False)
    related_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    requested_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(ApprovalStatusEnum, nullable=False, default="pending")
    request_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

