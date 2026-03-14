"""
FR11 — Reporting & Analytics
Endpoints for ESG/compliance/supplier reports, dashboard KPIs,
export generation, and scheduled report templates.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter

from app.dependencies.auth import AdminUser
from app.dependencies.db import DBSession
from app.dependencies.pagination import Pagination
from app.schemas.common import PaginatedResponse
from app.schemas.reporting import (
    AnalyticsSnapshotOut,
    DashboardOut,
    EsgReportOut,
    ComplianceReportOut,
    ExportOut,
    ExportRequest,
    ReportRunOut,
    SupplierReportOut,
    TemplateCreate,
    TemplateOut,
    TemplateUpdate,
)
from app.services import reporting_service
from app.services.workforce_service import _get_employee

router = APIRouter()


# ── Org resolver ──────────────────────────────────────────────────────────────

async def _get_org_id(db: DBSession, user_id: int) -> int:
    employee = await _get_employee(db, user_id)
    return employee.organization_id


def _default_date_range() -> tuple[date, date]:
    today = date.today()
    return date(today.year, 1, 1), today


# ── FR-11.1 / 11.2 / 11.3: Named reports ────────────────────────────────────

@router.get("/esg", response_model=EsgReportOut, summary="FR-11.1 ESG performance report")
async def esg_report(
    db: DBSession,
    current_user: AdminUser,
    start_date: date | None = None,
    end_date: date | None = None,
):
    org_id = await _get_org_id(db, current_user["user_id"])
    s, e = start_date or date(date.today().year, 1, 1), end_date or date.today()
    return await reporting_service.get_esg_report(db, org_id, s, e)


@router.get("/compliance", response_model=ComplianceReportOut, summary="FR-11.2 Compliance report")
async def compliance_report(
    db: DBSession,
    current_user: AdminUser,
    start_date: date | None = None,
    end_date: date | None = None,
):
    org_id = await _get_org_id(db, current_user["user_id"])
    s, e = start_date or date(date.today().year, 1, 1), end_date or date.today()
    return await reporting_service.get_compliance_report(db, org_id, s, e)


@router.get("/suppliers", response_model=SupplierReportOut, summary="FR-11.3 Supplier transparency report")
async def supplier_report(db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    return await reporting_service.get_supplier_report(db, org_id)


# ── FR-11.4: Dashboard ───────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardOut, summary="FR-11.4 Real-time dashboard KPIs")
async def dashboard_kpis(db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    return await reporting_service.get_dashboard_kpis(db, org_id)


@router.get("/dashboard/snapshots", response_model=PaginatedResponse[AnalyticsSnapshotOut], summary="FR-11.4 Historical analytics snapshots")
async def analytics_snapshots(db: DBSession, current_user: AdminUser, pagination: Pagination):
    org_id = await _get_org_id(db, current_user["user_id"])
    snapshots, total = await reporting_service.get_analytics_snapshots(db, org_id, pagination.offset, pagination.page_size)
    return PaginatedResponse.create(
        items=[AnalyticsSnapshotOut.model_validate(s) for s in snapshots],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


# ── FR-11.5: Exports ─────────────────────────────────────────────────────────

@router.post("/export", response_model=ExportOut, status_code=202, summary="FR-11.5 Trigger PDF or CSV export")
async def trigger_export(body: ExportRequest, db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    run, export = await reporting_service.trigger_export(db, body, org_id, current_user["user_id"])
    _, url = await reporting_service.get_export(db, export.id, org_id)
    return ExportOut(
        id=export.id,
        report_run_id=export.report_run_id,
        export_format=export.export_format,
        file_path=export.file_path,
        exported_by=export.exported_by,
        exported_at=export.exported_at,
        download_url=url,
    )


@router.get("/exports/{export_id}", response_model=ExportOut, summary="FR-11.5 Get export details and download URL")
async def get_export(export_id: int, db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    export, url = await reporting_service.get_export(db, export_id, org_id)
    return ExportOut(
        id=export.id,
        report_run_id=export.report_run_id,
        export_format=export.export_format,
        file_path=export.file_path,
        exported_by=export.exported_by,
        exported_at=export.exported_at,
        download_url=url,
    )


# ── FR-11.6: Scheduled report templates ─────────────────────────────────────

@router.get("/templates", response_model=PaginatedResponse[TemplateOut], summary="FR-11.6 List report templates")
async def list_templates(db: DBSession, current_user: AdminUser, pagination: Pagination):
    org_id = await _get_org_id(db, current_user["user_id"])
    templates, total = await reporting_service.list_templates(db, org_id, pagination.offset, pagination.page_size)
    return PaginatedResponse.create(
        items=[TemplateOut.model_validate(t) for t in templates],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/templates", response_model=TemplateOut, status_code=201, summary="FR-11.6 Create scheduled report template")
async def create_template(body: TemplateCreate, db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    template = await reporting_service.create_template(db, body, org_id, current_user["user_id"])
    return TemplateOut.model_validate(template)


@router.patch("/templates/{template_id}", response_model=TemplateOut, summary="FR-11.6 Update / toggle schedule")
async def update_template(template_id: int, body: TemplateUpdate, db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    template = await reporting_service.update_template(db, template_id, body, org_id)
    return TemplateOut.model_validate(template)


@router.post("/templates/{template_id}/run", response_model=ReportRunOut, status_code=202, summary="FR-11.6 Manual report trigger")
async def run_template(template_id: int, db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    run = await reporting_service.execute_report_run(db, template_id, org_id, current_user["user_id"])
    return ReportRunOut.model_validate(run)


@router.get("/runs", response_model=PaginatedResponse[ReportRunOut], summary="FR-11.6 Report run history")
async def list_runs(db: DBSession, current_user: AdminUser, pagination: Pagination):
    org_id = await _get_org_id(db, current_user["user_id"])
    runs, total = await reporting_service.list_runs(db, org_id, pagination.offset, pagination.page_size)
    return PaginatedResponse.create(
        items=[ReportRunOut.model_validate(r) for r in runs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/runs/{run_id}", response_model=ReportRunOut, summary="FR-11.6 Get run detail and status")
async def get_run(run_id: int, db: DBSession, current_user: AdminUser):
    org_id = await _get_org_id(db, current_user["user_id"])
    run = await reporting_service.get_run(db, run_id, org_id)
    return ReportRunOut.model_validate(run)
