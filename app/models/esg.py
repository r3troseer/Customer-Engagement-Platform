"""
ESG & SDG models — owned by Sunny (FR4).

Simplified FR4 design:
- esg_categories is absorbed into EsgObjective.category
- sdg_goals + esg_objective_sdg_map are absorbed into EsgObjective.sdg_goal_numbers
- esg_metrics + esg_metric_values are merged into EsgMetricValue

Tables represented:
- esg_objectives
- esg_metric_values
- esg_activities
- esg_reports
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    ActivityStatusEnum,
    ActivityTypeEnum,
    EsgObjectiveStatusEnum,
    MetricSourceEnum,
    ReportStatusEnum,
    ReportTypeEnum,
)


class EsgObjective(Base, TimestampMixin):
    __tablename__ = "esg_objectives"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 'environmental' | 'social' | 'governance'
    # Absorbs esg_categories table
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Absorbs sdg_goals + esg_objective_sdg_map
    # Example: [12, 13]
    sdg_goal_numbers: Mapped[list[int] | None] = mapped_column(JSONB, nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    target_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(EsgObjectiveStatusEnum, nullable=False, default="draft", index=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    metric_values: Mapped[list["EsgMetricValue"]] = relationship(
        "EsgMetricValue",
        back_populates="objective",
        lazy="selectin",
    )

    activities: Mapped[list["EsgActivity"]] = relationship(
        "EsgActivity",
        back_populates="objective",
        lazy="selectin",
    )

    # Seed: Reduce Food Waste (org 1, Environmental, SDG 12 + 13)


class EsgMetricValue(Base, TimestampMixin):
    """
    Flexible ESG metric reading table.

    This merges the metric definition + metric readings into one table.
    """

    __tablename__ = "esg_metric_values"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "location_id",
            "metric_code",
            "value_date",
            name="uq_esg_metric_value_org_loc_code_date",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    esg_objective_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("esg_objectives.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Should align with objective category values:
    # 'environmental' | 'social' | 'governance'
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    value_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    source_type: Mapped[str] = mapped_column(MetricSourceEnum, nullable=False, default="manual", index=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    recorded_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    objective: Mapped["EsgObjective | None"] = relationship(
        "EsgObjective",
        back_populates="metric_values",
        lazy="selectin",
    )


class EsgActivity(Base, TimestampMixin):
    __tablename__ = "esg_activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    esg_objective_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("esg_objectives.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_type: Mapped[str] = mapped_column(ActivityTypeEnum, nullable=False, index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    impact_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(ActivityStatusEnum, nullable=False, default="planned", index=True)

    objective: Mapped["EsgObjective | None"] = relationship(
        "EsgObjective",
        back_populates="activities",
        lazy="selectin",
    )


class EsgReport(Base, TimestampMixin):
    __tablename__ = "esg_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("restaurant_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(ReportTypeEnum, nullable=False, default="esg", index=True)

    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    report_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    generated_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # draft | generated | exported | archived
    status: Mapped[str] = mapped_column(ReportStatusEnum, nullable=False, default="draft", index=True)