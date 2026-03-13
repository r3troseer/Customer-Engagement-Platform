"""
FR3 — Compliance Core

Request/response schemas for compliance frameworks, requirements,
organization/location compliance tracking, evidence, reviews,
documents, document versions, status history, alerts, and scores.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


# ── Compliance Frameworks ─────────────────────────────────────────────────────

class ComplianceFrameworkCreate(BaseModel):
    name: str
    framework_code: str
    framework_type: str
    description: str | None = None
    version: str | None = None
    status: str = "active"
    created_by: int | None = None


class ComplianceFrameworkUpdate(BaseModel):
    name: str | None = None
    framework_code: str | None = None
    framework_type: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    created_by: int | None = None


class ComplianceFrameworkOut(BaseModel):
    id: int
    name: str
    framework_code: str
    framework_type: str
    description: str | None
    version: str | None
    status: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Requirements ───────────────────────────────────────────────────

class ComplianceRequirementCreate(BaseModel):
    framework_id: int
    requirement_code: str
    title: str
    description: str | None = None
    category: str | None = None
    priority: str | None = "medium"
    is_mandatory: bool = True
    sort_order: int | None = None
    applies_to: str = "organization"
    status: str = "active"
    created_by: int | None = None


class ComplianceRequirementUpdate(BaseModel):
    framework_id: int | None = None
    requirement_code: str | None = None
    title: str | None = None
    description: str | None = None
    category: str | None = None
    priority: str | None = None
    is_mandatory: bool | None = None
    sort_order: int | None = None
    applies_to: str | None = None
    status: str | None = None
    created_by: int | None = None


class ComplianceRequirementOut(BaseModel):
    id: int
    framework_id: int
    requirement_code: str
    title: str
    description: str | None
    category: str | None
    priority: str | None
    is_mandatory: bool
    sort_order: int | None
    applies_to: str
    status: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Organization Compliance ───────────────────────────────────────────────────

class OrganizationComplianceCreate(BaseModel):
    organization_id: int
    requirement_id: int
    status: str = "not_started"
    due_date: date | None = None
    expiry_date: date | None = None
    assigned_to: int | None = None
    last_reviewed_at: datetime | None = None
    notes: str | None = None


class OrganizationComplianceUpdate(BaseModel):
    status: str | None = None
    due_date: date | None = None
    expiry_date: date | None = None
    assigned_to: int | None = None
    last_reviewed_at: datetime | None = None
    notes: str | None = None


class OrganizationComplianceOut(BaseModel):
    id: int
    organization_id: int
    requirement_id: int
    status: str
    due_date: date | None
    expiry_date: date | None
    assigned_to: int | None
    last_reviewed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Location Compliance ───────────────────────────────────────────────────────

class LocationComplianceCreate(BaseModel):
    organization_id: int
    location_id: int
    requirement_id: int
    status: str = "not_started"
    due_date: date | None = None
    expiry_date: date | None = None
    assigned_to: int | None = None
    last_reviewed_at: datetime | None = None
    notes: str | None = None


class LocationComplianceUpdate(BaseModel):
    status: str | None = None
    due_date: date | None = None
    expiry_date: date | None = None
    assigned_to: int | None = None
    last_reviewed_at: datetime | None = None
    notes: str | None = None


class LocationComplianceOut(BaseModel):
    id: int
    organization_id: int
    location_id: int
    requirement_id: int
    status: str
    due_date: date | None
    expiry_date: date | None
    assigned_to: int | None
    last_reviewed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Evidence ───────────────────────────────────────────────────────

class ComplianceEvidenceCreate(BaseModel):
    organization_compliance_id: int | None = None
    location_compliance_id: int | None = None
    document_id: int | None = None
    submitted_by: int | None = None
    title: str
    description: str | None = None
    evidence_type: str = "document"
    status: str = "submitted"
    submitted_at: datetime | None = None


class ComplianceEvidenceUpdate(BaseModel):
    document_id: int | None = None
    submitted_by: int | None = None
    title: str | None = None
    description: str | None = None
    evidence_type: str | None = None
    status: str | None = None
    submitted_at: datetime | None = None


class ComplianceEvidenceOut(BaseModel):
    id: int
    organization_compliance_id: int | None
    location_compliance_id: int | None
    document_id: int | None
    submitted_by: int | None
    title: str
    description: str | None
    evidence_type: str
    status: str
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Reviews ────────────────────────────────────────────────────────

class ComplianceReviewCreate(BaseModel):
    evidence_id: int
    reviewer_id: int
    review_status: str = "pending"
    feedback: str | None = None
    reviewed_at: datetime | None = None


class ComplianceReviewUpdate(BaseModel):
    review_status: str | None = None
    feedback: str | None = None
    reviewed_at: datetime | None = None


class ComplianceReviewOut(BaseModel):
    id: int
    evidence_id: int
    reviewer_id: int
    review_status: str
    feedback: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Documents ──────────────────────────────────────────────────────

class ComplianceDocumentCreate(BaseModel):
    evidence_id: int | None = None
    organization_id: int | None = None
    location_id: int | None = None
    requirement_id: int | None = None
    file_name: str
    file_path: str
    mime_type: str | None = None
    file_size: int | None = None
    document_type: str | None = None
    document_status: str = "active"
    uploaded_by: int | None = None
    notes: str | None = None


class ComplianceDocumentUpdate(BaseModel):
    evidence_id: int | None = None
    organization_id: int | None = None
    location_id: int | None = None
    requirement_id: int | None = None
    file_name: str | None = None
    file_path: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    document_type: str | None = None
    document_status: str | None = None
    uploaded_by: int | None = None
    notes: str | None = None


class ComplianceDocumentOut(BaseModel):
    id: int
    evidence_id: int | None
    organization_id: int | None
    location_id: int | None
    requirement_id: int | None
    file_name: str
    file_path: str
    mime_type: str | None
    file_size: int | None
    document_type: str | None
    document_status: str
    uploaded_by: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Document Versions ──────────────────────────────────────────────

class ComplianceDocumentVersionCreate(BaseModel):
    document_id: int
    version_number: int
    file_name: str
    file_path: str
    mime_type: str | None = None
    file_size: int | None = None
    changed_by: int | None = None
    change_notes: str | None = None


class ComplianceDocumentVersionUpdate(BaseModel):
    file_name: str | None = None
    file_path: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    changed_by: int | None = None
    change_notes: str | None = None


class ComplianceDocumentVersionOut(BaseModel):
    id: int
    document_id: int
    version_number: int
    file_name: str
    file_path: str
    mime_type: str | None
    file_size: int | None
    changed_by: int | None
    change_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Status History ─────────────────────────────────────────────────

class ComplianceStatusHistoryCreate(BaseModel):
    organization_compliance_id: int | None = None
    location_compliance_id: int | None = None
    old_status: str | None = None
    new_status: str
    changed_by: int | None = None
    change_reason: str | None = None


class ComplianceStatusHistoryOut(BaseModel):
    id: int
    organization_compliance_id: int | None
    location_compliance_id: int | None
    old_status: str | None
    new_status: str
    changed_by: int | None
    change_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Alerts ─────────────────────────────────────────────────────────

class ComplianceAlertCreate(BaseModel):
    organization_id: int | None = None
    location_id: int | None = None
    requirement_id: int | None = None
    document_id: int | None = None
    alert_type: str
    title: str
    message: str | None = None
    alert_date: datetime | None = None
    due_date: date | None = None
    severity: str = "medium"
    is_resolved: bool = False
    resolved_by: int | None = None
    resolved_at: datetime | None = None


class ComplianceAlertUpdate(BaseModel):
    organization_id: int | None = None
    location_id: int | None = None
    requirement_id: int | None = None
    document_id: int | None = None
    alert_type: str | None = None
    title: str | None = None
    message: str | None = None
    alert_date: datetime | None = None
    due_date: date | None = None
    severity: str | None = None
    is_resolved: bool | None = None
    resolved_by: int | None = None
    resolved_at: datetime | None = None


class ComplianceAlertResolveRequest(BaseModel):
    resolved_by: int


class ComplianceAlertOut(BaseModel):
    id: int
    organization_id: int | None
    location_id: int | None
    requirement_id: int | None
    document_id: int | None
    alert_type: str
    title: str
    message: str | None
    alert_date: datetime | None
    due_date: date | None
    severity: str
    is_resolved: bool
    resolved_by: int | None
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Compliance Scores ─────────────────────────────────────────────────────────

class ComplianceScoreCreate(BaseModel):
    organization_id: int | None = None
    location_id: int | None = None
    framework_id: int
    score: Decimal
    compliant_count: int = 0
    non_compliant_count: int = 0
    pending_count: int = 0
    expired_count: int = 0
    period_start: date
    period_end: date
    calculated_at: datetime | None = None


class ComplianceScoreUpdate(BaseModel):
    organization_id: int | None = None
    location_id: int | None = None
    framework_id: int | None = None
    score: Decimal | None = None
    compliant_count: int | None = None
    non_compliant_count: int | None = None
    pending_count: int | None = None
    expired_count: int | None = None
    period_start: date | None = None
    period_end: date | None = None
    calculated_at: datetime | None = None


class ComplianceScoreOut(BaseModel):
    id: int
    organization_id: int | None
    location_id: int | None
    framework_id: int
    score: Decimal
    compliant_count: int
    non_compliant_count: int
    pending_count: int
    expired_count: int
    period_start: date
    period_end: date
    calculated_at: datetime | None

    model_config = {"from_attributes": True}


# ── Nested / Detail Schemas ───────────────────────────────────────────────────

class ComplianceFrameworkDetailOut(ComplianceFrameworkOut):
    requirements: list[ComplianceRequirementOut] = []

    model_config = {"from_attributes": True}


class OrganizationComplianceDetailOut(OrganizationComplianceOut):
    evidence_items: list[ComplianceEvidenceOut] = []
    status_history: list[ComplianceStatusHistoryOut] = []

    model_config = {"from_attributes": True}


class LocationComplianceDetailOut(LocationComplianceOut):
    evidence_items: list[ComplianceEvidenceOut] = []
    status_history: list[ComplianceStatusHistoryOut] = []

    model_config = {"from_attributes": True}


class ComplianceEvidenceDetailOut(ComplianceEvidenceOut):
    reviews: list[ComplianceReviewOut] = []
    document: ComplianceDocumentOut | None = None

    model_config = {"from_attributes": True}


class ComplianceDocumentDetailOut(ComplianceDocumentOut):
    versions: list[ComplianceDocumentVersionOut] = []

    model_config = {"from_attributes": True}


# ── Summary / Dashboard Style Schemas ─────────────────────────────────────────

class ComplianceRequirementProgressOut(BaseModel):
    requirement_id: int
    requirement_title: str
    status: str
    due_date: date | None
    expiry_date: date | None
    assigned_to: int | None


class OrganizationComplianceSummaryOut(BaseModel):
    organization_id: int
    total_requirements: int
    not_started: int
    in_progress: int
    pending_verification: int
    compliant: int
    non_compliant: int
    expired: int
    generated_at: datetime


class LocationComplianceSummaryOut(BaseModel):
    location_id: int
    total_requirements: int
    not_started: int
    in_progress: int
    pending_verification: int
    compliant: int
    non_compliant: int
    expired: int
    generated_at: datetime


class ComplianceDashboardOut(BaseModel):
    organization_id: int | None = None
    location_id: int | None = None
    framework_id: int | None = None
    total_frameworks: int = 0
    total_requirements: int = 0
    total_alerts: int = 0
    unresolved_alerts: int = 0
    latest_score: Decimal | None = None
    score_trend: list[dict[str, Any]] = []
    generated_at: datetime