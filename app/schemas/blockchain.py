"""
FR10 — Blockchain Verification schemas (Omar).
Includes Polygon integration for prototype.
"""
from datetime import datetime

from pydantic import BaseModel, Field


# ── Blockchain Transaction ────────────────────────────────────────────────────

class BlockchainTxCreate(BaseModel):
    network_name: str = Field(default="polygon-amoy", max_length=100)
    transaction_hash: str = Field(..., max_length=255)
    block_number: int | None = None
    wallet_address: str | None = None


class BlockchainTxOut(BaseModel):
    id: int
    network_name: str
    transaction_hash: str
    block_number: int | None = None
    wallet_address: str | None = None
    status: str
    submitted_at: datetime
    confirmed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Blockchain Record (anchor ESG/compliance data) ───────────────────────────

class BlockchainRecordCreate(BaseModel):
    organization_id: int | None = None
    location_id: int | None = None
    record_type: str
    reference_id: int
    reference_type: str = Field(..., max_length=100)


class BlockchainRecordUpdate(BaseModel):
    status: str | None = None
    is_public: bool | None = None
    public_title: str | None = None
    public_description: str | None = None


class BlockchainRecordOut(BaseModel):
    id: int
    organization_id: int | None = None
    location_id: int | None = None
    record_type: str
    reference_id: int
    reference_type: str
    blockchain_transaction_id: int | None = None
    anchored_at: datetime | None = None
    status: str
    created_by: int | None = None
    public_reference_code: str | None = None
    public_title: str | None = None
    public_description: str | None = None
    is_public: bool
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Blockchain Hash ───────────────────────────────────────────────────────────

class BlockchainHashCreate(BaseModel):
    blockchain_record_id: int
    hash_algorithm: str = "SHA-256"
    hash_value: str = Field(..., max_length=255)
    raw_data_reference: str | None = None


class BlockchainHashOut(BaseModel):
    id: int
    blockchain_record_id: int
    hash_algorithm: str
    hash_value: str
    raw_data_reference: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Public verification (FR-10.3) ────────────────────────────────────────────

class PublicVerificationOut(BaseModel):
    """Publicly accessible verification — no sensitive data."""
    public_reference_code: str
    public_title: str | None = None
    public_description: str | None = None
    record_type: str
    status: str
    anchored_at: datetime | None = None
    published_at: datetime | None = None
    hash_value: str | None = None
    transaction_hash: str | None = None
    network_name: str | None = None


# ── Anchor request (hash + submit to Polygon) ────────────────────────────────

class AnchorRequest(BaseModel):
    """Request to anchor a record's hash on Polygon."""
    record_id: int


class AnchorResponse(BaseModel):
    record_id: int
    hash_value: str
    transaction_hash: str
    network_name: str
    status: str
    message: str