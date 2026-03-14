"""
FR7 — Customer Engagement schemas (Omar).
"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    user_id: int
    preferred_location_id: int | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    city: str | None = None
    country: str | None = None
    allow_step_tracking: bool = False
    allow_marketing: bool = False
    sustainability_interests: str | None = None


class CustomerUpdate(BaseModel):
    preferred_location_id: int | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    city: str | None = None
    country: str | None = None
    allow_step_tracking: bool | None = None
    allow_marketing: bool | None = None
    sustainability_interests: str | None = None


class CustomerOut(BaseModel):
    id: int
    user_id: int
    preferred_location_id: int | None = None
    joined_at: datetime
    status: str
    date_of_birth: date | None = None
    gender: str | None = None
    city: str | None = None
    country: str | None = None
    allow_step_tracking: bool
    allow_marketing: bool
    sustainability_interests: str | None = None
    total_tokens_earned: Decimal
    total_tokens_donated: Decimal
    total_steps: int
    total_distance_km: Decimal
    total_co2_offset: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Customer Visit ────────────────────────────────────────────────────────────

class VisitCreate(BaseModel):
    customer_id: int
    location_id: int
    visit_datetime: datetime
    order_reference: str | None = None
    spend_amount: Decimal | None = None


class VisitOut(BaseModel):
    id: int
    customer_id: int
    location_id: int
    visit_datetime: datetime
    order_reference: str | None = None
    spend_amount: Decimal | None = None
    tokens_earned: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Mobility Log ──────────────────────────────────────────────────────────────

class MobilityLogCreate(BaseModel):
    customer_id: int
    activity_date: date
    step_count: int = 0
    distance_km: Decimal | None = None
    calories_burned: Decimal | None = None
    provider: str | None = None


class MobilityLogOut(BaseModel):
    id: int
    customer_id: int
    activity_date: date
    step_count: int
    distance_km: Decimal | None = None
    calories_burned: Decimal | None = None
    provider: str | None = None
    tokens_earned: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Challenge ─────────────────────────────────────────────────────────────────

class ChallengeCreate(BaseModel):
    organization_id: int | None = None
    title: str = Field(..., max_length=255)
    description: str | None = None
    challenge_type: str
    target_value: Decimal
    reward_tokens: Decimal
    start_date: date
    end_date: date


class ChallengeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class ChallengeOut(BaseModel):
    id: int
    organization_id: int | None = None
    title: str
    description: str | None = None
    challenge_type: str
    target_value: Decimal
    reward_tokens: Decimal
    start_date: date
    end_date: date
    status: str
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Challenge Participation ───────────────────────────────────────────────────

class JoinChallengeRequest(BaseModel):
    customer_id: int
    challenge_id: int


class ParticipationOut(BaseModel):
    id: int
    challenge_id: int
    customer_id: int
    joined_at: datetime
    progress_value: Decimal
    completed_at: datetime | None = None
    reward_granted: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProgressUpdate(BaseModel):
    progress_value: Decimal


# ── Impact summary ────────────────────────────────────────────────────────────

class CustomerImpactOut(BaseModel):
    customer_id: int
    total_tokens_earned: Decimal
    total_tokens_donated: Decimal
    total_steps: int
    total_distance_km: Decimal
    total_co2_offset: Decimal