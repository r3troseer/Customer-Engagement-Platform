"""
FR6 — Workforce Engagement & Incentive
Request/response schemas for work logs, wallet, leaderboard, and rewards.
"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# ── Work Logs ─────────────────────────────────────────────────────────────────

class WorkLogCreate(BaseModel):
    employee_id: int
    location_id: int
    work_date: date
    department: str | None = None
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    hours_worked: Decimal | None = None
    activity_notes: str | None = None
    sustainability_initiative: bool = False
    initiative_details: str | None = None


class WorkLogOut(BaseModel):
    id: int
    employee_id: int
    location_id: int
    department: str | None
    work_date: date
    check_in_time: datetime | None
    check_out_time: datetime | None
    hours_worked: Decimal | None
    activity_notes: str | None
    sustainability_initiative: bool
    initiative_details: str | None
    tokens_awarded: Decimal
    logged_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SustainabilityLogCreate(BaseModel):
    """FR-6.2: Convenience wrapper — sustainability_initiative is always True."""
    employee_id: int
    location_id: int
    work_date: date
    hours_worked: Decimal | None = None
    initiative_details: str


# ── Wallet ────────────────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    id: int
    transaction_type: str
    direction: str
    amount: Decimal
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletOut(BaseModel):
    wallet_id: int
    wallet_type: str
    balance: Decimal
    currency: str
    status: str
    recent_transactions: list[TransactionOut]


# ── Leaderboard ───────────────────────────────────────────────────────────────

class LeaderboardEntryOut(BaseModel):
    id: int
    rank_position: int | None
    employee_id: int
    employee_name: str
    score: Decimal
    total_tokens: Decimal
    bonus_tokens: Decimal
    bonus_paid: bool

    model_config = {"from_attributes": True}


class LeaderboardOut(BaseModel):
    snapshot_id: int
    organization_id: int
    leaderboard_type: str
    period_start: date
    period_end: date
    status: str
    entries: list[LeaderboardEntryOut]


# ── Rewards & Redemptions ─────────────────────────────────────────────────────

class RewardOut(BaseModel):
    id: int
    title: str
    description: str | None
    token_cost: Decimal
    reward_type: str
    applicable_to: str
    status: str

    model_config = {"from_attributes": True}


class RedemptionCreate(BaseModel):
    reward_id: int


class RedemptionOut(BaseModel):
    id: int
    actor_type: str
    employee_id: int | None
    reward_id: int
    tokens_used: Decimal
    status: str
    redeemed_at: datetime
    voucher_code: str | None
    notes: str | None

    model_config = {"from_attributes": True}
