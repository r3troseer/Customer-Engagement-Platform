"""
Reporting & analytics models — owned by Pius (FR11).
Tables: report_templates, report_runs, report_exports, dashboard_kpis,
        analytics_snapshots
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import ExportFormatEnum, ReportRunStatusEnum, ReportTypeEnum, SnapshotTypeEnum


class ReportTemplate(Base, TimestampMixin):
    """FR-11.6: Configurable scheduled report templates."""
    __tablename__ = "report_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(ReportTypeEnum, nullable=False)
    template_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # active | inactive
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_on_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class ReportRun(Base, TimestampMixin):
    """FR-11.6: Individual report execution record (manual or scheduled)."""
    __tablename__ = "report_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("report_templates.id", ondelete="SET NULL"), nullable=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(ReportTypeEnum, nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    run_status: Mapped[str] = mapped_column(ReportRunStatusEnum, nullable=False, default="queued")
    generated_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportExport(Base, TimestampMixin):
    """FR-11.5: Generated export files (PDF, CSV, XLSX)."""
    __tablename__ = "report_exports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("report_runs.id", ondelete="CASCADE"), nullable=False)
    export_format: Mapped[str] = mapped_column(ExportFormatEnum, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    exported_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    exported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DashboardKpi(Base, TimestampMixin):
    """FR-11.4: Pre-aggregated KPI values for the admin dashboard."""
    __tablename__ = "dashboard_kpis"
    __table_args__ = (UniqueConstraint("organization_id", "location_id", "kpi_code", "period_start", "period_end"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    kpi_name: Mapped[str] = mapped_column(String(255), nullable=False)
    kpi_code: Mapped[str] = mapped_column(String(100), nullable=False)
    kpi_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnalyticsSnapshot(Base, TimestampMixin):
    """FR-11.4: Point-in-time analytics blob per org/location."""
    __tablename__ = "analytics_snapshots"
    __table_args__ = (UniqueConstraint("organization_id", "location_id", "snapshot_type", "snapshot_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    snapshot_type: Mapped[str] = mapped_column(SnapshotTypeEnum, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
