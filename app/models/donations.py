"""
Donation models — owned by Sunny (FR9).
Tables: donation_causes, donations, donation_impacts
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import CauseTypeEnum, DonationStatusEnum, ImpactTypeEnum


class DonationCause(Base, TimestampMixin):
    __tablename__ = "donation_causes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    cause_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cause_type: Mapped[str] = mapped_column(CauseTypeEnum, nullable=False)
    partner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Donation(Base, TimestampMixin):
    __tablename__ = "donations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    cause_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("donation_causes.id", ondelete="RESTRICT"), nullable=False)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    wallet_transaction_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("wallet_transactions.id", ondelete="SET NULL"), nullable=True)
    token_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    # Absorbs donation_attributions
    attributed_tokens: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    attributed_impact_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    # Absorbs donation_conversions
    cash_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    conversion_rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=1, nullable=False)
    conversion_currency: Mapped[str] = mapped_column(String(10), default="GBP", nullable=False)
    donation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(DonationStatusEnum, nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class DonationImpact(Base, TimestampMixin):
    __tablename__ = "donation_impacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    donation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("donations.id", ondelete="CASCADE"), nullable=False)
    impact_type: Mapped[str] = mapped_column(ImpactTypeEnum, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
