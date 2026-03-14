"""
FR5 — Supplier Transparency & Compliance
Request/response schemas for supplier CRUD, documents, compliance, and public ESG view.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    supplier_name: str
    supplier_code: str
    company_registration_number: str | None = None
    tax_number: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postcode: str | None = None
    country: str | None = None
    supplier_type: str | None = None
    description: str | None = None
    is_public: bool = False
    public_summary: str | None = None
    esg_highlights: str | None = None


class SupplierUpdate(BaseModel):
    supplier_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postcode: str | None = None
    country: str | None = None
    supplier_type: str | None = None
    description: str | None = None
    status: str | None = None
    is_public: bool | None = None
    public_summary: str | None = None
    esg_highlights: str | None = None


class SupplierOut(BaseModel):
    id: int
    supplier_name: str
    supplier_code: str
    company_registration_number: str | None
    tax_number: str | None
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    website: str | None
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    state_region: str | None
    postcode: str | None
    country: str | None
    supplier_type: str | None
    description: str | None
    status: str
    esg_score: Decimal | None
    is_public: bool
    public_summary: str | None
    esg_highlights: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicSupplierOut(BaseModel):
    """FR-5.6: Limited fields for customer-facing public ESG view."""
    id: int
    supplier_name: str
    supplier_type: str | None
    country: str | None
    esg_score: Decimal | None
    public_summary: str | None
    esg_highlights: str | None

    model_config = {"from_attributes": True}


# ── Documents ────────────────────────────────────────────────────────────────

class SupplierDocumentOut(BaseModel):
    id: int
    supplier_id: int
    uploaded_by: int | None
    document_type: str
    title: str
    file_name: str
    file_path: str
    mime_type: str | None
    file_size: int | None
    issue_date: date | None
    expiry_date: date | None
    status: str
    notes: str | None
    reviewer_id: int | None
    review_status: str | None
    reviewed_at: datetime | None
    review_feedback: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentReviewIn(BaseModel):
    action: Literal["approved", "rejected", "needs_update"]
    feedback: str | None = None


# ── Compliance ────────────────────────────────────────────────────────────────

class ComplianceStatusOut(BaseModel):
    supplier_id: int
    supplier_name: str
    status: str
    esg_score: Decimal | None
    last_updated: datetime


class ComplianceUpdateIn(BaseModel):
    status: str
    esg_score: Decimal | None = None
    notes: str | None = None


class ComplianceHistoryEntry(BaseModel):
    changed_at: datetime
    previous_status: str | None
    new_status: str
    esg_score: Decimal | None
    changed_by: int | None
    notes: str | None


# ── Supplier Locations ────────────────────────────────────────────────────────

class SupplierLocationIn(BaseModel):
    organization_id: int | None = None
    location_id: int | None = None
    service_type: str | None = None
    relationship_type: str | None = None


class SupplierLocationOut(BaseModel):
    id: int
    supplier_id: int
    organization_id: int | None
    location_id: int | None
    service_type: str | None
    relationship_type: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
