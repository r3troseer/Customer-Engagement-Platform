"""
FR8 — Token Economy schemas (Omar).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Union

from pydantic import BaseModel, Field


# ── Wallet ────────────────────────────────────────────────────────────────────

class WalletCreate(BaseModel):
    user_id: int
    wallet_type: str


class WalletOut(BaseModel):
    id: int
    user_id: int
    wallet_type: str
    balance: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Wallet Transactions ──────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    wallet_id: int
    transaction_type: str
    direction: str
    amount: Decimal
    description: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None


class TransactionOut(BaseModel):
    id: int
    wallet_id: int
    transaction_type: str
    direction: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reference_type: str | None = None
    reference_id: int | None = None
    description: str | None = None
    transaction_date: datetime
    is_reversed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Token Rule Condition Models ───────────────────────────────────────────────

class VisitCondition(BaseModel):
    min_spend: Decimal | None = None
    location_id: int | None = None
    dining_type: str | None = None  # e.g. "dine_in", "takeaway"


class StepsCondition(BaseModel):
    min_steps: int
    period: Literal["daily", "weekly"] = "daily"


class EmployeeActivityCondition(BaseModel):
    activity_type: str  # e.g. "recycling", "energy_saving", "training"
    min_count: int = 1
    period: Literal["daily", "weekly", "monthly"] = "weekly"


class LeaderboardBonusCondition(BaseModel):
    top_n: int = 3
    period: Literal["weekly", "monthly"] = "weekly"


class ManualCondition(BaseModel):
    reason: str | None = None


class DonationBonusCondition(BaseModel):
    min_donation_tokens: Decimal | None = None
    cause_id: int | None = None


class OtherCondition(BaseModel):
    description: str | None = None


TokenRuleCondition = Union[
    VisitCondition,
    StepsCondition,
    EmployeeActivityCondition,
    LeaderboardBonusCondition,
    ManualCondition,
    DonationBonusCondition,
    OtherCondition,
]


# ── Reward Rule Condition Model ───────────────────────────────────────────────

class RewardRuleCondition(BaseModel):
    applicable_roles: list[str] | None = None
    min_wallet_balance: Decimal | None = None
    location_ids: list[int] | None = None
    valid_days: list[Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]] | None = None


# ── Token Rules ───────────────────────────────────────────────────────────────

class TokenRuleCreate(BaseModel):
    organization_id: int | None = None
    rule_name: str = Field(..., max_length=255)
    rule_type: str
    condition_details: TokenRuleCondition | None = None
    tokens_awarded: Decimal = Decimal("0")
    is_active: bool = True
    start_date: date | None = None
    end_date: date | None = None


class TokenRuleUpdate(BaseModel):
    rule_name: str | None = None
    condition_details: TokenRuleCondition | None = None
    tokens_awarded: Decimal | None = None
    is_active: bool | None = None
    start_date: date | None = None
    end_date: date | None = None


class TokenRuleOut(BaseModel):
    id: int
    organization_id: int | None = None
    rule_name: str
    rule_type: str
    condition_details: TokenRuleCondition | None = None
    tokens_awarded: Decimal
    is_active: bool
    start_date: date | None = None
    end_date: date | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Reward Rules ──────────────────────────────────────────────────────────────

class RewardRuleCreate(BaseModel):
    organization_id: int | None = None
    rule_name: str = Field(..., max_length=255)
    minimum_tokens_required: Decimal = Decimal("0")
    applicable_to: str
    conditions: RewardRuleCondition | None = None
    is_active: bool = True


class RewardRuleOut(BaseModel):
    id: int
    organization_id: int | None = None
    rule_name: str
    minimum_tokens_required: Decimal
    applicable_to: str
    conditions: RewardRuleCondition | None = None
    is_active: bool
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Rewards Catalog ───────────────────────────────────────────────────────────

class RewardCatalogCreate(BaseModel):
    organization_id: int | None = None
    title: str = Field(..., max_length=255)
    description: str | None = None
    reward_type: str
    token_cost: Decimal
    monetary_value: Decimal | None = None
    applicable_to: str
    start_date: date | None = None
    end_date: date | None = None
    quantity_available: int | None = None


class RewardCatalogUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    token_cost: Decimal | None = None
    quantity_available: int | None = None
    status: str | None = None


class RewardCatalogOut(BaseModel):
    id: int
    organization_id: int | None = None
    title: str
    description: str | None = None
    reward_type: str
    token_cost: Decimal
    monetary_value: Decimal | None = None
    applicable_to: str
    start_date: date | None = None
    end_date: date | None = None
    quantity_available: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Reward Voucher ────────────────────────────────────────────────────────────

class RedeemRequest(BaseModel):
    reward_id: int
    user_id: int


class VoucherOut(BaseModel):
    id: int
    reward_id: int
    user_id: int
    voucher_code: str
    issued_at: datetime
    expires_at: datetime | None = None
    redeemed_at: datetime | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}