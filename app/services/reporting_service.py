"""
FR11 — Reporting & Analytics service layer.
Report data aggregation, template management, scheduled execution, and export.
"""
import csv
import io
import json
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.compliance import ComplianceFramework, ComplianceRequirement, OrganizationCompliance
from app.models.esg import EsgMetricValue, EsgObjective
from app.models.org import Employee
from app.models.reporting import (
    AnalyticsSnapshot,
    DashboardKpi,
    ReportExport,
    ReportRun,
    ReportTemplate,
)
from app.models.suppliers import Supplier, SupplierDocument, SupplierLocation
from app.models.tokens import Wallet, WalletTransaction
from app.models.workforce import LeaderboardEntry, LeaderboardSnapshot
from app.schemas.reporting import (
    AnalyticsSnapshotOut,
    ComplianceFrameworkResult,
    ComplianceReportOut,
    DashboardKpiOut,
    DashboardOut,
    EsgObjectiveResult,
    EsgReportOut,
    ExportOut,
    ExportRequest,
    ReportRunOut,
    SupplierReportOut,
    TemplateCreate,
    TemplateOut,
    TemplateUpdate,
)
from app.utils.file_storage import get_download_url, save_upload

logger = logging.getLogger(__name__)


# ── Pure helpers (no I/O) ─────────────────────────────────────────────────────

def _week_start(d: date) -> date:
    """Return the Monday of the ISO week containing date d."""
    return d - timedelta(days=d.weekday())


def _compliance_rate(compliant: int, total: int) -> float:
    """Return compliance percentage; 0.0 if total is zero."""
    if total == 0:
        return 0.0
    return round(compliant / total * 100, 2)


def _esg_overall_score(pairs: list[tuple[Decimal, Decimal]]) -> Decimal:
    """
    Compute mean (actual / target * 100) across objectives.
    Skips objectives where target is zero. Returns 0 if all skipped.
    pairs: [(actual, target), ...]
    """
    scores = []
    for actual, target in pairs:
        if target and target != 0:
            scores.append(actual / target * Decimal("100"))
    if not scores:
        return Decimal("0")
    mean = sum(scores) / len(scores)
    return mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ── ESG report ────────────────────────────────────────────────────────────────

async def get_esg_report(
    db: AsyncSession,
    org_id: int,
    start_date: date,
    end_date: date,
) -> EsgReportOut:
    """FR-11.1: Aggregate EsgMetricValue grouped by EsgObjective."""
    objectives_result = await db.execute(
        select(EsgObjective).where(
            EsgObjective.organization_id == org_id,
            EsgObjective.status != "archived",
        )
    )
    objectives = objectives_result.scalars().all()

    objective_results: list[EsgObjectiveResult] = []
    score_pairs: list[tuple[Decimal, Decimal]] = []

    for obj in objectives:
        actual_result = await db.execute(
            select(func.coalesce(func.sum(EsgMetricValue.metric_value), 0)).where(
                EsgMetricValue.esg_objective_id == obj.id,
                EsgMetricValue.value_date >= start_date,
                EsgMetricValue.value_date <= end_date,
            )
        )
        actual = Decimal(str(actual_result.scalar_one()))

        target = obj.target_value or Decimal("0")
        if target and target != 0:
            score_pairs.append((actual, target))

        objective_results.append(EsgObjectiveResult(
            name=obj.title,
            target=target,
            actual=actual,
            unit=obj.target_unit or "",
            status=obj.status,
        ))

    return EsgReportOut(
        period_start=start_date,
        period_end=end_date,
        organization_id=org_id,
        overall_score=_esg_overall_score(score_pairs),
        objectives=objective_results,
        generated_at=datetime.now(timezone.utc),
    )


# ── Compliance report ─────────────────────────────────────────────────────────

async def get_compliance_report(
    db: AsyncSession,
    org_id: int,
    start_date: date,
    end_date: date,
) -> ComplianceReportOut:
    """FR-11.2: Aggregate OrganizationCompliance statuses per framework."""
    # Load all frameworks
    fw_result = await db.execute(
        select(ComplianceFramework).where(ComplianceFramework.status == "active")
    )
    frameworks = fw_result.scalars().all()

    framework_results: list[ComplianceFrameworkResult] = []
    total_all = 0
    compliant_all = 0

    for fw in frameworks:
        # Count org compliance records for this framework's requirements
        count_result = await db.execute(
            select(func.count())
            .select_from(OrganizationCompliance)
            .join(ComplianceRequirement, OrganizationCompliance.requirement_id == ComplianceRequirement.id)
            .where(
                OrganizationCompliance.organization_id == org_id,
                ComplianceRequirement.framework_id == fw.id,
            )
        )
        total = count_result.scalar_one()

        compliant_result = await db.execute(
            select(func.count())
            .select_from(OrganizationCompliance)
            .join(ComplianceRequirement, OrganizationCompliance.requirement_id == ComplianceRequirement.id)
            .where(
                OrganizationCompliance.organization_id == org_id,
                ComplianceRequirement.framework_id == fw.id,
                OrganizationCompliance.status == "compliant",
            )
        )
        compliant = compliant_result.scalar_one()

        if total > 0:
            framework_results.append(ComplianceFrameworkResult(
                framework_name=fw.name,
                compliant=compliant,
                total=total,
                percentage=_compliance_rate(compliant, total),
            ))
            total_all += total
            compliant_all += compliant

    return ComplianceReportOut(
        period_start=start_date,
        period_end=end_date,
        organization_id=org_id,
        frameworks=framework_results,
        overall_compliance_rate=_compliance_rate(compliant_all, total_all),
        generated_at=datetime.now(timezone.utc),
    )


# ── Supplier report ───────────────────────────────────────────────────────────

async def get_supplier_report(db: AsyncSession, org_id: int) -> SupplierReportOut:
    """FR-11.3: Aggregate supplier document statuses and ESG scores."""
    # Get supplier_ids for this org
    loc_result = await db.execute(
        select(SupplierLocation.supplier_id).where(
            SupplierLocation.organization_id == org_id
        ).distinct()
    )
    supplier_ids = [r[0] for r in loc_result.all()]

    if not supplier_ids:
        return SupplierReportOut(
            organization_id=org_id,
            total_suppliers=0,
            active_suppliers=0,
            inactive_suppliers=0,
            suspended_suppliers=0,
            avg_esg_score=None,
            documents_pending_review=0,
            certified_suppliers=0,
            generated_at=datetime.now(timezone.utc),
        )

    def _count_status(rows, status):
        return sum(1 for r in rows if r.status == status)

    suppliers_result = await db.execute(
        select(Supplier).where(Supplier.id.in_(supplier_ids))
    )
    suppliers = suppliers_result.scalars().all()

    esg_scores = [s.esg_score for s in suppliers if s.esg_score is not None]
    avg_esg = (sum(esg_scores) / len(esg_scores)).quantize(Decimal("0.01")) if esg_scores else None

    pending_result = await db.execute(
        select(func.count()).where(
            SupplierDocument.supplier_id.in_(supplier_ids),
            SupplierDocument.review_status == "pending",
        )
    )
    docs_pending = pending_result.scalar_one()

    # Certified = at least one approved doc
    certified_result = await db.execute(
        select(SupplierDocument.supplier_id).where(
            SupplierDocument.supplier_id.in_(supplier_ids),
            SupplierDocument.review_status == "approved",
        ).distinct()
    )
    certified_count = len(certified_result.all())

    return SupplierReportOut(
        organization_id=org_id,
        total_suppliers=len(suppliers),
        active_suppliers=_count_status(suppliers, "active"),
        inactive_suppliers=_count_status(suppliers, "inactive"),
        suspended_suppliers=_count_status(suppliers, "suspended"),
        avg_esg_score=avg_esg,
        documents_pending_review=docs_pending,
        certified_suppliers=certified_count,
        generated_at=datetime.now(timezone.utc),
    )


# ── Dashboard KPIs ────────────────────────────────────────────────────────────

async def get_dashboard_kpis(db: AsyncSession, org_id: int) -> DashboardOut:
    """FR-11.4: Live-calculated KPIs for the admin dashboard."""
    today = date.today()
    monday = _week_start(today)
    now = datetime.now(timezone.utc)

    # 1. Active employees
    emp_result = await db.execute(
        select(func.count()).where(
            Employee.organization_id == org_id,
            Employee.employment_status == "active",
        )
    )
    active_employees = emp_result.scalar_one()

    # 2. Tokens issued this week — via Wallet → Employee → org
    tokens_result = await db.execute(
        select(func.coalesce(func.sum(WalletTransaction.amount), 0))
        .join(Wallet, WalletTransaction.wallet_id == Wallet.id)
        .join(Employee, Wallet.user_id == Employee.user_id)
        .where(
            Employee.organization_id == org_id,
            WalletTransaction.direction == "credit",
            WalletTransaction.transaction_date >= datetime.combine(monday, datetime.min.time()),
        )
    )
    tokens_this_week = Decimal(str(tokens_result.scalar_one()))

    # 3. Open compliance items
    open_statuses = ("not_started", "in_progress", "pending_verification", "non_compliant")
    compliance_result = await db.execute(
        select(func.count()).where(
            OrganizationCompliance.organization_id == org_id,
            OrganizationCompliance.status.in_(open_statuses),
        )
    )
    open_compliance = compliance_result.scalar_one()

    # 4. Supplier docs pending review (via SupplierLocation)
    loc_result = await db.execute(
        select(SupplierLocation.supplier_id).where(
            SupplierLocation.organization_id == org_id
        ).distinct()
    )
    supplier_ids = [r[0] for r in loc_result.all()]

    if supplier_ids:
        pending_result = await db.execute(
            select(func.count()).where(
                SupplierDocument.supplier_id.in_(supplier_ids),
                SupplierDocument.review_status == "pending",
            )
        )
        docs_pending = pending_result.scalar_one()
    else:
        docs_pending = 0

    # 5. Leaderboard entries this week
    snapshot_result = await db.execute(
        select(LeaderboardSnapshot.id).where(
            LeaderboardSnapshot.organization_id == org_id,
            LeaderboardSnapshot.status == "open",
        ).limit(1)
    )
    snapshot_id = snapshot_result.scalar_one_or_none()

    if snapshot_id:
        lb_result = await db.execute(
            select(func.count()).where(LeaderboardEntry.leaderboard_id == snapshot_id)
        )
        lb_entries = lb_result.scalar_one()
    else:
        lb_entries = 0

    period_end = today

    kpi_counter = 0

    def _kpi(code, name, value, unit) -> DashboardKpiOut:
        nonlocal kpi_counter
        kpi_counter += 1
        return DashboardKpiOut(
            id=kpi_counter,
            kpi_code=code,
            kpi_name=name,
            kpi_value=Decimal(str(value)),
            unit=unit,
            period_start=monday,
            period_end=period_end,
            calculated_at=now,
        )

    kpis = [
        _kpi("ACTIVE_EMPLOYEES", "Active Employees", active_employees, "employees"),
        _kpi("TOKENS_ISSUED_THIS_WEEK", "Tokens Issued This Week", tokens_this_week, "tokens"),
        _kpi("OPEN_COMPLIANCE_ITEMS", "Open Compliance Items", open_compliance, "items"),
        _kpi("SUPPLIER_DOCS_PENDING", "Supplier Docs Pending Review", docs_pending, "documents"),
        _kpi("LEADERBOARD_ENTRIES_THIS_WEEK", "Leaderboard Entries This Week", lb_entries, "entries"),
    ]

    return DashboardOut(
        organization_id=org_id,
        kpis=kpis,
        generated_at=now,
    )


# ── Analytics snapshots ───────────────────────────────────────────────────────

async def get_analytics_snapshots(
    db: AsyncSession,
    org_id: int,
    offset: int,
    limit: int,
) -> tuple[list[AnalyticsSnapshot], int]:
    base = select(AnalyticsSnapshot).where(AnalyticsSnapshot.organization_id == org_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(
        base.order_by(AnalyticsSnapshot.snapshot_date.desc()).offset(offset).limit(limit)
    )).scalars().all()
    return list(rows), total


# ── Report templates ──────────────────────────────────────────────────────────

async def list_templates(
    db: AsyncSession,
    org_id: int,
    offset: int,
    limit: int,
) -> tuple[list[ReportTemplate], int]:
    base = select(ReportTemplate).where(ReportTemplate.organization_id == org_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.order_by(ReportTemplate.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return list(rows), total


async def create_template(
    db: AsyncSession,
    data: TemplateCreate,
    org_id: int,
    creator_id: int,
) -> ReportTemplate:
    template = ReportTemplate(
        organization_id=org_id,
        created_by=creator_id,
        **data.model_dump(),
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def _get_template(db: AsyncSession, template_id: int, org_id: int) -> ReportTemplate:
    result = await db.execute(
        select(ReportTemplate).where(
            ReportTemplate.id == template_id,
            ReportTemplate.organization_id == org_id,
        )
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise NotFoundError("ReportTemplate", template_id)
    return template


async def update_template(
    db: AsyncSession,
    template_id: int,
    data: TemplateUpdate,
    org_id: int,
) -> ReportTemplate:
    template = await _get_template(db, template_id, org_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    await db.commit()
    await db.refresh(template)
    return template


# ── Report runs ───────────────────────────────────────────────────────────────

async def list_runs(
    db: AsyncSession,
    org_id: int,
    offset: int,
    limit: int,
) -> tuple[list[ReportRun], int]:
    base = select(ReportRun).where(ReportRun.organization_id == org_id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await db.execute(base.order_by(ReportRun.created_at.desc()).offset(offset).limit(limit))).scalars().all()
    return list(rows), total


async def get_run(db: AsyncSession, run_id: int, org_id: int) -> ReportRun:
    result = await db.execute(
        select(ReportRun).where(ReportRun.id == run_id, ReportRun.organization_id == org_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("ReportRun", run_id)
    return run


# ── Aggregator dispatch ───────────────────────────────────────────────────────

async def _run_aggregator(db: AsyncSession, report_type: str, org_id: int, params: dict) -> dict:
    """Call the appropriate aggregator and return serialisable dict."""
    today = date.today()
    start = date.fromisoformat(params.get("start_date", str(date(today.year, 1, 1))))
    end = date.fromisoformat(params.get("end_date", str(today)))

    if report_type == "esg":
        out = await get_esg_report(db, org_id, start, end)
    elif report_type == "compliance":
        out = await get_compliance_report(db, org_id, start, end)
    elif report_type == "supplier":
        out = await get_supplier_report(db, org_id)
    elif report_type == "dashboard":
        out = await get_dashboard_kpis(db, org_id)
    else:
        out = {}  # type: ignore[assignment]

    return out.model_dump(mode="json") if hasattr(out, "model_dump") else {}


def _serialize_to_csv(data: dict) -> str:
    """Best-effort flat CSV from a report dict."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write top-level scalar fields as header/value row
    scalars = {k: v for k, v in data.items() if not isinstance(v, (list, dict))}
    if scalars:
        writer.writerow(list(scalars.keys()))
        writer.writerow(list(scalars.values()))
        writer.writerow([])

    # Write first list field as a table
    for key, value in data.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            writer.writerow([key])
            writer.writerow(list(value[0].keys()))
            for row in value:
                writer.writerow(list(row.values()))
            break

    return output.getvalue()


# ── Execute report run ────────────────────────────────────────────────────────

async def execute_report_run(
    db: AsyncSession,
    template_id: int,
    org_id: int,
    generated_by: int,
) -> ReportRun:
    """FR-11.6: Run a report from a template and save the output file."""
    from app.services import notification_service

    template = await _get_template(db, template_id, org_id)
    now = datetime.now(timezone.utc)

    run = ReportRun(
        template_id=template.id,
        organization_id=org_id,
        report_name=template.template_name,
        report_type=template.report_type,
        parameters=template.template_config or {},
        run_status="running",
        generated_by=generated_by,
        started_at=now,
    )
    db.add(run)
    await db.flush()

    try:
        params = template.template_config or {}
        data = await _run_aggregator(db, template.report_type, org_id, params)
        content = json.dumps(data, default=str).encode()

        import io as _io
        from fastapi import UploadFile
        file_obj = _io.BytesIO(content)
        file_obj.filename = f"{template.report_type}_report.json"  # type: ignore[attr-defined]
        file_obj.content_type = "application/json"  # type: ignore[attr-defined]

        file_path = await save_upload(file_obj, folder=f"reports/{org_id}")

        run.file_path = file_path
        run.run_status = "completed"
        run.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.error("execute_report_run failed for template %s: %s", template_id, exc)
        run.run_status = "failed"
        run.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(run)

    if template.notify_on_complete and run.run_status == "completed":
        await notification_service.notify_report_ready(db, run)

    return run


# ── Trigger ad-hoc export ─────────────────────────────────────────────────────

async def trigger_export(
    db: AsyncSession,
    body: ExportRequest,
    org_id: int,
    generated_by: int,
) -> tuple[ReportRun, ReportExport]:
    """FR-11.5: Ad-hoc report generation and export."""
    now = datetime.now(timezone.utc)
    params = body.parameters or {}

    run = ReportRun(
        organization_id=org_id,
        location_id=body.location_id,
        report_name=f"{body.report_type.title()} Export",
        report_type=body.report_type,
        parameters=params,
        run_status="running",
        generated_by=generated_by,
        started_at=now,
    )
    db.add(run)
    await db.flush()

    export_format = body.export_format
    try:
        data = await _run_aggregator(db, body.report_type, org_id, params)

        if export_format == "csv":
            raw = _serialize_to_csv(data).encode()
            ext = "csv"
            content_type = "text/csv"
        else:
            # pdf: not yet implemented — fall back to JSON
            raw = json.dumps(data, default=str).encode()
            ext = "json"
            export_format = "json"
            content_type = "application/json"

        import io as _io
        file_obj = _io.BytesIO(raw)
        file_obj.filename = f"{body.report_type}_export.{ext}"  # type: ignore[attr-defined]
        file_obj.content_type = content_type  # type: ignore[attr-defined]

        file_path = await save_upload(file_obj, folder=f"exports/{org_id}")

        run.file_path = file_path
        run.run_status = "completed"
        run.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.error("trigger_export failed: %s", exc)
        run.run_status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)
        raise

    export = ReportExport(
        report_run_id=run.id,
        export_format=export_format,
        file_path=file_path,
        exported_by=generated_by,
        exported_at=now,
    )
    db.add(export)
    await db.commit()
    await db.refresh(run)
    await db.refresh(export)
    return run, export


async def get_export(
    db: AsyncSession,
    export_id: int,
    org_id: int,
) -> tuple[ReportExport, str]:
    """Load a ReportExport, verify org ownership, return (export, download_url)."""
    result = await db.execute(
        select(ReportExport)
        .join(ReportRun, ReportExport.report_run_id == ReportRun.id)
        .where(
            ReportExport.id == export_id,
            ReportRun.organization_id == org_id,
        )
    )
    export = result.scalar_one_or_none()
    if export is None:
        raise NotFoundError("ReportExport", export_id)

    url = get_download_url(export.file_path)
    return export, url


# ── Scheduled template helpers ────────────────────────────────────────────────

async def get_scheduled_templates(db: AsyncSession) -> list[ReportTemplate]:
    result = await db.execute(
        select(ReportTemplate).where(
            ReportTemplate.schedule_enabled.is_(True),
            ReportTemplate.status == "active",
        )
    )
    return list(result.scalars().all())
