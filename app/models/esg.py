"""
ESG & SDG models — owned by Sunny (FR4).
Tables: esg_objectives, esg_metric_values, esg_activities, esg_reports
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    ActivityStatusEnum,
    ActivityTypeEnum,
    EsgObjectiveStatusEnum,
    MetricSourceEnum,
    ReportTypeEnum,
)


class EsgObjective(Base, TimestampMixin):
    __tablename__ = "esg_objectives"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    # 'environmental' | 'social' | 'governance' — absorbs esg_categories table
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    # Absorbs sdg_goals + esg_objective_sdg_map; e.g. [12, 13]
    sdg_goal_numbers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    target_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(EsgObjectiveStatusEnum, nullable=False, default="draft")
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Seed: Reduce Food Waste (org 1, Environmental, SDG 12 + 13)


class EsgMetricValue(Base, TimestampMixin):
    """Merges esg_metrics definition + readings into one flexible table."""
    __tablename__ = "esg_metric_values"
    __table_args__ = (UniqueConstraint("organization_id", "location_id", "metric_code", "value_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    esg_objective_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("esg_objectives.id", ondelete="SET NULL"), nullable=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_code: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    value_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_type: Mapped[str] = mapped_column(MetricSourceEnum, nullable=False, default="manual")
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class EsgActivity(Base, TimestampMixin):
    __tablename__ = "esg_activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    esg_objective_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("esg_objectives.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_type: Mapped[str] = mapped_column(ActivityTypeEnum, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    impact_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(ActivityStatusEnum, nullable=False, default="planned")


class EsgReport(Base, TimestampMixin):
    __tablename__ = "esg_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    location_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(ReportTypeEnum, nullable=False, default="esg")
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    report_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # draft | generated | exported | archived
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
