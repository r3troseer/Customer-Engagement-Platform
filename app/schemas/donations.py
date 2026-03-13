"""
FR9 — Donations and ESG Offset
Schemas for donation causes, donations, conversions, impacts, and attributions.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


# ── Donation Causes ───────────────────────────────────────────────────────────

class DonationCauseCreate(BaseModel):
    organization_id: int | None = None
    cause_name: str
    description: str | None = None
    cause_type: str
    partner_name: str | None = None
    is_active: bool = True


class DonationCauseUpdate(BaseModel):
    cause_name: str | None = None
    description: str | None = None
    cause_type: str | None = None
    partner_name: str | None = None
    is_active: bool | None = None


class DonationCauseOut(BaseModel):
    id: int
    organization_id: int | None
    cause_name: str
    description: str | None
    cause_type: str
    partner_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Donations ─────────────────────────────────────────────────────────────────

class DonationCreate(BaseModel):
    user_id: int
    cause_id: int
    organization_id: int | None = None
    wallet_transaction_id: int | None = None
    token_amount: Decimal
    donation_date: datetime
    status: str = "pending"
    notes: str | None = None


class DonationUpdate(BaseModel):
    wallet_transaction_id: int | None = None
    token_amount: Decimal | None = None
    donation_date: datetime | None = None
    status: str | None = None
    notes: str | None = None


class DonationOut(BaseModel):
    id: int
    user_id: int
    cause_id: int
    organization_id: int | None
    wallet_transaction_id: int | None
    token_amount: Decimal
    donation_date: datetime
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Donation Conversions ──────────────────────────────────────────────────────

class DonationConversionCreate(BaseModel):
    donation_id: int
    token_amount: Decimal
    cash_value: Decimal
    conversion_rate: Decimal
    conversion_currency: str
    converted_at: datetime


class DonationConversionUpdate(BaseModel):
    token_amount: Decimal | None = None
    cash_value: Decimal | None = None
    conversion_rate: Decimal | None = None
    conversion_currency: str | None = None
    converted_at: datetime | None = None


class DonationConversionOut(BaseModel):
    id: int
    donation_id: int
    token_amount: Decimal
    cash_value: Decimal
    conversion_rate: Decimal
    conversion_currency: str
    converted_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Donation Impacts ──────────────────────────────────────────────────────────

class DonationImpactCreate(BaseModel):
    donation_id: int
    impact_type: str
    quantity: Decimal
    unit: str | None = None
    description: str | None = None
    recorded_at: datetime


class DonationImpactUpdate(BaseModel):
    impact_type: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    description: str | None = None
    recorded_at: datetime | None = None


class DonationImpactOut(BaseModel):
    id: int
    donation_id: int
    impact_type: str
    quantity: Decimal
    unit: str | None
    description: str | None
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Donation Attributions ─────────────────────────────────────────────────────

class DonationAttributionCreate(BaseModel):
    donation_id: int
    user_id: int
    organization_id: int | None = None
    attributed_tokens: Decimal
    attributed_impact_value: Decimal


class DonationAttributionUpdate(BaseModel):
    attributed_tokens: Decimal | None = None
    attributed_impact_value: Decimal | None = None


class DonationAttributionOut(BaseModel):
    id: int
    donation_id: int
    user_id: int
    organization_id: int | None
    attributed_tokens: Decimal
    attributed_impact_value: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Detail Schemas ────────────────────────────────────────────────────────────

class DonationDetailOut(DonationOut):
    conversion: DonationConversionOut | None = None
    impacts: list[DonationImpactOut] = []
    attributions: list[DonationAttributionOut] = []

    model_config = {"from_attributes": True}