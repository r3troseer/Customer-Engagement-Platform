"""
FR11 — Reporting & Analytics
Request/response schemas for ESG/compliance/supplier reports, dashboard KPIs,
export generation, and scheduled report templates.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel


# ── Named Reports ─────────────────────────────────────────────────────────────

class EsgObjectiveResult(BaseModel):
    name: str
    target: Decimal | None
    actual: Decimal | None
    unit: str | None
    status: str


class EsgReportOut(BaseModel):
    period_start: date
    period_end: date
    organization_id: int | None
    overall_score: Decimal | None
    objectives: list[EsgObjectiveResult]
    generated_at: datetime


class ComplianceFrameworkResult(BaseModel):
    framework_name: str
    compliant: int
    total: int
    percentage: float


class ComplianceReportOut(BaseModel):
    period_start: date
    period_end: date
    organization_id: int | None
    frameworks: list[ComplianceFrameworkResult]
    overall_compliance_rate: float
    generated_at: datetime


class SupplierReportOut(BaseModel):
    organization_id: int | None
    total_suppliers: int
    active_suppliers: int
    inactive_suppliers: int
    suspended_suppliers: int
    avg_esg_score: Decimal | None
    documents_pending_review: int
    certified_suppliers: int
    generated_at: datetime


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardKpiOut(BaseModel):
    id: int
    kpi_code: str
    kpi_name: str
    kpi_value: Decimal
    unit: str | None
    period_start: date
    period_end: date
    calculated_at: datetime

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    organization_id: int | None
    kpis: list[DashboardKpiOut]
    generated_at: datetime


class AnalyticsSnapshotOut(BaseModel):
    id: int
    organization_id: int | None
    location_id: int | None
    snapshot_type: str
    snapshot_date: date
    metrics_json: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Exports ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    report_type: Literal["esg", "compliance", "supplier", "customer", "employee", "custom"]
    export_format: Literal["pdf", "csv", "xlsx", "json"]
    parameters: dict[str, Any] | None = None
    location_id: int | None = None


class ExportOut(BaseModel):
    id: int
    report_run_id: int
    export_format: str
    file_path: str
    exported_by: int | None
    exported_at: datetime
    download_url: str | None

    model_config = {"from_attributes": True}


class ReportRunOut(BaseModel):
    id: int
    template_id: int | None
    organization_id: int | None
    location_id: int | None
    report_name: str
    report_type: str
    parameters: dict[str, Any] | None
    file_path: str | None
    run_status: str
    generated_by: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Templates ─────────────────────────────────────────────────────────────────

class TemplateCreate(BaseModel):
    template_name: str
    report_type: Literal["esg", "compliance", "supplier", "customer", "employee", "custom"]
    template_config: dict[str, Any] | None = None
    schedule_enabled: bool = False
    notify_on_complete: bool = False


class TemplateUpdate(BaseModel):
    template_name: str | None = None
    template_config: dict[str, Any] | None = None
    status: str | None = None
    schedule_enabled: bool | None = None
    notify_on_complete: bool | None = None


class TemplateOut(BaseModel):
    id: int
    organization_id: int | None
    template_name: str
    report_type: str
    template_config: dict[str, Any] | None
    status: str
    schedule_enabled: bool
    notify_on_complete: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
