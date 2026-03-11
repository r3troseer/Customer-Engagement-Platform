"""
Workforce models — owned by Pius (FR6).
Tables: work_logs, leaderboard_snapshots, leaderboard_entries, redemptions
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    LeaderboardStatusEnum,
    LeaderboardTypeEnum,
    RedemptionActorEnum,
    RedemptionStatusEnum,
)


class WorkLog(Base, TimestampMixin):
    """FR-6.1 / FR-6.2: Employee work hours + sustainability activity logs."""
    __tablename__ = "work_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_in_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hours_worked: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    activity_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # FR-6.2: sustainability participation flag
    sustainability_initiative: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    initiative_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Tokens awarded for this log entry (calculated by leaderboard_service)
    tokens_awarded: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    logged_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class LeaderboardSnapshot(Base, TimestampMixin):
    """FR-6.5 / FR-6.6: Weekly snapshot of the leaderboard per org/location."""
    __tablename__ = "leaderboard_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    leaderboard_type: Mapped[str] = mapped_column(LeaderboardTypeEnum, nullable=False, default="weekly")
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    reset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(LeaderboardStatusEnum, nullable=False, default="open")

    entries: Mapped[list["LeaderboardEntry"]] = relationship("LeaderboardEntry", back_populates="snapshot", lazy="selectin")


class LeaderboardEntry(Base, TimestampMixin):
    """FR-6.5 / FR-6.7: Individual employee position in a leaderboard snapshot."""
    __tablename__ = "leaderboard_entries"
    __table_args__ = (UniqueConstraint("leaderboard_id", "employee_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    leaderboard_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("leaderboard_snapshots.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_tokens: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    # FR-6.7: Monday bonus tokens — absorbs employee_bonus_rewards
    bonus_tokens: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    bonus_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wallet_transaction_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("wallet_transactions.id", ondelete="SET NULL"), nullable=True)

    snapshot: Mapped["LeaderboardSnapshot"] = relationship("LeaderboardSnapshot", back_populates="entries", lazy="selectin")


class Redemption(Base, TimestampMixin):
    """FR-6.8: Token redemption — merges employee_redemptions + customer_redemptions.
    CHECK: employee_id IS NOT NULL OR customer_id IS NOT NULL (enforced at service layer).
    """
    __tablename__ = "redemptions"
    __table_args__ = (
        CheckConstraint(
            "employee_id IS NOT NULL OR customer_id IS NOT NULL",
            name="ck_redemptions_actor",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_type: Mapped[str] = mapped_column(RedemptionActorEnum, nullable=False)
    employee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=True)
    customer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("customers.id", ondelete="CASCADE"), nullable=True)
    reward_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rewards_catalog.id", ondelete="RESTRICT"), nullable=False)
    voucher_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("reward_vouchers.id", ondelete="SET NULL"), nullable=True)
    wallet_transaction_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("wallet_transactions.id", ondelete="SET NULL"), nullable=True)
    tokens_used: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(RedemptionStatusEnum, nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
