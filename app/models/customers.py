"""
Customer models — owned by Omar (FR7).
Tables: customers, customer_visits, mobility_logs, challenges, challenge_participation
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import ChallengeStatusEnum, ChallengeTypeEnum, CustomerStatusEnum, ParticipationStatusEnum


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    preferred_location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(CustomerStatusEnum, nullable=False, default="active")
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    allow_step_tracking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sustainability_interests: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Absorbs customer_impact_summary
    total_tokens_earned: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_tokens_donated: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_distance_km: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_co2_offset: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    # Seed: user_id=4 (Liam Customer), active


class CustomerVisit(Base, TimestampMixin):
    __tablename__ = "customer_visits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    visit_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    spend_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    tokens_earned: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)


class MobilityLog(Base, TimestampMixin):
    __tablename__ = "mobility_logs"
    __table_args__ = (UniqueConstraint("customer_id", "activity_date", "provider"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    step_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    calories_burned: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_earned: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)


class Challenge(Base, TimestampMixin):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    challenge_type: Mapped[str] = mapped_column(ChallengeTypeEnum, nullable=False)
    target_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reward_tokens: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(ChallengeStatusEnum, nullable=False, default="draft")
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class ChallengeParticipation(Base, TimestampMixin):
    __tablename__ = "challenge_participation"
    __table_args__ = (UniqueConstraint("challenge_id", "customer_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    challenge_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    progress_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reward_granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(ParticipationStatusEnum, nullable=False, default="joined")
